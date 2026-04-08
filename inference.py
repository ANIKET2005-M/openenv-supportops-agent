"""Baseline inference script for SupportOpsEnv benchmark."""

import os
import json
import sys
from typing import List, Optional
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

from supportopsenv import SupportOpsEnv, Action

# Load environment variables from .env
load_dotenv()


class BaselineAgent:
    """LLM-based baseline agent for SupportOpsEnv using Hugging Face Inference API."""
    
    def __init__(self, model_name: str = "meta-llama/Llama-3-8b-Instruct"):
        self.model_name = model_name
        # Initialize Hugging Face Inference client with HF_TOKEN
        hf_token = os.getenv("HF_TOKEN")
        if not hf_token:
            raise ValueError("HF_TOKEN environment variable is required")
        
        self.client = InferenceClient(api_key=hf_token)
        self.env = SupportOpsEnv()
        self.last_error = None  # Track last API error for reporting
    
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
            
            # Select action based on LLM policy
            action = self._select_action(observation)
            
            # Execute action
            try:
                result = self.env.step(action)
                observation = result.observation
                reward = result.reward
                done = result.done
                success = result.success
                
                step_rewards.append(reward)
                
                # Emit STEP with error tracking
                action_str = self._format_action(action)
                error_str = self.last_error if self.last_error else "null"
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
        
        # Format rewards (step rewards only, not final grader score)
        rewards_str = ",".join(f"{r:.2f}" for r in step_rewards)
        
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
    
    def _select_action(self, observation) -> Action:
        """Select action using Hugging Face LLM."""
        
        # Build prompt
        prompt = self._build_prompt(observation)
        
        # Call Hugging Face Inference API
        try:
            response = self.client.text_generation(
                prompt,
                model=self.model_name,
                max_new_tokens=200,
                temperature=0.1,  # Low temperature for deterministic actions
            )
            
            action_text = response.strip()
            self.last_error = None  # Clear error on success
            return self._parse_action(action_text, observation)
            
        except Exception as e:
            # Capture error for logging + fallback to heuristic
            self.last_error = "api_error"  # Simple error indicator
            print(f"HF API error: {e}", file=sys.stderr)
            return self._heuristic_fallback(observation)
    
    def _build_prompt(self, observation) -> str:
        """Build prompt for LLM."""
        prompt = f"""
You are handling customer support tickets. Your task: {observation.task_description}

Current tickets:
"""
        for ticket in observation.tickets:
            prompt += f"- Ticket {ticket.id}: {ticket.description} (Status: {ticket.status})\n"
        
        if observation.retrieved_records:
            prompt += "\nRetrieved information:\n"
            for key, value in observation.retrieved_records.items():
                prompt += f"- {key}: {value}\n"
        
        if observation.action_history:
            prompt += "\nPrevious actions:\n"
            for action in observation.action_history[-3:]:  # Last 3 actions
                prompt += f"- {action.action_type} on ticket {action.ticket_id}: reward {action.reward}\n"
        
        prompt += f"""
Step {observation.step_count + 1} of {observation.max_steps}

Available actions:
- classify_ticket: Categorize ticket (arguments: category)
- lookup_policy: Get policy info (arguments: topic)
- lookup_order: Check order details (arguments: order_id)
- lookup_account: Check customer account (arguments: customer_id)
- ask_customer: Request info from customer (arguments: question)
- draft_response: Draft response message (arguments: message)
- escalate: Escalate to specialist (arguments: reason)
- resolve: Close ticket (arguments: decision or resolution)

Choose the best action. Respond with JSON format:
{{"action_type": "action_name", "ticket_id": ticket_number, "arguments": {{"key": "value"}}}}
"""
        return prompt
    
    def _parse_action(self, action_text: str, observation) -> Action:
        """Parse LLM response into Action."""
        try:
            # Try to parse as JSON
            action_data = json.loads(action_text)
            return Action(
                action_type=action_data["action_type"],
                ticket_id=action_data.get("ticket_id", observation.tickets[0].id if observation.tickets else 1),
                arguments=action_data.get("arguments", {})
            )
        except json.JSONDecodeError:
            # Fallback: extract from text
            action_type = "resolve"  # default
            ticket_id = observation.tickets[0].id if observation.tickets else 1
            arguments = {}
            
            # Simple parsing
            if "classify_ticket" in action_text:
                action_type = "classify_ticket"
                if "refund" in action_text:
                    arguments = {"category": "refund"}
                elif "replacement" in action_text:
                    arguments = {"category": "replacement"}
            elif "lookup_policy" in action_text:
                action_type = "lookup_policy"
                arguments = {"topic": "refunds"}
            elif "lookup_order" in action_text:
                action_type = "lookup_order"
                arguments = {"order_id": observation.tickets[0].order_id if observation.tickets else None}
            elif "ask_customer" in action_text:
                action_type = "ask_customer"
                arguments = {"question": "Please provide more details"}
            elif "resolve" in action_text:
                action_type = "resolve"
                arguments = {"decision": "approved"}
            
            return Action(action_type=action_type, ticket_id=ticket_id, arguments=arguments)
    
    def _heuristic_fallback(self, observation) -> Action:
        """Simple heuristic fallback when API fails."""
        tickets = observation.tickets
        if not tickets:
            return Action(action_type="resolve", ticket_id=1, arguments={})
        
        ticket = tickets[0]
        step = observation.step_count + 1
        
        if observation.task_id == "refund_triage":
            if step == 1:
                return Action(action_type="classify_ticket", ticket_id=ticket.id, arguments={"category": "refund"})
            elif step == 2:
                return Action(action_type="lookup_policy", ticket_id=ticket.id, arguments={"topic": "refunds"})
            else:
                return Action(action_type="resolve", ticket_id=ticket.id, arguments={"decision": "approve"})
        
        # Default
        return Action(action_type="resolve", ticket_id=ticket.id, arguments={})
    
    def _format_action(self, action: Action) -> str:
        """Format action for STEP output."""
        args_str = ",".join(f"{k}={v}" for k, v in action.arguments.items())
        if args_str:
            return f"{action.action_type}({args_str})"
        return action.action_type


def main():
    """Run baseline inference."""
    # Get environment variables from .env
    model_name = os.getenv("MODEL_NAME", "meta-llama/Llama-3-8b-Instruct")
    task_id = os.getenv("TASK_ID", "refund_triage")
    seed = int(os.getenv("SEED", "42"))
    
    # Create and run agent (HF_TOKEN is checked in __init__)
    agent = BaselineAgent(model_name=model_name)
    
    try:
        result = agent.run_episode(task_id=task_id, seed=seed)
    except Exception as e:
        print(f"[ERROR] {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
