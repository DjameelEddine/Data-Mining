"""
/api/stats – overview.
"""

from __future__ import annotations

from fastapi import APIRouter

from services.data_service import get_reference_df, get_rcp_reference_df

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("/overview")
def overview():
    """High-level shipment counts for packages."""
    df = get_reference_df().copy()
    
    return {
        "total_shipments": len(df),
        "unique_packages": int(df["MAILITM_FID"].nunique()),
        "date_range_start": str(df["date"].min())[:10],
        "date_range_end": str(df["date"].max())[:10],
    }


@router.get("/overview/receptacles")
def overview_receptacles():
    """High-level counts for receptacles."""
    df = get_rcp_reference_df().copy()

    return {
        "total_records": len(df),
        "unique_receptacles": int(df["RECPTCL_FID"].nunique()),
        "date_range_start": str(df["date"].min())[:10],
        "date_range_end": str(df["date"].max())[:10],
    }
