import ast
import re

import numpy as np
import pandas as pd

from src.llm import ask_llm

COLUMNS = """
ticket_id
created_at
category
priority
status
response_time_hrs
resolution_time_hrs
agent_id
customer_rating
issue_summary
"""

ALLOWED_NAMES = {"df", "pd", "np"}
ALLOWED_METHODS = {
    "agg",
    "all",
    "any",
    "casefold",
    "contains",
    "count",
    "describe",
    "endswith",
    "dropna",
    "fillna",
    "first",
    "groupby",
    "head",
    "idxmax",
    "idxmin",
    "isna",
    "last",
    "lower",
    "max",
    "mean",
    "median",
    "min",
    "mode",
    "nlargest",
    "notna",
    "nsmallest",
    "reset_index",
    "round",
    "sort_index",
    "sort_values",
    "startswith",
    "std",
    "sum",
    "tail",
    "to_dict",
    "unique",
    "value_counts",
}
ALLOWED_ATTRIBUTES = ALLOWED_METHODS | {"dt", "shape", "str", "T"}
SAFE_NODE_TYPES = (
    ast.Expression,
    ast.Call,
    ast.Name,
    ast.Load,
    ast.Constant,
    ast.Subscript,
    ast.Attribute,
    ast.Tuple,
    ast.List,
    ast.Dict,
    ast.Slice,
    ast.BinOp,
    ast.BoolOp,
    ast.Compare,
    ast.UnaryOp,
    ast.keyword,
    ast.And,
    ast.Or,
    ast.Not,
    ast.Eq,
    ast.NotEq,
    ast.Lt,
    ast.LtE,
    ast.Gt,
    ast.GtE,
    ast.In,
    ast.NotIn,
    ast.Is,
    ast.IsNot,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.FloorDiv,
    ast.Mod,
    ast.Pow,
    ast.BitAnd,
    ast.BitOr,
    ast.USub,
    ast.UAdd,
)


def _clean_generated_code(code):
    code = code.strip()
    code = re.sub(r"^```(?:python|py)?\s*", "", code, flags=re.IGNORECASE)
    code = re.sub(r"\s*```$", "", code)
    if code.lower().startswith("answer:"):
        code = code.split(":", 1)[1].strip()
    return code.strip()


def _root_name(node):
    while isinstance(node, (ast.Attribute, ast.Subscript, ast.Call)):
        node = node.value if not isinstance(node, ast.Call) else node.func
    return node.id if isinstance(node, ast.Name) else None


def _validate_expression(code):
    tree = ast.parse(code, mode="eval")

    for node in ast.walk(tree):
        if not isinstance(node, SAFE_NODE_TYPES):
            raise ValueError(f"Unsupported expression element: {type(node).__name__}")

        if isinstance(node, ast.Name) and node.id not in ALLOWED_NAMES:
            raise ValueError(f"Unsupported name: {node.id}")

        if isinstance(node, ast.Attribute):
            if node.attr.startswith("_") or node.attr not in ALLOWED_ATTRIBUTES:
                raise ValueError(f"Unsupported attribute: {node.attr}")

        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Attribute):
                raise ValueError("Only DataFrame, Series, pandas, and numpy method calls are allowed.")
            if node.func.attr not in ALLOWED_METHODS:
                raise ValueError(f"Unsupported method call: {node.func.attr}")
            if _root_name(node.func) not in ALLOWED_NAMES:
                raise ValueError("Method call target is not allowed.")

    return tree


def _execute_pandas_expression(code, df):
    tree = _validate_expression(code)
    return eval(
        compile(tree, filename="<pandas-query>", mode="eval"),
        {"__builtins__": {}},
        {"df": df, "pd": pd, "np": np},
    )


def _fallback_query(question):
    normalized = question.lower().strip()

    if "open" in normalized and ("how many" in normalized or "count" in normalized):
        return 'df[df["status"].str.casefold()=="open"].shape[0]'

    if "lowest" in normalized and "customer rating" in normalized and "agent" in normalized:
        return 'df.groupby("agent_id")["customer_rating"].mean().idxmin()'

    if "resolved the most" in normalized and "agent" in normalized:
        return 'df[df["status"].str.casefold()=="resolved"].groupby("agent_id")["ticket_id"].count().idxmax()'

    if "average" in normalized and "customer rating" in normalized:
        if "technical" in normalized:
            return 'df[df["category"].str.casefold()=="technical"]["customer_rating"].mean()'
        return 'df["customer_rating"].mean()'

    if "critical" in normalized and ("unresolved" in normalized or "not resolved" in normalized):
        return 'df[(df["priority"].str.casefold()=="critical") & (df["status"].str.casefold()!="resolved")]'

    return None


def generate_pandas_query(question):
    """Convert natural language question to pandas expression using LLM"""
    fallback_code = _fallback_query(question)
    if fallback_code:
        return fallback_code

    prompt = f"""
You are a data analyst.

DataFrame name is df.

Available columns:

{COLUMNS}

Return ONLY one pandas expression.

Do not import anything.
Do not define functions.
Do not use loops.
Do not use print.

Return ONLY valid pandas code.

Examples:

Question: How many tickets are open?
Answer: df[df["status"]=="Open"].shape[0]

Question: What is the average customer rating?
Answer: df["customer_rating"].mean()

Question: {question}
"""

    return _clean_generated_code(ask_llm(prompt))

def run_query(question, df):
    """Execute natural language query on DataFrame"""
    if not question or not question.strip():
        return {
            "query": "",
            "error": "Please enter a question."
        }

    try:
        code = generate_pandas_query(question)
        result = _execute_pandas_expression(code, df)

        return {
            "query": code,
            "result": result
        }
    except Exception as e:
        return {
            "query": locals().get("code", ""),
            "error": str(e)
        }
