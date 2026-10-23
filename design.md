# Design notes

Background and design rationale for the multi-agent pop-up manager. For how to run it, the escalation rules and what is implemented, see the [README](../README.md).

---

## System Brief

### Problem Statement

Retail pop-up stores operate in highly dynamic environments where demand fluctuates rapidly due to weather, local events, staffing availability, and inventory constraints.

A single decision-making system struggles to balance competing objectives simultaneously:

- Preventing stockouts
- Maintaining customer satisfaction
- Managing staffing levels
- Protecting profit margins
- Responding quickly to operational disruptions

This project demonstrates how a Multi-Agent System can distribute these responsibilities among specialized agents while coordinating decisions through a supervisor layer.

### Stakeholders

**Primary:** Pop-up Store Manager, Store Employees, Customers, Business Owner

**Secondary:** Inventory Suppliers, Operations Team, Compliance and Governance Reviewers

### Failure Stakes

| Failure | Impact |
|---|---|
| Inventory stockout | Lost revenue, customer churn |
| Excess inventory waste | Margin loss |
| Long wait times | Customer dissatisfaction |
| Poor staffing decisions | Service breakdown |
| Unnecessary discounts | Revenue leak |
| Unsafe autonomous decisions | Legal, reputational, financial risk |

## Why Multi-Agent Systems?

A single agent managing all retail decisions would face an extremely large, coupled decision space. A pricing decision affects demand, which affects inventory, which affects staffing — a single agent would need to reason about all of these simultaneously without any modularity or fault isolation.

A Multi-Agent System is more appropriate here because:

- **Specialization:** Each domain (demand, inventory, labor, pricing, CX) has distinct inputs, logic, and failure modes. Separate agents are easier to test, debug, and explain.
- **Fault isolation:** A bug in the Pricing Agent does not corrupt the Inventory Agent's reasoning.
- **Independent evaluation:** All five agents evaluate the same scenario without depending on each other's output before the Supervisor synthesizes their recommendations. (The prototype runs them one after another in a loop, but they could run concurrently.)
- **Transparent explainability:** Human managers can see which agent raised which alert, rather than receiving an opaque combined output.
- **Scalability:** New agents (e.g., a supplier agent or weather agent) can be added without redesigning existing ones.

A single agent could handle this use case, but it would sacrifice all of the above properties with no meaningful benefit.

## Agent Roster

| Agent | Responsibility | Key Inputs | Output | Permissions |
|---|---|---|---|---|
| DemandAgent | Forecast customer demand | Time, nearby-event flag (weather is recorded as evidence only) | Demand forecast + severity | Read blackboard |
| InventoryAgent | Detect stockout risk (pizza dough only) | Pizza dough stock, expected customers | Restock alerts | Read blackboard, flag for human approval |
| LaborAgent | Monitor staffing adequacy | Wait times, staff count | Staffing recommendations | Read blackboard, flag for human approval |
| PricingAgent | Recommend pricing actions | Drink stock, expected customers | Discount or hold recommendations | Read blackboard, flag for human approval |
| CustomerExperienceAgent | Monitor service quality | Wait times, complaints | CX risk alerts | Read blackboard |
| SupervisorAgent | Coordinate all recommendations | All agent messages | Final decision or escalation | Write to audit log, trigger human escalation |

All agents are **read-only** with respect to the operational environment. No agent can take direct action — all recommendations pass through the Supervisor first.

## Coordination Mechanism

The chosen mechanism is **Supervisor-Based Coordination with a Shared Blackboard**.

### Why not other mechanisms?

| Mechanism | Why it was rejected |
|---|---|
| **Market / Auction** | Agents bidding on decisions adds complexity without benefit when there is no scarce resource to allocate between them |
| **Contract Net** | Best suited for task assignment across interchangeable agents; here each agent has a fixed role, so negotiation adds overhead with no gain |
| **Consensus / Voting** | Requires agents to have comparable authority; a CX alert and an inventory alert are incommensurable — a Supervisor is needed to weigh them |
| **Pure Blackboard** | Agents would need to self-coordinate after reading shared state, creating ambiguity about who acts on conflicting signals |

**Supervisor coordination fits because:**
- The retail environment has clear authority hierarchy (manager overrides agents)
- Signals from different agents (inventory vs. pricing vs. CX) are incommensurable, so one central point decides when to hand off to a human. The prototype does not yet detect or resolve conflicts itself; see the README's limitations
- Safety requires a single chokepoint before any action is recommended
- Human escalation needs a clear trigger, not a distributed vote

The Blackboard component adds value by decoupling agents from each other — the Inventory Agent does not need to call the Demand Agent directly; it reads from shared state. This allows agents to be added, replaced, or disabled without breaking inter-agent dependencies.

## Emergent Behavior

### Expected Emergent Behavior

**Compounded risk detection:** No single agent sees the full picture. When several agents raise high or critical alerts in the same cycle (as in the Friday rush demo: demand, stockout, staffing and wait-time alerts), the Supervisor's escalation rules fire on the combination, including alerts that would not have needed approval on their own.

**Earlier escalation:** Because agents operate in parallel and the Supervisor aggregates, the system can escalate based on a pattern of moderate signals (e.g., two "high" messages) rather than waiting for a single catastrophic signal.

### Unwanted Emergent Behavior

**Over-escalation cascade:** In a high-demand scenario, the Demand Agent, Inventory Agent, Labor Agent, and CX Agent may all independently fire high or critical alerts for symptoms of the same root cause (high demand). The Supervisor escalates based on alert count, so correlated alerts can make the system appear more critical than it is. In the Friday rush demo, four of the five alerts trace back to the same surge. *Mitigation: the Supervisor could be extended to deduplicate alerts by root cause.*

**Pricing-demand feedback loop:** If a future version allows the Pricing Agent to actually lower prices, reduced prices increase customer volume, which worsens the inventory stockout and staffing shortage that triggered the discount in the first place. This circular dependency is not present in the current prototype (pricing is advisory only) but is a real risk in a live system. *Mitigation: pricing changes require human approval before taking effect.*

**Conflicting local optima:** The Inventory Agent wants to restock (spend money); the Pricing Agent may simultaneously want to avoid discounts (protect margin). These are locally rational but globally contradictory. The prototype has no explicit conflict detection: a case like this escalates only when a rule fires (a critical alert or a message that requires approval, as pricing discounts do). Detecting conflicting recommendations explicitly is future work.

## Incentive Analysis

Each agent optimizes a local objective function:

| Agent | Local Objective | Global Tension |
|---|---|---|
| DemandAgent | Accurate demand forecasting | May trigger false urgency from other agents |
| InventoryAgent | Minimize stockout risk | May recommend costly restocking unnecessarily |
| LaborAgent | Minimize wait times | May over-staff, raising labor costs |
| PricingAgent | Protect revenue margin | May conflict with CX agent's push to reduce friction |
| CustomerExperienceAgent | Maximize satisfaction | May conflict with cost-control goals |

**Global objective:** Maximize operational efficiency while maintaining customer satisfaction and minimizing financial and reputational risk.

The Supervisor Agent acts as the mechanism that prevents any single agent's local objective from dominating system behavior. Because the Supervisor does not have its own reward function — it is purely coordinative — it does not introduce competing incentives at the coordination layer.

In a production system, a risk to watch is agents being tuned to reduce their own false negative rate (e.g., the Inventory Agent becoming hypersensitive to avoid stockouts) at the cost of spamming the Supervisor with low-confidence alerts.

## Interoperability

### Agent-to-agent communication (via the blackboard)

This is a design pattern, not an implementation of Google's Agent2Agent (A2A) protocol.

Agents do not call each other directly. They all read from the shared blackboard state and publish `AgentMessage` objects to the Supervisor. This decoupling means:

- Any agent can be swapped out without breaking others
- Message contracts are enforced by the `AgentMessage` schema
- The Supervisor is the only component that needs to understand all agent outputs

### MCP-Style Tool Integration (Future)

In a production system, each agent would connect to external tools via MCP-style boundaries:

| Agent | External Tool |
|---|---|
| DemandAgent | Weather API, local events API, POS historical data |
| InventoryAgent | Inventory management system, supplier ordering API |
| LaborAgent | Staff scheduling system, HR platform |
| PricingAgent | Pricing engine, competitor price feeds |
| CXAgent | Customer feedback platform, queue management system |

This prototype uses mocked data but the `AgentMessage` schema and blackboard interface are intended to make real tool integrations straightforward.

## MARL Bridge

Multi-Agent Reinforcement Learning (MARL) was evaluated and deliberately not implemented.

**Why MARL is not appropriate at this stage:**

- **Insufficient training data:** A rule-based prototype must exist before a simulation environment rich enough for RL can be built
- **Safety-critical decisions:** RL policies are difficult to audit; a manager cannot easily explain why an RL agent recommended emergency restocking
- **Explainability requirements:** Human managers need to understand and trust agent recommendations; black-box RL policies undermine this
- **Human approval requirements:** RL agents optimize for reward signals, not human oversight boundaries — aligning these is a non-trivial research problem

**Where MARL could add value in a future version:**

- The PricingAgent could learn dynamic discount policies from historical sales data
- The InventoryAgent could learn ordering thresholds from stockout history
- The LaborAgent could learn staffing patterns from wait-time and satisfaction outcomes

The current rule-based architecture is the correct starting point: it is interpretable, safe, and produces a labeled dataset of decisions that could later be used as demonstration data for imitation learning.

