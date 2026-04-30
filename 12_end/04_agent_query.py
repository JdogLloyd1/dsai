# 04_agent_query.py
# Agent with REST Tool Call
# Pairs with 04_agent_query.R
# Tim Fraser

import sys
import os
import json
import re
import ast
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
# Force import from 08_function_calling, not local 12_end/functions.py.
sys.path.insert(0, str(ROOT_DIR / "08_function_calling"))

from dotenv import load_dotenv
from functions import agent

import requests

# 1. CONFIG ###################################

load_dotenv(ROOT_DIR / "12_end" / ".env")

ENDPOINT_URL = os.getenv("API_PUBLIC_URL", "http://localhost:8000").rstrip("/")
MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:latest")

UNIT_NOTE = "vehicles observed in one representative minute (1m/t1 interval) within the requested hour and day of week"

# 2. DEFINE TOOL FUNCTION ###################################

def parse_day_of_week(day_value):
    # Convert common model outputs into ISO weekday integer (1=Mon, ..., 7=Sun).
    if isinstance(day_value, dict):
        day_value = (
            day_value.get("day_of_week")
            or day_value.get("value")
            or day_value.get("day")
            or day_value.get("weekday")
            or day_value.get("name")
        )

    if isinstance(day_value, str):
        name_map = {
            "monday": 1, "mon": 1,
            "tuesday": 2, "tue": 2, "tues": 2,
            "wednesday": 3, "wed": 3,
            "thursday": 4, "thu": 4, "thur": 4, "thurs": 4,
            "friday": 5, "fri": 5,
            "saturday": 6, "sat": 6,
            "sunday": 7, "sun": 7,
        }
        clean = day_value.strip().lower()
        if clean in name_map:
            return name_map[clean]
        return int(clean)

    return int(day_value)


def parse_hours_of_day(hours_value):
    # Accept several model-emitted formats:
    # - [0, 1, 2]
    # - "[0, 1, 2]"
    # - "0,1,2"
    # - "0 1 2"
    # - {"hours":[...]} / {"value":[...]}
    if isinstance(hours_value, dict):
        hours_value = (
            hours_value.get("hours_of_day")
            or hours_value.get("hours")
            or hours_value.get("value")
            or []
        )

    if isinstance(hours_value, str):
        text = hours_value.strip()
        if not text:
            return []

        # Try strict JSON first.
        try:
            parsed = json.loads(text)
            hours_value = parsed
        except json.JSONDecodeError:
            # Then try Python-literal list strings.
            try:
                parsed = ast.literal_eval(text)
                hours_value = parsed
            except (ValueError, SyntaxError):
                # Finally, extract all integers from free-form text.
                nums = re.findall(r"-?\d+", text)
                hours_value = [int(n) for n in nums]

    if isinstance(hours_value, (int, float)):
        hours_value = [hours_value]

    if not isinstance(hours_value, list):
        raise ValueError("hours_of_day must be list-like or a parseable hours string.")

    hours = [int(h) for h in hours_value if 0 <= int(h) <= 23]
    return hours


def predict_vehicle_count(day_of_week, hours_of_day):
    day_of_week = parse_day_of_week(day_of_week)

    hours = parse_hours_of_day(hours_of_day)
    if not hours:
        raise ValueError("hours_of_day must contain at least one integer between 0 and 23.")

    predictions = []
    for hour in hours:
        resp = requests.get(
            f"{ENDPOINT_URL}/predict",
            params={"day_of_week": int(day_of_week), "hour_of_day": hour},
            timeout=10,
        )
        resp.raise_for_status()
        predictions.append(
            {
                "hour_of_day": hour,
                "predicted_vehicle_count": float(resp.json()["predicted_vehicle_count"]),
            }
        )

    return {
        "day_of_week": day_of_week,
        "unit": "vehicles_observed_in_one_minute",
        "interval": "1m_t1",
        "note": "Each prediction is for one representative minute within that hour and day of week.",
        "predictions": predictions,
    }

# 3. DEFINE TOOL METADATA ###################################

tool_predict_vehicle_count = {
    "type": "function",
    "function": {
        "name": "predict_vehicle_count",
        "description": (
            "Predict Brussels vehicle count for a specific day of week and vector of hours. "
            "Returns one estimated vehicle count per requested hour. "
            "Each value is for one representative minute (1m/t1 interval) within that hour on that day of week."
        ),
        "parameters": {
            "type": "object",
            "required": ["day_of_week", "hours_of_day"],
            "properties": {
                "day_of_week": {"type": "integer", "description": "Day of week (1=Monday, ..., 7=Sunday)"},
                "hours_of_day": {
                    "type": "array",
                    "description": "Vector of hours to predict (0-23), e.g. [0,1,2,...,23].",
                    "items": {"type": "integer"},
                },
            }
        }
    }
}

# 4. RUN AGENT ###################################

# Prompt options:
# "Predict Brussels vehicle count for Monday for every hour (0 through 23)."
# "Predict Brussels vehicle count for Monday at 8 AM."
# "Predict Brussels vehicle count for Saturday at 10 PM."

messages = [
    {
        "role": "system",
        "content": (
            "You are a Brussels traffic assistant. "
            "Always report units clearly as vehicles observed in one representative minute "
            "(1m/t1 interval) within the requested hour and day of week. "
            "Call predict_vehicle_count using day_of_week and hours_of_day vector."
        ),
    },
    {
        "role": "user",
        "content": "Predict Brussels vehicle count for Monday for every hour (0 through 23).",
    }
]
tools = [tool_predict_vehicle_count]

raw_result = agent(
    messages=messages,
    model=MODEL,
    output="text",
    tools=tools,
    all=True
)

# Some local models return empty content without tool calls.
# If that happens, use a deterministic fallback so students still get a result.
tool_calls = raw_result.get("message", {}).get("tool_calls", [])
if tool_calls and tool_calls[-1].get("output") is not None:
    result = tool_calls[-1]["output"]
else:
    print("Warning: model returned no tool call; using direct fallback.")
    result = predict_vehicle_count(day_of_week=1, hours_of_day=list(range(24)))

print("Agent result:", result)

# 5. VERIFY ###################################

direct = predict_vehicle_count(day_of_week=1, hours_of_day=list(range(24)))
print("Direct API call predictions returned:", len(direct["predictions"]))
print(f"Sample one-minute vehicle count: {direct['predictions'][8]['predicted_vehicle_count']} (1m/t1 at Monday 08:00)")
print("Unit:", UNIT_NOTE)
print("Match:", str(direct["predictions"][8]["predicted_vehicle_count"]) in str(result))
