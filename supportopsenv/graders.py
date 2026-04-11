"""Grader functions for SupportOpsEnv benchmark tasks."""

from typing import Dict
from supportopsenv.models import State


def grade_refund_triage(state: State) -> float:
    """
    Grade refund_triage task.
    
    Deterministic scoring based on:
    - Correct classification (0-0.3)
    - Policy lookup (0-0.3)  
    - Order lookup (0-0.2)
    - Resolution action (0-0.2)
    """
    score = 0.0
    
    ticket = state.tickets[0] if state.tickets else None
    if not ticket:
        return 0.0
    
    # Classification scoring (0-0.3)
    if ticket.category == "refund":
        score += 0.3
    elif ticket.category in ["replacement", "escalation"]:
        score += 0.15
    else:
        score += 0.0
    
    # Policy lookup scoring (0-0.3)
    has_refund_policy = any("refunds" in k.lower() for k in state.retrieved_records.keys())
    has_damaged_policy = any("damaged" in k.lower() for k in state.retrieved_records.keys())
    
    if has_refund_policy:
        score += 0.3
    elif has_damaged_policy:
        score += 0.15
    else:
        score += 0.0
    
    # Order lookup scoring (0-0.2)
    if f"order_{ticket.order_id}" in state.retrieved_records:
        score += 0.2
    
    # Resolution action scoring (0-0.2)
    if ticket.status == "resolved":
        score += 0.2
    elif ticket.status == "escalated":
        score += 0.1
    
    # Ensure [0, 1] range
    score = min(0.99, max(0.01, score))
    return score


def grade_damaged_goods(state: State) -> float:
    """
    Grade damaged_goods task.
    
    Deterministic scoring based on:
    - Correct classification (0-0.25)
    - Evidence request (0-0.25)
    - Policy lookup (0-0.25)
    - Appropriate escalation/resolution (0-0.25)
    """
    score = 0.0
    
    ticket = state.tickets[0] if state.tickets else None
    if not ticket:
        return 0.0
    
    # Classification scoring (0-0.25)
    if ticket.category == "replacement":
        score += 0.25
    elif ticket.category == "escalation":
        score += 0.15
    else:
        score += 0.0
    
    # Evidence request scoring (0-0.25)
    # Check if ask_customer action was taken
    ask_actions = [a for a in state.action_history if a.action_type == "ask_customer"]
    if len(ask_actions) > 0:
        score += 0.25
    
    # Policy lookup scoring (0-0.25)
    has_damaged_policy = any("damaged" in k.lower() for k in state.retrieved_records.keys())
    if has_damaged_policy:
        score += 0.25
    
    # Escalation/resolution scoring (0-0.25)
    if ticket.status == "escalated":
        score += 0.25
    elif ticket.status == "resolved":
        score += 0.15
    
    # Ensure [0, 1] range
    score = min(0.99, max(0.01, score))
    return score


def grade_queue_priority(state: State) -> float:
    """
    Grade queue_priority task.
    
    Deterministic scoring based on:
    - Number of resolved tickets (0-0.4)
    - VIP prioritization (0-0.3)
    - Fraud risk handling (0-0.3)
    """
    score = 0.0
    
    # Resolved tickets scoring (0-0.4)
    resolved_count = sum(1 for t in state.tickets if t.status == "resolved")
    resolved_score = min(0.4, (resolved_count / 5.0) * 0.5)  # Max 0.4 at 5 tickets
    score += resolved_score
    
    # VIP detection and prioritization (0-0.3)
    vip_ticket_ids = [3, 6]  # Tickets 3 and 6 are VIP
    vip_tickets = [t for t in state.tickets if t.id in vip_ticket_ids]
    
    # Check if VIP tickets were resolved or escalated appropriately
    vip_resolved = sum(1 for t in vip_tickets if t.status in ["resolved", "escalated"])
    if vip_resolved >= 1:
        score += 0.15
    if vip_resolved >= 2:
        score += 0.15
    
    # Fraud risk handling (0-0.3)
    fraud_ticket_id = 4  # Ticket 4 is fraud risk
    fraud_ticket = next((t for t in state.tickets if t.id == fraud_ticket_id), None)
    
    if fraud_ticket:
        # Check if escalated or handled with lookups
        has_account_lookup = any("account_" in k and k.endswith("_102") or k.endswith("_104") 
                                for k in state.retrieved_records.keys())
        
        if fraud_ticket.status == "escalated":
            score += 0.3
        elif fraud_ticket.status == "resolved" and has_account_lookup:
            score += 0.15
    
    # Ensure [0, 1] range
    score = min(0.99, max(0.01, score))
    return score


def grade_task(state: State) -> Dict[str, float]:
    """
    Grade episode with component breakdown.
    
    Returns:
        Dictionary with 'score' and 'components'
    """
    if state.task_id == "refund_triage":
        score = grade_refund_triage(state)
    elif state.task_id == "damaged_goods":
        score = grade_damaged_goods(state)
    elif state.task_id == "queue_priority":
        score = grade_queue_priority(state)
    else:
        score = 0.0
    
    return {
        "score": score,
        "components": {
            "classification": 0.0,
            "lookups": 0.0,
            "actions": 0.0,
            "resolution": 0.0,
        }
    }

