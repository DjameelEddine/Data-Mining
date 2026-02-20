"""
Machine-learning service: CatBoost model loading, prediction, and logging.
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Optional

import pandas as pd
from catboost import CatBoostRegressor

from config import MODEL_PATH, PREDICTIONS_LOG

# ---------------------------------------------------------------------------
# Model singleton
# ---------------------------------------------------------------------------
_model: Optional[CatBoostRegressor] = None


def load_model() -> CatBoostRegressor:
    """Load the CatBoost model (cached in module-level variable)."""
    global _model
    if _model is not None:
        return _model
    _model = CatBoostRegressor()
    _model.load_model(MODEL_PATH)
    return _model


def get_model() -> CatBoostRegressor:
    if _model is None:
        return load_model()
    return _model


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------

def predict(features_df: pd.DataFrame) -> float:
    """Run a prediction and return the value (hours)."""
    model = get_model()
    return float(model.predict(features_df)[0])


# ---------------------------------------------------------------------------
# Prediction logging (append-only CSV)
# ---------------------------------------------------------------------------

def prediction_exists(mailitm_fid: str, features_df: pd.DataFrame) -> bool:
    if not os.path.exists(PREDICTIONS_LOG):
        return False
    existing_df = pd.read_csv(PREDICTIONS_LOG)
    if existing_df.empty:
        return False
    mask = (
        (existing_df["MAILITM_FID"] == mailitm_fid)
        & (existing_df["time_since_first_scan"].round(2) == features_df["time_since_first_scan"].iloc[0].round(2))
    )
    return bool(mask.any())


def log_prediction(mailitm_fid: str, prediction_val: float, features_df: pd.DataFrame) -> bool:
    """Append prediction to CSV. Returns True if saved, False if duplicate."""
    if prediction_exists(mailitm_fid, features_df):
        return False

    log_entry = features_df.copy()
    log_entry.insert(0, "prediction_timestamp", datetime.now())
    log_entry.insert(1, "MAILITM_FID", mailitm_fid)
    log_entry.insert(2, "predicted_duration_hours", round(prediction_val, 2))

    header = not os.path.exists(PREDICTIONS_LOG)
    log_entry.to_csv(PREDICTIONS_LOG, mode="a", index=False, header=header)
    return True


def get_predictions_log() -> Optional[pd.DataFrame]:
    """Return the predictions log as a DataFrame, or None if it doesn't exist."""
    if not os.path.exists(PREDICTIONS_LOG):
        return None
    df = pd.read_csv(PREDICTIONS_LOG)
    return df if not df.empty else None
