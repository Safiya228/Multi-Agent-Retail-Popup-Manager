from schemas import AgentMessage


class DemandAgent:
    def run(self, state):
        if state["event_nearby"] and state["time"] == "Friday 6 PM":
            severity = "high"
            demand = "high"
            action = "Prepare for increased orders."
            confidence = 0.88
        else:
            severity = "medium"
            demand = "normal"
            action = "Maintain normal operations."
            confidence = 0.75

        return AgentMessage(
            agent_name="DemandAgent",
            issue_type="demand_forecast",
            severity=severity,
            recommendation=f"Expected demand is {demand}. {action}",
            confidence=confidence,
            requires_human_approval=False,
            evidence={
                "time": state["time"],
                "weather": state["weather"],
                "event_nearby": state["event_nearby"]
            }
        )


class InventoryAgent:
    def run(self, state):
        dough = state["inventory"]["pizza_dough"]
        expected = state["expected_customers"]

        if dough < expected * 0.3:
            return AgentMessage(
                agent_name="InventoryAgent",
                issue_type="stockout_risk",
                severity="critical",
                recommendation="Restock pizza dough immediately.",
                confidence=0.93,
                requires_human_approval=True,
                evidence={
                    "pizza_dough_units": dough,
                    "expected_customers": expected
                }
            )

        return AgentMessage(
            agent_name="InventoryAgent",
            issue_type="inventory_ok",
            severity="low",
            recommendation="Inventory level is acceptable.",
            confidence=0.75,
            requires_human_approval=False,
            evidence=state["inventory"]
        )


class LaborAgent:
    def run(self, state):
        if state["average_wait_time"] > 15 and state["current_staff"] < 3:
            return AgentMessage(
                agent_name="LaborAgent",
                issue_type="staffing_shortage",
                severity="high",
                recommendation="Add one more staff member during the rush period.",
                confidence=0.86,
                requires_human_approval=True,
                evidence={
                    "current_staff": state["current_staff"],
                    "average_wait_time": state["average_wait_time"]
                }
            )

        return AgentMessage(
            agent_name="LaborAgent",
            issue_type="staffing_ok",
            severity="low",
            recommendation="Current staffing is acceptable.",
            confidence=0.70,
            requires_human_approval=False,
            evidence={
                "current_staff": state["current_staff"]
            }
        )


class PricingAgent:
    def run(self, state):
        drinks = state["inventory"]["drinks"]

        if drinks > 70 and state["expected_customers"] < 30:
            recommendation = "Offer a small drink discount to reduce excess stock."
            severity = "medium"
            approval = True
        else:
            recommendation = "Do not discount. Demand is strong enough."
            severity = "low"
            approval = False

        return AgentMessage(
            agent_name="PricingAgent",
            issue_type="pricing_decision",
            severity=severity,
            recommendation=recommendation,
            confidence=0.78,
            requires_human_approval=approval,
            evidence={
                "drink_inventory": drinks,
                "expected_customers": state["expected_customers"]
            }
        )


class CustomerExperienceAgent:
    def run(self, state):
        if state["average_wait_time"] > 15 or state["complaints_last_hour"] >= 5:
            return AgentMessage(
                agent_name="CustomerExperienceAgent",
                issue_type="customer_experience_risk",
                severity="high",
                recommendation="Reduce wait time and communicate delays to customers.",
                confidence=0.89,
                requires_human_approval=False,
                evidence={
                    "average_wait_time": state["average_wait_time"],
                    "complaints_last_hour": state["complaints_last_hour"]
                }
            )

        return AgentMessage(
            agent_name="CustomerExperienceAgent",
            issue_type="customer_experience_ok",
            severity="low",
            recommendation="Customer experience is stable.",
            confidence=0.72,
            requires_human_approval=False,
            evidence={
                "average_wait_time": state["average_wait_time"]
            }
        )