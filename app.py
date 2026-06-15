from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path
import os
import requests
import json
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
from dotenv import load_dotenv

# Load .env file
load_dotenv()

app = FastAPI(title="DOTMappers Support Tickets API")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_PATH = Path("extracted/support_tickets.csv")
HF_TOKEN = os.getenv("HF_API_TOKEN")
HF_MODEL = os.getenv("HF_MODEL", "google/flan-t5-base")


class QueryRequest(BaseModel):
    question: str


def load_data():
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Data file not found: {DATA_PATH}")
    df = pd.read_csv(DATA_PATH)
    # parse dates
    for c in ["created_at"]:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors="coerce")
    return df


def call_hf(prompt: str) -> str:
    if not HF_TOKEN:
        return ""
    url = f"https://api-inference.huggingface.co/models/{HF_MODEL}"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    payload = {"inputs": prompt, "parameters": {"max_new_tokens": 200}}
    r = requests.post(url, headers=headers, json=payload, timeout=30)
    r.raise_for_status()
    data = r.json()
    # inference API may return text in different shapes
    if isinstance(data, dict) and "error" in data:
        raise RuntimeError(data["error"])
    if isinstance(data, list) and len(data) > 0 and "generated_text" in data[0]:
        return data[0]["generated_text"]
    if isinstance(data, str):
        return data
    # fallback: join any text fields
    try:
        return json.dumps(data)
    except Exception:
        return str(data)


def parse_question(question: str) -> dict:
    # Use HF to convert question into a JSON action; fallback to simple rules when HF not available
    instructions = (
        "You are given a ticket dataset with columns: ticket_id, created_at, category, priority, status, "
        "response_time_hrs, resolution_time_hrs, agent_id, customer_rating, issue_summary.\n"
        "Return a JSON object with keys: action (one of 'filter_count','groupby_agg','list','raw'), "
        "filter (a pandas-query compatible expression or empty), group_by (list or null), agg (object or null).\n"
        "Example: {\"action\":\"filter_count\",\"filter\":\"priority == 'High' and status != 'Resolved'\",\"group_by\":null,\"agg\":null}\n"
        "ONLY return the JSON object and no other text. Question: " + question
    )
    try:
        if HF_TOKEN:
            resp = call_hf(instructions)
            # Try to extract JSON from response
            start = resp.find("{")
            if start != -1:
                resp_json = resp[start:]
                return json.loads(resp_json)
        # fallback simple rule-based parser
        q = question.lower()
        if "how many" in q or "count" in q:
            if "unresolved" in q or "not resolved" in q:
                if "critical" in q or "high priority" in q or "high-priority" in q or "high priority" in q:
                    filt = "(priority == 'High' or priority == 'Critical') and status != 'Resolved'"
                else:
                    filt = "status != 'Resolved'"
            else:
                filt = ""
            return {"action": "filter_count", "filter": filt, "group_by": None, "agg": None}
        if "which agent" in q or ("agent" in q and "average" in q):
            return {"action": "groupby_agg", "filter": "", "group_by": ["agent_id"], "agg": {"field": "customer_rating", "op": "mean"}}
        # default: return raw
        return {"action": "raw", "filter": "", "group_by": None, "agg": None}
    except Exception:
        return {"action": "raw", "filter": "", "group_by": None, "agg": None}


def sanitize(obj):
    # recursively sanitize objects for JSON
    if isinstance(obj, dict):
        return {k: sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [sanitize(x) for x in obj]
    if pd.isna(obj):
        return None
    if isinstance(obj, (pd.Timestamp, datetime)):
        return obj.isoformat()
    if isinstance(obj, float):
        if np.isinf(obj) or np.isnan(obj):
            return None
        return float(obj)
    return obj


@app.get("/")
def root():
    """Serve the UI"""
    index_path = Path("index.html")
    if index_path.exists():
        return FileResponse(str(index_path), media_type="text/html")
    return {"message": "UI not found. Ensure index.html exists in the root directory."}


@app.post("/query")
def query(req: QueryRequest):
    df = load_data()
    spec = parse_question(req.question)
    action = spec.get("action")
    filt = spec.get("filter") or ""
    try:
        if filt:
            subset = df.query(filt)
        else:
            subset = df
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid filter expression: {e}")

    if action == "filter_count":
        return {"count": int(subset.shape[0]), "explain": spec}
    if action == "groupby_agg":
        gb = subset.groupby(spec.get("group_by", []))
        agg = spec.get("agg") or {}
        field = agg.get("field")
        op = agg.get("op")
        if not field or not op:
            raise HTTPException(status_code=400, detail="Missing agg field/op")
        if op == "mean":
            res = gb[field].mean().reset_index().sort_values(by=field)
        elif op == "sum":
            res = gb[field].sum().reset_index()
        else:
            raise HTTPException(status_code=400, detail="Unsupported agg op")
        result = res.to_dict(orient="records")
        return {"result": sanitize(result), "explain": spec}
    if action == "list":
        items = subset.head(50).to_dict(orient="records")
        return {"items": sanitize(items), "explain": spec}
    # raw or unknown
    preview = subset.head(20).to_dict(orient="records")
    return {"preview": sanitize(preview), "explain": spec}


@app.get("/anomalies")
def anomalies():
    df = load_data()
    results = {}
    # anomaly 1: resolution_time_hrs unusually high
    if "resolution_time_hrs" in df.columns:
        series = df["resolution_time_hrs"].dropna()
        if not series.empty:
            mu = series.mean()
            sigma = series.std()
            thresh = mu + 3 * sigma
            hi = df[df["resolution_time_hrs"] > thresh]
            # sanitize dataframe for JSON (convert datetimes, replace inf/nan)
            hi = hi.replace([np.inf, -np.inf], np.nan)
            if "created_at" in hi.columns:
                hi["created_at"] = hi["created_at"].apply(lambda x: x if pd.notnull(x) else None)
            records = hi.head(50).to_dict(orient="records")
            results["slow_resolution"] = sanitize(records)
        else:
            results["slow_resolution"] = []
    # anomaly 2: unresolved high-priority older than 24 hours
    if "created_at" in df.columns and "priority" in df.columns and "status" in df.columns:
        now = pd.Timestamp.now()
        mask = (df["status"] != "Resolved") & (df["priority"].isin(["High", "Critical"])) & ((now - df["created_at"]) > pd.Timedelta(hours=24))
        chunk = df[mask].head(50)
        chunk = chunk.replace([np.inf, -np.inf], np.nan)
        if "created_at" in chunk.columns:
            chunk["created_at"] = chunk["created_at"].apply(lambda x: x if pd.notnull(x) else None)
        records = chunk.to_dict(orient="records")
        results["old_unresolved_high_priority"] = sanitize(records)
    return results


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
