# assigner_stage1.py
# Stage 1 Staff-Client Assigner (Ollama Cloud)
# Pairs with ACTIVITY_assigner.md
# Jonathan Lloyd
#
# This script sends Stage 1 assignment instructions to Ollama Cloud, validates
# assignment constraints, and forces one retry when constraints are violated.
# It saves both markdown output and raw API response for transparency.

# 0. Setup #################################

## 0.1 Load packages ############################

import json
import os
import re
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

OUTPUT_MARKDOWN_PATH = OUTPUT_DIR / "stage1_result.md"
OUTPUT_RAW_JSON_PATH = OUTPUT_DIR / "stage1_raw_response.json"

STAFF_NAMES = [
    "Alex Chen",
    "Brianna Okafor",
    "Carla Mendez",
    "Dana Park",
    "Elliot Vasquez",
    "Fiona Marsh",
]

CLIENT_NAMES = [
    "Client A",
    "Client B",
    "Client C",
    "Client D",
    "Client E",
    "Client F",
    "Client G",
    "Client H",
    "Client I",
    "Client J",
    "Client K",
    "Client L",
]

EXPECTED_TABLE_HEADER = "| Staff Member | Client 1 | Client 2 | Rationale (1 sentence) |"

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

## 0.4 Prompt text and data ############################

SYSTEM_PROMPT = """
You are a managing partner at a consulting firm making staffing assignments.
Your job is to read unstructured descriptions of staff members and clients,
then assign each staff member to exactly 2 clients based on fit.

Return format (must match exactly):
## Assignment Table
[markdown table]

## Assignment Logic Summary
[3-5 sentence paragraph]

Rules:
- Each staff member gets exactly 2 clients
- Each client is assigned to exactly 1 staff member
- No client may be left unassigned
- Base assignments on demonstrated fit: skills, experience, communication style
- Flag weak-fit assignments in rationale and explain briefly
- Return valid Markdown only (no code fences)
- Keep rationale to exactly one sentence per row

Table constraints:
- Use exactly this header row:
| Staff Member | Client 1 | Client 2 | Rationale (1 sentence) |
- Include exactly 6 staff rows (one per staff member)
- Use client identifiers Client A through Client L
""".strip()

USER_PROMPT = """
Below are descriptions of our 6 staff members and 12 clients.
Please make the best possible assignments.

--- STAFF ---

Alex Chen
Senior consultant, 9 years experience. Background in financial services and
regulatory compliance. Known for being methodical and detail-oriented.
Prefers clients who are organized and have clear deliverables.
Not great with ambiguous or fast-moving projects.

Brianna Okafor
Mid-level consultant, 4 years experience. Specialist in nonprofit and public
sector work. Very strong communicator — clients love her. Comfortable with
messy, evolving scopes. Has done a lot of stakeholder engagement work.

Carla Mendez
Senior consultant, 7 years experience. Deep expertise in healthcare and life
sciences. Data-heavy work is her strength — she's built several dashboards and
automated reporting tools. Tends to be blunt and efficient; not the warmest
bedside manner but clients respect her results.

Dana Park
Junior consultant, 2 years experience. Background is in marketing and consumer
research. Eager and creative. Better on smaller, well-defined tasks.
Still building confidence with senior client stakeholders.

Elliot Vasquez
Partner-level, 15 years experience. Generalist with a strong track record in
strategy and organizational change. Good relationship manager. Prefers high-stakes,
high-visibility engagements. Gets bored on smaller tactical work.

Fiona Marsh
Mid-level consultant, 5 years experience. Former journalist turned researcher.
Excellent writer and communicator. Often assigned to deliverable-heavy projects
(reports, white papers, presentations). Works well independently.
Prefers clients who give her creative latitude.

--- CLIENTS ---

Client A — Riverdale Community Health Clinic
Small nonprofit health clinic undergoing a strategic planning process.
Moderate budget. Stakeholders include the board, medical staff, and community
advocates. Very collaborative, but decisions are slow due to committee structure.
Main need: facilitation support and a written strategic plan.

Client B — Atlas Financial Group
Large regional bank. Highly regulated environment. Project involves auditing
their compliance documentation and recommending process improvements.
Very organized client — they have a detailed project plan. Expects formal
deliverables and regular status reports.

Client C — BrightPath Schools (Charter Network)
Fast-growing charter school network. Expanding from 3 to 8 schools.
Needs help with org design and HR policy. Client is enthusiastic but somewhat
disorganized. Decision-maker is the founder/CEO — she's visionary but hard to pin
down for meetings.

Client D — Nexagen Pharmaceuticals
Mid-size pharma company. Project is a data audit and KPI dashboard buildout
for their clinical operations team. Technical stakeholders who want results,
not hand-holding. Timeline is tight.

Client E — Greenway Transit Authority
Regional transit agency. Unionized workforce. Project involves a service
redesign study with significant community engagement components.
Political sensitivities — several board members have conflicting opinions.
Long timeline, phased project.

Client F — Solstice Consumer Goods
Consumer packaged goods brand. Needs a market research summary and brand
positioning analysis ahead of a product launch. Fun client, collaborative,
lots of back and forth. Not a huge budget. Creative work valued.

Client G — Meridian Capital Partners
Private equity firm. Fast-moving, high-expectations. Needs an org assessment
of a portfolio company. Very low patience for process — they want findings fast.
Elliot has a pre-existing relationship with the managing partner.

Client H — Harbor City Government (Parks Dept.)
Municipal parks department doing a 10-year capital planning study.
Lots of stakeholders — parks staff, city council, community groups.
Needs public engagement support and a formal report for the city council.

Client I — ClearView Diagnostics
Healthcare tech startup. Building a clinical decision support tool.
Needs help structuring their regulatory strategy and drafting FDA submission
materials. Technical and regulatory complexity is high. Startup culture —
informal, fast, sometimes chaotic.

Client J — The Holloway Foundation
Private philanthropy. Wants a landscape scan and strategic options memo on
workforce development funding. Small team, thoughtful, low-maintenance.
Primarily needs a polished, well-written deliverable.

Client K — Summit Retail Group
Multi-location retail chain. Undergoing a cost reduction initiative.
Wants operational benchmarking and process recommendations.
Client stakeholders are skeptical of consultants — they've had bad experiences
before. Need someone who can build trust quickly.

Client L — Vance Biomedical Research Institute
Academic research institute. Needs help redesigning their grant reporting
process and building a data tracking system. Methodical, detail-oriented
stakeholders. Comfortable with technical complexity.
""".strip()

## 0.5 Validation and API helpers ############################


def extract_assignment_rows(markdown_text: str) -> list[dict]:
    """Extract staff/client rows from the markdown table."""
    rows = []
    for line in markdown_text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or stripped.startswith("|---"):
            continue
        if stripped == EXPECTED_TABLE_HEADER:
            continue

        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if len(cells) != 4:
            continue
        if cells[0] in STAFF_NAMES:
            rows.append(
                {
                    "staff_member": cells[0],
                    "client_1": cells[1],
                    "client_2": cells[2],
                    "rationale": cells[3],
                }
            )
    return rows


def normalize_client(value: str) -> str:
    """Normalize client text to a canonical label like 'Client A' when possible."""
    match = re.search(r"\bClient\s+([A-L])\b", value)
    if match:
        return f"Client {match.group(1)}"
    return value.strip()


def validate_response(markdown_text: str) -> list[str]:
    """Validate strict format and assignment constraints."""
    issues = []

    if "## Assignment Table" not in markdown_text:
        issues.append("Missing required heading: ## Assignment Table")
    if "## Assignment Logic Summary" not in markdown_text:
        issues.append("Missing required heading: ## Assignment Logic Summary")
    if EXPECTED_TABLE_HEADER not in markdown_text:
        issues.append("Table header does not match expected columns/order exactly.")

    rows = extract_assignment_rows(markdown_text)
    if len(rows) != 6:
        issues.append(f"Expected 6 assignment rows, found {len(rows)}.")

    staff_seen = set()
    clients_assigned = []
    for row in rows:
        staff = row["staff_member"]
        c1 = normalize_client(row["client_1"])
        c2 = normalize_client(row["client_2"])

        if staff in staff_seen:
            issues.append(f"Duplicate staff row detected: {staff}")
        staff_seen.add(staff)

        clients_assigned.extend([c1, c2])

    missing_staff = sorted(set(STAFF_NAMES) - staff_seen)
    if missing_staff:
        issues.append(f"Missing staff rows: {', '.join(missing_staff)}")

    client_counts = {}
    for client in clients_assigned:
        client_counts[client] = client_counts.get(client, 0) + 1

    missing_clients = [client for client in CLIENT_NAMES if client_counts.get(client, 0) == 0]
    duplicate_clients = [client for client, count in client_counts.items() if count > 1]

    if missing_clients:
        issues.append(f"Unassigned clients: {', '.join(missing_clients)}")
    if duplicate_clients:
        issues.append(f"Clients assigned more than once: {', '.join(sorted(duplicate_clients))}")
    if len(clients_assigned) != 12:
        issues.append(f"Expected 12 client assignments total, found {len(clients_assigned)}.")

    return issues


def build_payload(extra_user_instruction: str = "") -> dict:
    """Build chat payload with optional corrective instruction for retry."""
    user_content = USER_PROMPT
    if extra_user_instruction:
        user_content = (
            user_content
            + "\n\nCorrection required:\n"
            + extra_user_instruction
            + "\nReturn a fully corrected response now."
        )

    return {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        "stream": False,
    }


# 1. Run Stage 1 #################################

print("\n" + "=" * 64)
print("ASSIGNER STAGE 1: OLLAMA CLOUD REQUEST")
print("=" * 64)
print(f"Model: {OLLAMA_MODEL}")
print(f"Output directory: {OUTPUT_DIR}")

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
        print("Constraint violations detected. Triggering forced retry now.")
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
        print("Constraint checks passed on this attempt.")
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
    print("The model still violated constraints after forced retry:")
    for issue in last_issues:
        print(f"- {issue}")
else:
    print("\nFinal status: PASS")
    print("All strict format and assignment constraints satisfied.")

print("\nDone.\n")
