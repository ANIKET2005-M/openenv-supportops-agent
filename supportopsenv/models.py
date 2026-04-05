"""Pydantic models for SupportOpsEnv benchmark."""

from typing import Any, List, Literal, Optional, Dict
from pydantic import BaseModel, Field


class Action(BaseModel):
    """Agent action in support operations domain."""
    
    action_type: Literal[
        "classify_ticket",
        "lookup_policy",
        "lookup_order",
        "lookup_account",
        "ask_customer",
        "draft_response",
        "escalate",
        "resolve"
    ]
    ticket_id: Optional[int] = None
    arguments: Dict[str, Any] = Field(default_factory=dict)
    message: Optional[str] = None


class Ticket(BaseModel):
    """Customer support ticket."""
    
    id: int
    category: Optional[str] = None
    priority: Optional[str] = None
    status: str = "open"
    customer_id: int
    order_id: Optional[int] = None
    description: str
    has_evidence: bool = False
    resolved: bool = False
    escalated: bool = False


class ActionSummary(BaseModel):
    """Summary of taken action for observation history."""
    
    step: int
    action_type: str
    ticket_id: Optional[int] = None
    arguments: Dict[str, Any]
    reward: float = 0.0
    error: Optional[str] = None


class Observation(BaseModel):
    """Environment observation returned to agent."""
    
    task_id: str
    task_description: str
    tickets: List[Ticket]
    retrieved_records: Dict[str, Any] = Field(default_factory=dict)
    action_history: List[ActionSummary] = Field(default_factory=list)
    step_count: int = 0
    max_steps: int = 20
    summary_text: str = ""


class State(BaseModel):
    """Complete environment state."""
    
    task_id: str
    seed: int
    episode_step: int
    max_steps: int
    tickets: List[Ticket]
    retrieved_records: Dict[str, Any] = Field(default_factory=dict)
    action_history: List[ActionSummary] = Field(default_factory=list)
    cumulative_reward: float = 0.0
    done: bool = False
    success: bool = False
    grader_score: float = 0.0


class StepResult(BaseModel):
    """Result of taking a step in environment."""
    
    observation: Observation
    reward: float
    done: bool
    success: bool
    info: Dict[str, Any] = Field(default_factory=dict)
