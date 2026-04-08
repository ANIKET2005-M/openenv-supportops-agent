from fastapi import FastAPI
from supportopsenv.environment import SupportOpsEnv

app = FastAPI()
env = SupportOpsEnv()

@app.get("/")
def root():
    return {"status": "running"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/reset")
def reset():
    obs = env.reset()
    return obs

@app.post("/step")
def step(action: dict):
    return env.step(action)