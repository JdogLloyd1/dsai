# 02_ai_quality_control.py
# AI-Assisted Text Quality Control
# Tim Fraser

# This script demonstrates how to use AI (Ollama or OpenAI) to perform quality control
# on AI-generated text reports. It implements quality control criteria including
# boolean accuracy checks and Likert scales for multiple quality dimensions.
# Students learn to design quality control prompts and structure AI outputs as JSON.

# 0. Setup #################################

## 0.1 Load Packages #################################

# If you haven't already, install required packages:
# pip install pandas requests python-dotenv

import pandas as pd  # for data wrangling
import re  # for text processing
import requests  # for HTTP requests
import json  # for JSON operations
import os  # for environment variables
from dotenv import load_dotenv  # for loading .env file

## 0.2 Configuration #################################

load_dotenv()

# Choose your AI provider: "ollama" or "openai"
AI_PROVIDER = "ollama"  # Change to "openai" if using OpenAI

# Ollama configuration (override with OLLAMA_HOST / OLLAMA_MODEL in .env if needed)
PORT = 11434
_base = os.getenv("OLLAMA_HOST", f"http://localhost:{PORT}").rstrip("/")
OLLAMA_HOST = _base
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:latest")  # Use a model that supports JSON output
# Lower = more deterministic QC scores (Ollama /api/chat and /api/generate "options")
OLLAMA_TEMPERATURE = float(os.getenv("OLLAMA_TEMPERATURE", "0.1"))
OLLAMA_TEMPERATURE = max(0.0, min(OLLAMA_TEMPERATURE, 2.0))
# Fixed seed improves repeatability with the same model + prompt (set OLLAMA_SEED in .env to override)
OLLAMA_SEED = int(os.getenv("OLLAMA_SEED", "42"))


def _ollama_options():
    """Options passed to Ollama generate/chat (temperature + seed)."""
    return {"temperature": OLLAMA_TEMPERATURE, "seed": OLLAMA_SEED}

# OpenAI configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = "gpt-4o-mini"  # Low-cost model

## 0.3 Load Sample Data #################################


def load_sample_data():
    """Load sample reports and fixed source data used for accuracy checks."""
    with open("09_text_analysis/data/sample_reports.txt", "r", encoding="utf-8") as f:
        sample_text = f.read()
    reports = [r.strip() for r in sample_text.split("\n\n") if r.strip()]
    source_data = """White County, IL | 2015 | PM10 | Time Driven | hours
|type        |label_value |label_percent |
|:-----------|:-----------|:-------------|
|Light Truck |2.7 M       |51.8%         |
|Car/ Bike   |1.9 M       |36.1%         |
|Combo Truck |381.3 k     |7.3%          |
|Heavy Truck |220.7 k     |4.2%          |
|Bus         |30.6 k      |0.6%          |"""
    return reports, source_data


# 1. AI Quality Control Function #################################

## 1.1 Create Quality Control Prompt #################################

# Create a comprehensive quality control prompt based on samplevalidation.tex
# This prompt asks the AI to evaluate text on multiple criteria
def create_quality_control_prompt(report_text, source_data=None):
    # Tight role + output contract reduces hedging and invalid JSON (e.g. copying "true/false").
    instructions = (
        "You are a strict quality-control validator for short data reports. "
        "Score conservatively: prefer lower scores when uncertain. "
        "Respond with ONE JSON object only—no markdown fences, no text before or after the JSON."
    )

    if source_data is not None:
        data_context = (
            "\n\n--- SOURCE DATA (ground truth for factual checks) ---\n"
            f"{source_data.strip()}\n"
            "---\n"
            "Treat this as the only authority for checkable facts (geography, year, pollutant, "
            "category labels, counts, and percentages). Accept small rounding if clearly the same "
            "quantity (e.g. 12% vs 12.1%).\n"
        )
        accuracy_block = """
**accurate** (boolean): **Data-only gate.** true if every checkable claim in the report matches the Source Data (or sensible rounding of the same quantity). false only if something factual is wrong: a contradicting number, wrong label/category, wrong geography/year/pollutant, a bad combined total, or an invented figure.
  - Do **not** set false for writing quality, tone, vagueness, or “could be clearer”—use **clarity**, **formality**, **succinctness**, and the **accuracy** Likert for that.
  - If all facts in the report match the Source Data, **accurate must be true**, even if you rate **accuracy** below 5 because phrasing is loose.

**accuracy** (integer 1–5): How well the report reflects the **substance** of the Source Data (values, relationships, groupings). 1 = major factual errors; 3 = facts basically right but some ambiguous or imprecise wording; 5 = fully consistent. Reserve low scores for misread numbers or wrong relationships—not mere style. Before scoring, verify place/year/pollutant; then shares/totals; then combined groups (sums).
"""
    else:
        data_context = ""
        accuracy_block = """
**accurate** (boolean): **Internal logic only** (no Source Data). true if the paragraph’s numbers and claims do not contradict each other and arithmetic is possible. false only for internal contradictions or impossible arithmetic—not for informal tone or wordiness.

**accuracy** (integer 1–5): Coherence of numbers and claims within the paragraph. 1 = serious internal inconsistency; 3 = mostly coherent; 5 = self-consistent. Do not mark down for style; use **clarity** / **succinctness** for prose quality.
"""

    criteria = f"""
Evaluation workflow: (1) Decide **accurate** using **data facts or internal arithmetic only**—not style. (2) Score **accuracy** (Likert) for substance; then **faithfulness**. (3) Score style dimensions (**formality**, **clarity**, **succinctness**, **relevance**, **neutral_tone**).

{accuracy_block.strip()}

**faithfulness** (integer 1–5): 1 = grand claims, causal leaps, or implications not supported by the (available) data; 3 = mild overstatement; 5 = claims stay tightly tied to what the data can support. When Source Data is given, **accuracy** = numeric/factual fit; **faithfulness** = not overstating beyond evidence.

**formality** (integer 1–5): 1 = conversational; 3 = neutral professional; 5 = formal government or technical memo style.

**clarity** (integer 1–5): 1 = vague or hard to follow; 3 = understandable; 5 = precise and logically ordered.

**succinctness** (integer 1–5): 1 = padded or repetitive; 3 = reasonable; 5 = tight with no needless words.

**relevance** (integer 1–5): How much of the prose is *necessary* to interpret the supplied data vs generic commentary that could apply without these numbers. Score the *whole paragraph*, not just one sentence.
  - 1–2 = substantial off-topic filler, vague slogans, or generic environmental advice with little tie to the specific breakdown/year/place/pollutant.
  - 3 = a mix: core sentences follow the data, but noticeable generic policy language or repetition that does not add information from the data.
  - 4 = almost all content maps to categories, shares, or defensible implications from the data; at most one mildly generic clause.
  - 5 = every substantive sentence references the dataset’s entities (e.g. year, geography, pollutant, vehicle groups) or a direct implication; no purely generic paragraphs.
  Do not give 5 if most of the text is boilerplate that would read the same with different numbers removed. (This is separate from **faithfulness**, which is about *truth of claims*; **relevance** is about *whether sentences need this dataset at all*.)

**neutral_tone** (integer 1–5): **Bias and loaded language.** Higher = more appropriate for evidence-based reporting.
  - 1–2 = sensational, blame-oriented, or politically loaded wording; stereotypes; moralizing beyond what the data supports; “obviously / clearly / crisis” without justification.
  - 3 = mostly factual but some unnecessary heat or vague finger-pointing.
  - 4–5 = neutral, policy-appropriate tone; attributes findings to data; avoids undue alarmism or dismissiveness.
  (Aligns with manual QC flags like hyperbole or belittling phrases—score those here rather than under **accurate**.)

**details** (string, max ~50 words): If **accurate** is false, name the **specific data mismatch** (which figure or label is wrong). If any Likert is ≤2, say why. Do not cite “could be more concise” or style as the reason for **accurate** = false. Otherwise one short sentence on overall quality.

Rules: Likert fields must be integers 1–5 only. "accurate" must be JSON booleans true or false (lowercase). Example shape (replace with your scores):

{{
  "accurate": true,
  "accuracy": 1-5,
  "formality": 1-5,
  "faithfulness": 1-5,
  "clarity": 1-5,
  "succinctness": 1-5,
  "relevance": 1-5,
  "neutral_tone": 1-5,
  "details": "Brief justification, 0-50 words."
}}
"""

    full_prompt = f"{instructions}{data_context}\n\n--- REPORT TEXT ---\n{report_text.strip()}\n\n{criteria}"
    return full_prompt

## 1.2 Query AI Function #################################

# Function to query AI and get quality control results
def query_ai_quality_control(prompt, provider=AI_PROVIDER):
    if provider == "ollama":
        # Query Ollama (/api/chat is standard; /api/generate fallback for some proxies / older builds)
        chat_url = f"{OLLAMA_HOST}/api/chat"
        chat_body = {
            "model": OLLAMA_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "format": "json",
            "stream": False,
            "options": _ollama_options(),
        }
        response = requests.post(chat_url, json=chat_body, timeout=300)
        if response.status_code == 404:
            gen_url = f"{OLLAMA_HOST}/api/generate"
            gen_body = {
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "format": "json",
                "stream": False,
                "options": _ollama_options(),
            }
            response = requests.post(gen_url, json=gen_body, timeout=300)
        if not response.ok:
            hint = (
                " Is Ollama running (`ollama serve` or the desktop app)? "
                "Try `ollama pull " + OLLAMA_MODEL.split(":")[0] + "` and open "
                f"{OLLAMA_HOST}/api/tags in a browser (should list models). "
                "Or set AI_PROVIDER = \"openai\" with OPENAI_API_KEY in .env."
            )
            raise requests.HTTPError(
                f"{response.status_code} {response.reason} for url: {response.url}.{hint}",
                response=response,
            )
        response_data = response.json()
        if "message" in response_data:
            output = response_data["message"]["content"]
        else:
            output = response_data.get("response", "")
        
    elif provider == "openai":
        # Query OpenAI
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not found in .env file. Please set it up first.")
        
        url = "https://api.openai.com/v1/chat/completions"
        
        body = {
            "model": OPENAI_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a quality control validator. Always return your responses as valid JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "response_format": {"type": "json_object"},  # Request JSON output
            "temperature": 0.3  # Lower temperature for more consistent validation
        }
        
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(url, headers=headers, json=body)
        response.raise_for_status()
        response_data = response.json()
        output = response_data["choices"][0]["message"]["content"]
        
    else:
        raise ValueError("Invalid provider. Use 'ollama' or 'openai'.")
    
    return output

## 1.3 Parse Quality Control Results #################################

# Parse JSON response and convert to DataFrame
def parse_quality_control_results(json_response):
    # Try to parse JSON
    # Sometimes AI returns text with JSON, so we extract JSON if needed
    json_match = re.search(r"\{.*\}", json_response, re.DOTALL)
    if json_match:
        json_response = json_match.group(0)
    
    # Parse JSON
    quality_data = json.loads(json_response)
    
    # Convert to DataFrame
    results = pd.DataFrame({
        "accurate": [quality_data["accurate"]],
        "accuracy": [quality_data["accuracy"]],
        "formality": [quality_data["formality"]],
        "faithfulness": [quality_data["faithfulness"]],
        "clarity": [quality_data["clarity"]],
        "succinctness": [quality_data["succinctness"]],
        "relevance": [quality_data["relevance"]],
        "neutral_tone": [quality_data["neutral_tone"]],
        "details": [quality_data["details"]],
    })
    
    return results


# 3. Quality Control Multiple Reports #################################

## 3.1 Batch Quality Control Function #################################


def check_multiple_reports(reports, source_data=None):
    print(f"🔄 Performing quality control on {len(reports)} reports...\n")

    all_results = []

    for i, report_text in enumerate(reports, 1):
        print(f"Checking report {i} of {len(reports)}...")

        prompt = create_quality_control_prompt(report_text, source_data)

        try:
            response = query_ai_quality_control(prompt, provider=AI_PROVIDER)
            results = parse_quality_control_results(response)
            results["report_id"] = i
            all_results.append(results)
        except Exception as e:
            print(f"❌ Error checking report {i}: {e}")

        import time

        time.sleep(1)

    if all_results:
        return pd.concat(all_results, ignore_index=True)
    return pd.DataFrame()


# 2. Run Quality Control (script entry) #################################


def main():
    reports, source_data = load_sample_data()
    report = reports[0]

    print("📝 Report for Quality Control:")
    print("---")
    print(report)
    print("---\n")

    quality_prompt = create_quality_control_prompt(report, source_data)

    print("🤖 Querying AI for quality control...\n")

    ai_response = query_ai_quality_control(quality_prompt, provider=AI_PROVIDER)

    print("📥 AI Response (raw):")
    print(ai_response)
    print()

    quality_results = parse_quality_control_results(ai_response)

    print("✅ Quality Control Results:")
    print(quality_results)
    print()
    print("📝 Details (full):")
    print(quality_results["details"].iloc[0])
    print()

    likert_scores = quality_results[
        [
            "accuracy",
            "formality",
            "faithfulness",
            "clarity",
            "succinctness",
            "relevance",
            "neutral_tone",
        ]
    ]
    overall_score = likert_scores.mean(axis=1).values[0]

    quality_results["overall_score"] = round(overall_score, 2)

    print(f"📊 Overall Quality Score (average of Likert scales): {overall_score:.2f} / 5.0")
    print(f"📊 Accuracy Check: {'✅ PASS' if quality_results['accurate'].values[0] else '❌ FAIL'}\n")

    # Uncomment to check all reports
    # if len(reports) > 1:
    #     batch_results = check_multiple_reports(reports, source_data)
    #     print("\n📊 Batch Quality Control Results:")
    #     print(batch_results)

    print("✅ AI quality control complete!")
    print(
        "💡 Compare these results with manual quality control (01_manual_quality_control.py) to see how AI performs."
    )


if __name__ == "__main__":
    main()
