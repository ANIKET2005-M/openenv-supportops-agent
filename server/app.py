"""FastAPI server for SupportOpsEnv benchmark."""

from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from supportopsenv import SupportOpsEnv, Action, Observation

app = FastAPI(title="SupportOpsEnv", version="0.1.0")

# Global environment instance
env = SupportOpsEnv()


class ResetRequest(BaseModel):
    """Reset request parameters."""
    task_id: str = "refund_triage"
    seed: int = 42


class StepRequest(BaseModel):
    """Step request with action."""
    action: Action


class StateResponse(BaseModel):
    """State response."""
    task_id: str
    episode_step: int
    max_steps: int
    cumulative_reward: float
    done: bool
    success: bool
    grader_score: float


@app.on_event("startup")
async def startup_event():
    """Initialize environment on startup."""
    global env
    env = SupportOpsEnv()


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}


@app.post("/reset")
async def reset(request: Optional[ResetRequest] = None):
    """
    Reset environment and return initial observation.
    
    Returns:
        HTTP 200 with observation
    """
    if request is None:
        request = ResetRequest()
    
    try:
        observation = env.reset(task_id=request.task_id, seed=request.seed)
        return JSONResponse(
            status_code=200,
            content=observation.model_dump()
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/step")
async def step(request: StepRequest):
    """
    Execute action and return step result.
    
    Returns:
        Step result with observation, reward, done, success
    """
    try:
        result = env.step(request.action)
        return {
            "observation": result.observation.model_dump(),
            "reward": result.reward,
            "done": result.done,
            "success": result.success,
            "info": result.info,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/state")
async def get_state():
    """
    Get current environment state.
    
    Returns:
        Current state
    """
    try:
        state = env.state
        if state is None:
            raise HTTPException(status_code=400, detail="Environment not initialized. Call /reset first.")
        
        return {
            "task_id": state.task_id,
            "episode_step": state.episode_step,
            "max_steps": state.max_steps,
            "cumulative_reward": state.cumulative_reward,
            "done": state.done,
            "success": state.success,
            "grader_score": state.grader_score,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "SupportOpsEnv",
        "version": "0.1.0",
        "description": "OpenEnv benchmark for customer support operations",
        "endpoints": {
            "POST /reset": "Reset environment and get initial observation",
            "POST /step": "Execute action and get step result",
            "GET /state": "Get current environment state",
            "GET /health": "Health check",
        }
    }
