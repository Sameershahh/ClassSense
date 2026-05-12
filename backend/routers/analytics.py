# backend/routers/analytics.py
# Analytics, reports, and course-level trend endpoints.
#
# GET /api/analytics/{id}/summary          → session summary stats
# GET /api/analytics/{id}/timeseries       → per-frame time-series chart data
# GET /api/analytics/{id}/report/pdf       → download PDF report
# GET /api/analytics/{id}/report/csv       → download CSV data
# GET /api/analytics/course/{name}         → cross-session course trend
# GET /api/analytics/model-status          → ML health check

import os
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import func

from backend.database import get_db
from backend.auth import get_current_user, TokenData
from backend.models.session import (Session as SessionModel,
                                    FrameAnalytic, SessionSummary)
from backend.models.schemas import (SessionSummaryResponse, AnalyticsTimeSeries,
                                    EngagementPoint, CourseAnalytics,
                                    CourseSessionItem, ModelStatusResponse)
from backend.services.report import generate_pdf_report, generate_csv_report
from backend.services.ml_runner import ml_runner

logger = logging.getLogger(__name__)
router = APIRouter()


def _get_summary_or_404(session_id: int, db: DBSession) -> SessionSummary:
    s = db.query(SessionSummary).filter_by(session_id=session_id).first()
    if not s:
        raise HTTPException(
            status_code=404,
            detail=(f"No summary found for session {session_id}. "
                    "Call POST /api/sessions/{id}/end first."),
        )
    return s


# ══════════════════════════════════════════════════════════════
# ML Model Health
# ══════════════════════════════════════════════════════════════

@router.get("/model-status", response_model=ModelStatusResponse,
            summary="Check ML model health")
def model_status(user: TokenData = Depends(get_current_user)):
    """
    Returns whether the fine-tuned emotion model is loaded.
    If `model_loaded` is false, the system still runs but returns
    neutral emotion defaults — you must copy the .pth file.
    """
    loaded = ml_runner.model_loaded
    return ModelStatusResponse(
        model_loaded = loaded,
        weights_path = ml_runner.weights_path,
        message      = (
            "Fine-tuned MobileNetV2 loaded and ready."
            if loaded else
            "Model weights not found. "
            "Copy classsense_BEST.pth from Google Drive to "
            "ml/emotion/model_weights/classsense_mobilenetv2.pth"
        ),
    )


# ══════════════════════════════════════════════════════════════
# Session Summary
# ══════════════════════════════════════════════════════════════

@router.get("/{session_id}/summary",
            response_model=SessionSummaryResponse,
            summary="Get aggregated summary for a completed session")
def get_session_summary(
    session_id: int,
    db        : DBSession = Depends(get_db),
    user      : TokenData = Depends(get_current_user),
):
    """
    Returns the aggregated engagement statistics for a session.
    Used to populate the Session Summary screen and PDF report header.
    Requires the session to have been ended first.
    """
    summary = _get_summary_or_404(session_id, db)
    session = db.query(SessionModel).filter(
        SessionModel.id == session_id).first()

    return SessionSummaryResponse(
        session_id      = session_id,
        course_name     = session.course_name  if session else None,
        time_slot       = session.time_slot    if session else None,
        avg_engagement  = summary.avg_engagement  or 0.0,
        peak_engagement = summary.peak_engagement or 0.0,
        min_engagement  = summary.min_engagement  or 0.0,
        avg_students    = summary.avg_students    or 0.0,
        duration_mins   = summary.duration_mins,
        frames_processed= summary.frames_processed,
        total_attentive = summary.total_attentive  or 0,
        total_confused  = summary.total_confused   or 0,
        total_distracted= summary.total_distracted or 0,
        pdf_report_path = summary.pdf_report_path,
        csv_report_path = summary.csv_report_path,
    )


# ══════════════════════════════════════════════════════════════
# Time-series (Dashboard Chart)
# ══════════════════════════════════════════════════════════════

@router.get("/{session_id}/timeseries",
            response_model=AnalyticsTimeSeries,
            summary="Get per-frame engagement time-series")
def get_timeseries(
    session_id : int,
    downsample : int = Query(
        default=1, ge=1, le=100,
        description="Return every Nth frame (1=all, 5=every 5th, …). "
                    "Use higher values for large videos to reduce payload size.",
    ),
    db         : DBSession = Depends(get_db),
    user       : TokenData = Depends(get_current_user),
):
    """
    Returns the per-frame engagement data ordered by timestamp.
    Used to render the Engagement Trend line chart on the dashboard.

    **Tip:** For a 30-minute lecture at 30fps, there are ~54,000 frames.
    Use `downsample=30` to return ~1,800 points — plenty for charting.
    """
    rows = (
        db.query(FrameAnalytic)
          .filter(FrameAnalytic.session_id == session_id)
          .order_by(FrameAnalytic.timestamp.asc())
          .all()
    )

    if not rows:
        raise HTTPException(
            status_code=404,
            detail=f"No analytics data for session {session_id}. "
                   "Process a video first.",
        )

    sampled = rows[::downsample]

    points = [
        EngagementPoint(
            frame_number  = r.frame_number,
            timestamp     = r.timestamp,
            engagement_pct= round(r.engagement_pct, 1),
            student_count = r.student_count,
            attentive     = (r.distribution or {}).get("attentive",  0),
            confused      = (r.distribution or {}).get("confused",   0),
            distracted    = (r.distribution or {}).get("distracted", 0),
        )
        for r in sampled
    ]

    return AnalyticsTimeSeries(
        session_id   = session_id,
        total_frames = len(rows),
        points       = points,
    )


# ══════════════════════════════════════════════════════════════
# PDF Report Download
# ══════════════════════════════════════════════════════════════

@router.get("/{session_id}/report/pdf",
            summary="Download the PDF session report")
def download_pdf_report(
    session_id: int,
    db        : DBSession = Depends(get_db),
    user      : TokenData = Depends(get_current_user),
):
    """
    Generate (or re-generate) a PDF report for the session and return it
    as a downloadable file.

    The PDF includes:
    - Session metadata (course, time slot, date)
    - Engagement summary table (avg, peak, min, duration)
    - Emotion distribution table (attentive/confused/distracted counts)
    - Trend analysis by session quarter
    - Instructor recommendations
    """
    summary = _get_summary_or_404(session_id, db)
    session = db.query(SessionModel).filter(
        SessionModel.id == session_id).first()
    frames  = (
        db.query(FrameAnalytic)
          .filter(FrameAnalytic.session_id == session_id)
          .order_by(FrameAnalytic.timestamp.asc())
          .all()
    )

    path = generate_pdf_report(
        session_id  = session_id,
        summary     = summary.__dict__,
        frames      = [f.__dict__ for f in frames],
        course_name = session.course_name if session else "",
        time_slot   = session.time_slot   if session else "",
    )

    # Cache path on summary so the frontend knows whether to show Download
    summary.pdf_report_path = path
    db.commit()

    return FileResponse(
        path,
        media_type="application/pdf",
        filename=f"classsense_session_{session_id}.pdf",
    )


# ══════════════════════════════════════════════════════════════
# CSV Report Download
# ══════════════════════════════════════════════════════════════

@router.get("/{session_id}/report/csv",
            summary="Download the CSV data export")
def download_csv_report(
    session_id: int,
    db        : DBSession = Depends(get_db),
    user      : TokenData = Depends(get_current_user),
):
    """
    Export all frame-level engagement data as a CSV file.

    Columns: frame_number, timestamp, engagement_pct,
             student_count, attentive, confused, distracted
    """
    frames = (
        db.query(FrameAnalytic)
          .filter(FrameAnalytic.session_id == session_id)
          .order_by(FrameAnalytic.timestamp.asc())
          .all()
    )

    if not frames:
        raise HTTPException(status_code=404,
                            detail="No data found for this session.")

    path = generate_csv_report(session_id, [f.__dict__ for f in frames])

    # Cache path
    summary = db.query(SessionSummary).filter_by(session_id=session_id).first()
    if summary:
        summary.csv_report_path = path
        db.commit()

    return FileResponse(
        path,
        media_type="text/csv",
        filename=f"classsense_session_{session_id}.csv",
    )


# ══════════════════════════════════════════════════════════════
# Course Analytics (cross-session trend)
# ══════════════════════════════════════════════════════════════

@router.get("/course/{course_name}",
            response_model=CourseAnalytics,
            summary="Cross-session engagement trend for one course")
def get_course_analytics(
    course_name: str,
    db         : DBSession = Depends(get_db),
    user       : TokenData = Depends(get_current_user),
):
    """
    Returns aggregated analytics across all ended sessions for a course.
    Powers the Course Analytics line chart (engagement trend over time).

    `trend_direction` is `improving` / `declining` / `stable` based on
    whether the second half of sessions averaged higher than the first.
    """
    sessions = (
        db.query(SessionModel)
          .filter(SessionModel.course_name == course_name,
                  SessionModel.status      == "ended")
          .order_by(SessionModel.started_at.asc())
          .all()
    )

    if not sessions:
        raise HTTPException(
            status_code=404,
            detail=f"No completed sessions for course '{course_name}'.",
        )

    items      : List[CourseSessionItem] = []
    eng_values : List[float]             = []

    for s in sessions:
        sm = db.query(SessionSummary).filter_by(session_id=s.id).first()
        if not sm:
            continue

        dur = None
        if s.started_at and s.ended_at:
            dur = round((s.ended_at - s.started_at).total_seconds() / 60, 1)

        avg = sm.avg_engagement or 0.0
        eng_values.append(avg)

        items.append(CourseSessionItem(
            session_id     = s.id,
            started_at     = s.started_at,
            avg_engagement = round(avg, 1),
            peak_engagement= round(sm.peak_engagement or 0.0, 1),
            avg_students   = round(sm.avg_students    or 0.0, 1),
            duration_mins  = dur,
        ))

    # Trend direction
    trend = "stable"
    if len(eng_values) >= 4:
        mid   = len(eng_values) // 2
        first = sum(eng_values[:mid]) / mid
        last  = sum(eng_values[mid:]) / (len(eng_values) - mid)
        if last - first >  3.0:
            trend = "improving"
        elif first - last > 3.0:
            trend = "declining"

    overall = round(sum(eng_values) / len(eng_values), 1) if eng_values else 0.0

    return CourseAnalytics(
        course_name    = course_name,
        session_count  = len(items),
        overall_avg    = overall,
        trend_direction= trend,
        sessions       = items,
    )
