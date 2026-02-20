"""
AI chat service using Google Gemini.
"""

from __future__ import annotations

from typing import Any, Optional

import pandas as pd
import google.generativeai as genai

from config import GEMINI_API_KEY

# ---------------------------------------------------------------------------
# Initialise Gemini
# ---------------------------------------------------------------------------
genai.configure(api_key=GEMINI_API_KEY)
_ai_model = genai.GenerativeModel("gemini-2.5-flash")


def query_data_with_ai(
    user_query: str,
    reference_df: pd.DataFrame,
    predictions_df: Optional[pd.DataFrame],
) -> dict[str, Any]:
    """
    Ask Gemini to write pandas code, execute it, and return the result.
    Returns {"reply": str, "data": Any}.
    """
    pred_cols = list(predictions_df.columns) if predictions_df is not None else "No predictions logged yet."

    prompt = f"""
You are a data assistant for Algerie Post.
Dataframes available:
1. `reference_df`: Historical scans. Columns: {list(reference_df.columns)}
2. `predictions_df`: Past predictions. Columns: {pred_cols}

User Query: "{user_query}"

Task: Write ONLY Python code using pandas to answer.
- Store the final result in a variable named `result`.
- If the user asks for "today", use `pd.Timestamp.now()`.
- Return ONLY the code. No markdown, no backticks, no explanations.
"""

    try:
        response = _ai_model.generate_content(prompt)
        clean_code = response.text.replace("```python", "").replace("```", "").strip()

        context_vars: dict[str, Any] = {
            "reference_df": reference_df,
            "predictions_df": predictions_df,
            "pd": pd,
        }
        exec(clean_code, {}, context_vars)  # noqa: S102
        result = context_vars.get("result", "I couldn't find an answer.")

        # Serialise pandas objects to something JSON-friendly
        if isinstance(result, pd.DataFrame):
            return {"reply": "Here are the results:", "data": result.to_dict(orient="records")}
        if isinstance(result, pd.Series):
            return {"reply": "Here are the results:", "data": result.to_dict()}
        return {"reply": str(result), "data": None}

    except Exception as exc:
        return {"reply": f"AI Error: {exc}", "data": None}
