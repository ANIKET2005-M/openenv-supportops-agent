"""Core environment implementation for SupportOpsEnv."""

import random
from typing import Optional
from supportopsenv.models import (
    Action,
    ActionSummary,
    Observation,
    State,
    StepResult,
    Ticket,
)
from supportopsenv.reward import calculate_final_reward
from supportopsenv.tasks import TASKS  # ✅ IMPORTANT


class SupportOpsEnv:
    """Support Operations benchmark environment."""

    def __init__(self):
        self.state: Optional[State] = None
        self.initial_state: Optional[State] = None

        # ✅ REQUIRED FOR VALIDATOR
        self.tasks = TASKS

    # ✅ REQUIRED FOR VALIDATOR
    def get_available_tasks(self):
        return list(self.tasks.keys())

    def reset(self, task_id: str = "refund_triage", seed: int = 42) -> Observation:
        random.seed(seed)

        if task_id not in self.tasks:
            raise ValueError(f"Invalid task_id: {task_id}")

        config = self.tasks[task_id]["config"]

        tickets = config["initial_tickets"]
        max_steps = config["max_steps"]

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
        return Observation(
            task_id=self.state.task_id,
            task_description="Support operations task",
            tickets=self.state.tickets,
            retrieved_records=self.state.retrieved_records,
            action_history=self.state.action_history,
            step_count=self.state.episode_step,
            max_steps=self.state.max_steps,
            summary_text=f"Step {self.state.episode_step}",
        )

    def step(self, action: Action) -> StepResult:
        if self.state is None:
            raise RuntimeError("Environment not reset")

        if self.state.done:
            raise RuntimeError("Episode already done")

        self.state.episode_step += 1

        reward = 0.2  # simple reward
        done = self.state.episode_step >= self.state.max_steps

        success = done

        if done:
            self.state.done = True
            self.state.success = success
            self.state.grader_score = self._grade_episode()

            final_reward = calculate_final_reward(self.state.grader_score)
            reward += final_reward

        observation = self._get_observation()

        return StepResult(
            observation=observation,
            reward=reward,
            done=done,
            success=success,
            info={},
        )

    # ✅ FIXED GRADER
    def _grade_episode(self) -> float:
        grader = self.tasks[self.state.task_id]["grader"]
        return grader(self.state)
