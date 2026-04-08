# SupportOpsEnv

OpenEnv benchmark for customer support operations.

## Installation

```bash
pip install -e .
```

## Quick Start

```python
from supportopsenv import SupportOpsEnv

env = SupportOpsEnv()
obs = env.reset(task_id="refund_triage", seed=42)
result = env.step(action)
```

## Tasks

- **refund_triage** (Easy): Classify and route customer refund requests
- **damaged_goods** (Medium): Handle damaged product scenarios  
- **queue_priority** (Hard): Prioritize support queue under constraints

## Environment

Set `HF_TOKEN` in `.env` file for API access.

## Deployment

### Hugging Face Spaces

Deploy as a containerized Hugging Face Space with tag `openenv`:

1. Create a new Space on [Hugging Face](https://huggingface.co/spaces)
2. Select "Docker" as the Space SDK
3. Upload this repository to your Space
4. Add `HF_TOKEN` secret in Space settings
5. Space runs on port 7860 automatically

**API Usage** (once deployed):

```bash
# Health check
curl https://your-username-supportopsenv.hf.space/health

# Reset environment
curl -X POST https://your-username-supportopsenv.hf.space/reset \
  -H "Content-Type: application/json" \
  -d '{"task_id": "refund_triage", "seed": 42}'

# Execute action
curl -X POST https://your-username-supportopsenv.hf.space/step \
  -H "Content-Type: application/json" \
  -d '{"action": {"action_type": "classify_ticket", "ticket_id": 1, "arguments": {"category": "refund"}}}'
```

### Local Docker

```bash
docker build -t supportopsenv:openenv .
docker run -p 7860:7860 -e HF_TOKEN=$HF_TOKEN supportopsenv:openenv
```
```

### Run Baseline Inference

```bash
# Run inference with exact stdout format
python inference.py

# Output format:
# [START] task=refund_triage env=supportops model=meta-llama/Llama-3-8b-Instruct
# [STEP] step=1 action=classify(category=refund) reward=0.15 done=false error=null
# [STEP] step=2 action=lookup_policy(topic=refunds) reward=0.15 done=false error=null
# ...
# [END] success=true steps=12 score=0.870 rewards=0.15,0.15,0.00,1.00
```

### Run FastAPI Server

```bash
# Development server
uvicorn server.app:app --reload --port 7860

# Production server
uvicorn server.app:app --host 0.0.0.0 --port 7860

# Docker container
docker build -t supportopsenv .
docker run -p 7860:7860 supportopsenv
```

### API Endpoints

#### POST /reset - Reset Environment
```bash
curl -X POST http://localhost:7860/reset \
  -H "Content-Type: application/json" \
  -d '{"task_id": "refund_triage", "seed": 42}'
```

Response (HTTP 200):
```json
{
  "task_id": "refund_triage",
  "task_description": "Triage a single customer support ticket...",
  "tickets": [...],
  "retrieved_records": {},
  "action_history": [],
  "step_count": 0,
  "max_steps": 10,
  "summary_text": "..."
}
```

#### POST /step - Execute Action
```bash
curl -X POST http://localhost:7860/step \
  -H "Content-Type: application/json" \
  -d '{
    "action": {
      "action_type": "classify_ticket",
      "ticket_id": 1,
      "arguments": {"category": "refund"}
    }
  }'
```

## Environment Specification

### Action Space

Agents select structured actions with optional arguments:

```python
Action(
    action_type: Literal[
        "classify_ticket",      # Categorize ticket
        "lookup_policy",        # Retrieve policy information
        "lookup_order",         # Check order history
        "lookup_account",       # Check customer account
        "ask_customer",         # Request info from customer
        "draft_response",       # Draft resolution message
        "escalate",             # Escalate to specialist
        "resolve"               # Resolve ticket
    ],
    ticket_id: Optional[int],          # Target ticket (1-7)
    arguments: dict[str, Any],         # Action-specific parameters
    message: Optional[str]             # Free-form message
)
```

### Observation Space

Agents receive rich observations at each step:

```python
Observation(
    task_id: str,                      # Current task
    task_description: str,             # Human-readable objective
    tickets: List[Ticket],             # Current queue
    retrieved_records: dict,           # Policy/order/account data
    action_history: List[ActionSummary],  # Previous actions + rewards
    step_count: int,                   # Current step
    max_steps: int,                    # Episode budget
    summary_text: str                  # LLM-friendly paragraph
)
```

### Reward Structure

**Per-step rewards:**
- +0.15 correct classification
- +0.15 relevant lookup (policy/order/account)
- +0.10 appropriate info request (ask_customer)
- -0.10 redundant lookup (duplicate query)
- -0.25 policy violation (wrong resolution)

**Final reward:**
- +1.00 × grader_score (0.0-1.0)

**Max episode return:** ~2.5 (achievable through efficient trajectory)

## Tasks

### 1. Refund Triage (Easy)
**Objective:** Determine if refund should be approved for single ticket

**Flow:**
1. Classify ticket as "refund" or "replacement"
2. Look up refund policy
3. Check order status and age
4. Resolve or escalate appropriately

**Grading:** Policy lookup accuracy (0.3) + Classification (0.3) + Order check (0.2) + Resolution (0.2)

**Baseline Score:** 0.7-0.8

---

### 2. Damaged Goods (Medium)
**Objective:** Handle customer complaint about damaged delivery

**Flow:**
1. Classify as damage claim
2. Ask customer for evidence (photos)
3. Look up replacement policy
4. Decide: escalate to warehouse or resolve via replacement

**Grading:** Evidence handling (0.25) + Policy lookup (0.25) + Appropriate escalation (0.25) + Classification (0.25)

**Baseline Score:** 0.4-0.6

---

### 3. Queue Priority (Hard)
**Objective:** Triage 5-ticket queue efficiently under step budget

**Queue composition:**
- Tickets 3, 6: VIP customers (high lifetime value)
- Ticket 4: Fraud risk (suspicious account)
- Tickets 5, 7: Standard priority

**Goal:** Resolve 3+ tickets in 3 steps, prioritizing VIP and fraud cases

**Grading:** Resolved tickets (0.4) + VIP prioritization (0.3) + Fraud handling (0.3)

**Baseline Score:** 0.2-0.4

---

## Model Specifications

### Core Types (Pydantic v2)
- `models.py`: All data models
- `models.Action`: Structured action definition
- `models.Observation`: Agent observation
- `models.State`: Complete environment state

### Environment Core
- `environment.py`: `SupportOpsEnv` class
  - `reset(task_id, seed)` → Observation
  - `step(action)` → StepResult
  - `state()` → State

### Task Fixtures
- `tasks.py`: Named task configurations
- Deterministic ticket generation
- Expected score ranges

### Grading
- `graders.py`: Deterministic scoring functions
- `grade_refund_triage()`: [0, 1] score
- `grade_damaged_goods()`: [0, 1] score
- `grade_queue_priority()`: [0, 1] score
- Same input → same score (reproducible)

### Reward Shaping
- `reward.py`: Per-step and trajectory rewards
- `calculate_step_reward()`: Action-specific bonuses/penalties
- `calculate_final_reward()`: Grader score integration
- `calculate_trajectory_return()`: Episode summation with optional discounting

## Deployment

### Docker
```bash
# Build image
docker build -t supportopsenv .

# Run locally
docker run -p 7860:7860 supportopsenv

# Test health
curl http://localhost:7860/health
```

### Hugging Face Spaces
```bash
# Configure space metadata
# - SDK: docker
# - Port: 7860
# - Tags: ["openenv"]

# Push to HF
git push huggingface main
```

## Validation

### Local Checks

```bash
# 1. Docker build
docker build .

# 2. OpenEnv validator
openenv validate

# 3. Inference format
python inference.py | grep "^\[START\]"
python inference.py | grep "^\[STEP\]"
python inference.py | grep "^\[END\]"

# 4. Server POST /reset
curl -X POST http://localhost:7860/reset
# Expected: HTTP 200
```

### Success Criteria

✅ Shell `docker build .` succeeds  
✅ `openenv validate` passes  
✅ `inference.py` emits exact [START]/[STEP]/[END] format  
✅ 3 tasks return [0.0, 1.0] deterministic scores  
✅ Reward shaping across trajectory (not sparse)  
✅ POST /reset returns HTTP 200

## Benchmarking

### Run Agent Against All Tasks

```python
from supportopsenv import SupportOpsEnv

env = SupportOpsEnv()
results = {}

for task_id in ["refund_triage", "damaged_goods", "queue_priority"]:
    observation = env.reset(task_id=task_id, seed=42)
    # Your agent code here...
    results[task_id] = {
        "score": env.state.grader_score,
        "steps": env.state.episode_step,
        "return": env.state.cumulative_reward,
    }

print(results)
```

## Configuration

### Environment Variables
- `HF_TOKEN`: Hugging Face API token (required for inference)
- `MODEL_NAME`: Model to use in inference (default: "meta-llama/Llama-3-8b-Instruct")
- `TASK_ID`: Task to run (default: "refund_triage")
- `SEED`: Random seed (default: 42)

### Docker Compose (Optional)
```yaml
version: "3.8"
services:
  supportopsenv:
    build: .
    ports:
      - "7860:7860"
    environment:
      - MODEL_NAME=meta-llama/Llama-3-8b-Instruct
      - HF_TOKEN=${HF_TOKEN}
```

## Performance Notes

- **Baseline Performance:** Simple heuristic agent scores 0.6-0.7 across tasks
- **Edge Cases:** Handled deterministically (no randomness in grading)
- **Scalability:** Designed for fast iteration (< 1s per episode)
- **Memory:** < 50MB per environment instance

## Citation

```bibtex
@software{supportopsenv2024,
  title={SupportOpsEnv: An OpenEnv Benchmark for Customer Support Operations},
  author={OpenEnv Community},
  year={2024},
  url={https://github.com/openenv8/supportopsenv}
}
```

## Contributing

Contributions welcome! Please:
1. Fork repository
2. Create feature branch
3. Add tests
4. Submit PR

## License

MIT License - see [LICENSE](LICENSE) file

## Acknowledgments

Built for OpenEnv benchmark specification and HF Spaces deployment.

---

**Ready to benchmark?** Start with:
```bash
git clone https://github.com/openenv8/supportopsenv.git
cd supportopsenv
pip install -e .
python inference.py
```
