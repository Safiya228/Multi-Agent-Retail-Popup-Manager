LOW_CONFIDENCE_THRESHOLD = 0.70
HIGH_ALERTS_BEFORE_ESCALATION = 2


def _names(messages):
    return ", ".join(m.agent_name for m in messages)


class SupervisorAgent:
    """Aggregates agent messages and decides: auto-recommend or escalate to a human.

    Escalation rules (any one is enough):
      1. at least one critical-severity message
      2. two or more high-severity messages
      3. any message that requests human approval
      4. any message with confidence below LOW_CONFIDENCE_THRESHOLD
    The Supervisor does not take actions or resolve conflicts between agents;
    it only routes.
    """

    def run(self, messages):
        critical = [m for m in messages if m.severity == "critical"]
        high = [m for m in messages if m.severity == "high"]
        approval = [m for m in messages if m.requires_human_approval]
        low_conf = [m for m in messages if m.confidence < LOW_CONFIDENCE_THRESHOLD]

        reasons = []
        if critical:
            reasons.append(f"critical alert from {_names(critical)}")
        if len(high) >= HIGH_ALERTS_BEFORE_ESCALATION:
            reasons.append(f"{len(high)} high-severity alerts ({_names(high)})")
        if approval:
            reasons.append(f"human approval requested by {_names(approval)}")
        if low_conf:
            reasons.append(
                f"confidence below {LOW_CONFIDENCE_THRESHOLD:.2f} from {_names(low_conf)}"
            )

        final_actions = [
            {
                "from": m.agent_name,
                "issue": m.issue_type,
                "recommendation": m.recommendation,
                "severity": m.severity,
            }
            for m in messages
        ]

        if reasons:
            decision = "ESCALATE_TO_HUMAN"
            reason = "; ".join(reasons)
        else:
            decision = "AUTO_RECOMMEND"
            reason = "No escalation rule triggered."

        return {
            "decision": decision,
            "reason": reason,
            "reasons": reasons,
            "final_actions": final_actions,
            "human_approval_required": decision == "ESCALATE_TO_HUMAN",
        }
