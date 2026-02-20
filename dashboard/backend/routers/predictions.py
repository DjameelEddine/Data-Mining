"""
/api/predict – run a prediction for a given package.
/api/predictions – view prediction log.
"""

from __future__ import annotations

from fastapi import APIRouter

from services.data_service import get_reference_df, prepare_features
from services.ml_service import predict, log_prediction, get_predictions_log

router = APIRouter(prefix="/api", tags=["predictions"])


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
    total_estimated_time = time_since_first_scan + prediction

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
        "total_estimated_hours": round(total_estimated_time, 2),
        "total_estimated_days": round(total_estimated_time / 24, 1),
        "route_speed": route_speed,
        "current_location": str(row_data.get("etablissement_postal", "N/A")),
        "next_location": str(row_data.get("next_etablissement_postal", "")) or None,
        "event_type": str(row_data.get("EVENT_TYPE_CD", "N/A")),
        "last_scan_date": str(row_data["date"])[:19],
        "total_scans": len(package_history),
        "was_saved": was_saved,
        "features": features_dict,
        "journey_history": journey_history,
    }


@router.get("/predictions/log")
def predictions_log():
    """Return the full predictions log."""
    df = get_predictions_log()
    if df is None:
        return {"total": 0, "predictions": []}
    return {
        "total": len(df),
        "predictions": df.to_dict(orient="records"),
    }
