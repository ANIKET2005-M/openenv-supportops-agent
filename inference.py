"""Baseline inference script for SupportOpsEnv benchmark."""

import os
import json
import sys
from typing import Optional
from dotenv import load_dotenv
from openai import OpenAI

from supportopsenv import SupportOpsEnv, Action

# Load env
load_dotenv()

# ✅ REQUIRED ENV FORMAT
API_BASE_URL = os.getenv("API_BASE_URL", "https://api-inference.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "meta-llama/Llama-3-8b-Instruct")
HF_TOKEN = os.getenv("HF_TOKEN")  # ❗ NO DEFAULT

if not HF_TOKEN:
    raise ValueError("HF_TOKEN environment variable is required")


class BaselineAgent:
    def __init__(self, model_name: str = MODEL_NAME):
        self.model_name = model_name

        # ✅ OpenAI client (REQUIRED BY RULES)
        self.client = OpenAI(
            base_url=API_BASE_URL,
            api_key=HF_TOKEN
        )

        self.env = SupportOpsEnv()
        self.last_error = None

    def run_episode(self, task_id: str = "refund_triage", seed: int = 42):

        observation = self.env.reset(task_id=task_id, seed=seed)

        print(f"[START] task={task_id} env=supportops model={self.model_name}")
        sys.stdout.flush()

        step_rewards = []
        done = False
        success = False
        steps = 0

        while not done and steps < observation.max_steps:
            steps += 1

            action = self._select_action(observation)

            try:
                result = self.env.step(action)
                observation = result.observation
                reward = result.reward
                done = result.done
                success = result.success

                step_rewards.append(reward)

                action_str = self._format_action(action)
                error_str = self.last_error if self.last_error else "null"

                print(f"[STEP] step={steps} action={action_str} reward={reward:.2f} done={str(done).lower()} error={error_str}")
                sys.stdout.flush()

            except Exception as e:
                step_rewards.append(-0.1)
                print(f"[STEP] step={steps} action=error reward=-0.10 done=false error={str(e)}")
                sys.stdout.flush()
                break

        final_score = self.env.state.grader_score if self.env.state else 0.0
        rewards_str = ",".join(f"{r:.2f}" for r in step_rewards)

        print(f"[END] success={str(success).lower()} steps={steps} score={final_score:.3f} rewards={rewards_str}")
        sys.stdout.flush()

    def _select_action(self, observation) -> Action:

        prompt = self._build_prompt(observation)

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
            )

            action_text = response.choices[0].message.content.strip()
            self.last_error = None
            return self._parse_action(action_text, observation)

        except Exception as e:
            self.last_error = "api_error"
            print(f"API error: {e}", file=sys.stderr)
            return self._heuristic_fallback(observation)

    def _build_prompt(self, observation):

        prompt = f"You are handling customer support tickets.\nTask: {observation.task_description}\n\n"

        for t in observation.tickets:
            prompt += f"- Ticket {t.id}: {t.description} (Status: {t.status})\n"

        prompt += "\nChoose best action in JSON:\n"
        prompt += '{"action_type":"resolve","ticket_id":1,"arguments":{}}\n'

        return prompt

    def _parse_action(self, action_text, observation):

        try:
            data = json.loads(action_text)
            return Action(
                action_type=data["action_type"],
                ticket_id=data.get("ticket_id", 1),
                arguments=data.get("arguments", {})
            )
        except:
            return self._heuristic_fallback(observation)

    def _heuristic_fallback(self, observation):

        ticket_id = observation.tickets[0].id if observation.tickets else 1

        return Action(
            action_type="resolve",
            ticket_id=ticket_id,
            arguments={"decision": "approved"}
        )

    def _format_action(self, action: Action):
        args = ",".join(f"{k}={v}" for k, v in action.arguments.items())
        return f"{action.action_type}({args})" if args else action.action_type


def main():
    task_id = os.getenv("TASK_ID", "refund_triage")
    seed = int(os.getenv("SEED", "42"))

    agent = BaselineAgent()
    agent.run_episode(task_id=task_id, seed=seed)


if __name__ == "__main__":
    main()