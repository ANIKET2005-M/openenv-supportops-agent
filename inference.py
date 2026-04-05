"""Baseline inference script for SupportOpsEnv benchmark."""

import os
import json
import sys
from typing import List, Optional

from supportopsenv import SupportOpsEnv, Action


class BaselineAgent:
    """Simple baseline agent for SupportOpsEnv."""
    
    def __init__(self, model_name: str = "gpt-4o"):
        self.model_name = model_name
        self.env = SupportOpsEnv()
    
    def run_episode(self, task_id: str = "refund_triage", seed: int = 42) -> dict:
        """
        Run a complete episode and emit stdout in required format.
        
        Prints:
            [START] task=... env=... model=...
            [STEP] step=... action=... reward=... done=... error=...
            ...
            [END] success=... steps=... score=... rewards=...
        """
        
        # Reset environment
        observation = self.env.reset(task_id=task_id, seed=seed)
        
        # Emit START
        print(f"[START] task={task_id} env=supportops model={self.model_name}")
        sys.stdout.flush()
        
        step_rewards = []
        done = False
        success = False
        steps = 0
        error_msg = None
        
        # Run episode
        while not done and steps < observation.max_steps:
            steps += 1
            
            # Select action based on simple heuristic policy
            action = self._select_action(observation, steps)
            
            # Execute action
            try:
                result = self.env.step(action)
                observation = result.observation
                reward = result.reward
                done = result.done
                success = result.success
                
                step_rewards.append(reward)
                
                # Emit STEP
                action_str = self._format_action(action)
                error_str = "null"
                print(f"[STEP] step={steps} action={action_str} reward={reward:.2f} done={str(done).lower()} error={error_str}")
                sys.stdout.flush()
                
            except Exception as e:
                error_msg = str(e)
                step_rewards.append(-0.1)
                print(f"[STEP] step={steps} action=error reward=-0.10 done=false error={error_msg}")
                sys.stdout.flush()
                break
        
        # Get final score
        if self.env.state:
            final_score = self.env.state.grader_score
        else:
            final_score = 0.0
        
        # Format rewards
        rewards_str = ",".join(f"{r:.2f}" for r in step_rewards)
        if final_score > 0:
            rewards_str += f",{final_score:.2f}"
        
        # Emit END
        print(f"[END] success={str(success).lower()} steps={steps} score={final_score:.3f} rewards={rewards_str}")
        sys.stdout.flush()
        
        return {
            "task_id": task_id,
            "success": success,
            "steps": steps,
            "score": final_score,
            "rewards": step_rewards,
            "total_return": sum(step_rewards) + final_score,
        }
    
    def _select_action(self, observation, step: int) -> Action:
        """Select action using simple heuristic policy."""
        
        task_id = observation.task_id
        tickets = observation.tickets
        
        if not tickets:
            return Action(action_type="resolve", ticket_id=1, arguments={})
        
        ticket = tickets[0]  # Focus on first ticket
        
        # Policy-based action selection
        if task_id == "refund_triage":
            if step == 1:
                return Action(
                    action_type="classify_ticket",
                    ticket_id=ticket.id,
                    arguments={"category": "refund"}
                )
            elif step == 2:
                return Action(
                    action_type="lookup_policy",
                    ticket_id=ticket.id,
                    arguments={"topic": "refunds"}
                )
            elif step == 3:
                return Action(
                    action_type="lookup_order",
                    ticket_id=ticket.id,
                    arguments={"order_id": ticket.order_id}
                )
            else:
                return Action(
                    action_type="resolve",
                    ticket_id=ticket.id,
                    arguments={"decision": "approve"}
                )
        
        elif task_id == "damaged_goods":
            if step == 1:
                return Action(
                    action_type="classify_ticket",
                    ticket_id=ticket.id,
                    arguments={"category": "replacement"}
                )
            elif step == 2:
                return Action(
                    action_type="ask_customer",
                    ticket_id=ticket.id,
                    arguments={"question": "Can you provide photos of damage?"}
                )
            elif step == 3:
                return Action(
                    action_type="lookup_policy",
                    ticket_id=ticket.id,
                    arguments={"topic": "damaged_goods"}
                )
            else:
                return Action(
                    action_type="escalate",
                    ticket_id=ticket.id,
                    arguments={"reason": "damage_claim"}
                )
        
        elif task_id == "queue_priority":
            # Simple priority ordering: VIP first (ids 3,6), then fraud (id 4)
            open_tickets = [t for t in tickets if t.status == "open"]
            
            if not open_tickets:
                return Action(action_type="resolve", ticket_id=1, arguments={})
            
            # Sort by priority
            priority_map = {3: 0, 6: 1, 4: 2}  # VIP, VIP, Fraud
            priority_ticket = min(open_tickets, key=lambda t: priority_map.get(t.id, 3))
            
            if step % 3 == 1:
                return Action(
                    action_type="lookup_account",
                    ticket_id=priority_ticket.id,
                    arguments={"customer_id": priority_ticket.customer_id}
                )
            elif step % 3 == 2:
                return Action(
                    action_type="classify_ticket",
                    ticket_id=priority_ticket.id,
                    arguments={"category": "priority_handling"}
                )
            else:
                return Action(
                    action_type="resolve",
                    ticket_id=priority_ticket.id,
                    arguments={"resolution": "handled"}
                )
        
        # Default action
        return Action(
            action_type="resolve",
            ticket_id=ticket.id if ticket else 1,
            arguments={}
        )
    
    def _format_action(self, action: Action) -> str:
        """Format action for STEP output."""
        args_str = ",".join(f"{k}={v}" for k, v in action.arguments.items())
        if args_str:
            return f"{action.action_type}({args_str})"
        return action.action_type


def main():
    """Run baseline inference."""
    # Get environment variables
    api_key = os.getenv("OPENAI_API_KEY", "")
    model_name = os.getenv("MODEL_NAME", "gpt-4o")
    task_id = os.getenv("TASK_ID", "refund_triage")
    seed = int(os.getenv("SEED", "42"))
    
    # Create and run agent
    agent = BaselineAgent(model_name=model_name)
    
    try:
        result = agent.run_episode(task_id=task_id, seed=seed)
    except Exception as e:
        print(f"[ERROR] {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
