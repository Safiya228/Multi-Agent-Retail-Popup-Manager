# Safety and Governance

The prototype only produces recommendations. No agent or Supervisor action changes anything in the (mock) store, so "controls" below are about when a human must be pulled in.

## Human-in-the-loop controls

| Control | Status |
|---|---|
| Emergency restocking needs human approval | Implemented: `InventoryAgent` sets `requires_human_approval` on a critical stockout |
| Staffing changes need human approval | Implemented: `LaborAgent` sets the flag when it recommends more staff |
| Price changes need human approval | Implemented: `PricingAgent` sets the flag when it proposes a discount |
| Any critical-severity alert escalates | Implemented in `SupervisorAgent` |
| Two or more high-severity alerts escalate | Implemented in `SupervisorAgent` |
| Any message with confidence below 0.70 escalates | Implemented in `SupervisorAgent` |
| A human approves or rejects the escalation | Planned: the prototype stops at "escalate" |

## Audit logs

Each run appends one JSON line to `audit_log.jsonl` (see `examples/sample_audit_log.jsonl`) with:
- the input scenario
- every agent message (severity, confidence, recommendation, evidence, approval flag)
- the Supervisor's decision and the list of rules that triggered it

Planned: human approval status and the final action taken (needs a human step and real actions).

## Failure and abuse cases

| Failure | Mitigation | Status |
|---|---|---|
| Agent overreacts to noisy data | Confidence threshold, human review | Implemented (threshold) |
| Pricing agent discounts during high demand | Discounts need approval; pricing only discounts when expected customers are low | Implemented |
| Inventory agent misses a stockout | Threshold in `agents.py`; scenario tests for known stockouts | Partly: only pizza dough is monitored |
| Supervisor escalates too often | Escalation reasons are logged so thresholds can be tuned | Partly: no override tracking yet |
| Correlated alerts inflate escalation | Root-cause deduplication | Planned |
| Human ignores a critical alert | Alert is always logged | Partly: no acknowledgement tracking |
| Feedback loop: discount, demand spike, stockout | Pricing is advisory only | Implemented |

## Rollback

Planned for a version that takes real actions: cancel unconfirmed supplier orders, revert price changes, disable an agent that keeps producing unsafe recommendations, restore previous operating rules.
