# testme_local.py
# Quick local smoke-test for the agentpy FastAPI server (Stage 3)
# Pairs with app/api.py — assumes `python -m uvicorn app.api:app --port 8000`
# Tim Fraser

# 0. Setup #################################

import json
import sys

import requests

BASE = "http://127.0.0.1:8000"

# 1. Health check ##########################

print("=" * 60)
print("📋 Local Agent Smoke Test")
print("=" * 60)

print("\n--- Step 1: Health check ---")
try:
    r = requests.get(f"{BASE}/health", timeout=10)
except requests.ConnectionError:
    print("❌ Cannot reach server — is uvicorn running on port 8000?")
    sys.exit(1)

print(f"✅ GET /health  →  {r.status_code}")
health = r.json()
print(json.dumps(health, indent=2))

# 2. Send a task ###########################

print("\n--- Step 2: POST /hooks/agent ---")

task_payload = {
    "task": (
        "Your disaster snapshot or follow-up: "
        "Morning brief on Hurricane Helene, southeastern US, last 24 hours — "
        "power outages, shelters, and road closures if reported."
    ),
}

print(f"📤 Sending task ({len(task_payload['task'])} chars) …")

r2 = requests.post(
    f"{BASE}/hooks/agent",
    headers={"Content-Type": "application/json"},
    json=task_payload,
    timeout=120,
)

print(f"✅ POST /hooks/agent  →  {r2.status_code}")
data = r2.json()

# 3. Inspect the response ##################

print("\n--- Step 3: Response fields ---")

status = data.get("status")
turns_used = data.get("turns_used")
turn_cap = data.get("turn_cap")
session_id = data.get("session_id")
resume_token = data.get("resume_token")

print(f"   status        : {status}")
print(f"   turns_used    : {turns_used}")
print(f"   turn_cap      : {turn_cap}")
print(f"   session_id    : {session_id}")

# If paused, show resume_token for follow-up
if status == "paused_for_human":
    print(f"   ⚠️  Paused — model hit the turn cap.")
    print(f"   resume_token  : {resume_token}")
    print(
        "\n   To continue, re-run with session_id and resume_token "
        "(see agentpy/README.md)."
    )

# Print the reply (truncated preview)
reply = data.get("reply", "")
print(f"\n--- Reply preview (first 800 chars) ---\n")
print(reply[:800])
if len(reply) > 800:
    print(f"\n   … ({len(reply)} chars total)")

# 4. Summary ###############################

print("\n" + "=" * 60)
print("📊 Done")
print(f"   status       = {status}")
print(f"   turns_used   = {turns_used} / {turn_cap}")
if status == "paused_for_human":
    print(f"   resume_token = {resume_token}")
print("=" * 60)
