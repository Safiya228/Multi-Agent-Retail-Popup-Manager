import argparse
import json
from dataclasses import asdict
from datetime import datetime, timezone

from agents import (
    CustomerExperienceAgent,
    DemandAgent,
    InventoryAgent,
    LaborAgent,
    PricingAgent,
)
from simulation import SCENARIOS, get_mock_scenario
from supervisor import SupervisorAgent


def build_agents():
    return [
        DemandAgent(),
        InventoryAgent(),
        LaborAgent(),
        PricingAgent(),
        CustomerExperienceAgent(),
    ]


def run_cycle(state):
    """One decision cycle: every agent reads the state, then the Supervisor decides."""
    messages = [agent.run(state) for agent in build_agents()]
    decision = SupervisorAgent().run(messages)
    return messages, decision


def write_audit_log(path, scenario_name, state, messages, decision):
    """Append one JSON line per cycle: input, every agent message, and the decision."""
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "scenario": scenario_name,
        "state": state,
        "messages": [asdict(m) for m in messages],
        "decision": {
            "decision": decision["decision"],
            "reasons": decision["reasons"],
            "human_approval_required": decision["human_approval_required"],
        },
    }
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def print_cycle(name, state, messages, decision):
    print(f"=== SCENARIO: {name} ===")
    print(state)

    print("\n=== AGENT MESSAGES ===")
    for m in messages:
        print("\n-------------------")
        print(f"Agent: {m.agent_name}")
        print(f"Issue: {m.issue_type}")
        print(f"Severity: {m.severity}")
        print(f"Recommendation: {m.recommendation}")
        print(f"Confidence: {m.confidence}")

    print("\n=== SUPERVISOR DECISION ===")
    print(f"Decision: {decision['decision']}")
    print(f"Reason: {decision['reason']}")
    print(f"Human Approval Required: {decision['human_approval_required']}")

    print("\n=== AUDIT LOG ===")
    for m in messages:
        print(f"[{m.severity.upper()}] {m.agent_name} -> {m.issue_type} | {m.recommendation}")

    print("\nFinal Recommended Actions:")
    for a in decision["final_actions"]:
        print(f"- {a['from']}: {a['recommendation']} ({a['severity']})")


def main():
    parser = argparse.ArgumentParser(description="Multi-agent retail pop-up manager (prototype)")
    parser.add_argument("--scenario", default="friday_rush", choices=sorted(SCENARIOS),
                        help="scenario to run (default: friday_rush)")
    parser.add_argument("--all", action="store_true", help="run every scenario")
    parser.add_argument("--list", action="store_true", help="list scenarios and exit")
    parser.add_argument("--audit-log", default="audit_log.jsonl",
                        help="JSON-lines file to append the audit record to")
    args = parser.parse_args()

    if args.list:
        print("\n".join(sorted(SCENARIOS)))
        return

    names = sorted(SCENARIOS) if args.all else [args.scenario]
    for i, name in enumerate(names):
        if i:
            print("\n" + "=" * 60 + "\n")
        state = get_mock_scenario(name)
        messages, decision = run_cycle(state)
        print_cycle(name, state, messages, decision)
        write_audit_log(args.audit_log, name, state, messages, decision)

    print(f"\nAudit record(s) appended to {args.audit_log}")


if __name__ == "__main__":
    main()
