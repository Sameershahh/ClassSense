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

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import func

from backend.database import get_db
from backend.auth import get_current_user, TokenData
from backend.models.session import (Session as SessionModel,
                                    FrameAnalytic, SessionSummary)
from backend.models.user import User as DbUser
from backend.models.schemas import (SessionSummaryResponse, AnalyticsTimeSeries,
                                    EngagementPoint, CourseAnalytics,
                                    CourseSessionItem, ModelStatusResponse,
                                    SemesterStatusResponse, SemesterSessionItem,
                                    SemesterReportResponse)
from backend.services.report import generate_pdf_report, generate_csv_report
from backend.services.ml_runner import ml_runner

logger = logging.getLogger(__name__)
router = APIRouter()

# ── Clamping & Normalization helpers ──────────────────────────
def clamp_percentage(value) -> float:
    try:
        val = float(value)
        return max(10.0, min(90.0, val))
    except (ValueError, TypeError):
        return 10.0

def clamp_and_normalize_emotions(attentive, confused, distracted) -> tuple:
    att_val = float(attentive or 0)
    conf_val = float(confused or 0)
    dist_val = float(distracted or 0)
    
    total = att_val + conf_val + dist_val
    if total == 0:
        return 33.3, 33.3, 33.4
        
    ap = (att_val / total) * 100.0
    cp = (conf_val / total) * 100.0
    dp = (dist_val / total) * 100.0
    
    ap_c = max(10.0, min(90.0, ap))
    cp_c = max(10.0, min(90.0, cp))
    dp_c = max(10.0, min(90.0, dp))
    
    for _ in range(5):
        tot = ap_c + cp_c + dp_c
        if abs(tot - 100.0) < 0.01:
            break
        factor = 100.0 / tot
        ap_c = max(10.0, min(90.0, ap_c * factor))
        cp_c = max(10.0, min(90.0, cp_c * factor))
        dp_c = max(10.0, min(90.0, dp_c * factor))
        
    diff = 100.0 - (ap_c + cp_c + dp_c)
    if diff != 0:
        vals = [ap_c, cp_c, dp_c]
        max_idx = vals.index(max(vals))
        vals[max_idx] = max(10.0, min(90.0, vals[max_idx] + diff))
        ap_c, cp_c, dp_c = vals
        
    return round(ap_c, 1), round(cp_c, 1), round(dp_c, 1)


def _verify_session_access(session_id: int, user: TokenData, db: DBSession) -> SessionModel:
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
    db_user = db.query(DbUser).filter(DbUser.email == user.username).first()
    if not db_user:
        raise HTTPException(status_code=401, detail="User profile not found")
        
    if db_user.role == "instructor" and session.instructor_id != db_user.id:
        raise HTTPException(
            status_code=403,
            detail="Forbidden: You do not have permission to access this session's analytics."
        )
        
    return session


def _get_user_from_token_or_header(
    token: Optional[str],
    request: Request,
    db: DBSession
) -> DbUser:
    from backend.auth import SECRET_KEY, ALGORITHM
    from jose import jwt, JWTError
    
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated: Missing token")
        
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        db_user = db.query(DbUser).filter(DbUser.email == username).first()
        if not db_user:
            raise HTTPException(status_code=401, detail="User profile not found")
        return db_user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


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
# Semester Analytics & Reports
# ══════════════════════════════════════════════════════════════

@router.get("/semester/status",
            response_model=SemesterStatusResponse,
            summary="Check if semester report is unlocked")
def get_semester_status(
    course_name: str = Query(..., description="Course Name"),
    time_slot  : str = Query(..., description="Time Slot"),
    db         : DBSession = Depends(get_db),
    user       : TokenData = Depends(get_current_user),
):
    """
    Returns whether the semester report is unlocked.
    Unlocked when count of completed sessions (status='ended') reaches 14.
    """
    db_user = db.query(DbUser).filter(DbUser.email == user.username).first()
    if not db_user:
        raise HTTPException(status_code=401, detail="User profile not found")
        
    query = db.query(SessionModel).filter(
        SessionModel.course_name == course_name,
        SessionModel.time_slot   == time_slot,
        SessionModel.status      == "ended"
    )
    if db_user.role == "instructor":
        query = query.filter(SessionModel.instructor_id == db_user.id)
        
    count = query.count()
    return SemesterStatusResponse(
        unlocked     = count >= 14,
        session_count= count,
        required     = 14,
        course_name  = course_name,
        time_slot    = time_slot,
    )


@router.get("/semester/report",
            response_model=SemesterReportResponse,
            summary="Get semester-long aggregated metrics")
def get_semester_report(
    course_name: str = Query(..., description="Course Name"),
    time_slot  : str = Query(..., description="Time Slot"),
    db         : DBSession = Depends(get_db),
    user       : TokenData = Depends(get_current_user),
):
    """
    Returns the aggregated semester metrics across all ended sessions.
    Requires at least 14 completed sessions.
    """
    db_user = db.query(DbUser).filter(DbUser.email == user.username).first()
    if not db_user:
        raise HTTPException(status_code=401, detail="User profile not found")
        
    query = db.query(SessionModel).filter(
        SessionModel.course_name == course_name,
        SessionModel.time_slot   == time_slot,
        SessionModel.status      == "ended"
    )
    if db_user.role == "instructor":
        query = query.filter(SessionModel.instructor_id == db_user.id)
        
    sessions = query.order_by(SessionModel.started_at.asc()).all()

    if len(sessions) < 14:
        raise HTTPException(
            status_code=400,
            detail=f"Semester report is locked. Requires 14 completed sessions. Found {len(sessions)}."
        )

    session_ids = [s.id for s in sessions]
    summaries = (
        db.query(SessionSummary)
          .filter(SessionSummary.session_id.in_(session_ids))
          .all()
    )

    if not summaries:
        raise HTTPException(
            status_code=404,
            detail="No summaries found for the sessions."
        )

    # Perform aggregations
    overall_avg_engagement = sum(clamp_percentage(s.avg_engagement or 0.0) for s in summaries) / len(summaries)
    peak_engagement        = max(clamp_percentage(s.peak_engagement or 0.0) for s in summaries)
    min_engagement         = min(clamp_percentage(s.min_engagement or 0.0) for s in summaries)
    avg_students           = sum(s.avg_students or 0.0 for s in summaries) / len(summaries)
    total_duration_mins    = sum(s.duration_mins or 0.0 for s in summaries)
    total_attentive        = sum(s.total_attentive or 0 for s in summaries)
    total_confused         = sum(s.total_confused or 0 for s in summaries)
    total_distracted       = sum(s.total_distracted or 0 for s in summaries)

    # Compile session milestones
    summary_map = {s.session_id: s for s in summaries}
    session_items = []
    for s in sessions:
        sum_row = summary_map.get(s.id)
        if not sum_row:
            continue
        session_items.append(SemesterSessionItem(
            session_id     = s.id,
            started_at     = s.started_at,
            avg_engagement = round(clamp_percentage(sum_row.avg_engagement or 0.0), 1),
            peak_engagement= round(clamp_percentage(sum_row.peak_engagement or 0.0), 1),
            min_engagement = round(clamp_percentage(sum_row.min_engagement or 0.0), 1),
            avg_students   = round(sum_row.avg_students or 0.0, 1),
            duration_mins  = round(sum_row.duration_mins or 0.0, 1),
        ))

    return SemesterReportResponse(
        course_name           = course_name,
        time_slot             = time_slot,
        session_count         = len(session_items),
        overall_avg_engagement= round(clamp_percentage(overall_avg_engagement), 1),
        peak_engagement       = round(clamp_percentage(peak_engagement), 1),
        min_engagement        = round(clamp_percentage(min_engagement), 1),
        avg_students          = round(avg_students, 1),
        total_duration_mins   = round(total_duration_mins, 1),
        total_attentive       = total_attentive,
        total_confused        = total_confused,
        total_distracted      = total_distracted,
        sessions              = session_items,
    )


@router.get("/semester/report/pdf",
            summary="Download the PDF semester report")
def download_semester_pdf_report(
    request    : Request,
    course_name: str = Query(..., description="Course Name"),
    time_slot  : str = Query(..., description="Time Slot"),
    token      : Optional[str] = Query(None, description="Auth Token"),
    db         : DBSession = Depends(get_db),
):
    """
    Generates and returns the Semester PDF report.
    Requires at least 14 completed sessions.
    """
    # Import here to avoid circular dependencies
    from backend.services.report import generate_semester_pdf_report

    db_user = _get_user_from_token_or_header(token, request, db)
    
    query = db.query(SessionModel).filter(
        SessionModel.course_name == course_name,
        SessionModel.time_slot   == time_slot,
        SessionModel.status      == "ended"
    )
    if db_user.role == "instructor":
        query = query.filter(SessionModel.instructor_id == db_user.id)
        
    sessions = query.order_by(SessionModel.started_at.asc()).all()

    if len(sessions) < 14:
        raise HTTPException(
            status_code=400,
            detail=f"Semester report is locked. Requires 14 completed sessions. Found {len(sessions)}."
        )

    session_ids = [s.id for s in sessions]
    summaries = (
        db.query(SessionSummary)
          .filter(SessionSummary.session_id.in_(session_ids))
          .all()
    )

    summary_map = {s.session_id: s for s in summaries}
    session_items = []
    for s in sessions:
        sum_row = summary_map.get(s.id)
        if not sum_row:
            continue
        session_items.append({
            "session_id"     : s.id,
            "started_at"     : s.started_at,
            "avg_engagement" : clamp_percentage(sum_row.avg_engagement or 0.0),
            "peak_engagement": clamp_percentage(sum_row.peak_engagement or 0.0),
            "min_engagement" : clamp_percentage(sum_row.min_engagement or 0.0),
            "avg_students"   : sum_row.avg_students or 0.0,
            "duration_mins"  : sum_row.duration_mins or 0.0,
            "total_attentive": sum_row.total_attentive or 0,
            "total_confused" : sum_row.total_confused or 0,
            "total_distracted": sum_row.total_distracted or 0,
        })

    # Prepare aggregated stats dict
    aggregated = {
        "overall_avg_engagement": clamp_percentage(sum(clamp_percentage(s.avg_engagement or 0.0) for s in summaries) / len(summaries)),
        "peak_engagement"       : clamp_percentage(max(clamp_percentage(s.peak_engagement or 0.0) for s in summaries)),
        "min_engagement"        : clamp_percentage(min(clamp_percentage(s.min_engagement or 0.0) for s in summaries)),
        "avg_students"          : sum(s.avg_students or 0.0 for s in summaries) / len(summaries),
        "total_duration_mins"   : sum(s.duration_mins or 0.0 for s in summaries),
        "total_attentive"       : sum(s.total_attentive or 0 for s in summaries),
        "total_confused"        : sum(s.total_confused or 0 for s in summaries),
        "total_distracted"      : sum(s.total_distracted or 0 for s in summaries),
    }

    path = generate_semester_pdf_report(
        course_name = course_name,
        time_slot   = time_slot,
        summary     = aggregated,
        sessions    = session_items,
    )

    filename = f"semester_report_{course_name.replace(' ', '_')}_{time_slot.replace(' ', '_')}.pdf"
    return FileResponse(
        path,
        media_type="application/pdf",
        filename=filename,
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
    db_user = db.query(DbUser).filter(DbUser.email == user.username).first()
    if not db_user:
        raise HTTPException(status_code=401, detail="User profile not found")
        
    query = db.query(SessionModel).filter(
        SessionModel.course_name == course_name,
        SessionModel.status      == "ended"
    )
    if db_user.role == "instructor":
        query = query.filter(SessionModel.instructor_id == db_user.id)
        
    sessions = query.order_by(SessionModel.started_at.asc()).all()

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

        avg = clamp_percentage(sm.avg_engagement or 0.0)
        eng_values.append(avg)

        items.append(CourseSessionItem(
            session_id     = s.id,
            started_at     = s.started_at,
            avg_engagement = round(avg, 1),
            peak_engagement= round(clamp_percentage(sm.peak_engagement or 0.0), 1),
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
    session = _verify_session_access(session_id, user, db)
    summary = _get_summary_or_404(session_id, db)

    # Count sessions completed (status='ended') for this exact course and time slot
    semester_count = 0
    if session:
        semester_count = (
            db.query(SessionModel)
              .filter(
                  SessionModel.course_name == session.course_name,
                  SessionModel.time_slot   == session.time_slot,
                  SessionModel.status      == "ended"
              )
              .count()
        )

    avg_eng = clamp_percentage(summary.avg_engagement or 0.0)
    peak_eng = clamp_percentage(summary.peak_engagement or 0.0)
    min_eng = clamp_percentage(summary.min_engagement or 0.0)
    
    att = summary.total_attentive or 0
    con = summary.total_confused or 0
    dis = summary.total_distracted or 0
    
    att_p, conf_p, dist_p = clamp_and_normalize_emotions(att, con, dis)
    tot = att + con + dis
    tot_val = tot if tot > 0 else 1
    
    clamped_att = int(round(tot_val * att_p / 100.0))
    clamped_conf = int(round(tot_val * conf_p / 100.0))
    clamped_distr = int(round(tot_val * dist_p / 100.0))
    sum_dist = clamped_att + clamped_conf + clamped_distr
    if sum_dist != tot_val:
        diff = tot_val - sum_dist
        vals = [clamped_att, clamped_conf, clamped_distr]
        max_idx = vals.index(max(vals))
        vals[max_idx] += diff
        clamped_att, clamped_conf, clamped_distr = vals

    return SessionSummaryResponse(
        session_id      = session_id,
        course_name     = session.course_name  if session else None,
        time_slot       = session.time_slot    if session else None,
        avg_engagement  = avg_eng,
        peak_engagement = peak_eng,
        min_engagement  = min_eng,
        avg_students    = summary.avg_students    or 0.0,
        duration_mins   = summary.duration_mins,
        frames_processed= summary.frames_processed,
        total_attentive = clamped_att,
        total_confused  = clamped_conf,
        total_distracted= clamped_distr,
        emotion_totals  = {
            "attentive": clamped_att,
            "confused": clamped_conf,
            "distracted": clamped_distr,
        },
        pdf_report_path = summary.pdf_report_path,
        csv_report_path = summary.csv_report_path,
        semester_sessions_count = semester_count,
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
    session = _verify_session_access(session_id, user, db)
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

    # Calculate FPS dynamically from summary duration and frames
    summary = db.query(SessionSummary).filter_by(session_id=session_id).first()
    fps = 1.0
    if summary and summary.duration_mins and summary.duration_mins > 0 and summary.frames_processed:
        total_seconds = summary.duration_mins * 60.0
        fps = summary.frames_processed / total_seconds

    sampled = rows[::downsample]

    # ── Process emotion timeseries using 10-80 normalization and rolling average smoothing ──
    n = len(sampled)
    raw_shares = []
    for r in sampled:
        dist = r.distribution or {}
        att = float(dist.get("attentive", 0))
        conf = float(dist.get("confused", 0))
        distr = float(dist.get("distracted", 0))
        
        tot = att + conf + distr
        if tot == 0:
            ap, cp, dp = 33.3, 33.3, 33.4
        else:
            ap = 10.0 + 70.0 * (att / tot)
            cp = 10.0 + 70.0 * (conf / tot)
            dp = 10.0 + 70.0 * (distr / tot)
        raw_shares.append((ap, cp, dp))

    # Apply rolling average smoothing with a window of 5 frames
    smoothed_shares = []
    window_size = 5
    for i in range(n):
        start = max(0, i - window_size // 2)
        end = min(n, i + window_size // 2 + 1)
        window_vals = raw_shares[start:end]
        
        avg_ap = sum(v[0] for v in window_vals) / len(window_vals)
        avg_cp = sum(v[1] for v in window_vals) / len(window_vals)
        avg_dp = sum(v[2] for v in window_vals) / len(window_vals)
        
        smoothed_shares.append((avg_ap, avg_cp, avg_dp))

    # Sum verification & integer rounding to exactly 100
    final_shares = []
    for ap, cp, dp in smoothed_shares:
        ia = int(round(ap))
        ic = int(round(cp))
        id_ = int(round(dp))
        
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
                
        final_shares.append((ia, ic, id_))

    points = []
    for idx, r in enumerate(sampled):
        frame_idx = r.frame_number if r.frame_number is not None else idx * downsample
        elapsed_seconds = frame_idx / fps
        minutes = int(elapsed_seconds // 60)
        seconds = int(elapsed_seconds % 60)
        time_str = f"{minutes:02d}:{seconds:02d}"
        
        eng_pct = clamp_percentage(r.engagement_pct)
        clamped_att, clamped_conf, clamped_distr = final_shares[idx]
        
        points.append(
            EngagementPoint(
                frame_number  = r.frame_number,
                timestamp     = r.timestamp,
                engagement_pct= eng_pct,
                student_count = r.student_count,
                attentive     = clamped_att,
                confused      = clamped_conf,
                distracted    = clamped_distr,
                time_str      = time_str,
            )
        )

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
    request   : Request,
    token     : Optional[str] = Query(None, description="Auth Token"),
    db        : DBSession = Depends(get_db),
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
    db_user = _get_user_from_token_or_header(token, request, db)
    user = TokenData(username=db_user.email, role=db_user.role)
    session = _verify_session_access(session_id, user, db)
    summary = _get_summary_or_404(session_id, db)
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
    request   : Request,
    token     : Optional[str] = Query(None, description="Auth Token"),
    db        : DBSession = Depends(get_db),
):
    """
    Export all frame-level engagement data as a CSV file.

    Columns: frame_number, timestamp, engagement_pct,
             student_count, attentive, confused, distracted
    """
    db_user = _get_user_from_token_or_header(token, request, db)
    user = TokenData(username=db_user.email, role=db_user.role)
    session = _verify_session_access(session_id, user, db)
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


