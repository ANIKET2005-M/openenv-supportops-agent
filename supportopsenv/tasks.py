"""Task fixtures for SupportOpsEnv benchmark."""

from typing import Dict, List
from supportopsenv.models import Ticket


# Task 1: Refund Triage (Easy)
REFUND_TRIAGE_TASK = {
    "id": "refund_triage",
    "difficulty": "easy",
    "description": "Triage a single customer support ticket to determine if a refund should be granted. Classify the ticket, lookup relevant policies, check order details, and determine appropriate resolution.",
    "max_steps": 10,
    "initial_tickets": [
        Ticket(
            id=1,
            category=None,
            priority=None,
            status="open",
            customer_id=101,
            order_id=1001,
            description="Item arrived defective, would like refund",
            has_evidence=False,
            resolved=False,
            escalated=False,
        )
    ],
    "expected_actions": [
        "classify_ticket",
        "lookup_policy",
        "lookup_order",
        "resolve"
    ],
    "success_criteria": {
        "must_classify": True,
        "must_lookup_policy": True,
        "must_check_order": True,
        "must_resolve_or_escalate": True,
    },
    "expected_score_range": (0.7, 0.8),
}


# Task 2: Damaged Goods (Medium)
DAMAGED_GOODS_TASK = {
    "id": "damaged_goods",
    "difficulty": "medium",
    "description": "Handle a damaged goods case by classifying the ticket, requesting evidence if needed, looking up replacement policies, and deciding between escalation or resolution.",
    "max_steps": 15,
    "initial_tickets": [
        Ticket(
            id=2,
            category=None,
            priority=None,
            status="open",
            customer_id=102,
            order_id=1002,
            description="Package arrived with damaged contents",
            has_evidence=False,
            resolved=False,
            escalated=False,
        )
    ],
    "expected_actions": [
        "classify_ticket",
        "ask_customer",
        "lookup_policy",
        "escalate"
    ],
    "success_criteria": {
        "must_classify": True,
        "must_request_evidence": True,
        "must_lookup_policy": True,
        "must_escalate_or_resolve": True,
    },
    "expected_score_range": (0.4, 0.6),
}


# Task 3: Queue Priority (Hard)
QUEUE_PRIORITY_TASK = {
    "id": "queue_priority",
    "difficulty": "hard",
    "description": "Manage a queue of 5 support tickets by prioritizing high-value and risk cases, then resolving at least 3 tickets within the step budget.",
    "max_steps": 20,
    "initial_tickets": [
        Ticket(
            id=3,
            category=None,
            priority=None,
            status="open",
            customer_id=101,
            order_id=1003,
            description="VIP customer - urgent issue",
            has_evidence=False,
            resolved=False,
            escalated=False,
        ),
        Ticket(
            id=4,
            category=None,
            priority=None,
            status="open",
            customer_id=102,
            order_id=1004,
            description="Suspected fraudulent order",
            has_evidence=False,
            resolved=False,
            escalated=False,
        ),
        Ticket(
            id=5,
            category=None,
            priority=None,
            status="open",
            customer_id=103,
            order_id=1005,
            description="Standard refund request",
            has_evidence=False,
            resolved=False,
            escalated=False,
        ),
        Ticket(
            id=6,
            category=None,
            priority=None,
            status="open",
            customer_id=104,
            order_id=1001,
            description="VIP - billing issue",
            has_evidence=False,
            resolved=False,
            escalated=False,
        ),
        Ticket(
            id=7,
            category=None,
            priority=None,
            status="open",
            customer_id=105,
            order_id=1005,
            description="Low value - general inquiry",
            has_evidence=False,
            resolved=False,
            escalated=False,
        ),
    ],
    "expected_actions": [
        "lookup_account",
        "classify_ticket",
        "resolve",
    ],
    "success_criteria": {
        "min_resolved": 3,
        "must_prioritize_vip": True,
        "must_handle_fraud_risk": True,
    },
    "expected_score_range": (0.2, 0.4),
}


def get_task(task_id: str) -> Dict:
    """Get task by ID."""
    tasks = {
        "refund_triage": REFUND_TRIAGE_TASK,
        "damaged_goods": DAMAGED_GOODS_TASK,
        "queue_priority": QUEUE_PRIORITY_TASK,
    }
    
    if task_id not in tasks:
        raise ValueError(f"Unknown task: {task_id}")
    
    return tasks[task_id]


def list_tasks() -> List[str]:
    """List all available task IDs."""
    return ["refund_triage", "damaged_goods", "queue_priority"]
