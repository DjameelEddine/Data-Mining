"""
/api/export – PDF download endpoint.
"""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import Response

from services.data_service import get_reference_df, prepare_features
from services.export_service import generate_pdf_report

router = APIRouter(prefix="/api/export", tags=["export"])


@router.get("/pdf/{mailitm_fid}")
def export_pdf(mailitm_fid: str):
    """Generate and download a PDF report for a package."""
    ref = get_reference_df()
    package_history = ref[ref["MAILITM_FID"] == mailitm_fid.strip()].sort_values("date")

    if package_history.empty:
        return {"error": f"Package {mailitm_fid} not found."}

    latest_row = package_history.iloc[[-1]]
    row_data = latest_row.iloc[0].to_dict()

    features_df = prepare_features(latest_row, package_history, ref)

    from services.ml_service import predict as ml_predict

    prediction = ml_predict(features_df)
    tsfs = float(features_df["time_since_first_scan"].iloc[0])
    total = tsfs + prediction

    pdf_bytes = generate_pdf_report(
        mailitm_fid, row_data, prediction, tsfs, total, features_df, package_history
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=report_{mailitm_fid}.pdf"},
    )
