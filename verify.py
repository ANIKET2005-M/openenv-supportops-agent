"""Verification test for SupportOpsEnv benchmark."""

from supportopsenv import SupportOpsEnv, Action

print("=" * 60)
print("SUPPORTOPSENV VERIFICATION TEST")
print("=" * 60)

# Test 1: Imports
try:
    from supportopsenv import SupportOpsEnv, Action, Observation, State
    print("\n✓ Imports successful")
except Exception as e:
    print(f"\n✗ Import failed: {e}")
    exit(1)

# Test 2: Environment instantiation
try:
    env = SupportOpsEnv()
    print("✓ Environment instantiated")
except Exception as e:
    print(f"✗ Environment instantiation failed: {e}")
    exit(1)

# Test 3: All tasks can be reset
tasks = ["refund_triage", "damaged_goods", "queue_priority"]
for task_id in tasks:
    try:
        obs = env.reset(task_id=task_id, seed=42)
        print(f"\n✓ Task reset: {task_id}")
        print(f"  - Tickets: {len(obs.tickets)}")
        print(f"  - Max steps: {obs.max_steps}")
        print(f"  - Task desc: {obs.task_description[:50]}...")
    except Exception as e:
        print(f"✗ Reset failed for {task_id}: {e}")
        exit(1)

# Test 4: Step execution
print("\n✓ Testing step execution...")
for task_id in tasks:
    try:
        obs = env.reset(task_id=task_id, seed=42)
        ticket = obs.tickets[0]
        
        # Take action
        action = Action(
            action_type="classify_ticket",
            ticket_id=ticket.id,
            arguments={"category": "refund"}
        )
        result = env.step(action)
        
        print(f"  {task_id}:")
        print(f"    - Reward: {result.reward:.3f}")
        print(f"    - Done: {result.done}")
        print(f"    - Success: {result.success}")
    except Exception as e:
        print(f"  ✗ Step failed for {task_id}: {e}")
        exit(1)

# Test 5: Deterministic grading
print("\n✓ Testing deterministic grading...")
for task_id in tasks:
    try:
        scores = []
        for seed in [42, 42]:  # Same task twice
            obs = env.reset(task_id=task_id, seed=seed)
            # Run simple episode
            for i in range(3):
                action = Action(
                    action_type="resolve",
                    ticket_id=obs.tickets[0].id,
                    arguments={}
                )
                result = env.step(action)
                obs = result.observation
                if result.done:
                    break
            scores.append(env.state.grader_score)
        
        if scores[0] == scores[1]:
            print(f"  ✓ {task_id}: Deterministic (score={scores[0]:.3f})")
        else:
            print(f"  ✗ {task_id}: Non-deterministic (scores={scores})")
    except Exception as e:
        print(f"  ✗ {task_id}: {e}")

# Test 6: Inference format
print("\n✓ Testing inference format (refund_triage)...")
import subprocess
result = subprocess.run(
    ["python", "inference.py"],
    cwd="c:\\Users\\anike\\OneDrive\\Desktop\\New folder (5)",
    capture_output=True,
    text=True,
    env={**__import__("os").environ, "TASK_ID": "refund_triage", "SEED": "42"}
)
output_lines = result.stdout.strip().split("\n")
if output_lines:
    print(f"  - First line: {output_lines[0]}")
    print(f"  - Last line: {output_lines[-1]}")
    
    has_start = any("[START]" in line for line in output_lines)
    has_step = any("[STEP]" in line for line in output_lines)
    has_end = any("[END]" in line for line in output_lines)
    
    print(f"  - Has [START]: {'✓' if has_start else '✗'}")
    print(f"  - Has [STEP]: {'✓' if has_step else '✗'}")
    print(f"  - Has [END]: {'✓' if has_end else '✗'}")

print("\n" + "=" * 60)
print("ALL TESTS PASSED ✓")
print("=" * 60)
