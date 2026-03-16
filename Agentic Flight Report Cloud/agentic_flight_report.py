# agentic_flight_report.py
# Agentic Flight Report Multi-Agent Workflow
# Pairs with agentic_flight_report_functions.py
# Tim Fraser
#
# This script demonstrates how to build a set of agents to query live web data,
# build an on-time picture of the US airspace, and interpret that picture for a
# specific flight. Students will learn how to orchestrate multiple agents and
# how to use a single web_search tool to pull real-time information.

# 0. SETUP ###################################

## 0.1 Load Packages #################################

import pandas as pd  # for potential data manipulation (not heavily used yet)
import requests      # for HTTP requests used by helper functions
import os
from pathlib import Path

# If you haven't already, install these packages...
# pip install pandas requests

# Set working directory to this script's folder.
# This makes relative imports and file paths consistent.
os.chdir("C:/Users/jonyl/iCloudDrive/Documents/GitHub/dsai/12_end")

## 0.2 Load Functions #################################

# Load helper functions for agent orchestration
from agentic_flight_report_functions import agent_run


# 1. CONFIGURATION ###################################

# Select model of interest (cloud-hosted)
MODEL = "qwen3.5:cloud"

# User flight information (students can edit these values)
user_flight = {
    "carrier": "AA",
    "flight_number": "849",
    "date": "2026-03-16",
    "origin": "DFW",
    "destination": "BOS"
}


def format_flight_info(flight_dict):
    """
    Format user flight information as a short text block.
    """
    return (
        f"Carrier: {flight_dict.get('carrier', '')}\n"
        f"Flight number: {flight_dict.get('flight_number', '')}\n"
        f"Date: {flight_dict.get('date', '')}\n"
        f"Origin: {flight_dict.get('origin', '')}\n"
        f"Destination: {flight_dict.get('destination', '')}"
    )


# 2. WORKFLOW EXECUTION ###################################

# Task 1 - Airspace + Network Summary Agent -------------------------

# This agent gathers FAA, weather, and flight status information for the US
# airspace (using Ollama Cloud's integrated web/browsing capabilities) and
# produces a network-level summary in one step.
role_scraper = (
    "I am an aviation operations and weather research assistant and network "
    "analyst. I build an objective snapshot of the current and near-term "
    "status of the U.S. National Airspace System (NAS) by browsing the web "
    "to check official FAA status pages, aviation weather products, and "
    "high-quality flight-tracking statistics, then I synthesize this "
    "information into a network-level summary. I clearly distinguish between "
    "official sources and third-party summaries."
)

task_scraper = (
    "Use your integrated web browsing and web search capabilities to "
    "construct a concise but detailed snapshot of the current and near-term "
    "U.S. airspace situation for today, and then synthesize that information "
    "into a network-level summary. Always start by consulting the core sites "
    "below, then optionally add more sources if the picture is incomplete. "
    "Do not look up any specific individual flight yet.\n\n"
    "Core sites to check (you may navigate and search within them as needed):\n"
    "- FAA NAS status: https://nasstatus.faa.gov/\n"
    "- Aviation Weather Center Terminal Weather Dashboard (text-centric): https://aviationweather.gov/impactboard/\n"
    "- System-wide delays and cancellations from FlightAware: https://www.flightaware.com/live/cancelled\n\n"
    "Optional enrichment when needed (only if necessary to clarify the picture):\n"
    "- FAA NOTAM or TFR pages for large airspace restrictions or special events.\n"
    "- Airline or airport bulletins and travel waivers on major carrier or hub airport sites.\n\n"
    "When reading each page, ignore navigation menus, cookie banners, legal notices, "
    "and generic UI or marketing text. Focus only on numeric statistics, operational "
    "summaries, and natural-language descriptions of delays, cancellations, traffic "
    "flow programs, and weather impacts on air traffic.\n\n"
    "After gathering information, output a structured plain-text report with "
    "clear sections titled exactly:\n"
    "- NAS Status (FAA)\n"
    "- Current Operational Weather (AWC)\n"
    "- System-Level Delays and Cancellations (FlightAware)\n"
    "- Other Operational Factors (NOTAMs, TFRs, airline/airport issues)\n"
    "- Network-Level Summary by Region and Hub\n\n"
    "In the Network-Level Summary section, include:\n"
    "- A short executive overview (2–3 sentences) describing overall network "
    "health (for example, mostly on time, moderately disrupted, or severely "
    "disrupted).\n"
    "- A by-region breakdown of conditions and causes.\n"
    "- A list of the top 3–5 most impacted hubs with brief explanations.\n"
    "- Any notable trends through the day (improving, stable, or worsening, if "
    "supported by the data).\n\n"
    "User flight (for context only, do not analyze it yet):\n\n"
    + format_flight_info(user_flight)
)

airspace_summary = agent_run(
    role=role_scraper,
    task=task_scraper,
    model=MODEL,
    tools=None,
    output="text"
)

print("Task 1 complete")
print(f"[DEBUG] Airspace summary length: {len(airspace_summary) if airspace_summary else 0}")
print(f"[DEBUG] Airspace summary preview: {repr(airspace_summary[:400]) if airspace_summary else 'EMPTY'}")


# Task 2 - Personal Flight Agent -------------------------

# This agent explains how the current US airspace situation affects the user's flight.
role_personal = (
    "I am a personal flight advisor. I interpret the current U.S. airspace and "
    "weather situation in the context of one specific passenger’s itinerary. "
    "I explain, in plain language, how network-level disruptions and weather "
    "patterns are likely to affect that flight, including delay/cancellation "
    "risk, connection risk, and practical recommendations for the traveler."
)

task_personal = (
    "You are given a network-level on-time picture of the U.S. airspace and a "
    "specific user flight (carrier, flight number, date, origin, destination). "
    "Your job is to translate this into concrete, traveler-focused guidance.\n\n"
    "Your analysis should:\n"
    "- Summarize key parts of the network picture that matter for this itinerary: conditions at origin and destination airports (and any known connections) and any region-wide issues along the route.\n"
    "- Assess the likelihood of delay or cancellation for this flight in qualitative terms (for example, low, moderate, or high), based on the network picture.\n"
    "- If there is a connection, assess connection risk (whether a normal layover is likely sufficient under today’s conditions).\n\n"
    "You may use your integrated web browsing and web search capabilities "
    "sparingly if needed to refine the assessment—for example, to check "
    "airline or airport travel advisories, aggregate disruption statistics, "
    "or generic flight status search pages (such as airline status portals "
    "or general search pages). Avoid constructing deep, hand-crafted URLs; "
    "instead, navigate via known landing pages and search fields. If a page "
    "clearly provides no useful information, treat this as 'no specific data "
    "available' and move on, rather than focusing on error details.\n\n"
    "Output a structured explanation that includes:\n"
    "- A short plain-language summary of the situation for the passenger (for example, low risk of disruption, moderate risk of delay, or high risk of significant disruption).\n"
    "- A brief explanation of key risk drivers (weather at origin/destination, en-route weather, congestion at hubs, ATC programs, non-weather issues).\n"
    "- Practical recommendations: when to arrive at the airport, whether to monitor for waivers, whether to consider alternative flights, and what to prepare for (for example, possible overnight).\n"
    "- Explicit statements about uncertainty (for example, these are likelihoods, not guarantees).\n\n"
    "Network picture:\n"
    + airspace_summary
    + "\n\nUser flight:\n"
    + format_flight_info(user_flight)
)

personal_report = agent_run(
    role=role_personal,
    task=task_personal,
    model=MODEL,
    tools=None,
    output="text"
)


# 3. VIEW RESULTS ###################################

print("US Airspace + Network Summary (from Agent 1):")
if airspace_summary:
    print(airspace_summary)
else:
    print("(No airspace summary text returned from the model.)")

print("\nAgentic Flight Report (personalized):")
print(personal_report)

