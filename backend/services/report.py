# backend/services/report.py
# Generates downloadable PDF and CSV reports from session analytics.

import os
import logging
from datetime import datetime
from typing import Optional

import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table,
    TableStyle, HRFlowable, PageBreak,
)

logger   = logging.getLogger(__name__)
RPT_DIR  = "reports"

# ClassSense brand colours
CS_BLUE      = colors.HexColor("#1565C0")
CS_BLUE_LIGHT= colors.HexColor("#E3F2FD")
CS_GREEN     = colors.HexColor("#1B5E20")
CS_ORANGE    = colors.HexColor("#E65100")
CS_RED       = colors.HexColor("#B71C1C")
CS_GREY      = colors.HexColor("#455A64")
CS_LIGHT_GREY= colors.HexColor("#F5F7FA")
TABLE_GRID   = colors.HexColor("#CFD8DC")


def _ensure_reports_dir():
    os.makedirs(RPT_DIR, exist_ok=True)


def _engagement_level(avg: float) -> tuple:
    """Returns (label, colour) based on average engagement."""
    if avg >= 75:
        return "High", CS_GREEN
    elif avg >= 50:
        return "Moderate", CS_ORANGE
    else:
        return "Low", CS_RED


# ══════════════════════════════════════════════════════════════
# PDF Report
# ══════════════════════════════════════════════════════════════

def generate_pdf_report(
    session_id  : int,
    summary     : dict,
    frames      : list,
    course_name : str = "",
    time_slot   : str = "",
    instructor  : str = "Instructor",
) -> str:
    """
    Generate a professional A4 PDF report for one ClassSense session.

    Args:
        session_id  : Used for filename and header.
        summary     : SessionSummary.__dict__ from the DB.
        frames      : List of FrameAnalytic.__dict__ from the DB.
        course_name : e.g. "CS101 — Data Structures"
        time_slot   : e.g. "Monday 10:00 AM – 11:30 AM"
        instructor  : Instructor name for the header.

    Returns:
        Absolute path to the saved PDF.
    """
    _ensure_reports_dir()
    out_path = os.path.abspath(
        os.path.join(RPT_DIR, f"session_{session_id}_report.pdf")
    )

    doc    = SimpleDocTemplate(
        out_path, pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=2.5*cm, bottomMargin=2*cm,
    )
    styles = getSampleStyleSheet()

    # ── Custom paragraph styles ─────────────────────────────
    title_style = ParagraphStyle(
        "CSTitle", fontSize=22, spaceAfter=4,
        textColor=CS_BLUE, alignment=TA_CENTER, fontName="Helvetica-Bold",
    )
    subtitle_style = ParagraphStyle(
        "CSSub", fontSize=11, spaceAfter=2,
        textColor=CS_GREY, alignment=TA_CENTER, fontName="Helvetica",
    )
    section_style = ParagraphStyle(
        "CSSection", fontSize=13, spaceBefore=16, spaceAfter=6,
        textColor=CS_BLUE, fontName="Helvetica-Bold",
    )
    body_style   = styles["Normal"]
    footer_style = ParagraphStyle(
        "CSFooter", fontSize=7.5, textColor=colors.HexColor("#90A4AE"),
        alignment=TA_CENTER, fontName="Helvetica",
    )

    story = []

    # ── Page 1: Header ───────────────────────────────────────
    story.append(Paragraph("ClassSense", title_style))
    story.append(Paragraph(
        "Classroom Engagement &amp; Emotion Analysis Report", subtitle_style))
    story.append(HRFlowable(
        width="100%", thickness=1.5, color=CS_BLUE, spaceAfter=14))

    # Session metadata table
    meta = [
        ["Session ID",   str(session_id)],
        ["Course",       course_name or "—"],
        ["Time Slot",    time_slot   or "—"],
        ["Instructor",   instructor],
        ["Report Date",  datetime.now().strftime("%d %B %Y, %H:%M")],
    ]
    meta_tbl = Table(meta, colWidths=[5*cm, 11*cm])
    meta_tbl.setStyle(TableStyle([
        ("FONTNAME",       (0,0), (0,-1), "Helvetica-Bold"),
        ("FONTSIZE",       (0,0), (-1,-1), 10),
        ("TEXTCOLOR",      (0,0), (0,-1), CS_GREY),
        ("ROWBACKGROUNDS", (0,0), (-1,-1), [CS_LIGHT_GREY, colors.white]),
        ("GRID",           (0,0), (-1,-1), 0.3, TABLE_GRID),
        ("TOPPADDING",     (0,0), (-1,-1), 6),
        ("BOTTOMPADDING",  (0,0), (-1,-1), 6),
        ("LEFTPADDING",    (0,0), (-1,-1), 8),
    ]))
    story.append(meta_tbl)
    story.append(Spacer(1, 18))

    # ── Engagement summary ───────────────────────────────────
    story.append(Paragraph("Engagement Summary", section_style))

    avg  = summary.get("avg_engagement",  0.0) or 0.0
    peak = summary.get("peak_engagement", 0.0) or 0.0
    low  = summary.get("min_engagement",  0.0) or 0.0
    stu  = summary.get("avg_students",    0.0) or 0.0
    dur  = summary.get("duration_mins",   None)
    fp   = summary.get("frames_processed", summary.get("frames_processed", 0)) or 0

    eng_level, eng_colour = _engagement_level(avg)

    summary_data = [
        ["Metric",                     "Value",          ""],
        ["Average Engagement",         f"{avg:.1f}%",    eng_level],
        ["Peak Engagement",            f"{peak:.1f}%",   ""],
        ["Minimum Engagement",         f"{low:.1f}%",    ""],
        ["Average Students Detected",  f"{stu:.0f}",     ""],
        ["Session Duration",           f"{dur:.0f} min" if dur else "N/A", ""],
        ["Frames Analysed",            str(fp),          ""],
    ]
    s_tbl = Table(summary_data, colWidths=[7*cm, 4*cm, 5*cm])
    s_tbl.setStyle(TableStyle([
        ("BACKGROUND",     (0,0), (-1,0), CS_BLUE),
        ("TEXTCOLOR",      (0,0), (-1,0), colors.white),
        ("FONTNAME",       (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTNAME",       (0,1), (0,-1), "Helvetica-Bold"),
        ("FONTSIZE",       (0,0), (-1,-1), 10),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [CS_BLUE_LIGHT, colors.white]),
        ("GRID",           (0,0), (-1,-1), 0.3, TABLE_GRID),
        ("TOPPADDING",     (0,0), (-1,-1), 7),
        ("BOTTOMPADDING",  (0,0), (-1,-1), 7),
        ("LEFTPADDING",    (0,0), (-1,-1), 8),
        # Colour the engagement level cell
        ("TEXTCOLOR",      (2,1), (2,1), eng_colour),
        ("FONTNAME",       (2,1), (2,1), "Helvetica-BoldOblique"),
    ]))
    story.append(s_tbl)
    story.append(Spacer(1, 18))

    # ── Emotion distribution ─────────────────────────────────
    story.append(Paragraph("Emotion Distribution", section_style))

    att = summary.get("total_attentive",  0) or 0
    con = summary.get("total_confused",   0) or 0
    dis = summary.get("total_distracted", 0) or 0
    tot_em = att + con + dis or 1

    em_data = [
        ["Emotion",     "Frame Count", "Share (%)", "Engagement Score"],
        ["Attentive",   str(att), f"{100*att/tot_em:.1f}%", "1.0  (fully engaged)"],
        ["Confused",    str(con), f"{100*con/tot_em:.1f}%", "0.5  (partially engaged)"],
        ["Distracted",  str(dis), f"{100*dis/tot_em:.1f}%", "0.0  (disengaged)"],
    ]
    em_tbl = Table(em_data, colWidths=[4*cm, 3.5*cm, 3.5*cm, 5*cm])
    em_tbl.setStyle(TableStyle([
        ("BACKGROUND",     (0,0), (-1,0), CS_BLUE),
        ("TEXTCOLOR",      (0,0), (-1,0), colors.white),
        ("FONTNAME",       (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",       (0,0), (-1,-1), 10),
        ("ROWBACKGROUNDS", (0,1), (-1,-1),
         [colors.HexColor("#E8F5E9"),
          colors.HexColor("#FFF8E1"),
          colors.HexColor("#FFEBEE")]),
        ("GRID",           (0,0), (-1,-1), 0.3, TABLE_GRID),
        ("TOPPADDING",     (0,0), (-1,-1), 7),
        ("BOTTOMPADDING",  (0,0), (-1,-1), 7),
        ("ALIGN",          (1,0), (-1,-1), "CENTER"),
        ("LEFTPADDING",    (0,0), (-1,-1), 8),
    ]))
    story.append(em_tbl)
    story.append(Spacer(1, 18))

    # ── Trend analysis (text) ────────────────────────────────
    if frames:
        story.append(Paragraph("Trend Observations", section_style))
        pcts = [f.get("engagement_pct", 0) for f in frames
                if f.get("engagement_pct") is not None]
        if len(pcts) >= 4:
            n = len(pcts)
            q1 = sum(pcts[:n//4]) / (n//4)
            q4 = sum(pcts[-n//4:]) / (n//4)
            if q4 > q1 + 5:
                trend = ("Engagement increased over the course of the session. "
                         "Content pacing or increasing student involvement likely contributed.")
            elif q1 > q4 + 5:
                trend = ("Engagement declined towards the end. "
                         "Students may have fatigued — consider a mid-session break or activity change.")
            else:
                trend = "Engagement remained relatively stable throughout the session."
            story.append(Paragraph(trend, body_style))
        story.append(Spacer(1, 8))

        # Engagement by time buckets (quarters)
        if len(pcts) >= 8:
            n = len(pcts)
            q = n // 4
            buckets = [
                ["Quarter", "Avg Engagement"],
                ["First 25%",  f"{sum(pcts[:q])/q:.1f}%"],
                ["25%–50%",    f"{sum(pcts[q:2*q])/(q):.1f}%"],
                ["50%–75%",    f"{sum(pcts[2*q:3*q])/(q):.1f}%"],
                ["Last 25%",   f"{sum(pcts[3*q:])/(n-3*q):.1f}%"],
            ]
            bkt_tbl = Table(buckets, colWidths=[6*cm, 6*cm])
            bkt_tbl.setStyle(TableStyle([
                ("BACKGROUND",     (0,0), (-1,0), CS_BLUE),
                ("TEXTCOLOR",      (0,0), (-1,0), colors.white),
                ("FONTNAME",       (0,0), (-1,0), "Helvetica-Bold"),
                ("FONTSIZE",       (0,0), (-1,-1), 10),
                ("ROWBACKGROUNDS", (0,1), (-1,-1), [CS_BLUE_LIGHT, colors.white]),
                ("GRID",           (0,0), (-1,-1), 0.3, TABLE_GRID),
                ("TOPPADDING",     (0,0), (-1,-1), 6),
                ("BOTTOMPADDING",  (0,0), (-1,-1), 6),
                ("ALIGN",          (1,0), (-1,-1), "CENTER"),
                ("LEFTPADDING",    (0,0), (-1,-1), 8),
            ]))
            story.append(bkt_tbl)
            story.append(Spacer(1, 18))

    # ── Recommendations ──────────────────────────────────────
    story.append(Paragraph("Recommendations", section_style))
    recs = []
    if avg < 50:
        recs.append("• Consider breaking the lecture into shorter segments with interactive activities.")
    if con / tot_em > 0.3:
        recs.append("• High confusion detected — revisit the topic with worked examples or Q&A.")
    if dis / tot_em > 0.25:
        recs.append("• Significant distraction observed — check classroom environment and pacing.")
    if not recs:
        recs.append("• Session shows healthy engagement. Maintain the current teaching approach.")
    for rec in recs:
        story.append(Paragraph(rec, body_style))
        story.append(Spacer(1, 4))

    # ── Footer ───────────────────────────────────────────────
    story.append(Spacer(1, 24))
    story.append(HRFlowable(width="100%", thickness=0.5,
                             color=colors.HexColor("#B0BEC5")))
    story.append(Paragraph(
        "Generated by ClassSense | Iqra University FYP 2025-2026 | "
        "Sameer Shah &amp; Ismail Haroon | Supervisor: Ms. Zuha Soomro",
        footer_style,
    ))

    doc.build(story)
    logger.info("PDF report saved: %s", out_path)
    return out_path


# ══════════════════════════════════════════════════════════════
# CSV Report
# ══════════════════════════════════════════════════════════════

def generate_csv_report(session_id: int, frames: list) -> str:
    """
    Generate a frame-level CSV data export.

    Columns:
        frame_number, timestamp, engagement_pct,
        student_count, attentive, confused, distracted
    """
    _ensure_reports_dir()
    out_path = os.path.abspath(
        os.path.join(RPT_DIR, f"session_{session_id}_data.csv")
    )

    rows = []
    for f in frames:
        dist = f.get("distribution") or {}
        rows.append({
            "frame_number"  : f.get("frame_number", ""),
            "timestamp"     : f.get("timestamp", ""),
            "engagement_pct": round(f.get("engagement_pct", 0), 2),
            "student_count" : f.get("student_count", 0),
            "attentive"     : dist.get("attentive",  0),
            "confused"      : dist.get("confused",   0),
            "distracted"    : dist.get("distracted", 0),
        })

    df = pd.DataFrame(rows)
    df.to_csv(out_path, index=False)
    logger.info("CSV report saved: %s (%d rows)", out_path, len(rows))
    return out_path
