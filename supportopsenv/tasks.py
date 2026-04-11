"""Task fixtures for SupportOpsEnv benchmark."""

from typing import Dict, List
from supportopsenv.models import Ticket
from supportopsenv.graders import (
    grade_refund_triage,
    grade_damaged_goods,
    grade_queue_priority,
)

# ---------------- TASK DEFINITIONS ---------------- #

REFUND_TRIAGE_TASK = {
    "id": "refund_triage",
    "difficulty": "easy",
    "description": "Refund triage task",
    "max_steps": 10,
    "initial_tickets": [
        Ticket(
            id=1,
            category=None,
            priority=None,
            status="open",
            customer_id=101,
            order_id=1001,
            description="Item arrived defective",
            has_evidence=False,
            resolved=False,
            escalated=False,
        )
    ],
}

DAMAGED_GOODS_TASK = {
    "id": "damaged_goods",
    "difficulty": "medium",
    "description": "Damaged goods task",
    "max_steps": 15,
    "initial_tickets": [
        Ticket(
            id=2,
            category=None,
            priority=None,
            status="open",
            customer_id=102,
            order_id=1002,
            description="Package damaged",
            has_evidence=False,
            resolved=False,
            escalated=False,
        )
    ],
}

QUEUE_PRIORITY_TASK = {
    "id": "queue_priority",
    "difficulty": "hard",
    "description": "Queue priority task",
    "max_steps": 20,
    "initial_tickets": [
        Ticket(
            id=3,
            category=None,
            priority=None,
            status="open",
            customer_id=201,
            order_id=2001,
            description="VIP customer issue",
            has_evidence=False,
            resolved=False,
            escalated=False,
        ),
        Ticket(
            id=4,
            category=None,
            priority=None,
            status="open",
            customer_id=202,
            order_id=2002,
            description="Fraud suspicion",
            has_evidence=False,
            resolved=False,
            escalated=False,
        ),
    ],
}

# ---------------- VALIDATOR REQUIRED ---------------- #

TASKS = {
    "refund_triage": {
        "config": REFUND_TRIAGE_TASK,
        "grader": grade_refund_triage,
    },
    "damaged_goods": {
        "config": DAMAGED_GOODS_TASK,
        "grader": grade_damaged_goods,
    },
    "queue_priority": {
        "config": QUEUE_PRIORITY_TASK,
        "grader": grade_queue_priority,
    },
}

def get_task(task_id: str) -> Dict:
    if task_id not in TASKS:
        raise ValueError(f"Unknown task: {task_id}")
    return TASKS[task_id]["config"]

def list_tasks() -> List[str]:
    return list(TASKS.keys())
