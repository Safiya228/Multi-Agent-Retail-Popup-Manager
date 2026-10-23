# Evaluation

## Implemented: scenario tests

`python -m unittest -v` runs 16 tests (standard library only). Seven scenarios are defined in `simulation.py`; each test checks the agents' messages and the Supervisor's decision.

| Scenario | What it checks | Expected decision | Why |
|---|---|---|---|
| `friday_rush` | Original demo: rain, event, 2 staff, 18 min wait | Escalate | Critical stockout + 3 high alerts + approval requests |
| `normal_day` | Everything within limits | Auto-recommend | No escalation rule fires |
| `high_demand_low_inventory` | High demand + low dough | Escalate | Critical stockout alert |
| `low_demand_high_inventory` | Excess drinks, few customers | Escalate | Pricing proposes a discount, which needs approval |
| `high_wait_low_staffing` | Long waits, 2 staff | Escalate | 2 high alerts + staffing change needs approval |
| `conflicting_pricing_and_demand` | Event-driven demand vs. discount proposal | Escalate | Discount needs approval (no explicit conflict detection) |
| `critical_stockout` | Dough nearly out on a normal day | Escalate | Critical alert |

Supervisor rule tests: a single high alert does not escalate, two do, a critical alert alone does, confidence below 0.70 escalates, confidence of exactly 0.70 does not.

Other checks: message schema validity across all scenarios (invalid severity or confidence is rejected), agents never modify the shared state, and the audit log is valid JSON lines.

## Planned: not implemented

These need real or simulated outcome data, which the prototype does not have.

**Agent-level**
- Demand classification accuracy against actual foot traffic
- Stockout precision and recall
- Staffing recommendation correctness against actual wait times
- Unnecessary discount rate
- Wait-time risk detection rate

**Interaction-level**
- Conflict detection rate (needs explicit conflict detection first)
- Escalation correctness and unnecessary escalation rate

**System-level**
- Stockout frequency, average wait time, revenue impact, inventory waste, complaint rate

**Human-level**
- Override rate, manager trust score, explanation clarity, time saved per decision
