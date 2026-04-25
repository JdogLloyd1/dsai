# decider_stage2.py
# Stage 2 Wedding Venue Decider (Ollama Cloud)
# Pairs with ACTIVITY_decider.md
# Jonathan Lloyd
#
# This script sends the Stage 2 wedding venue task to Ollama Cloud with shifted
# priorities, then asks for a strict comparison against Stage 1 rankings.
# It saves both the markdown response and raw JSON API response.

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
OUTPUT_DIR = ASSIGNMENT_DIR / "decider_output"

OLLAMA_HOST = "https://ollama.com"
OLLAMA_MODEL = "gpt-oss:120b"
OLLAMA_ENDPOINT = "/api/chat"
REQUEST_TIMEOUT_SECONDS = 120

STAGE1_RESULT_PATH = OUTPUT_DIR / "stage1_result.md"
OUTPUT_MARKDOWN_PATH = OUTPUT_DIR / "stage2_result.md"
OUTPUT_RAW_JSON_PATH = OUTPUT_DIR / "stage2_raw_response.json"

EXPECTED_TABLE_HEADER = (
    "| Venue | Capacity | Approx. Price/Night | Catering | Outdoor | Parking | Vibe (1 word) |"
)

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

## 0.4 Stage 2 prompts and venue data ############################

SYSTEM_PROMPT = """
You are a structured data extractor and decision analyst.

Task:
Extract key attributes from unstructured venue descriptions, build a comparison table,
and recommend the top 3 venues based on Stage 2 client priorities.

Critical rules:
- Return valid Markdown only (no code fences).
- Do not invent or infer facts not present in the descriptions.
- If a value is missing or unclear, write exactly: Unknown.
- Never exclude any venue from the comparison table because information is missing.
- Keep explanations concise and factual.
- If Stage 1 shortlist is provided, compare Stage 2 shortlist against it.

Return format (must match exactly):
## Comparison Table
[markdown table]

## Top 3 Shortlist
1. [Venue Name] - [exactly one sentence justification]
2. [Venue Name] - [exactly one sentence justification]
3. [Venue Name] - [exactly one sentence justification]

## Movement vs Stage 1
- [Venue Name]: [Moved up / moved down / newly entered / dropped out / unchanged] - [short reason]
- [Venue Name]: [Moved up / moved down / newly entered / dropped out / unchanged] - [short reason]
- [Venue Name]: [Moved up / moved down / newly entered / dropped out / unchanged] - [short reason]

## Missing Information Note
[exactly one sentence explaining what fields were unknown/ambiguous and how that affected confidence]

The table must include all 16 venues and exactly these columns in this order:
Venue, Capacity, Approx. Price/Night, Catering, Outdoor, Parking, Vibe (1 word)
""".strip()

USER_PROMPT = """
Here are the couple's Stage 2 priorities:
- Budget: flexible, up to $15,000
- Guest count: ~200 people
- Vibe: elegant, grand
- Outdoor is a nice-to-have but not required
- No catering constraint

Here are descriptions of 16 venues. Please analyze and recommend.

Venue 1 — The Rosewood Estate
A sprawling property in the Hudson Valley with manicured gardens and a restored barn.
Capacity up to 175 guests. Rental fee is $17,500 Friday–Sunday. They have a preferred
catering list with 4 approved vendors. Outdoor ceremony space available with a rain
backup tent. Parking for ~80 cars on site.

Venue 2 — The Grand Metropolitan Hotel
Downtown ballroom, seats up to 300. In-house catering only. Pricing starts at $12,000
for the ballroom rental, catering packages extra. Valet parking. No outdoor space.

Venue 3 — Lakeview Pavilion
Outdoor lakeside pavilion. No indoor backup. BYOB catering. Fits about 90 people
comfortably, 110 at a squeeze. Very affordable — around $2,500 for a weekend.

Venue 4 — Thornfield Manor
Historic manor house, 8 acres. Exclusive use for the weekend. Price: $18,000.
In-house catering team. Ceremony can be held on the grounds or in the chapel.
Capacity 150. Featured in several bridal magazines.

Venue 5 — The Foundry at Millworks
Industrial-chic converted factory. Very trendy. Capacity 250. Bring your own vendors.
Rental is $5,000. Rooftop available for cocktail hour. No on-site parking — street
parking and nearby garage only.

Venue 6 — Sunrise Farm & Vineyard
Working vineyard with barn and outdoor ceremony terrace. Stunning views. Capacity 130.
Weekend rental $9,800. Catering through their in-house team or 2 approved vendors.
Ample parking. Very popular — books 18 months out.

Venue 7 — The Atrium Club
Corporate event space that does weddings on weekends. Very flexible on catering.
Fits 300+. Located downtown. Pricing on request — sales team says "typically $9,000–$14,000
depending on date." Not particularly romantic but very professional.

Venue 8 — Cedar Hollow Retreat
Rustic woodland lodge. Intimate and cozy. Max 60 guests. $3,200 for a Saturday.
Outside catering allowed. No formal parking lot — guests park in a field.

Venue 9 — The Belvedere
Upscale rooftop venue with skyline views. Indoor/outdoor setup. Capacity 180.
In-house catering required. Rental + minimum catering spend is $28,000.
Very elegant. Valet only.

Venue 10 — Harborside Event Center
Waterfront venue, brand new. Capacity 220. Pricing TBD — still finalizing packages.
Flexible on catering. Outdoor terrace available. Large parking lot.

Venue 11 — The Ivy House
Garden venue in a residential neighborhood. Permits outdoor ceremonies.
Capacity 100. $4,500 rental. BYOB catering. Street parking only — coordinator
recommends a shuttle from a nearby lot.

Venue 12 — Maple Ridge Country Club
Classic country club setting. Capacity 160. In-house catering only, known for
being very good. Rental from $28,500. Golf course backdrop for photos.
Ample parking. Private feel.

Venue 13 — The Glasshouse Conservatory
All-glass event space surrounded by botanical gardens. Very dramatic.
Capacity 140. $18,000 rental, catering open. Outdoor garden available for ceremonies.
Parking on site. Popular for spring weddings.

Venue 14 — Millbrook Inn
Country inn with event lawn. Venue rental $10,500. Capacity 120. Outside catering
allowed. Some overnight rooms available for wedding party. Very charming.

Venue 15 — The Warehouse District Loft
Raw, urban space. Very minimal. No catering kitchen. Capacity 200.
$8,800 rental. Not ideal for traditional weddings.

Venue 16 — Cloverfield Farms
Family-owned working farm. Barn + outdoor space. Capacity 135.
$6,000 Friday–Sunday. Preferred caterer list (3 vendors).
Casual, warm atmosphere. Lots of parking. Dogs welcome.
""".strip()


def build_stage1_context() -> str:
    """Attach Stage 1 result to support movement comparison, if available."""
    if not STAGE1_RESULT_PATH.exists():
        return (
            "No Stage 1 result file was available. In Movement vs Stage 1, write "
            "'Unknown comparison baseline' for each bullet."
        )

    stage1_text = STAGE1_RESULT_PATH.read_text(encoding="utf-8").strip()
    return (
        "Use the Stage 1 output below as the baseline for movement analysis.\n"
        "If Stage 1 ranking is unclear, state that uncertainty explicitly.\n\n"
        "=== Stage 1 Output Start ===\n"
        f"{stage1_text}\n"
        "=== Stage 1 Output End ==="
    )


## 0.5 API helpers ############################


def build_payload() -> dict:
    """Build the Ollama chat payload for Stage 2."""
    user_prompt = USER_PROMPT + "\n\n" + build_stage1_context()
    return {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "stream": False,
    }


def validate_response(markdown_text: str) -> list[str]:
    """Run lightweight checks for required Stage 2 formatting."""
    issues = []

    if "## Comparison Table" not in markdown_text:
        issues.append("Missing required heading: ## Comparison Table")
    if "## Top 3 Shortlist" not in markdown_text:
        issues.append("Missing required heading: ## Top 3 Shortlist")
    if "## Movement vs Stage 1" not in markdown_text:
        issues.append("Missing required heading: ## Movement vs Stage 1")
    if "## Missing Information Note" not in markdown_text:
        issues.append("Missing required heading: ## Missing Information Note")
    if EXPECTED_TABLE_HEADER not in markdown_text:
        issues.append("Table header does not match expected columns/order exactly.")

    for expected_rank in ["1. ", "2. ", "3. "]:
        if expected_rank not in markdown_text:
            issues.append(f"Shortlist appears to be missing item starting with '{expected_rank.strip()}'.")

    movement_lines = [line for line in markdown_text.splitlines() if line.strip().startswith("- ")]
    if len(movement_lines) < 3:
        issues.append("Movement vs Stage 1 should include at least 3 bullet lines.")

    return issues


# 1. Run Stage 2 #################################

print("\n" + "=" * 62)
print("DECIDER STAGE 2: OLLAMA CLOUD REQUEST")
print("=" * 62)
print(f"Model: {OLLAMA_MODEL}")
print(f"Output directory: {OUTPUT_DIR}")
print(f"Stage 1 baseline file: {STAGE1_RESULT_PATH}")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

url = f"{OLLAMA_HOST}{OLLAMA_ENDPOINT}"
headers = {"Authorization": f"Bearer {OLLAMA_API_KEY}", "Content-Type": "application/json"}
payload = build_payload()

response = requests.post(url, headers=headers, json=payload, timeout=REQUEST_TIMEOUT_SECONDS)
response.raise_for_status()

raw_result = response.json()
message = raw_result.get("message", {})
markdown_output = message.get("content", "").strip()

if not markdown_output:
    raise ValueError("The model response was empty. Check model availability or prompt format.")

## 1.1 Save outputs ############################

OUTPUT_MARKDOWN_PATH.write_text(markdown_output + "\n", encoding="utf-8")
OUTPUT_RAW_JSON_PATH.write_text(json.dumps(raw_result, indent=2), encoding="utf-8")

## 1.2 Validate and report ############################

format_issues = validate_response(markdown_output)

print("\nSaved files:")
print(f"- {OUTPUT_MARKDOWN_PATH}")
print(f"- {OUTPUT_RAW_JSON_PATH}")

if format_issues:
    print("\nFormat checks: WARN")
    for issue in format_issues:
        print(f"- {issue}")
    print("You can re-run after tightening prompt constraints if needed.")
else:
    print("\nFormat checks: PASS")

print("\nDone.\n")
