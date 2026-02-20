"""
/api/predict – run a prediction for a given package.
/api/predict/receptacle – run a prediction for a given receptacle.
/api/predictions – view prediction logs (separate for packages and receptacles).
"""

from __future__ import annotations

from fastapi import APIRouter

from services.data_service import (
    get_reference_df,
    get_rcp_reference_df,
    prepare_features,
    prepare_rcp_features,
    parse_recptcl_fid,
)
from services.ml_service import (
    predict,
    predict_receptacle,
    log_prediction,
    log_rcp_prediction,
    get_predictions_log,
    get_rcp_predictions_log,
)

router = APIRouter(prefix="/api", tags=["predictions"])

# ---------------------------------------------------------------------------
# 15-day threshold in hours
# ---------------------------------------------------------------------------
DELAY_THRESHOLD_HOURS = 15 * 24  # 360 hours


@router.post("/predict/{mailitm_fid}")
def predict_route(mailitm_fid: str):
    """Run the CatBoost model for the latest scan of a package."""
    ref = get_reference_df()
    package_history = ref[ref["MAILITM_FID"] == mailitm_fid.strip()].sort_values("date")

    if package_history.empty:
        return {"error": f"Package ID {mailitm_fid} not found."}

    latest_row = package_history.iloc[[-1]]
    row_data = latest_row.iloc[0]

    features_df = prepare_features(latest_row, package_history, ref)
    prediction = predict(features_df)

    time_since_first_scan = float(features_df["time_since_first_scan"].iloc[0])

    # ── Total duration calculation ──
    # Find the RECPTCL_FID for this package's latest scan
    recptcl_fid = str(row_data.get("RECPTCL_FID", ""))
    receptacle_time_since_first_scan = 0.0
    if recptcl_fid:
        # Look up the receptacle in the receptacles dataset
        rcp_ref = get_rcp_reference_df()
        rcp_records = rcp_ref[rcp_ref["RECPTCL_FID"] == recptcl_fid].sort_values("date")
        if not rcp_records.empty:
            rcp_first_scan = rcp_records["date"].min()
            rcp_latest_scan = rcp_records["date"].max()
            receptacle_time_since_first_scan = (
                (rcp_latest_scan - rcp_first_scan).total_seconds() / 3600
            )

    total_estimated_time = receptacle_time_since_first_scan + prediction
    is_delayed = total_estimated_time > DELAY_THRESHOLD_HOURS

    # Determine speed label
    if prediction < 6:
        route_speed = "fast"
    elif prediction < 24:
        route_speed = "normal"
    else:
        route_speed = "slow"

    was_saved = log_prediction(mailitm_fid, prediction, features_df)

    # Build features dict for display
    features_dict = {col: str(features_df[col].iloc[0]) for col in features_df.columns}

    # Build journey history
    history_cols = ["date", "etablissement_postal", "next_etablissement_postal", "EVENT_TYPE_CD"]
    history = (
        package_history[history_cols]
        .sort_values("date", ascending=False)
        .head(10)
    )
    journey_history = []
    for _, hr in history.iterrows():
        journey_history.append({
            "date": str(hr["date"])[:19],
            "etablissement_postal": str(hr["etablissement_postal"]),
            "next_etablissement_postal": str(hr.get("next_etablissement_postal", "")),
            "EVENT_TYPE_CD": str(hr["EVENT_TYPE_CD"]),
        })

    return {
        "mailitm_fid": mailitm_fid,
        "prediction_hours": round(prediction, 2),
        "time_since_first_scan_hours": round(time_since_first_scan, 2),
        "receptacle_time_since_first_scan_hours": round(receptacle_time_since_first_scan, 2),
        "total_estimated_hours": round(total_estimated_time, 2),
        "total_estimated_days": round(total_estimated_time / 24, 1),
        "is_delayed": is_delayed,
        "delay_threshold_days": 15,
        "route_speed": route_speed,
        "current_location": str(row_data.get("etablissement_postal", "N/A")),
        "next_location": str(row_data.get("next_etablissement_postal", "")) or None,
        "event_type": str(row_data.get("EVENT_TYPE_CD", "N/A")),
        "last_scan_date": str(row_data["date"])[:19],
        "total_scans": len(package_history),
        "recptcl_fid": recptcl_fid,
        "was_saved": was_saved,
        "features": features_dict,
        "journey_history": journey_history,
    }


@router.post("/predict/receptacle/{recptcl_fid}")
def predict_receptacle_route(recptcl_fid: str):
    """Run the CatBoost receptacle model for the latest scan of a receptacle."""
    rcp_ref = get_rcp_reference_df()
    receptacle_history = rcp_ref[rcp_ref["RECPTCL_FID"] == recptcl_fid.strip()].sort_values("date")

    if receptacle_history.empty:
        return {"error": f"Receptacle ID {recptcl_fid} not found."}

    latest_row = receptacle_history.iloc[[-1]]
    row_data = latest_row.iloc[0]

    features_df = prepare_rcp_features(latest_row, receptacle_history, rcp_ref)
    prediction = predict_receptacle(features_df)

    time_since_first_scan = float(features_df["time_since_first_scan"].iloc[0])
    total_estimated_time = time_since_first_scan + prediction

    # Determine speed label
    if prediction < 6:
        route_speed = "fast"
    elif prediction < 24:
        route_speed = "normal"
    else:
        route_speed = "slow"

    was_saved = log_rcp_prediction(recptcl_fid, prediction, features_df)

    # Build features dict for display
    features_dict = {col: str(features_df[col].iloc[0]) for col in features_df.columns}

    # Parse origin/destination for display
    origin_country, destination_country = parse_recptcl_fid(recptcl_fid)

    # Build journey history
    history_cols = ["date", "etablissement_postal", "next_etablissement_postal", "EVENT_TYPE_CD"]
    avail_cols = [c for c in history_cols if c in receptacle_history.columns]
    history = (
        receptacle_history[avail_cols]
        .sort_values("date", ascending=False)
        .head(10)
    )
    journey_history = []
    for _, hr in history.iterrows():
        journey_history.append({
            "date": str(hr["date"])[:19],
            "etablissement_postal": str(hr.get("etablissement_postal", "")),
            "next_etablissement_postal": str(hr.get("next_etablissement_postal", "")),
            "EVENT_TYPE_CD": str(hr.get("EVENT_TYPE_CD", "")),
        })

    return {
        "recptcl_fid": recptcl_fid,
        "prediction_hours": round(prediction, 2),
        "time_since_first_scan_hours": round(time_since_first_scan, 2),
        "total_estimated_hours": round(total_estimated_time, 2),
        "total_estimated_days": round(total_estimated_time / 24, 1),
        "route_speed": route_speed,
        "origin_country": origin_country,
        "destination_country": destination_country,
        "current_location": str(row_data.get("etablissement_postal", "N/A")),
        "next_location": str(row_data.get("next_etablissement_postal", "")) or None,
        "event_type": str(row_data.get("EVENT_TYPE_CD", "N/A")),
        "last_scan_date": str(row_data["date"])[:19],
        "total_scans": len(receptacle_history),
        "was_saved": was_saved,
        "features": features_dict,
        "journey_history": journey_history,
    }


@router.get("/predictions/log")
def predictions_log():
    """Return the package predictions log."""
    df = get_predictions_log()
    if df is None:
        return {"total": 0, "predictions": []}
    return {
        "total": len(df),
        "predictions": df.to_dict(orient="records"),
    }


@router.get("/predictions/receptacle/log")
def rcp_predictions_log():
    """Return the receptacle predictions log."""
    df = get_rcp_predictions_log()
    if df is None:
        return {"total": 0, "predictions": []}
    return {
        "total": len(df),
        "predictions": df.to_dict(orient="records"),
    }
