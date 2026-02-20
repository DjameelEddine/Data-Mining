"""
Application configuration and constants.
"""

import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths – resolved relative to the project root (two levels up from here)
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent.parent  # Data-Mining/

PKG_MODEL_PATH = str(BASE_DIR / "models" / "final_pkg_route_duration_model.cbm")
RCP_MODEL_PATH = str(BASE_DIR / "models" / "final_rcp_route_duration_model.cbm")
# Keep legacy alias
MODEL_PATH = PKG_MODEL_PATH

PKG_DATA_PATH = str(BASE_DIR / "data" / "test" / "small_test_data.csv")
RCP_DATA_PATH = str(BASE_DIR / "data" / "test" / "receptacles_test.csv")
# Keep legacy alias
DATA_PATH = PKG_DATA_PATH

PKG_PREDICTIONS_LOG = str(BASE_DIR / "data" / "pkg_predictions_log.csv")
RCP_PREDICTIONS_LOG = str(BASE_DIR / "data" / "rcp_predictions_log.csv")
# Keep legacy alias
PREDICTIONS_LOG = PKG_PREDICTIONS_LOG

# ---------------------------------------------------------------------------
# Gemini AI
# ---------------------------------------------------------------------------
GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY",
    "AIzaSyAuwnAJ0NOpna6ci-zmxHeOM2F0HEwKbxo",
)

# ---------------------------------------------------------------------------
# Feature order – MUST match the order the CatBoost model was trained with
# ---------------------------------------------------------------------------
FINAL_FEATURE_ORDER = [
    "etablissement_postal",
    "EVENT_TYPE_CD",
    "next_etablissement_postal",
    "hour",
    "day_of_week",
    "service_indicator",
    "origin_destination",
    "month",
    "is_weekend",
    "first_last_week_day",
    "country_service",
    "days_since_last_holiday",
    "days_until_next_holiday",
    "etab_load_1h",
    "route_load_1h",
    "time_since_first_scan",
    "time_since_last_scan",
]

RCP_FINAL_FEATURE_ORDER = [
    "etablissement_postal",
    "EVENT_TYPE_CD",
    "next_etablissement_postal",
    "origin_destination",
    "flow_type",
    "month",
    "hour",
    "day_of_week",
    "packages_per_receptacle",
    "etab_load_1h",
    "route_load_1h",
    "time_since_first_scan",
    "time_since_last_scan",
]

CATEGORICAL_FEATURES = [
    "etablissement_postal",
    "next_etablissement_postal",
    "day_of_week",
    "service_indicator",
    "origin_destination",
    "country_service",
]

RCP_CATEGORICAL_FEATURES = [
    "etablissement_postal",
    "next_etablissement_postal",
    "day_of_week",
    "origin_destination",
    "EVENT_TYPE_CD",
    "flow_type",
]

# ---------------------------------------------------------------------------
# CORS – allow the Next.js dev server
# ---------------------------------------------------------------------------
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
