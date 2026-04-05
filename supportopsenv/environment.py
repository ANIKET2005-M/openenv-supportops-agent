"""Core environment implementation for SupportOpsEnv."""

import random
from typing import Any, Dict, List, Optional, Tuple
from supportopsenv.models import (
    Action,
    ActionSummary,
    Observation,
    State,
    StepResult,
    Ticket,
)
from supportopsenv.graders import grade_refund_triage, grade_damaged_goods, grade_queue_priority
from supportopsenv.reward import calculate_step_reward, calculate_final_reward


class SupportOpsEnv:
    """Support Operations benchmark environment."""

    def __init__(self):
        """Initialize environment."""
        self.state: Optional[State] = None
        self.initial_state: Optional[State] = None
        
        # Task data
        self.policies = {
            "refunds": {
                "eligible_conditions": ["within_30_days", "defective", "wrong_item"],
                "standard_refund_days": 30,
            },
            "damaged_goods": {
                "requires_evidence": True,
                "replacement_eligible": True,
                "refund_eligible_if_no_replacement": True,
            },
            "priority": {
                "vip_priority": 1,
                "fraud_risk_priority": 1,
                "standard_priority": 2,
                "low_priority": 3,
            }
        }
        
        self.orders = {
            1001: {"status": "delivered", "amount": 99.99, "days_since_purchase": 5},
            1002: {"status": "delivered", "amount": 149.99, "days_since_purchase": 35},
            1003: {"status": "delivered", "amount": 49.99, "days_since_purchase": 10},
            1004: {"status": "delivered", "amount": 199.99, "days_since_purchase": 2},
            1005: {"status": "delivered", "amount": 79.99, "days_since_purchase": 15},
        }
        
        self.accounts = {
            101: {"vip": True, "lifetime_value": 5000},
            102: {"vip": False, "lifetime_value": 150},
            103: {"vip": False, "lifetime_value": 200},
            104: {"vip": True, "lifetime_value": 8000},
            105: {"vip": False, "lifetime_value": 50},
        }

    def reset(self, task_id: str = "refund_triage", seed: int = 42) -> Observation:
        """Reset environment for task."""
        random.seed(seed)
        
        # Create task-specific initial state
        if task_id == "refund_triage":
            tickets = [
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
            ]
            max_steps = 10
        elif task_id == "damaged_goods":
            tickets = [
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
            ]
            max_steps = 15
        elif task_id == "queue_priority":
            tickets = [
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
            ]
            max_steps = 20
        else:
            raise ValueError(f"Unknown task_id: {task_id}")
        
        self.state = State(
            task_id=task_id,
            seed=seed,
            episode_step=0,
            max_steps=max_steps,
            tickets=tickets,
            retrieved_records={},
            action_history=[],
            cumulative_reward=0.0,
            done=False,
            success=False,
            grader_score=0.0,
        )
        self.initial_state = self.state.model_copy(deep=True)
        
        return self._get_observation()

    def _get_observation(self) -> Observation:
        """Get current observation from state."""
        summary_text = self._generate_summary_text()
        
        return Observation(
            task_id=self.state.task_id,
            task_description=self._get_task_description(),
            tickets=self.state.tickets,
            retrieved_records=self.state.retrieved_records,
            action_history=self.state.action_history,
            step_count=self.state.episode_step,
            max_steps=self.state.max_steps,
            summary_text=summary_text,
        )

    def _get_task_description(self) -> str:
        """Get human-readable task description."""
        descriptions = {
            "refund_triage": "Triage a single customer support ticket to determine if a refund should be granted. Classify the ticket, lookup relevant policies, check order details, and determine appropriate resolution.",
            "damaged_goods": "Handle a damaged goods case by classifying the ticket, requesting evidence if needed, looking up replacement policies, and deciding between escalation or resolution.",
            "queue_priority": "Manage a queue of 5 support tickets by prioritizing high-value and risk cases, then resolving at least 3 tickets within the step budget.",
        }
        return descriptions.get(self.state.task_id, "Support operations task")

    def _generate_summary_text(self) -> str:
        """Generate LLM-friendly summary of current state."""
        tickets_summary = "; ".join(
            f"Ticket {t.id}: {t.description} (status={t.status})"
            for t in self.state.tickets[:3]
        )
        records_summary = "; ".join(
            f"{k}={v}" for k, v in list(self.state.retrieved_records.items())[:3]
        )
        
        summary = f"Task: {self.state.task_id}. Step {self.state.episode_step}/{self.state.max_steps}. Tickets: {tickets_summary}"
        if records_summary:
            summary += f". Records: {records_summary}"
        
        return summary

    def step(self, action: Action) -> StepResult:
        """Execute action and return result."""
        if self.state is None:
            raise RuntimeError("Environment not reset")
        
        if self.state.done:
            raise RuntimeError("Episode already done")
        
        self.state.episode_step += 1
        error = None
        step_reward = 0.0
        action_reward = 0.0
        
        # Process action
        try:
            if action.action_type == "classify_ticket":
                action_reward = self._handle_classify(action)
            elif action.action_type == "lookup_policy":
                action_reward = self._handle_lookup_policy(action)
            elif action.action_type == "lookup_order":
                action_reward = self._handle_lookup_order(action)
            elif action.action_type == "lookup_account":
                action_reward = self._handle_lookup_account(action)
            elif action.action_type == "ask_customer":
                action_reward = self._handle_ask_customer(action)
            elif action.action_type == "draft_response":
                action_reward = self._handle_draft_response(action)
            elif action.action_type == "escalate":
                action_reward = self._handle_escalate(action)
            elif action.action_type == "resolve":
                action_reward = self._handle_resolve(action)
        except Exception as e:
            error = str(e)
            action_reward = -0.1
        
        # Add to history
        action_summary = ActionSummary(
            step=self.state.episode_step,
            action_type=action.action_type,
            ticket_id=action.ticket_id,
            arguments=action.arguments,
            reward=action_reward,
            error=error,
        )
        self.state.action_history.append(action_summary)
        
        step_reward = action_reward
        self.state.cumulative_reward += step_reward
        
        # Check termination conditions
        done = self._check_done()
        success = self._check_success()
        
        if done:
            self.state.done = True
            self.state.success = success
            # Calculate final grader score
            self.state.grader_score = self._grade_episode()
            # Add final reward
            final_reward = calculate_final_reward(self.state.grader_score)
            self.state.cumulative_reward += final_reward
            step_reward += final_reward
        
        self.state.done = done
        
        observation = self._get_observation()
        
        return StepResult(
            observation=observation,
            reward=step_reward,
            done=done,
            success=success,
            info={
                "step": self.state.episode_step,
                "cumulative_reward": self.state.cumulative_reward,
                "grader_score": self.state.grader_score,
                "error": error,
            },
        )

    def _handle_classify(self, action: Action) -> float:
        """Handle classify_ticket action."""
        ticket_id = action.ticket_id
        if not ticket_id:
            return -0.1
        
        ticket = next((t for t in self.state.tickets if t.id == ticket_id), None)
        if not ticket:
            return -0.1
        
        category = action.arguments.get("category")
        if category in ["refund", "replacement", "escalation"]:
            ticket.category = category
            return 0.15  # Correct classification reward
        
        return -0.05

    def _handle_lookup_policy(self, action: Action) -> float:
        """Handle lookup_policy action."""
        topic = action.arguments.get("topic")
        
        # Check for redundant lookup (already retrieved)
        if topic in self.state.retrieved_records:
            return -0.10  # Redundant lookup penalty
        
        if topic in self.policies:
            self.state.retrieved_records[f"policy_{topic}"] = self.policies[topic]
            return 0.15  # Relevant lookup reward
        
        return -0.05

    def _handle_lookup_order(self, action: Action) -> float:
        """Handle lookup_order action."""
        order_id = action.arguments.get("order_id")
        
        if order_id in self.orders:
            if f"order_{order_id}" in self.state.retrieved_records:
                return -0.10  # Redundant lookup
            
            self.state.retrieved_records[f"order_{order_id}"] = self.orders[order_id]
            return 0.15
        
        return -0.05

    def _handle_lookup_account(self, action: Action) -> float:
        """Handle lookup_account action."""
        customer_id = action.arguments.get("customer_id")
        
        if customer_id in self.accounts:
            if f"account_{customer_id}" in self.state.retrieved_records:
                return -0.10
            
            self.state.retrieved_records[f"account_{customer_id}"] = self.accounts[customer_id]
            return 0.15
        
        return -0.05

    def _handle_ask_customer(self, action: Action) -> float:
        """Handle ask_customer action."""
        question = action.arguments.get("question")
        if question and isinstance(question, str) and len(question) > 3:
            return 0.10  # Appropriate info request
        
        return -0.05

    def _handle_draft_response(self, action: Action) -> float:
        """Handle draft_response action."""
        response = action.arguments.get("response")
        if response and isinstance(response, str) and len(response) > 10:
            return 0.05
        
        return 0.0

    def _handle_escalate(self, action: Action) -> float:
        """Handle escalate action."""
        ticket_id = action.ticket_id
        if not ticket_id:
            return 0.0
        
        ticket = next((t for t in self.state.tickets if t.id == ticket_id), None)
        if ticket:
            ticket.escalated = True
            ticket.status = "escalated"
            return 0.1
        
        return 0.0

    def _handle_resolve(self, action: Action) -> float:
        """Handle resolve action."""
        ticket_id = action.ticket_id
        if not ticket_id:
            return -0.1
        
        ticket = next((t for t in self.state.tickets if t.id == ticket_id), None)
        if ticket:
            ticket.resolved = True
            ticket.status = "resolved"
            return 0.2
        
        return -0.1

    def _check_done(self) -> bool:
        """Check if episode is done."""
        # Episode ends when max steps reached or all tickets resolved/escalated
        if self.state.episode_step >= self.state.max_steps:
            return True
        
        open_tickets = [t for t in self.state.tickets if t.status == "open"]
        if len(open_tickets) == 0:
            return True
        
        # For queue_priority, need to resolve 3+ of 5 tickets
        if self.state.task_id == "queue_priority":
            resolved_count = sum(1 for t in self.state.tickets if t.status == "resolved")
            if resolved_count >= 3 and self.state.episode_step >= 8:
                return True
        
        return False

    def _check_success(self) -> bool:
        """Check if task completed successfully."""
        if self.state.task_id == "refund_triage":
            # Needs categorization + policy lookup + resolution
            ticket = self.state.tickets[0]
            has_category = ticket.category is not None
            has_policy = any("policy" in k for k in self.state.retrieved_records.keys())
            has_resolution = ticket.status in ["resolved", "escalated"]
            return has_category and has_policy and has_resolution
        
        elif self.state.task_id == "damaged_goods":
            # Needs proper handling of evidence and escalation
            ticket = self.state.tickets[0]
            return ticket.status in ["resolved", "escalated"]
        
        elif self.state.task_id == "queue_priority":
            # Needs to resolve at least 3 of 5 tickets
            resolved_count = sum(1 for t in self.state.tickets if t.status == "resolved")
            return resolved_count >= 3
        
        return False

    def _grade_episode(self) -> float:
        """Grade episode using task-specific grader."""
        if self.state.task_id == "refund_triage":
            return grade_refund_triage(self.state)
        elif self.state.task_id == "damaged_goods":
            return grade_damaged_goods(self.state)
        elif self.state.task_id == "queue_priority":
            return grade_queue_priority(self.state)
        
        return 0.0

    def state(self) -> State:
        """Get current state."""
        if self.state is None:
            raise RuntimeError("Environment not reset")
        return self.state
