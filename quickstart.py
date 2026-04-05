#!/usr/bin/env python3
"""
Quick start guide for SupportOpsEnv benchmark.
Shows how to use the environment with examples.
"""

from supportopsenv import SupportOpsEnv, Action

print("=" * 70)
print("SUPPORTOPSENV QUICK START")
print("=" * 70)

# Initialize environment
env = SupportOpsEnv()

# Example 1: Refund Triage Task
print("\n" + "=" * 70)
print("EXAMPLE 1: Refund Triage (Easy Task)")
print("=" * 70)

observation = env.reset(task_id="refund_triage", seed=42)
print(f"\nTask: {observation.task_id}")
print(f"Description: {observation.task_description}")
print(f"Ticket: {observation.tickets[0].id} - {observation.tickets[0].description}")
print(f"Budget: {observation.step_count}/{observation.max_steps} steps")

# Step 1: Classify ticket
print("\n[Step 1] Classifying ticket as 'refund'...")
action = Action(
    action_type="classify_ticket",
    ticket_id=1,
    arguments={"category": "refund"}
)
result = env.step(action)
print(f"Reward: +{result.reward:.2f}, Done: {result.done}")

# Step 2: Lookup policy
print("\n[Step 2] Looking up refund policy...")
action = Action(
    action_type="lookup_policy",
    ticket_id=1,
    arguments={"topic": "refunds"}
)
result = env.step(action)
print(f"Reward: +{result.reward:.2f}, Done: {result.done}")
print(f"Retrieved: {list(result.observation.retrieved_records.keys())}")

# Step 3: Check order
print("\n[Step 3] Looking up order status...")
action = Action(
    action_type="lookup_order",
    ticket_id=1,
    arguments={"order_id": 1001}
)
result = env.step(action)
print(f"Reward: +{result.reward:.2f}, Done: {result.done}")

# Step 4: Resolve
print("\n[Step 4] Resolving ticket...")
action = Action(
    action_type="resolve",
    ticket_id=1,
    arguments={"decision": "approve_refund"}
)
result = env.step(action)
print(f"Reward: +{result.reward:.2f}, Done: {result.done}, Success: {result.success}")
print(f"\n[OK] Episode finished!")
print(f"Total reward: {result.info['cumulative_reward']:.2f}")
print(f"Grader score: {result.info['grader_score']:.3f}")

# Example 2: Damaged Goods Task
print("\n" + "=" * 70)
print("EXAMPLE 2: Damaged Goods (Medium Task)")
print("=" * 70)

env = SupportOpsEnv()
observation = env.reset(task_id="damaged_goods", seed=42)
print(f"\nTask: {observation.task_id}")
print(f"Ticket: {observation.tickets[0].id} - {observation.tickets[0].description}")

steps_taken = 0
while not env.state.done and steps_taken < observation.max_steps:
    steps_taken += 1
    
    if steps_taken == 1:
        action = Action(
            action_type="classify_ticket",
            ticket_id=2,
            arguments={"category": "replacement"}
        )
        print(f"\n[Step {steps_taken}] Classifying as replacement...")
    elif steps_taken == 2:
        action = Action(
            action_type="ask_customer",
            ticket_id=2,
            arguments={"question": "Can you provide photos of the damage?"}
        )
        print(f"\n[Step {steps_taken}] Requesting evidence...")
    elif steps_taken == 3:
        action = Action(
            action_type="lookup_policy",
            ticket_id=2,
            arguments={"topic": "damaged_goods"}
        )
        print(f"\n[Step {steps_taken}] Looking up damaged goods policy...")
    else:
        action = Action(
            action_type="escalate",
            ticket_id=2,
            arguments={"reason": "damage_claim"}
        )
        print(f"\n[Step {steps_taken}] Escalating case...")
    
    result = env.step(action)
    print(f"Reward: +{result.reward:.2f}, Done: {result.done}")

print(f"\n[OK] Episode finished!")
print(f"Total reward: {result.info['cumulative_reward']:.2f}")
print(f"Grader score: {result.info['grader_score']:.3f}")

# Example 3: Queue Priority Task
print("\n" + "=" * 70)
print("EXAMPLE 3: Queue Priority (Hard Task)")
print("=" * 70)

env = SupportOpsEnv()
observation = env.reset(task_id="queue_priority", seed=42)
print(f"\nTask: {observation.task_id}")
print(f"Queue size: {len(observation.tickets)} tickets")
print("Tickets:")
for ticket in observation.tickets:
    vip = " [VIP]" if ticket.customer_id in [101, 104] else ""
    fraud = " [FRAUD RISK]" if "fraudulent" in ticket.description.lower() else ""
    print(f"  - Ticket {ticket.id} (Customer {ticket.customer_id}): {ticket.description[:40]}{vip}{fraud}")

print("\nStrategy: Prioritize VIP and fraud cases...")
resolved = 0
steps_taken = 0

while not env.state.done and steps_taken < 20 and resolved < 3:
    steps_taken += 1
    
    # Get first unresolved ticket (prioritized: VIP first, then fraud, then standard)
    open_tickets = [t for t in env.state.tickets if t.status == "open"]
    if not open_tickets:
        break
    
    priority_ticket = open_tickets[0]  # Simplified for demo
    
    if steps_taken % 3 == 1:
        action = Action(
            action_type="lookup_account",
            ticket_id=priority_ticket.id,
            arguments={"customer_id": priority_ticket.customer_id}
        )
        print(f"\n[Step {steps_taken}] Checking account for ticket {priority_ticket.id}...")
    elif steps_taken % 3 == 2:
        action = Action(
            action_type="classify_ticket",
            ticket_id=priority_ticket.id,
            arguments={"category": "priority"}
        )
        print(f"\n[Step {steps_taken}] Classifying ticket {priority_ticket.id}...")
    else:
        action = Action(
            action_type="resolve",
            ticket_id=priority_ticket.id,
            arguments={"resolution": "handled"}
        )
        print(f"\n[Step {steps_taken}] Resolving ticket {priority_ticket.id}...")
        resolved += 1
    
    result = env.step(action)
    print(f"Reward: +{result.reward:.2f}, Resolved: {resolved}/3")

print(f"\n[OK] Episode finished!")
print(f"Success: {result.success}")

print("\n" + "=" * 70)
print("QUICK START COMPLETE")
print("=" * 70)
print("\nNext steps:")
print("1. Run full inference: python inference.py")
print("2. Start API server: uvicorn server.app:app --port 7860")
print("3. Check README.md for full documentation")
print("=" * 70)
