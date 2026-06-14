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
    TableStyle, HRFlowable, PageBreak, Image,
)
from backend.routers.sessions import clamp_percentage, clamp_and_normalize_emotions

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


def _generate_report_charts(session_id: int, summary: dict, frames: list) -> tuple:
    """
    Generates two PNG charts:
    1. Engagement Trend Line Graph with shaded Drop-off zones (engagement < 50%)
    2. Emotion Flow Stacked Area Chart (Attentive, Confused, Distracted)
    Saves them as temporary files and returns their paths.
    """
    try:
        import matplotlib
        matplotlib.use('Agg')  # Headless mode
        import matplotlib.pyplot as plt
        import numpy as np

        # Calculate FPS dynamically
        fps = 1.0
        dur = summary.get("duration_mins", 0.0)
        fp = summary.get("frames_processed", 0)
        if dur and dur > 0 and fp:
            total_seconds = dur * 60.0
            fps = fp / total_seconds

        # Extract time series data
        time_seconds = []
        engagement = []
        attentive = []
        confused = []
        distracted = []

        # Extract raw shares
        raw_shares = []
        for f in frames:
            frame_idx = f.get("frame_number", 0)
            time_seconds.append(frame_idx / fps)
            engagement.append(clamp_percentage(f.get("engagement_pct", 0.0)))
            dist = f.get("distribution") or {}
            att_val = float(dist.get("attentive", 0))
            conf_val = float(dist.get("confused", 0))
            dist_val = float(dist.get("distracted", 0))
            
            tot = att_val + conf_val + dist_val
            if tot == 0:
                ap, cp, dp = 33.3, 33.3, 33.4
            else:
                ap = 10.0 + 70.0 * (att_val / tot)
                cp = 10.0 + 70.0 * (conf_val / tot)
                dp = 10.0 + 70.0 * (dist_val / tot)
            raw_shares.append((ap, cp, dp))

        # Apply rolling average smoothing (window of 5)
        n = len(frames)
        window_size = 5
        for i in range(n):
            start = max(0, i - window_size // 2)
            end = min(n, i + window_size // 2 + 1)
            window_vals = raw_shares[start:end]
            
            avg_ap = sum(v[0] for v in window_vals) / len(window_vals)
            avg_cp = sum(v[1] for v in window_vals) / len(window_vals)
            avg_dp = sum(v[2] for v in window_vals) / len(window_vals)
            
            # Sum verification & rounding to sum to exactly 100
            ia = int(round(avg_ap))
            ic = int(round(avg_cp))
            id_ = int(round(avg_dp))
            
            ia = max(10, min(80, ia))
            ic = max(10, min(80, ic))
            id_ = max(10, min(80, id_))
            
            total_sum = ia + ic + id_
            if total_sum != 100:
                diff = 100 - total_sum
                vals = [ia, ic, id_]
                max_idx = vals.index(max(vals))
                vals[max_idx] = max(10, min(80, vals[max_idx] + diff))
                
                total_sum = sum(vals)
                if total_sum != 100:
                    diff = 100 - total_sum
                    for j in range(3):
                        if j != max_idx:
                            vals[j] = max(10, min(80, vals[j] + diff))
                            break
                ia, ic, id_ = vals
                
            attentive.append(ia)
            confused.append(ic)
            distracted.append(id_)

        # Ticks formatting for X axis (MM:SS)
        def format_time(sec):
            m = int(sec // 60)
            s = int(sec % 60)
            return f"{m:02d}:{s:02d}"

        # 1. Engagement Trend Chart
        fig, ax = plt.subplots(figsize=(8.5, 3.2))
        ax.plot(time_seconds, engagement, color='#1565C0', linewidth=2, label='Engagement %')
        
        # Shade drop-off zones (engagement < 50%)
        engagement_arr = np.array(engagement)
        time_arr = np.array(time_seconds)
        if len(engagement_arr) > 0:
            ax.fill_between(time_arr, engagement_arr, 50, where=(engagement_arr < 50), 
                            color='#EF5350', alpha=0.3, interpolate=True, label='Drop-off Zone (<50%)')
        
        # Add a horizontal line at 50%
        ax.axhline(50, color='#EF5350', linestyle='--', linewidth=1, alpha=0.7)
        
        ax.set_ylim(0, 105)
        ax.set_title("Engagement Trend & Drop-off Zones", fontsize=11, fontweight='bold', color='#1565C0')
        ax.set_ylabel("Engagement %", fontsize=9)
        ax.set_xlabel("Timeline (MM:SS)", fontsize=9)
        ax.grid(True, linestyle=':', alpha=0.6)
        
        # Format X ticks
        if len(time_seconds) > 0:
            xticks = np.linspace(time_seconds[0], time_seconds[-1], min(8, len(time_seconds)))
            ax.set_xticks(xticks)
            ax.set_xticklabels([format_time(x) for x in xticks], fontsize=8)
        ax.legend(loc='lower left', fontsize=8)
        plt.tight_layout()
        chart1_path = os.path.abspath(os.path.join(RPT_DIR, f"temp_trend_{session_id}.png"))
        plt.savefig(chart1_path, dpi=200)
        plt.close()

        # 2. Emotion Flow Chart (Stacked Area Chart)
        fig, ax = plt.subplots(figsize=(8.5, 3.2))
        
        # Colors matching ClassSense: Attentive=Green, Confused=Yellow, Distracted=Red
        colors_list = ['#4ADE80', '#FACC15', '#F87171']
        
        if len(time_seconds) > 0:
            ax.stackplot(time_seconds, attentive, confused, distracted, 
                         labels=['Attentive %', 'Confused %', 'Distracted %'], colors=colors_list, alpha=0.8)
        
        ax.set_title("Emotion Share Flow", fontsize=11, fontweight='bold', color='#1565C0')
        ax.set_ylabel("Emotion Share %", fontsize=9)
        ax.set_xlabel("Timeline (MM:SS)", fontsize=9)
        ax.set_ylim(0, 100)
        ax.grid(True, linestyle=':', alpha=0.6)
        
        # Format X ticks
        if len(time_seconds) > 0:
            xticks = np.linspace(time_seconds[0], time_seconds[-1], min(8, len(time_seconds)))
            ax.set_xticks(xticks)
            ax.set_xticklabels([format_time(x) for x in xticks], fontsize=8)
        ax.legend(loc='upper left', fontsize=8)
        plt.tight_layout()
        chart2_path = os.path.abspath(os.path.join(RPT_DIR, f"temp_emotions_{session_id}.png"))
        plt.savefig(chart2_path, dpi=200)
        plt.close()

        return chart1_path, chart2_path
    except Exception as e:
        logger.error("Failed to generate PDF report charts: %s", e, exc_info=True)
        return None, None


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
    dur  = summary.get("duration_mins",   None)
    fp   = summary.get("frames_processed", summary.get("frames_processed", 0)) or 0

    eng_level, eng_colour = _engagement_level(avg)

    summary_data = [
        ["Metric",                     "Value",          ""],
        ["Average Engagement",         f"{avg:.1f}%",    eng_level],
        ["Peak Engagement",            f"{peak:.1f}%",   ""],
        ["Minimum Engagement",         f"{low:.1f}%",    ""],
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
        ["Emotion",     "Share (%)", "Engagement Score"],
        ["Attentive",   f"{100*att/tot_em:.1f}%", "1.0  (fully engaged)"],
        ["Confused",    f"{100*con/tot_em:.1f}%", "0.5  (partially engaged)"],
        ["Distracted",  f"{100*dis/tot_em:.1f}%", "0.0  (disengaged)"],
    ]
    em_tbl = Table(em_data, colWidths=[5.5*cm, 5*cm, 5.5*cm])
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

    # ── Page 2: Visual Charts & Session Highlights ───────────
    chart1_path, chart2_path = _generate_report_charts(session_id, summary, frames)
    
    story.append(PageBreak())
    story.append(Paragraph("Session Highlights &amp; Insights", section_style))
    story.append(Spacer(1, 6))

    # Calculate highlights
    peak_val = 0.0
    peak_time_str = "00:00"
    min_val = 100.0
    min_time_str = "00:00"
    max_conf = 0
    max_conf_pct = 0.0
    max_conf_time_str = "00:00"
    max_dist = 0
    max_dist_pct = 0.0
    max_dist_time_str = "00:00"

    # Calculate FPS dynamically for highlights time format
    fps_calc = 1.0
    dur_val = summary.get("duration_mins", 0.0)
    fp_val = summary.get("frames_processed", 0)
    if dur_val and dur_val > 0 and fp_val:
        total_seconds_calc = dur_val * 60.0
        fps_calc = fp_val / total_seconds_calc

    def format_time_calc(sec):
        m = int(sec // 60)
        s = int(sec % 60)
        return f"{m:02d}:{s:02d}"

    if frames:
        engagement_list = [clamp_percentage(f.get("engagement_pct", 0.0)) for f in frames]
        time_sec_list = [f.get("frame_number", 0) / fps_calc for f in frames]
        
        peak_idx = max(range(len(engagement_list)), key=lambda i: engagement_list[i]) if engagement_list else 0
        min_idx = min(range(len(engagement_list)), key=lambda i: engagement_list[i]) if engagement_list else 0
        
        peak_val = engagement_list[peak_idx]
        peak_time_str = format_time_calc(time_sec_list[peak_idx])
        
        min_val = engagement_list[min_idx]
        min_time_str = format_time_calc(time_sec_list[min_idx])
        
        # Calculate totals per frame to compute relative percentages
        tot_counts = []
        for f in frames:
            dist = f.get("distribution") or {}
            tot_counts.append(dist.get("attentive", 0) + dist.get("confused", 0) + dist.get("distracted", 0))
            
        conf_pcts = []
        for idx, f in enumerate(frames):
            tot = tot_counts[idx]
            dist = f.get("distribution") or {}
            conf_pcts.append(clamp_percentage((dist.get("confused", 0) / tot * 100) if tot > 0 else 0.0))
            
        max_conf_idx = max(range(len(conf_pcts)), key=lambda i: conf_pcts[i]) if conf_pcts else 0
        max_conf_pct = conf_pcts[max_conf_idx]
        max_conf_time_str = format_time_calc(time_sec_list[max_conf_idx])
        
        dist_pcts = []
        for idx, f in enumerate(frames):
            tot = tot_counts[idx]
            dist = f.get("distribution") or {}
            dist_pcts.append((dist.get("distracted", 0) / tot * 100) if tot > 0 else 0.0)
            
        max_dist_idx = max(range(len(dist_pcts)), key=lambda i: dist_pcts[i]) if dist_pcts else 0
        max_dist_pct = dist_pcts[max_dist_idx]
        max_dist_time_str = format_time_calc(time_sec_list[max_dist_idx])

    highlights_data = [
        ["Highlights Descriptor", "Recorded Value", "Time (MM:SS)"],
        ["Peak Engagement Level", f"{peak_val:.1f}%", peak_time_str],
        ["Minimum Engagement Level", f"{min_val:.1f}%", min_time_str],
        ["Peak Confusion Recorded", f"{max_conf_pct:.1f}%", max_conf_time_str],
        ["Peak Distraction Recorded", f"{max_dist_pct:.1f}%", max_dist_time_str],
    ]
    h_tbl = Table(highlights_data, colWidths=[6.5*cm, 5*cm, 4.5*cm])
    h_tbl.setStyle(TableStyle([
        ("BACKGROUND",     (0,0), (-1,0), CS_BLUE),
        ("TEXTCOLOR",      (0,0), (-1,0), colors.white),
        ("FONTNAME",       (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",       (0,0), (-1,-1), 9.5),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [CS_BLUE_LIGHT, colors.white]),
        ("GRID",           (0,0), (-1,-1), 0.3, TABLE_GRID),
        ("TOPPADDING",     (0,0), (-1,-1), 5),
        ("BOTTOMPADDING",  (0,0), (-1,-1), 5),
        ("LEFTPADDING",    (0,0), (-1,-1), 8),
        ("ALIGN",          (1,0), (-1,-1), "CENTER"),
        ("ALIGN",          (2,0), (-1,-1), "CENTER"),
    ]))
    story.append(h_tbl)
    story.append(Spacer(1, 14))

    # Add charts to story
    if chart1_path and os.path.exists(chart1_path):
        story.append(Image(chart1_path, width=16*cm, height=6*cm))
        story.append(Spacer(1, 8))
    if chart2_path and os.path.exists(chart2_path):
        story.append(Image(chart2_path, width=16*cm, height=6*cm))

    # ── Page 3: Qualitative Observations & Footer ───────────
    story.append(PageBreak())
    
    # Trend observations
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
                ["First 25% of class",  f"{sum(pcts[:q])/q:.1f}%"],
                ["25%–50% of class",    f"{sum(pcts[q:2*q])/(q):.1f}%"],
                ["50%–75% of class",    f"{sum(pcts[2*q:3*q])/(q):.1f}%"],
                ["Last 25% of class",   f"{sum(pcts[3*q:])/(n-3*q):.1f}%"],
            ]
            bkt_tbl = Table(buckets, colWidths=[8*cm, 8*cm])
            bkt_tbl.setStyle(TableStyle([
                ("BACKGROUND",     (0,0), (-1,0), CS_BLUE),
                ("TEXTCOLOR",      (0,0), (-1,0), colors.white),
                ("FONTNAME",       (0,0), (-1,0), "Helvetica-Bold"),
                ("FONTSIZE",       (0,0), (-1,-1), 9.5),
                ("ROWBACKGROUNDS", (0,1), (-1,-1), [CS_BLUE_LIGHT, colors.white]),
                ("GRID",           (0,0), (-1,-1), 0.3, TABLE_GRID),
                ("TOPPADDING",     (0,0), (-1,-1), 5),
                ("BOTTOMPADDING",  (0,0), (-1,-1), 5),
                ("ALIGN",          (1,0), (-1,-1), "CENTER"),
                ("LEFTPADDING",    (0,0), (-1,-1), 8),
            ]))
            story.append(bkt_tbl)
            story.append(Spacer(1, 14))

    # Recommendations
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

    # Footer
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=0.5,
                             color=colors.HexColor("#B0BEC5")))
    story.append(Paragraph(
        "Generated by ClassSense | Iqra University FYP 2025-2026 | "
        "Sameer Shah &amp; Ismail Haroon | Supervisor: Ms. Zuha Soomro",
        footer_style,
    ))

    try:
        doc.build(story)
    finally:
        # Clean up temporary chart images
        for path in (chart1_path, chart2_path):
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except Exception as cleanup_exc:
                    logger.error("Failed to delete temp chart file %s: %s", path, cleanup_exc)

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


# ══════════════════════════════════════════════════════════════
# Semester PDF Report
# ══════════════════════════════════════════════════════════════

def generate_semester_pdf_report(
    course_name: str,
    time_slot  : str,
    summary    : dict,
    sessions   : list,
    instructor : str = "Instructor",
) -> str:
    """
    Generate a professional A4 PDF report aggregating a full semester of sessions (14+).
    """
    _ensure_reports_dir()
    safe_course = course_name.replace("/", "_").replace("\\", "_").replace(" ", "_")
    safe_time = time_slot.replace(":", "-").replace(" ", "_")
    out_path = os.path.abspath(
        os.path.join(RPT_DIR, f"semester_report_{safe_course}_{safe_time}.pdf")
    )

    doc    = SimpleDocTemplate(
        out_path, pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=2.5*cm, bottomMargin=2*cm,
    )
    styles = getSampleStyleSheet()

    # Custom paragraph styles
    title_style = ParagraphStyle(
        "CSTitle", fontSize=20, spaceAfter=4,
        textColor=CS_BLUE, alignment=TA_CENTER, fontName="Helvetica-Bold",
    )
    subtitle_style = ParagraphStyle(
        "CSSub", fontSize=11, spaceAfter=2,
        textColor=CS_GREY, alignment=TA_CENTER, fontName="Helvetica",
    )
    section_style = ParagraphStyle(
        "CSSection", fontSize=13, spaceBefore=14, spaceAfter=6,
        textColor=CS_BLUE, fontName="Helvetica-Bold",
    )
    body_style   = styles["Normal"]
    footer_style = ParagraphStyle(
        "CSFooter", fontSize=7.5, textColor=colors.HexColor("#90A4AE"),
        alignment=TA_CENTER, fontName="Helvetica",
    )

    story = []

    # Header
    story.append(Paragraph("ClassSense", title_style))
    story.append(Paragraph(
        "Semester-Long Course Engagement &amp; Emotion Report", subtitle_style))
    story.append(HRFlowable(
        width="100%", thickness=1.5, color=CS_BLUE, spaceAfter=14))

    # Metadata table
    start_date = sessions[0]["started_at"].strftime("%d %b %Y") if sessions else "N/A"
    end_date = sessions[-1]["started_at"].strftime("%d %b %Y") if sessions else "N/A"
    
    meta = [
        ["Course Name",   course_name or "—"],
        ["Time Slot",     time_slot   or "—"],
        ["Sessions Count", f"{len(sessions)} ended sessions"],
        ["Date Range",    f"{start_date} – {end_date}"],
        ["Total Duration", f"{round(summary.get('total_duration_mins', 0.0) / 60, 1)} hours monitored"],
        ["Report Date",   datetime.now().strftime("%d %B %Y, %H:%M")],
    ]
    meta_tbl = Table(meta, colWidths=[5*cm, 11*cm])
    meta_tbl.setStyle(TableStyle([
        ("FONTNAME",       (0,0), (0,-1), "Helvetica-Bold"),
        ("FONTSIZE",       (0,0), (-1,-1), 10),
        ("TEXTCOLOR",      (0,0), (0,-1), CS_GREY),
        ("ROWBACKGROUNDS", (0,0), (-1,-1), [CS_LIGHT_GREY, colors.white]),
        ("GRID",           (0,0), (-1,-1), 0.3, TABLE_GRID),
        ("TOPPADDING",     (0,0), (-1,-1), 5),
        ("BOTTOMPADDING",  (0,0), (-1,-1), 5),
        ("LEFTPADDING",    (0,0), (-1,-1), 8),
    ]))
    story.append(meta_tbl)
    story.append(Spacer(1, 14))

    # Semester Summary metrics
    story.append(Paragraph("Semester Engagement Summary", section_style))

    overall_avg = clamp_percentage(summary.get("overall_avg_engagement", 0.0))
    peak_eng    = clamp_percentage(summary.get("peak_engagement", 0.0))
    min_eng     = clamp_percentage(summary.get("min_engagement", 0.0))
    # Find peak and lowest session details
    peak_sess_id = "—"
    min_sess_id  = "—"
    if sessions:
        peak_sess = max(sessions, key=lambda x: clamp_percentage(x["avg_engagement"]))
        min_sess  = min(sessions, key=lambda x: clamp_percentage(x["avg_engagement"]))
        peak_sess_id = f"Session #{peak_sess['session_id']} ({clamp_percentage(peak_sess['avg_engagement']):.1f}%)"
        min_sess_id  = f"Session #{min_sess['session_id']} ({clamp_percentage(min_sess['avg_engagement']):.1f}%)"

    summary_data = [
        ["Metric",                     "Value",          "Reference / Details"],
        ["Overall Semester Average",   f"{overall_avg:.1f}%",    _engagement_level(overall_avg)[0]],
        ["Peak Session Average",       f"{peak_eng:.1f}%",       peak_sess_id],
        ["Lowest Session Average",     f"{min_eng:.1f}%",        min_sess_id],
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
        ("TOPPADDING",     (0,0), (-1,-1), 6),
        ("BOTTOMPADDING",  (0,0), (-1,-1), 6),
        ("LEFTPADDING",    (0,0), (-1,-1), 8),
    ]))
    story.append(s_tbl)
    story.append(Spacer(1, 14))

    # Emotion breakdown
    story.append(Paragraph("Cumulative Emotion Distribution", section_style))
    att = summary.get("total_attentive", 0)
    con = summary.get("total_confused", 0)
    dis = summary.get("total_distracted", 0)
    tot = att + con + dis or 1

    att_p, con_p, dis_p = clamp_and_normalize_emotions(att, con, dis)
    em_data = [
        ["Emotion",     "Share (%)", "Engagement Weight"],
        ["Attentive",   f"{att_p:.1f}%", "1.0  (fully engaged)"],
        ["Confused",    f"{con_p:.1f}%", "0.5  (partially engaged)"],
        ["Distracted",  f"{dis_p:.1f}%", "0.0  (disengaged)"],
    ]
    em_tbl = Table(em_data, colWidths=[5.5*cm, 5*cm, 5.5*cm])
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
        ("TOPPADDING",     (0,0), (-1,-1), 6),
        ("BOTTOMPADDING",  (0,0), (-1,-1), 6),
        ("ALIGN",          (1,0), (-1,-1), "CENTER"),
        ("LEFTPADDING",    (0,0), (-1,-1), 8),
    ]))
    story.append(em_tbl)
    story.append(Spacer(1, 14))

    # Trend Observations
    if len(sessions) >= 4:
        story.append(Paragraph("Semester Trend Observations", section_style))
        engs = [s["avg_engagement"] for s in sessions]
        n = len(engs)
        mid = n // 2
        first = sum(engs[:mid]) / mid
        last = sum(engs[mid:]) / (n - mid)
        
        if last - first > 2.0:
            trend = (f"Overall student engagement improved across the semester, rising from an average of "
                     f"{first:.1f}% in the first half to {last:.1f}% in the second half. "
                     "This indicates effective course pacing and rising student interest/adaptation.")
        elif first - last > 2.0:
            trend = (f"Student engagement declined over the semester, dropping from {first:.1f}% in the first half "
                     f"to {last:.1f}% in the second half. This suggests student fatigue, rising difficulty of topics, "
                     "or a need to introduce more interactive check-ins in later weeks.")
        else:
            trend = (f"Student engagement remained highly stable and consistent throughout the semester, "
                     f"averaging {first:.1f}% in the first half and {last:.1f}% in the second half.")
        story.append(Paragraph(trend, body_style))
        story.append(Spacer(1, 14))

    # Page Break for session milestones list to make it clean
    story.append(PageBreak())

    # Session Milestones list
    story.append(Paragraph("Individual Session Milestones", section_style))
    story.append(Paragraph("Below is the chronological breakdown of all monitored sessions for this semester:", body_style))
    story.append(Spacer(1, 8))

    tbl_headers = ["ID", "Date", "Duration", "Avg Eng", "Peak Eng"]
    tbl_rows = [tbl_headers]
    for s in sessions:
        date_str = s["started_at"].strftime("%d %b %Y")
        tbl_rows.append([
            f"#{s['session_id']}",
            date_str,
            f"{s['duration_mins']:.0f}m",
            f"{clamp_percentage(s['avg_engagement']):.1f}%",
            f"{clamp_percentage(s['peak_engagement']):.1f}%",
        ])
    
    milestones_tbl = Table(tbl_rows, colWidths=[3*cm, 4.5*cm, 2.5*cm, 3*cm, 3*cm])
    milestones_tbl.setStyle(TableStyle([
        ("BACKGROUND",     (0,0), (-1,0), CS_BLUE),
        ("TEXTCOLOR",      (0,0), (-1,0), colors.white),
        ("FONTNAME",       (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",       (0,0), (-1,-1), 9),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [CS_BLUE_LIGHT, colors.white]),
        ("GRID",           (0,0), (-1,-1), 0.3, TABLE_GRID),
        ("TOPPADDING",     (0,0), (-1,-1), 5),
        ("BOTTOMPADDING",  (0,0), (-1,-1), 5),
        ("ALIGN",          (2,0), (-1,-1), "CENTER"),
        ("LEFTPADDING",    (0,0), (-1,-1), 6),
    ]))
    story.append(milestones_tbl)

    # Footer credit
    story.append(Spacer(1, 24))
    story.append(HRFlowable(width="100%", thickness=0.5,
                             color=colors.HexColor("#B0BEC5")))
    story.append(Paragraph(
        "Generated by ClassSense | Iqra University FYP 2025-2026 | "
        "Sameer Shah &amp; Ismail Haroon | Supervisor: Ms. Zuha Soomro",
        footer_style,
    ))

    doc.build(story)
    logger.info("Semester PDF report saved: %s", out_path)
    return out_path
