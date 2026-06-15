# DOTMappers Support Tickets API

Prototype FastAPI application that ingests the provided `support_tickets` CSV and exposes:

- `POST /query` — answer natural-language queries (uses Hugging Face for parsing if `HF_API_TOKEN` is set)
- `GET /anomalies` — returns simple rule-based anomalies

Setup

1. Create virtualenv and install:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

2. Ensure the data exists at `extracted/support_tickets.csv` (the extractor script previously run creates it).

3. (Optional) Set Hugging Face token to enable LLM parsing:

```powershell
setx HF_API_TOKEN "your_token_here"
```

Run

```bash
uvicorn app:app --reload
```

Tests

```bash
pytest -q
```
