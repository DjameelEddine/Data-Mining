"""
Data loading, feature engineering, and holiday helpers.

This module mirrors the logic from the original Streamlit dashboard.py
but is structured as reusable functions for the FastAPI backend.
"""

from __future__ import annotations

from typing import Optional

import numpy as np
import holidays
import pandas as pd

from config import (
    CATEGORICAL_FEATURES,
    RCP_CATEGORICAL_FEATURES,
    DATA_PATH,
    RCP_DATA_PATH,
    PKG_DATA_PATH,
    FINAL_FEATURE_ORDER,
    RCP_FINAL_FEATURE_ORDER,
)

# ---------------------------------------------------------------------------
# Algerian holidays look-up table
# ---------------------------------------------------------------------------
_al_holidays = holidays.Algeria(years=list(range(2023, 2027)))
_holiday_df = (
    pd.DataFrame({"holiday_date": pd.to_datetime(list(_al_holidays.keys()))})
    .sort_values("holiday_date")
    .reset_index(drop=True)
)

# ---------------------------------------------------------------------------
# In-memory reference data (loaded once)
# ---------------------------------------------------------------------------
_reference_df: Optional[pd.DataFrame] = None
_rcp_reference_df: Optional[pd.DataFrame] = None


def load_reference_data() -> pd.DataFrame:
    """Load & normalise the packages test / reference CSV. Cached in module-level var."""
    global _reference_df
    if _reference_df is not None:
        return _reference_df

    df = pd.read_csv(PKG_DATA_PATH, encoding="latin-1")
    # Handle accented column names
    df.columns = df.columns.str.replace("Ã©", "e").str.replace("é", "e")
    df["date"] = pd.to_datetime(df["date"])
    df["MAILITM_FID"] = df["MAILITM_FID"].str.strip()
    if "next_etablissement_postal" in df.columns:
        df["next_etablissement_postal"] = df["next_etablissement_postal"].str.strip()
    _reference_df = df
    return _reference_df


def load_rcp_reference_data() -> pd.DataFrame:
    """Load & normalise the receptacles test / reference CSV. Cached in module-level var."""
    global _rcp_reference_df
    if _rcp_reference_df is not None:
        return _rcp_reference_df

    df = pd.read_csv(RCP_DATA_PATH, encoding="utf-8-sig")
    # Normalise column names to match expected names
    col_map = {}
    for c in df.columns:
        clean = c.strip().replace("\ufeff", "")
        # Map receptacle-specific column names to standard names
        if clean.upper() == "RECPTCL_FID" or "RECPTCL_FID" in clean:
            col_map[c] = "RECPTCL_FID"
        elif clean.replace("_", "").lower() in ("eventtypecd", "event_type_cd", "eventtypecd"):
            col_map[c] = "EVENT_TYPE_CD"
        elif clean.replace("_", "").lower() in ("nextetablissementpostal", "next_etablissement_postal", "nextetablissement_postal"):
            col_map[c] = "next_etablissement_postal"
        elif clean.replace("_", "").lower() in ("etablissementpostal", "etablissement_postal"):
            col_map[c] = "etablissement_postal"
        else:
            col_map[c] = clean
    df = df.rename(columns=col_map)

    df["date"] = pd.to_datetime(df["date"])
    df["RECPTCL_FID"] = df["RECPTCL_FID"].str.strip()
    if "next_etablissement_postal" in df.columns:
        df["next_etablissement_postal"] = df["next_etablissement_postal"].str.strip()
    # Cast EVENT_TYPE_CD to string
    if "EVENT_TYPE_CD" in df.columns:
        df["EVENT_TYPE_CD"] = df["EVENT_TYPE_CD"].astype(str)
    _rcp_reference_df = df
    return _rcp_reference_df


def get_reference_df() -> pd.DataFrame:
    """Return the cached packages reference dataframe."""
    if _reference_df is None:
        return load_reference_data()
    return _reference_df


def get_rcp_reference_df() -> pd.DataFrame:
    """Return the cached receptacles reference dataframe."""
    if _rcp_reference_df is None:
        return load_rcp_reference_data()
    return _rcp_reference_df


# ---------------------------------------------------------------------------
# ID parsing helpers
# ---------------------------------------------------------------------------

def parse_recptcl_fid(id_str: str):
    """Extract origin_country, destination_country from RECPTCL_FID."""
    return id_str[0:2], id_str[6:8]


def parse_mailitm_fid(id_str: str):
    """Extract service_indicator, serial_number, country_code from MAILITM_FID."""
    return id_str[0:2], id_str[2:11], id_str[11:14].strip()


# ---------------------------------------------------------------------------
# Flow type helper (used for receptacles)
# ---------------------------------------------------------------------------

def get_flow_type(origin_country: str, destination_country: str) -> str:
    """Determine flow type from origin and destination country codes."""
    if destination_country == "DZ" and origin_country == "DZ":
        return "local"
    elif destination_country == "DZ":
        return "inbound"
    elif origin_country == "DZ":
        return "outbound"
    return "other"


# ---------------------------------------------------------------------------
# Holiday features
# ---------------------------------------------------------------------------

def add_holidays_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")
    # Align datetime resolution to avoid merge_asof dtype mismatch
    holiday_df = _holiday_df.copy()
    holiday_df["holiday_date"] = holiday_df["holiday_date"].dt.as_unit(df["date"].dt.unit)
    df = pd.merge_asof(df, holiday_df, left_on="date", right_on="holiday_date", direction="backward")
    df["days_since_last_holiday"] = (df["date"] - df["holiday_date"]).dt.days.fillna(30).clip(upper=30)
    df = pd.merge_asof(
        df.drop(columns=["holiday_date"]),
        holiday_df,
        left_on="date",
        right_on="holiday_date",
        direction="forward",
    )
    df["days_until_next_holiday"] = (df["holiday_date"] - df["date"]).dt.days.fillna(30).clip(upper=30)
    return df.drop(columns=["holiday_date"])


# ---------------------------------------------------------------------------
# Load helpers (1-hour windows)
# ---------------------------------------------------------------------------

def calculate_etab_load_1h_single(row, full_df: pd.DataFrame) -> int:
    mask = (
        (full_df["etablissement_postal"] == row["etablissement_postal"])
        & (full_df["date"] >= row["date"] - pd.Timedelta(hours=1))
        & (full_df["date"] < row["date"])
    )
    return int(mask.sum())


def calculate_route_load_1h_single(row, full_df: pd.DataFrame) -> int:
    mask = (
        (full_df["etablissement_postal"] == row["etablissement_postal"])
        & (full_df["next_etablissement_postal"] == row["next_etablissement_postal"])
        & (full_df["date"] >= row["date"] - pd.Timedelta(hours=1))
        & (full_df["date"] < row["date"])
    )
    return int(mask.sum())


# ---------------------------------------------------------------------------
# Full feature engineering pipeline (single row prediction)
# ---------------------------------------------------------------------------

def prepare_features(row_df: pd.DataFrame, package_history: pd.DataFrame, full_df: pd.DataFrame) -> pd.DataFrame:
    """
    Reproduce the exact feature engineering used during model training.
    Returns a single-row DataFrame with columns in FINAL_FEATURE_ORDER.
    """
    df = row_df.copy()

    # Parse IDs
    mailitm_data = list(df["MAILITM_FID"].apply(parse_mailitm_fid))
    df[["service_indicator", "serial_number", "country_code"]] = pd.DataFrame(mailitm_data, index=df.index)
    recptcl_data = list(df["RECPTCL_FID"].apply(parse_recptcl_fid))
    df[["origin_country", "destination_country"]] = pd.DataFrame(recptcl_data, index=df.index)

    # Derived columns
    df["origin_destination"] = df["origin_country"] + "_" + df["destination_country"]
    df["country_service"] = df["origin_country"].astype(str) + "_" + df["service_indicator"].astype(str)
    df["month"] = df["date"].dt.month
    df["hour"] = df["date"].dt.hour
    df["day_of_week"] = df["date"].dt.day_name()
    df["is_weekend"] = df["date"].dt.dayofweek.isin([4, 5]).astype(int)
    df["first_last_week_day"] = df["date"].dt.dayofweek.isin([0, 4]).astype(int)

    df = add_holidays_features(df)

    # Loads
    df["etab_load_1h"] = calculate_etab_load_1h_single(df.iloc[0], full_df)
    df["route_load_1h"] = calculate_route_load_1h_single(df.iloc[0], full_df)

    # Time since first / last scan
    df["time_since_first_scan"] = (
        (df.iloc[0]["date"] - package_history["date"].min()).total_seconds() / 3600
    )
    if len(package_history) > 1:
        sorted_history = package_history.sort_values("date")
        df["time_since_last_scan"] = (
            (df.iloc[0]["date"] - sorted_history.iloc[-2]["date"]).total_seconds() / 3600
        )
    else:
        df["time_since_last_scan"] = 0.0

    # Fill NaN for categorical features
    for col in CATEGORICAL_FEATURES:
        if col in df.columns:
            df[col] = df[col].fillna("UNKNOWN").astype(str)

    return df[FINAL_FEATURE_ORDER]


# ---------------------------------------------------------------------------
# Receptacle feature engineering pipeline (single row prediction)
# ---------------------------------------------------------------------------

def prepare_rcp_features(
    row_df: pd.DataFrame,
    receptacle_history: pd.DataFrame,
    full_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Reproduce the exact feature engineering used during receptacle model training.
    Returns a single-row DataFrame with columns in RCP_FINAL_FEATURE_ORDER.
    """
    df = row_df.copy()

    # Parse RECPTCL_FID
    recptcl_data = list(df["RECPTCL_FID"].apply(parse_recptcl_fid))
    df[["origin_country", "destination_country"]] = pd.DataFrame(recptcl_data, index=df.index)

    # Derived columns
    df["origin_destination"] = df["origin_country"] + "_" + df["destination_country"]
    df["flow_type"] = df.apply(
        lambda r: get_flow_type(r["origin_country"], r["destination_country"]), axis=1
    )
    df["month"] = df["date"].dt.month
    df["hour"] = df["date"].dt.hour
    df["day_of_week"] = df["date"].dt.day_name()

    # Loads
    df["etab_load_1h"] = calculate_etab_load_1h_single(df.iloc[0], full_df)
    df["route_load_1h"] = calculate_route_load_1h_single(df.iloc[0], full_df)

    # Time since first / last scan
    df["time_since_first_scan"] = (
        (df.iloc[0]["date"] - receptacle_history["date"].min()).total_seconds() / 3600
    )
    if len(receptacle_history) > 1:
        sorted_history = receptacle_history.sort_values("date")
        df["time_since_last_scan"] = (
            (df.iloc[0]["date"] - sorted_history.iloc[-2]["date"]).total_seconds() / 3600
        )
    else:
        df["time_since_last_scan"] = 0.0

    # packages_per_receptacle: count of packages in the package reference df
    # that share this RECPTCL_FID
    pkg_ref = get_reference_df()
    recptcl_fid = df.iloc[0]["RECPTCL_FID"]
    packages_count = int((pkg_ref["RECPTCL_FID"] == recptcl_fid).sum())
    df["packages_per_receptacle"] = packages_count

    # EVENT_TYPE_CD should be string for categorical
    df["EVENT_TYPE_CD"] = df["EVENT_TYPE_CD"].astype(str)

    # Fill NaN for categorical features
    for col in RCP_CATEGORICAL_FEATURES:
        if col in df.columns:
            df[col] = df[col].fillna("UNKNOWN").astype(str)

    return df[RCP_FINAL_FEATURE_ORDER]

