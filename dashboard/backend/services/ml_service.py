"""
Machine-learning service: CatBoost model loading, prediction, and logging.
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Optional

import pandas as pd
from catboost import CatBoostRegressor

from config import PKG_MODEL_PATH, RCP_MODEL_PATH, PKG_PREDICTIONS_LOG, RCP_PREDICTIONS_LOG

# ---------------------------------------------------------------------------
# Model singletons
# ---------------------------------------------------------------------------
_pkg_model: Optional[CatBoostRegressor] = None
_rcp_model: Optional[CatBoostRegressor] = None


def load_model() -> CatBoostRegressor:
    """Load the packages CatBoost model (cached)."""
    global _pkg_model
    if _pkg_model is not None:
        return _pkg_model
    _pkg_model = CatBoostRegressor()
    _pkg_model.load_model(PKG_MODEL_PATH)
    return _pkg_model


def load_rcp_model() -> CatBoostRegressor:
    """Load the receptacles CatBoost model (cached)."""
    global _rcp_model
    if _rcp_model is not None:
        return _rcp_model
    _rcp_model = CatBoostRegressor()
    _rcp_model.load_model(RCP_MODEL_PATH)
    return _rcp_model


def get_model() -> CatBoostRegressor:
    if _pkg_model is None:
        return load_model()
    return _pkg_model


def get_rcp_model() -> CatBoostRegressor:
    if _rcp_model is None:
        return load_rcp_model()
    return _rcp_model


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------

def predict(features_df: pd.DataFrame) -> float:
    """Run a package prediction and return the value (hours)."""
    model = get_model()
    return float(model.predict(features_df)[0])


def predict_receptacle(features_df: pd.DataFrame) -> float:
    """Run a receptacle prediction and return the value (hours)."""
    model = get_rcp_model()
    return float(model.predict(features_df)[0])


# ---------------------------------------------------------------------------
# Prediction logging (append-only CSV) – separate logs
# ---------------------------------------------------------------------------

def _prediction_exists(log_path: str, id_col: str, id_val: str, features_df: pd.DataFrame) -> bool:
    if not os.path.exists(log_path):
        return False
    existing_df = pd.read_csv(log_path)
    if existing_df.empty:
        return False
    mask = (
        (existing_df[id_col] == id_val)
        & (existing_df["time_since_first_scan"].round(2) == features_df["time_since_first_scan"].iloc[0].round(2))
    )
    return bool(mask.any())


def _log_prediction(log_path: str, id_col: str, id_val: str, prediction_val: float, features_df: pd.DataFrame) -> bool:
    """Append prediction to CSV. Returns True if saved, False if duplicate."""
    if _prediction_exists(log_path, id_col, id_val, features_df):
        return False

    log_entry = features_df.copy()
    log_entry.insert(0, "prediction_timestamp", datetime.now())
    log_entry.insert(1, id_col, id_val)
    log_entry.insert(2, "predicted_duration_hours", round(prediction_val, 2))

    header = not os.path.exists(log_path)
    log_entry.to_csv(log_path, mode="a", index=False, header=header)
    return True


# --- Package-specific wrappers ---

def prediction_exists(mailitm_fid: str, features_df: pd.DataFrame) -> bool:
    return _prediction_exists(PKG_PREDICTIONS_LOG, "MAILITM_FID", mailitm_fid, features_df)


def log_prediction(mailitm_fid: str, prediction_val: float, features_df: pd.DataFrame) -> bool:
    return _log_prediction(PKG_PREDICTIONS_LOG, "MAILITM_FID", mailitm_fid, prediction_val, features_df)


def get_predictions_log() -> Optional[pd.DataFrame]:
    """Return the package predictions log as a DataFrame, or None."""
    if not os.path.exists(PKG_PREDICTIONS_LOG):
        return None
    df = pd.read_csv(PKG_PREDICTIONS_LOG)
    return df if not df.empty else None


# --- Receptacle-specific wrappers ---

def rcp_prediction_exists(recptcl_fid: str, features_df: pd.DataFrame) -> bool:
    return _prediction_exists(RCP_PREDICTIONS_LOG, "RECPTCL_FID", recptcl_fid, features_df)


def log_rcp_prediction(recptcl_fid: str, prediction_val: float, features_df: pd.DataFrame) -> bool:
    return _log_prediction(RCP_PREDICTIONS_LOG, "RECPTCL_FID", recptcl_fid, prediction_val, features_df)


def get_rcp_predictions_log() -> Optional[pd.DataFrame]:
    """Return the receptacle predictions log as a DataFrame, or None."""
    if not os.path.exists(RCP_PREDICTIONS_LOG):
        return None
    df = pd.read_csv(RCP_PREDICTIONS_LOG)
    return df if not df.empty else None
