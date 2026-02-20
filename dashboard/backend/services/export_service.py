"""
PDF export helper.
"""

from __future__ import annotations

from datetime import datetime

import pandas as pd
from fpdf import FPDF


def generate_pdf_report(
    mailitm_fid: str,
    row_data: dict,
    prediction: float,
    time_since_first_scan: float,
    total_estimated_time: float,
    features_df: pd.DataFrame,
    package_history: pd.DataFrame,
) -> bytes:
    """Build a PDF report and return the raw bytes."""
    pdf = FPDF()
    pdf.add_page()

    # Title
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Algerie Post - Package Prediction Report", 0, 1, "C")
    pdf.ln(5)

    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 8, f'Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', 0, 1, "R")
    pdf.ln(5)

    # --- Package Information ---
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Package Information", 0, 1)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(3)

    info_items = [
        ("Package ID:", mailitm_fid),
        ("Current Location:", str(row_data.get("etablissement_postal", "N/A"))),
        ("Next Location:", str(row_data.get("next_etablissement_postal", "N/A"))),
        ("Event Type:", str(row_data.get("EVENT_TYPE_CD", "N/A"))),
        ("Last Scan Date:", str(row_data.get("date", ""))[:19]),
        ("Total Scans:", str(len(package_history))),
    ]
    for label, value in info_items:
        pdf.set_font("Arial", "B", 11)
        pdf.cell(50, 8, label, 0, 0)
        pdf.set_font("Arial", "", 11)
        pdf.cell(0, 8, value, 0, 1)
    pdf.ln(5)

    # --- Prediction Results ---
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Prediction Results", 0, 1)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(3)

    pred_items = [
        ("Time Since First Scan:", f"{time_since_first_scan:.2f} hours"),
        ("Predicted Route Duration:", f"{prediction:.2f} hours"),
        ("Total Estimated Time:", f"{total_estimated_time:.2f} hours ({total_estimated_time / 24:.1f} days)"),
    ]
    for label, value in pred_items:
        pdf.set_font("Arial", "B", 11)
        pdf.cell(60, 8, label, 0, 0)
        pdf.set_font("Arial", "", 11)
        pdf.cell(0, 8, value, 0, 1)
    pdf.ln(5)

    # --- Features ---
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Features Used for Prediction", 0, 1)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(3)

    pdf.set_font("Arial", "", 9)
    for col in features_df.columns:
        val = features_df[col].iloc[0]
        pdf.cell(70, 6, str(col)[:35], 0, 0)
        pdf.cell(0, 6, str(val)[:50], 0, 1)
    pdf.ln(5)

    # --- Journey History ---
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Package Journey History (Last 10)", 0, 1)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(3)

    history_display = package_history[
        ["date", "etablissement_postal", "next_etablissement_postal", "EVENT_TYPE_CD"]
    ].copy()
    history_display = history_display.sort_values("date", ascending=False).head(10)

    pdf.set_font("Arial", "B", 9)
    pdf.cell(45, 7, "Date", 1, 0, "C")
    pdf.cell(45, 7, "Location", 1, 0, "C")
    pdf.cell(45, 7, "Next Location", 1, 0, "C")
    pdf.cell(30, 7, "Event", 1, 1, "C")

    pdf.set_font("Arial", "", 8)
    for _, row in history_display.iterrows():
        pdf.cell(45, 6, str(row["date"])[:19], 1, 0)
        pdf.cell(45, 6, str(row["etablissement_postal"])[:20], 1, 0)
        pdf.cell(45, 6, str(row["next_etablissement_postal"])[:20], 1, 0)
        pdf.cell(30, 6, str(row["EVENT_TYPE_CD"])[:15], 1, 1)

    return bytes(pdf.output())
