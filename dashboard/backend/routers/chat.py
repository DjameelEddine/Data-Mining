"""
/api/chat – AI chat endpoint.
"""

from __future__ import annotations

from fastapi import APIRouter

from schemas import ChatRequest
from services.ai_service import query_data_with_ai
from services.data_service import get_reference_df
from services.ml_service import get_predictions_log

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat")
def chat(body: ChatRequest):
    """Ask the AI assistant a question about the data."""
    ref_df = get_reference_df()
    pred_df = get_predictions_log()
    result = query_data_with_ai(body.message, ref_df, pred_df)
    return result
