# agentic_flight_report_functions.py
# Agentic Flight Report - Helper Functions
# Pairs with agentic_flight_report.py
# Tim Fraser (adapted)
#
# This script contains helper functions used for the Agentic Flight Report
# multi-agent orchestration example, including a single web_search tool
# that local Ollama models can call via the /api/chat tools interface.

# 0. SETUP ###################################

## 0.1 Load Packages #################################

import os
import requests  # for HTTP requests
import json      # for working with JSON
import pandas as pd  # for data manipulation
from dotenv import load_dotenv

# If you haven't already, install these packages...
# pip install requests pandas

## 0.2 Configuration #################################

# Default model and Ollama Cloud connection (native /api/chat)
DEFAULT_MODEL = "smollm2:1.7b"
OLLAMA_CLOUD_BASE = "https://ollama.com/api"
CHAT_URL = f"{OLLAMA_CLOUD_BASE}/chat"

# Load environment variables from .env (if present) and read API key
load_dotenv()
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY")


# 1. AGENT FUNCTION ###################################

def agent(messages, model=DEFAULT_MODEL, output="text", tools=None, all=False):
    """
    Agent wrapper function that runs a single agent, with or without tools.
    """
    
    # Build headers with API key
    if not OLLAMA_API_KEY:
        raise ValueError("OLLAMA_API_KEY not found in environment. Please set it in your .env file.")

    headers = {
        "Authorization": f"Bearer {OLLAMA_API_KEY}",
        "Content-Type": "application/json",
    }

    # Native Ollama Cloud /api/chat body
    body = {
        "model": model,
        "messages": messages,
        "stream": False,
    }

    # NOTE: For Cloud, we rely on Ollama's built-in web/RAG.
    # We do not send local tool definitions in this request body.

    response = requests.post(CHAT_URL, headers=headers, json=body)
    response.raise_for_status()
    result = response.json()

    # Native /api/chat responses put the content here:
    # result["message"]["content"]
    if all:
        return result
    else:
        return result.get("message", {}).get("content", "")


def agent_run(role, task, tools=None, output="text", model=DEFAULT_MODEL):
    """
    Run an agent with a specific role and task.
    """
    
    messages = [
        {"role": "system", "content": role},
        {"role": "user", "content": task}
    ]
    
    resp = agent(messages=messages, model=model, output=output, tools=tools)
    return resp


# 2. DATA CONVERSION FUNCTION ###################################

def df_as_text(df):
    """
    Convert a pandas DataFrame to a markdown table string.
    """
    
    tab = df.to_markdown(index=False)
    return tab


# 3. WEB PAGE FETCH TOOL FUNCTIONS ###################################

def url_query(url, max_chars=20000):
    """
    Fetch a web page and return its main text content.
    
    Designed to be used as an Ollama tool. The model should pass a full URL
    (for example, https://nasstatus.faa.gov/) and will receive back the page
    text with HTML tags stripped and whitespace normalized.
    """
    
    # Coerce max_chars to an integer, with a safe fallback
    try:
        max_chars_int = int(max_chars)
    except (TypeError, ValueError):
        max_chars_int = 20000
    
    try:
        response = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
    except Exception as e:
        return f"Error fetching URL {url}: {e}"
    
    html = response.text
    
    # Strip scripts, styles, and tags, then normalize whitespace
    import re
    # Remove script and style blocks (case-insensitive, dot matches newlines)
    text = re.sub(r"(?is)<script.*?</script>", " ", html)
    text = re.sub(r"(?is)<style.*?</style>", " ", text)
    # Remove all remaining HTML tags
    text = re.sub(r"<[^>]+>", " ", text)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    
    if not text:
        return f"No readable text content found at {url}."
    
    return text[:max_chars_int]


def web_search_general(query, max_results=5):
    """
    Perform a general web search using a public API (DuckDuckGo Instant Answer)
    and return a summarized text of the most relevant results.
    """
    
    # Coerce max_results to an integer with a safe fallback
    try:
        max_results_int = int(max_results)
    except (TypeError, ValueError):
        max_results_int = 5
    
    url = "https://api.duckduckgo.com/"
    params = {
        "q": query,
        "format": "json",
        "no_redirect": 1,
        "no_html": 1
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        return f"Error performing general web search for '{query}': {e}"
    
    pieces = []
    
    abstract = data.get("AbstractText")
    if abstract:
        pieces.append(f"Abstract: {abstract}")
    
    heading = data.get("Heading")
    if heading:
        pieces.append(f"Heading: {heading}")
    
    related = data.get("RelatedTopics", [])[:max_results_int]
    for item in related:
        if isinstance(item, dict) and item.get("Text"):
            text = item.get("Text", "")
            url_item = item.get("FirstURL", "")
            pieces.append(f"- {text} (URL: {url_item})")
    
    if not pieces:
        return f"No results found for general search query: {query}"
    
    return "\n".join(pieces)


# 4. TOOL METADATA FOR WEB SEARCH ###################################

WEB_SEARCH_TOOLS = [
    # Tool 1: fetch a specific URL and return its text content
    {
        "type": "function",
        "function": {
            "name": "url_query",
            "description": "Fetch a web page and return its main text content, given a full URL.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "Full URL of the page to fetch."
                    },
                    "max_chars": {
                        "type": "integer",
                        "description": "Maximum number of characters of page text to return.",
                        "default": 20000
                    }
                },
                "required": ["url"]
            }
        }
    },
    # Tool 2: perform a general web search and return summarized results
    {
        "type": "function",
        "function": {
            "name": "web_search_general",
            "description": "Perform a general web search for live information and return a summarized text of the most relevant results.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query describing the information needed."
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to summarize.",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        }
    }
]

