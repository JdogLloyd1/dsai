# assigner_stage2.py
# Stage 2 Staff-Client Assigner Stress Test (Ollama Cloud)
# Pairs with ACTIVITY_assigner.md
# Jonathan Lloyd
#
# This script runs a Stage 2 stress-test follow-up using Stage 1 output as context.
# You manually set the pairing to challenge before running.
# It enforces strict output format and forces one retry if constraints fail.

# 0. Setup #################################

## 0.1 Load packages ############################

import json
import os
from pathlib import Path

import requests

## 0.2 Configuration ############################

SCRIPT_PATH = Path(__file__).resolve()
ASSIGNMENT_DIR = SCRIPT_PATH.parent
REPO_ROOT = ASSIGNMENT_DIR.parent
OUTPUT_DIR = ASSIGNMENT_DIR / "assigner_output"

OLLAMA_HOST = "https://ollama.com"
OLLAMA_MODEL = "gpt-oss:120b"
OLLAMA_ENDPOINT = "/api/chat"
REQUEST_TIMEOUT_SECONDS = 120
MAX_ATTEMPTS = 2  # first attempt + forced retry

STAGE1_RESULT_PATH = OUTPUT_DIR / "stage1_result.md"
OUTPUT_MARKDOWN_PATH = OUTPUT_DIR / "stage2_result.md"
OUTPUT_RAW_JSON_PATH = OUTPUT_DIR / "stage2_raw_response.json"

# Set this manually before running Stage 2.
STAFF_NAME_TO_CHALLENGE = "Dana Park"
CLIENT_NAME_TO_CHALLENGE = "Client I"

## 0.3 Load repo-level .env without modifying it ############################


def load_env_file(env_path: Path) -> None:
    """Load a .env file into process env without overwriting existing keys."""
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


load_env_file(REPO_ROOT / ".env")

OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY")
if not OLLAMA_API_KEY:
    raise ValueError("OLLAMA_API_KEY is missing. Add it to the repo-level .env or environment.")

## 0.4 Prompt text ############################

SYSTEM_PROMPT = """
You are a managing partner reviewing staffing assignments.
Your job is to evaluate one challenged staff-client pairing using the full Stage 1 assignment as context.

Return format (must match exactly):
## Pairing Review
[exactly 3-5 sentences evaluating the challenged pairing]

## Recommendation
[exactly one sentence: either defend current pairing OR suggest a specific alternative pairing]

## Revised Assignment Impact
- [bullet 1: direct effect on assignments]
- [bullet 2: tradeoff or risk]
- [bullet 3: why this is acceptable or not]

Rules:
- Return valid Markdown only (no code fences)
- Use the provided Stage 1 output as the baseline
- If suggesting an alternative, name both the replacement client and who takes the displaced client
- Do not invent staff or clients beyond the provided list
- Keep reasoning concise and specific
""".strip()


def build_stage2_user_prompt() -> str:
    """Build user prompt with Stage 1 context and manual challenge question."""
    if not STAGE1_RESULT_PATH.exists():
        raise FileNotFoundError(
            f"Stage 1 output not found at {STAGE1_RESULT_PATH}. "
            "Run assigner_stage1.py first."
        )

    stage1_text = STAGE1_RESULT_PATH.read_text(encoding="utf-8").strip()
    return (
        "Below is the Stage 1 assignment output.\n\n"
        "=== Stage 1 Output Start ===\n"
        f"{stage1_text}\n"
        "=== Stage 1 Output End ===\n\n"
        f"I'm not sure about the assignment of {STAFF_NAME_TO_CHALLENGE} to {CLIENT_NAME_TO_CHALLENGE}. "
        "Can you reconsider this pairing and either defend it or suggest an alternative?"
    )


## 0.5 Helpers ############################


def validate_response(markdown_text: str) -> list[str]:
    """Validate strict Stage 2 follow-up format."""
    issues = []
    if "## Pairing Review" not in markdown_text:
        issues.append("Missing required heading: ## Pairing Review")
    if "## Recommendation" not in markdown_text:
        issues.append("Missing required heading: ## Recommendation")
    if "## Revised Assignment Impact" not in markdown_text:
        issues.append("Missing required heading: ## Revised Assignment Impact")

    impact_bullets = [line for line in markdown_text.splitlines() if line.strip().startswith("- ")]
    if len(impact_bullets) < 3:
        issues.append("Expected at least 3 bullets under ## Revised Assignment Impact.")

    return issues


def build_payload(extra_user_instruction: str = "") -> dict:
    """Build chat payload with optional corrective instruction."""
    user_prompt = build_stage2_user_prompt()
    if extra_user_instruction:
        user_prompt = (
            user_prompt
            + "\n\nCorrection required:\n"
            + extra_user_instruction
            + "\nReturn a fully corrected response now."
        )

    return {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "stream": False,
    }


# 1. Run Stage 2 #################################

print("\n" + "=" * 64)
print("ASSIGNER STAGE 2: OLLAMA CLOUD STRESS TEST")
print("=" * 64)
print(f"Model: {OLLAMA_MODEL}")
print(f"Output directory: {OUTPUT_DIR}")
print(f"Challenge pairing: {STAFF_NAME_TO_CHALLENGE} + {CLIENT_NAME_TO_CHALLENGE}")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

url = f"{OLLAMA_HOST}{OLLAMA_ENDPOINT}"
headers = {"Authorization": f"Bearer {OLLAMA_API_KEY}", "Content-Type": "application/json"}

last_raw_result = None
last_markdown = ""
last_issues = []

for attempt in range(1, MAX_ATTEMPTS + 1):
    print(f"\nAttempt {attempt}/{MAX_ATTEMPTS}...")

    correction_note = ""
    if attempt > 1 and last_issues:
        # Live progress notice requested by user.
        print("Format violations detected. Triggering forced retry now.")
        for issue in last_issues:
            print(f"- {issue}")
        correction_note = "Please fix these issues exactly:\n- " + "\n- ".join(last_issues)

    payload = build_payload(extra_user_instruction=correction_note)
    response = requests.post(url, headers=headers, json=payload, timeout=REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()

    last_raw_result = response.json()
    message = last_raw_result.get("message", {})
    last_markdown = message.get("content", "").strip()

    if not last_markdown:
        last_issues = ["The model response was empty."]
        continue

    last_issues = validate_response(last_markdown)
    if not last_issues:
        print("Format checks passed on this attempt.")
        break

if not last_markdown:
    raise ValueError("No markdown response returned by model.")

## 1.1 Save outputs ############################

OUTPUT_MARKDOWN_PATH.write_text(last_markdown + "\n", encoding="utf-8")
OUTPUT_RAW_JSON_PATH.write_text(json.dumps(last_raw_result, indent=2), encoding="utf-8")

## 1.2 Report ############################

print("\nSaved files:")
print(f"- {OUTPUT_MARKDOWN_PATH}")
print(f"- {OUTPUT_RAW_JSON_PATH}")

if last_issues:
    print("\nFinal status: WARN")
    print("The model still violated Stage 2 format after forced retry:")
    for issue in last_issues:
        print(f"- {issue}")
else:
    print("\nFinal status: PASS")
    print("All strict Stage 2 format checks satisfied.")

print("\nDone.\n")
