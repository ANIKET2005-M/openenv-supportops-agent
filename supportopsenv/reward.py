"""Reward shaping for SupportOpsEnv benchmark."""

from typing import List


def calculate_step_reward(
    action_type: str,
    is_redundant: bool = False,
    is_correct: bool = True,
    policy_violation: bool = False,
) -> float:
    """
    Calculate per-step reward based on action quality.
    
    Step rewards:
    - +0.15 correct classification
    - +0.15 relevant lookup
    - +0.10 appropriate info request
    - -0.10 redundant lookup  
    - -0.25 policy violation
    - +1.00 final grader score
    """
    
    if policy_violation:
        return -0.25
    
    if is_redundant:
        return -0.10
    
    if action_type == "classify_ticket":
        return 0.15 if is_correct else -0.05
    elif action_type == "lookup_policy":
        return 0.15 if is_correct else -0.05
    elif action_type == "lookup_order":
        return 0.15 if is_correct else -0.05
    elif action_type == "lookup_account":
        return 0.15 if is_correct else -0.05
    elif action_type == "ask_customer":
        return 0.10 if is_correct else -0.05
    elif action_type == "draft_response":
        return 0.05 if is_correct else 0.0
    elif action_type == "escalate":
        return 0.10 if is_correct else 0.0
    elif action_type == "resolve":
        return 0.20 if is_correct else -0.10
    
    return 0.0


def calculate_final_reward(grader_score: float) -> float:
    """
    Calculate final reward from grader score.
    
    Final reward = 1.0 * grader_score (normalized [0,1])
    """
    return 1.0 * grader_score


def calculate_trajectory_return(
    step_rewards: List[float],
    final_grader_score: float,
    gamma: float = 1.0,
) -> float:
    """
    Calculate total episode return with optional discounting.
    
    Returns:
        Sum of discounted rewards plus final grader score
    """
    discounted_sum = sum(gamma ** i * r for i, r in enumerate(step_rewards))
    total_return = discounted_sum + calculate_final_reward(final_grader_score)
    
    return total_return


def get_reward_breakdown(
    step_rewards: List[float],
    final_grader_score: float,
) -> dict:
    """
    Get detailed reward breakdown for analysis.
    
    Returns:
        Dictionary with statistics about rewards
    """
    step_total = sum(step_rewards)
    final_reward = calculate_final_reward(final_grader_score)
    total_return = step_total + final_reward
    
    return {
        "step_count": len(step_rewards),
        "step_rewards_sum": step_total,
        "step_rewards_mean": step_total / len(step_rewards) if step_rewards else 0.0,
        "final_score": final_grader_score,
        "final_reward": final_reward,
        "total_return": total_return,
        "max_possible_return": 2.5,  # Approximate max with good trajectory
    }
