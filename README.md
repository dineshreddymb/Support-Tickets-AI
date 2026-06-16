# AI Support Ticket Assistant

An interactive Streamlit app for exploring support ticket data, asking natural-language questions, and detecting operational anomalies.

## Features

- View the full support ticket dataset in a browser.
- Ask common ticket analytics questions in plain English.
- Use Groq for LLM-generated Pandas queries when a question is not handled by built-in rules.
- Detect critical unresolved tickets, long resolution times, and low customer ratings.
- Run locally with a simple Windows batch file or Streamlit command.

## Project Structure

```text
.
├── app.py
├── requirements.txt
├── run.bat
├── .env.example
├── data/
│   └── support_tickets.csv
├── docs/
│   └── PROJECT_SUMMARY.md
└── src/
    ├── __init__.py
    ├── anomaly_detector.py
    ├── data_loader.py
    ├── llm.py
    └── query_engine.py
```

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Create a local `.env` file if you want LLM-backed questions:

```text
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
```

The app still works without a Groq key for built-in common questions and anomaly detection.

## Run

```powershell
python -m streamlit run app.py
```

Or on Windows:

```powershell
.\run.bat
```

Open:

```text
http://localhost:8501
```

## Example Questions

- How many tickets are currently open?
- Which agent has the lowest average customer rating?
- What is the average customer rating for Technical tickets?
- Show all Critical tickets that remain unresolved.
- Which agent resolved the most tickets?

## Validation

```powershell
python -m compileall app.py src
```

## Notes

- Do not commit `.env`; use `.env.example` as the template.
- The canonical dataset is `data/support_tickets.csv`.
- Generated files such as `.venv/`, `__pycache__/`, and logs are ignored.
