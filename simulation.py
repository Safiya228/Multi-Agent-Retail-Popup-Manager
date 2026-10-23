"""Mock blackboard states. Each scenario is a snapshot of the pop-up's operations."""
from copy import deepcopy

SCENARIOS = {
    # The original demo scenario.
    "friday_rush": {
        "time": "Friday 6 PM", "weather": "rainy", "event_nearby": True,
        "expected_customers": 55,
        "inventory": {"pizza_dough": 8, "drinks": 80, "sauce": 25},
        "current_staff": 2, "average_wait_time": 18, "complaints_last_hour": 5,
    },
    # Everything fine -> should NOT escalate.
    "normal_day": {
        "time": "Tuesday 2 PM", "weather": "clear", "event_nearby": False,
        "expected_customers": 20,
        "inventory": {"pizza_dough": 40, "drinks": 50, "sauce": 30},
        "current_staff": 3, "average_wait_time": 5, "complaints_last_hour": 0,
    },
    # Test scenario 1: high demand + low inventory.
    "high_demand_low_inventory": {
        "time": "Friday 6 PM", "weather": "clear", "event_nearby": True,
        "expected_customers": 55,
        "inventory": {"pizza_dough": 8, "drinks": 60, "sauce": 25},
        "current_staff": 4, "average_wait_time": 8, "complaints_last_hour": 0,
    },
    # Test scenario 2: low demand + high inventory (pricing proposes a discount).
    "low_demand_high_inventory": {
        "time": "Tuesday 2 PM", "weather": "clear", "event_nearby": False,
        "expected_customers": 20,
        "inventory": {"pizza_dough": 40, "drinks": 90, "sauce": 30},
        "current_staff": 3, "average_wait_time": 5, "complaints_last_hour": 0,
    },
    # Test scenario 3: high wait time + low staffing.
    "high_wait_low_staffing": {
        "time": "Tuesday 2 PM", "weather": "clear", "event_nearby": False,
        "expected_customers": 40,
        "inventory": {"pizza_dough": 40, "drinks": 50, "sauce": 30},
        "current_staff": 2, "average_wait_time": 20, "complaints_last_hour": 3,
    },
    # Test scenario 4: conflicting signals (event/high demand vs. low expected customers + excess drinks).
    "conflicting_pricing_and_demand": {
        "time": "Friday 6 PM", "weather": "clear", "event_nearby": True,
        "expected_customers": 25,
        "inventory": {"pizza_dough": 40, "drinks": 85, "sauce": 30},
        "current_staff": 3, "average_wait_time": 5, "complaints_last_hour": 0,
    },
    # Test scenario 5: critical stockout.
    "critical_stockout": {
        "time": "Tuesday 2 PM", "weather": "clear", "event_nearby": False,
        "expected_customers": 40,
        "inventory": {"pizza_dough": 5, "drinks": 50, "sauce": 30},
        "current_staff": 3, "average_wait_time": 5, "complaints_last_hour": 0,
    },
}


def get_mock_scenario(name="friday_rush"):
    return deepcopy(SCENARIOS[name])
