from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_FILES = (
    PROJECT_ROOT / "data" / "support_tickets.csv",
    PROJECT_ROOT / "data" / "support_tickets.xlsx",
    PROJECT_ROOT / "extracted" / "support_tickets.csv",
)

REQUIRED_COLUMNS = {
    "ticket_id",
    "created_at",
    "category",
    "priority",
    "status",
    "response_time_hrs",
    "resolution_time_hrs",
    "agent_id",
    "customer_rating",
    "issue_summary",
}

NUMERIC_COLUMNS = (
    "response_time_hrs",
    "resolution_time_hrs",
    "customer_rating",
)


def _read_data_file(path):
    if path.suffix.lower() in {".xlsx", ".xls"}:
        return pd.read_excel(path)
    return pd.read_csv(path)


def load_data():
    """Load and normalize the support ticket dataset."""
    for path in DATA_FILES:
        if path.exists():
            df = _read_data_file(path)
            break
    else:
        searched = ", ".join(str(path.relative_to(PROJECT_ROOT)) for path in DATA_FILES)
        raise FileNotFoundError(f"Support ticket data not found. Searched: {searched}")

    missing_columns = REQUIRED_COLUMNS.difference(df.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Dataset is missing required columns: {missing}")

    df = df.copy()
    df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")

    for column in NUMERIC_COLUMNS:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    return df
