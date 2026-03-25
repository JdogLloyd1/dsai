# lab_lloyd_rag.py
# RAG workflow template for Rye NYRCR plan
# Based on 02_txt.py
# Tim Fraser
#
# This script demonstrates Retrieval-Augmented Generation (RAG) on the
# Rye NYRCR plan text file. Edit the query section below to explore
# different topics and question prompts.

# 0. SETUP ###################################

## 0.1 Load Packages #################################

import os        # for file path operations
import sys       # for Python import path
import runpy     # for executing another Python script
import requests  # for HTTP requests
import json      # for working with JSON

## 0.2 Working Directory #################################

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

## 0.3 Start Ollama Server (source 01_ollama.py) #################################

# Execute 01_ollama.py as if we were sourcing it in R.
# This will configure environment variables and start `ollama serve` in the background.
ollama_script_path = os.path.join(script_dir, "01_ollama.py")
_ = runpy.run_path(ollama_script_path)

## 0.4 Load Functions #################################

# Load helper functions for agent orchestration
from functions import agent_run

## 0.5 Configuration #################################

# Select model of interest
MODEL = "smollm2:1.7b"  # use this small model
PORT = 11434
OLLAMA_HOST = f"http://localhost:{PORT}"
DOCUMENT = os.path.join(script_dir, "data", "plans", "rye_nyrcr_plan.txt")

# 1. EDITABLE INPUTS ###################################

# Edit these two fields for your lab work.
# - SEARCH_QUERY controls what content gets retrieved from the plan.
# - USER_QUESTION is what the LLM answers using that retrieved content.
SEARCH_QUERY = "Rye Golf Club"  
USER_QUESTION = "What does the plan say about this topic?  Format as plain, easily readable text for terminal window output with a title and well-structured paragraphs."


# Optional: number of matching lines to keep (top-to-bottom as found)
MAX_MATCH_LINES = 25

# 2. SEARCH FUNCTION ###################################

def search_text(query, document_path, max_lines=25):
    """
    Search a text file for lines containing the query.

    Returns a dictionary with retrieved text and metadata.
    """

    # Read the text file line-by-line
    with open(document_path, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    # Keep lines that contain the query (case-insensitive)
    query_lower = query.lower().strip()
    matches = [line.strip() for line in lines if query_lower in line.lower()]

    # Trim to a manageable amount of context for the model
    kept_matches = matches[:max_lines]
    result_text = "\n".join(kept_matches)

    return {
        "query": query,
        "document": os.path.basename(document_path),
        "document_path": document_path,
        "num_lines_found": len(matches),
        "num_lines_kept": len(kept_matches),
        "matching_content": result_text
    }

# 3. TEST SEARCH FUNCTION ###################################

print("Testing search function...")
test_result = search_text(SEARCH_QUERY, DOCUMENT, max_lines=MAX_MATCH_LINES)
print(f"Found {test_result['num_lines_found']} matching lines")
print(f"Keeping {test_result['num_lines_kept']} lines for LLM context")
print()

# 4. RAG WORKFLOW ###################################

# Task 1: Retrieve relevant plan content
result1 = search_text(SEARCH_QUERY, DOCUMENT, max_lines=MAX_MATCH_LINES)
result1_json = json.dumps(result1, indent=2)

# Task 2: Ask the model to answer using only retrieved context
role = (
    "You are a policy analysis assistant. "
    "Answer the user question using only the retrieved plan text provided. "
    "If the retrieved text is incomplete, explicitly say what is missing. "
    "Format your response in markdown with a title and bullet points."
)

task = (
    f"User question: {USER_QUESTION}\n\n"
    f"Retrieved context (JSON):\n{result1_json}"
)

result2 = agent_run(
    role=role,
    task=task,
    model=MODEL,
    output="text"
)

print("Generated Answer:")
print(result2)
print()

# 5. ALTERNATIVE: MANUAL CHAT APPROACH ###################################

CHAT_URL = f"{OLLAMA_HOST}/api/chat"
messages = [
    {"role": "system", "content": role},
    {"role": "user", "content": task}
]
body = {
    "model": MODEL,
    "messages": messages,
    "stream": False
}

response = requests.post(CHAT_URL, json=body)
response.raise_for_status()
response_data = response.json()
result2b = response_data["message"]["content"]

print("Alternative Approach Result:")
print(result2b)
