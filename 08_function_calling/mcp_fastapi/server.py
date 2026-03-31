# server.py
# Stateless MCP Server — FastAPI (Python)
# Pairs with mcp_plumber/plumber.R
# Tim Fraser

# What this file is:
#   A FastAPI app that speaks the Model Context Protocol (MCP) over HTTP.
#   It mirrors plumber.R: same tools, same JSON-RPC methods, Streamable HTTP behavior.
#   Stateless: each POST /mcp is one JSON-RPC request → one JSON response (or 202 for notifications).
#
# How to run locally:
#   uvicorn server:app --port 8000 --reload
#   or: python runme.py
#
# How to deploy:
#   See deployme.py
#
# Packages:
#   pip install fastapi uvicorn pandas
#   (requests only needed if you use testme.py for Ollama)

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
import pandas as pd
import json

app = FastAPI()

# ── Tool definitions (what the LLM sees) ────────────────────

TOOLS = [
    {
        "name": "summarize_dataset",
        "description": "Returns mean, sd, min, and max for each numeric column in a dataset.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "dataset_name": {
                    "type": "string",
                    "description": "Dataset to summarize. Options: 'mtcars' or 'iris'.",
                }
            },
            "required": ["dataset_name"],
        },
    },
    {
        "name": "linear_regression",
        "description": "Fits a simple linear regression y ~ a + b*x between two numeric columns.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "dataset_name": {
                    "type": "string",
                    "description": "Dataset to use. Options: 'mtcars' or 'iris'.",
                },
                "x_variable": {
                    "type": "string",
                    "description": "Numeric column name to use as the predictor (x).",
                },
                "y_variable": {
                    "type": "string",
                    "description": "Numeric column name to use as the response (y).",
                },
            },
            "required": ["dataset_name", "x_variable", "y_variable"],
        },
    },
]

# ── Tool logic (same datasets as R: mtcars, iris via Rdatasets CSV) ──

_DATASET_URLS = {
    "mtcars": "https://vincentarelbundock.github.io/Rdatasets/csv/datasets/mtcars.csv",
    "iris": "https://vincentarelbundock.github.io/Rdatasets/csv/datasets/iris.csv",
}
DATASETS = {name: pd.read_csv(url) for name, url in _DATASET_URLS.items()}


def run_tool(name: str, args: dict) -> str:
    if name == "summarize_dataset":
        nm = args.get("dataset_name")
        if nm not in DATASETS:
            raise ValueError(f"Unknown dataset: '{nm}' — choose 'mtcars' or 'iris'")

        df = DATASETS[nm].select_dtypes(include="number")
        summary = df.agg(["mean", "std", "min", "max"]).round(2).T
        summary.index.name = "variable"
        summary.columns = ["mean", "sd", "min", "max"]
        return summary.reset_index().to_json(orient="records", indent=2)

    if name == "linear_regression":
        nm = args.get("dataset_name")
        if nm not in DATASETS:
            raise ValueError(f"Unknown dataset: '{nm}' — choose 'mtcars' or 'iris'")

        x_col = args.get("x_variable")
        y_col = args.get("y_variable")
        if not x_col or not y_col:
            raise ValueError("Missing required inputs: 'x_variable' and 'y_variable'")

        df = DATASETS[nm].select_dtypes(include="number")
        if x_col not in df.columns:
            raise ValueError(f"Unknown x_variable '{x_col}' for dataset '{nm}'")
        if y_col not in df.columns:
            raise ValueError(f"Unknown y_variable '{y_col}' for dataset '{nm}'")

        xy = df[[x_col, y_col]].dropna()
        n = len(xy)
        if n < 2:
            raise ValueError("Need at least 2 non-missing paired observations to fit regression")

        x = xy[x_col]
        y = xy[y_col]

        # OLS for a simple regression y ~ a + b*x using covariance/variance identities.
        x_var = x.var()
        if x_var == 0:
            raise ValueError("x_variable has zero variance; regression slope is undefined")

        slope = x.cov(y) / x_var
        intercept = y.mean() - slope * x.mean()

        y_pred = intercept + slope * x
        residuals = y - y_pred

        sse = (residuals**2).sum()
        sst = ((y - y.mean()) ** 2).sum()
        r_squared = None if sst == 0 else 1 - (sse / sst)

        result = {
            "dataset_name": nm,
            "x_variable": x_col,
            "y_variable": y_col,
            "n": int(n),
            "slope": round(float(slope), 6),
            "intercept": round(float(intercept), 6),
            "r_squared": None if r_squared is None else round(float(r_squared), 6),
            "x_mean": round(float(x.mean()), 6),
            "y_mean": round(float(y.mean()), 6),
        }
        return json.dumps(result, indent=2)

    raise ValueError(f"Unknown tool: {name}")


# ── MCP JSON-RPC router ──────────────────────────────────────


@app.post("/mcp")
async def mcp_post(request: Request):
    body = await request.json()

    method = body.get("method")
    id_ = body.get("id")

    if isinstance(method, str) and method.startswith("notifications/"):
        return Response(status_code=202)

    try:
        if method == "initialize":
            result = {
                "protocolVersion": "2025-03-26",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "py-summarizer", "version": "0.1.0"},
            }
        elif method == "ping":
            result = {}
        elif method == "tools/list":
            result = {"tools": TOOLS}
        elif method == "tools/call":
            tool_result = run_tool(
                body["params"]["name"],
                body["params"]["arguments"],
            )
            result = {
                "content": [{"type": "text", "text": tool_result}],
                "isError": False,
            }
        else:
            raise ValueError(f"Method not found: {method}")

    except Exception as e:
        return JSONResponse(
            {"jsonrpc": "2.0", "id": id_, "error": {"code": -32601, "message": str(e)}}
        )

    return JSONResponse({"jsonrpc": "2.0", "id": id_, "result": result})


@app.options("/mcp")
async def mcp_options():
    return Response(
        status_code=204,
        headers={"Allow": "GET, POST, OPTIONS"},
    )


@app.get("/mcp")
async def mcp_get():
    return Response(
        content=json.dumps(
            {"error": "This MCP server uses stateless HTTP. Use POST."}
        ),
        status_code=405,
        headers={"Allow": "GET, POST, OPTIONS"},
        media_type="application/json",
    )
