"""Scenario tests for the multi-agent pop-up manager. Run: python -m unittest -v"""
import copy
import json
import os
import tempfile
import unittest
from dataclasses import asdict

from main import run_cycle, write_audit_log
from schemas import AgentMessage
from simulation import SCENARIOS, get_mock_scenario
from supervisor import SupervisorAgent

ESCALATE, AUTO = "ESCALATE_TO_HUMAN", "AUTO_RECOMMEND"


def run(name):
    messages, decision = run_cycle(get_mock_scenario(name))
    return {m.agent_name: m for m in messages}, decision


class ScenarioTests(unittest.TestCase):
    def test_friday_rush_escalates_on_every_rule_but_confidence(self):
        msgs, d = run("friday_rush")
        self.assertEqual(d["decision"], ESCALATE)
        self.assertEqual(msgs["DemandAgent"].severity, "high")
        self.assertEqual(msgs["InventoryAgent"].severity, "critical")
        self.assertEqual(msgs["LaborAgent"].severity, "high")
        self.assertEqual(msgs["PricingAgent"].severity, "low")
        self.assertEqual(msgs["CustomerExperienceAgent"].severity, "high")
        self.assertEqual(len(d["reasons"]), 3)  # critical, 2+ high, approval

    def test_normal_day_is_auto_recommended(self):
        _, d = run("normal_day")
        self.assertEqual(d["decision"], AUTO)
        self.assertFalse(d["human_approval_required"])
        self.assertEqual(d["reasons"], [])

    def test_high_demand_low_inventory_escalates(self):
        msgs, d = run("high_demand_low_inventory")
        self.assertEqual(d["decision"], ESCALATE)
        self.assertEqual(msgs["DemandAgent"].severity, "high")
        self.assertEqual(msgs["InventoryAgent"].severity, "critical")

    def test_low_demand_high_inventory_escalates_because_discount_needs_approval(self):
        msgs, d = run("low_demand_high_inventory")
        self.assertEqual(d["decision"], ESCALATE)
        self.assertTrue(msgs["PricingAgent"].requires_human_approval)
        self.assertIn("discount", msgs["PricingAgent"].recommendation.lower())
        # Nothing critical or high here: approval is the only trigger.
        self.assertEqual(len(d["reasons"]), 1)
        self.assertIn("human approval requested by PricingAgent", d["reasons"][0])

    def test_high_wait_low_staffing_escalates(self):
        msgs, d = run("high_wait_low_staffing")
        self.assertEqual(d["decision"], ESCALATE)
        self.assertEqual(msgs["LaborAgent"].severity, "high")
        self.assertEqual(msgs["CustomerExperienceAgent"].severity, "high")
        self.assertTrue(any("2 high-severity alerts" in r for r in d["reasons"]))

    def test_conflicting_pricing_and_demand_escalates(self):
        # The agents disagree (demand says prepare for a rush, pricing says discount).
        # The Supervisor has no explicit conflict detection: it escalates only because
        # the discount requires human approval.
        msgs, d = run("conflicting_pricing_and_demand")
        self.assertEqual(msgs["DemandAgent"].severity, "high")
        self.assertIn("discount", msgs["PricingAgent"].recommendation.lower())
        self.assertEqual(d["decision"], ESCALATE)
        self.assertEqual(len(d["reasons"]), 1)

    def test_critical_stockout_escalates(self):
        msgs, d = run("critical_stockout")
        self.assertEqual(msgs["InventoryAgent"].severity, "critical")
        self.assertEqual(d["decision"], ESCALATE)
        self.assertTrue(any(r.startswith("critical alert") for r in d["reasons"]))


class SupervisorRuleTests(unittest.TestCase):
    @staticmethod
    def msg(severity="low", confidence=0.9, approval=False, name="TestAgent"):
        return AgentMessage(name, "test", severity, "do something", confidence, approval, {})

    def test_low_confidence_alone_escalates(self):
        d = SupervisorAgent().run([self.msg(confidence=0.60)])
        self.assertEqual(d["decision"], ESCALATE)
        self.assertIn("confidence below 0.70", d["reason"])

    def test_confidence_exactly_at_threshold_does_not_escalate(self):
        self.assertEqual(SupervisorAgent().run([self.msg(confidence=0.70)])["decision"], AUTO)

    def test_single_high_alert_does_not_escalate(self):
        self.assertEqual(SupervisorAgent().run([self.msg(severity="high")])["decision"], AUTO)

    def test_two_high_alerts_escalate(self):
        d = SupervisorAgent().run([self.msg("high", name="A"), self.msg("high", name="B")])
        self.assertEqual(d["decision"], ESCALATE)

    def test_critical_alone_escalates(self):
        self.assertEqual(SupervisorAgent().run([self.msg("critical")])["decision"], ESCALATE)


class SchemaAndLoggingTests(unittest.TestCase):
    def test_every_message_in_every_scenario_is_valid(self):
        for name in SCENARIOS:
            messages, _ = run_cycle(get_mock_scenario(name))
            self.assertEqual(len(messages), 5, name)
            for m in messages:
                self.assertIn(m.severity, ("low", "medium", "high", "critical"), name)
                self.assertTrue(0.0 <= m.confidence <= 1.0, name)
                self.assertIsInstance(m.requires_human_approval, bool, name)

    def test_invalid_messages_are_rejected(self):
        with self.assertRaises(ValueError):
            AgentMessage("A", "t", "urgent", "r", 0.9, False, {})
        with self.assertRaises(ValueError):
            AgentMessage("A", "t", "low", "r", 1.5, False, {})

    def test_agents_do_not_modify_the_blackboard(self):
        for name in SCENARIOS:
            state = get_mock_scenario(name)
            before = copy.deepcopy(state)
            run_cycle(state)
            self.assertEqual(state, before, name)

    def test_audit_log_is_valid_json_lines(self):
        state = get_mock_scenario("friday_rush")
        messages, decision = run_cycle(state)
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "audit.jsonl")
            write_audit_log(path, "friday_rush", state, messages, decision)
            write_audit_log(path, "friday_rush", state, messages, decision)
            with open(path, encoding="utf-8") as f:
                lines = f.read().splitlines()
        self.assertEqual(len(lines), 2)
        record = json.loads(lines[0])
        self.assertEqual(record["scenario"], "friday_rush")
        self.assertEqual(len(record["messages"]), 5)
        self.assertEqual(record["messages"][0], asdict(messages[0]))
        self.assertEqual(record["decision"]["decision"], ESCALATE)


if __name__ == "__main__":
    unittest.main()
