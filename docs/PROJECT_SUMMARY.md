# AI Support Ticket Assistant - Project Summary

## Overview

This project is a Streamlit-based support ticket analytics assistant. It loads a local ticket dataset, provides a dashboard for exploration, supports natural-language questions, and highlights operational anomalies.

## Technology Stack

- Frontend and app runtime: Streamlit
- Data processing: Pandas and NumPy
- LLM provider: Groq
- Configuration: python-dotenv
- Dataset: CSV

## Dataset

The canonical dataset is:

```text
data/support_tickets.csv
```

Expected columns:

| Column | Description |
| --- | --- |
| ticket_id | Unique ticket identifier |
| created_at | Ticket creation timestamp |
| category | Ticket category |
| priority | Priority level |
| status | Current ticket status |
| response_time_hrs | Hours until first response |
| resolution_time_hrs | Hours until resolution |
| agent_id | Support agent identifier |
| customer_rating | Customer satisfaction rating |
| issue_summary | Short issue description |

## Main Files

- `app.py`: Streamlit interface and app entry point.
- `src/data_loader.py`: Loads CSV/XLSX data, validates schema, and normalizes types.
- `src/query_engine.py`: Converts questions to safe Pandas expressions and executes them.
- `src/llm.py`: Optional Groq integration for LLM-generated queries.
- `src/anomaly_detector.py`: Rule-based anomaly detection.
- `data/support_tickets.csv`: Ticket dataset used by the app.

## Query Flow

1. User enters a question in the Streamlit UI.
2. `run_query()` checks for built-in deterministic question patterns.
3. If no built-in pattern matches, the prompt is sent to Groq when `GROQ_API_KEY` is configured.
4. The generated Pandas expression is validated with an AST allowlist.
5. The expression runs against the in-memory DataFrame.
6. The result is displayed as a value or table.

## Built-in Questions

The app can answer these common questions without calling Groq:

- Count currently open tickets.
- Find the agent with the lowest average customer rating.
- Calculate average customer rating overall or for Technical tickets.
- List Critical tickets that are not resolved.
- Find the agent who resolved the most tickets.

## Anomaly Detection

The anomaly tab reports:

- Long resolution times: `resolution_time_hrs > mean + 2 * standard deviation`
- Critical unresolved tickets: `priority == Critical` and `status != Resolved`
- Low customer ratings: `customer_rating <= 2`

## Running Locally

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Open `http://localhost:8501`.

## Environment

Use `.env.example` as a template:

```text
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
```

Do not commit `.env`.
