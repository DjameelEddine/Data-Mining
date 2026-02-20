"""
/api/stats – overview.
"""

from __future__ import annotations

from fastapi import APIRouter

from services.data_service import derive_status, get_reference_df

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("/overview")
def overview():
    """High-level shipment counts."""
    df = get_reference_df().copy()
    df["status"] = df["EVENT_TYPE_CD"].apply(derive_status)

    delivered = int((df["status"] == "Delivered").sum())
    delayed = int((df["status"] == "Delayed").sum())
    in_transit = int((df["status"] == "In Transit").sum())

    return {
        "total_shipments": len(df),
        "delivered": delivered,
        "in_transit": in_transit,
        "delayed": delayed,
        "unique_packages": int(df["MAILITM_FID"].nunique()),
        "date_range_start": str(df["date"].min())[:10],
        "date_range_end": str(df["date"].max())[:10],
    }
