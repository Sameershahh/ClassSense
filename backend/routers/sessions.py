# backend/routers/sessions.py
# Session lifecycle endpoints.
#
# POST   /api/sessions/              → create session
# GET    /api/sessions/              → list all sessions
# GET    /api/sessions/{id}          → get one session
# DELETE /api/sessions/{id}          → delete session
# POST   /api/sessions/{id}/upload-video  → process uploaded video
# POST   /api/sessions/{id}/upload-image  → process single image
# POST   /api/sessions/{id}/end      → end session + compute summary

import os
import shutil
import logging
import time as time_module
from typing import List, Optional

from fastapi import (APIRouter, Depends, UploadFile, File,
                     HTTPException, BackgroundTasks, Query, status,
                     WebSocket, WebSocketDisconnect)
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session as DBSession
import json
import asyncio

from backend.database import get_db
from backend.auth import get_current_user, TokenData
from backend.models.session import (Session as SessionModel,
                                    FrameAnalytic, SessionSummary)
from backend.models.schemas import (SessionCreate, SessionResponse,
                                    SessionListItem, ProcessingStatus,
                                    ImageAnalysisResult)
from backend.services.ml_runner import ml_runner

logger = logging.getLogger(__name__)
router = APIRouter()

# ── Upload constraints ────────────────────────────────────────
TMP_DIR             = "/tmp/classsense_uploads"
ALLOWED_VIDEO_EXT   = {".mp4", ".avi", ".mov", ".mkv", ".webm"}
ALLOWED_IMAGE_EXT   = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
MAX_VIDEO_MB        = 500
MAX_IMAGE_MB        = 20

os.makedirs(TMP_DIR, exist_ok=True)


# ── Helpers ───────────────────────────────────────────────────

def _get_session_or_404(session_id: int, db: DBSession) -> SessionModel:
    s = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not s:
        raise HTTPException(status_code=404,
                            detail=f"Session {session_id} not found")
    return s


def _bulk_save_frame_analytics(session_id: int, results: list,
                                db: DBSession) -> int:
    """Insert all frame analytics rows in one commit. Returns row count."""
    rows = []
    for idx, r in enumerate(results):
        eng = r.get("engagement", {})
        if eng.get("student_count", 0) == 0:
            continue
        rows.append(FrameAnalytic(
            session_id    = session_id,
            frame_number  = r.get("frame_id", idx),
            engagement_pct= eng.get("engagement_pct", 0.0),
            student_count = eng.get("student_count",  0),
            distribution  = eng.get("distribution",   {}),
        ))
    if rows:
        db.bulk_save_objects(rows)
        db.commit()
    return len(rows)


# ══════════════════════════════════════════════════════════════
# CRUD
# ══════════════════════════════════════════════════════════════

@router.post("/", response_model=SessionResponse, status_code=201,
             summary="Start a new session")
def start_session(
    payload: SessionCreate,
    db     : DBSession = Depends(get_db),
    user   : TokenData = Depends(get_current_user),
):
    """
    Create a session record and prime the ML pipeline.

    **Body:**
    ```json
    { "course_name": "CS101", "time_slot": "Mon 10:00 AM" }
    ```
    """
    session = SessionModel(
        instructor_id = payload.instructor_id,
        course_name   = payload.course_name,
        time_slot     = payload.time_slot,
        status        = "active",
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    ml_runner.start_session(session.id)
    logger.info("Session %d started — course: %s", session.id, session.course_name)

    return SessionResponse(
        session_id  = session.id,
        course_name = session.course_name,
        time_slot   = session.time_slot,
        status      = session.status,
        started_at  = session.started_at,
    )


@router.get("/", response_model=List[SessionListItem],
            summary="List all sessions")
def list_sessions(
    limit : int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0,  ge=0),
    status: Optional[str] = Query(default=None,
                                  description="Filter: active | ended | processing"),
    db    : DBSession = Depends(get_db),
    user  : TokenData = Depends(get_current_user),
):
    """Return sessions newest-first, with optional status filter."""
    q = db.query(SessionModel).order_by(SessionModel.started_at.desc())
    if status:
        q = q.filter(SessionModel.status == status)
    sessions = q.offset(offset).limit(limit).all()
    return [
        SessionListItem(
            id          = s.id,
            course_name = s.course_name,
            time_slot   = s.time_slot,
            status      = s.status,
            started_at  = s.started_at,
            ended_at    = s.ended_at,
        )
        for s in sessions
    ]


@router.get("/{session_id}", response_model=SessionResponse,
            summary="Get one session")
def get_session(
    session_id: int,
    db        : DBSession = Depends(get_db),
    user      : TokenData = Depends(get_current_user),
):
    s = _get_session_or_404(session_id, db)
    return SessionResponse(
        session_id  = s.id,
        course_name = s.course_name,
        time_slot   = s.time_slot,
        status      = s.status,
        started_at  = s.started_at,
        ended_at    = s.ended_at,
    )


@router.delete("/{session_id}", status_code=204,
               summary="Delete a session and all its data")
def delete_session(
    session_id: int,
    db        : DBSession = Depends(get_db),
    user      : TokenData = Depends(get_current_user),
):
    s = _get_session_or_404(session_id, db)
    db.delete(s)
    db.commit()


# ══════════════════════════════════════════════════════════════
# VIDEO UPLOAD & PROCESSING
# ══════════════════════════════════════════════════════════════

@router.post("/{session_id}/upload-video",
             response_model=ProcessingStatus,
             summary="Upload a classroom video and process it")
async def upload_and_process_video(
    session_id: int,
    file      : UploadFile = File(...),
    db        : DBSession  = Depends(get_db),
    user      : TokenData  = Depends(get_current_user),
):
    """
    Upload a classroom video file. The full ML pipeline runs on every frame:
    face detection → tracking → emotion recognition → gaze → engagement score.
    All per-frame results are saved to the database.

    **Accepted formats:** .mp4, .avi, .mov, .mkv, .webm
    **Max size:** 500 MB

    After uploading, call `POST /{session_id}/end` to compute the summary.
    """
    # Validate session exists and is active
    session = _get_session_or_404(session_id, db)
    if session.status not in ("active",):
        raise HTTPException(
            status_code=400,
            detail=f"Session {session_id} is not active (status: {session.status}). "
                   f"Only active sessions can receive video uploads.",
        )

    # Validate file extension
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_VIDEO_EXT:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported file type '{ext}'. Allowed: {sorted(ALLOWED_VIDEO_EXT)}",
        )

    # Save upload to temp file
    tmp_path = os.path.join(TMP_DIR, f"session_{session_id}{ext}")
    try:
        with open(tmp_path, "wb") as fp:
            shutil.copyfileobj(file.file, fp)

        size_mb = os.path.getsize(tmp_path) / 1e6
        if size_mb > MAX_VIDEO_MB:
            raise HTTPException(
                status_code=413,
                detail=f"File too large ({size_mb:.0f} MB). Limit: {MAX_VIDEO_MB} MB",
            )

        logger.info("[Session %d] Video upload: %s (%.1f MB)",
                    session_id, file.filename, size_mb)

        # Mark session as processing
        session.status = "processing"
        db.commit()

        # ── Run ML pipeline ──────────────────────────────────
        t_start  = time_module.time()
        all_results = list(ml_runner.process_video(tmp_path, session_id))
        elapsed     = time_module.time() - t_start

        # ── Persist analytics ────────────────────────────────
        saved_rows = _bulk_save_frame_analytics(session_id, all_results, db)

        # ── Gather quick summary for response ────────────────
        pcts   = [r["engagement"]["engagement_pct"]
                  for r in all_results
                  if r["engagement"]["student_count"] > 0]
        counts = [r["engagement"]["student_count"]
                  for r in all_results
                  if r["engagement"]["student_count"] > 0]

        avg_eng  = sum(pcts)   / len(pcts)   if pcts   else 0.0
        peak_eng = max(pcts)                 if pcts   else 0.0
        min_eng  = min(pcts)                 if pcts   else 0.0
        avg_stu  = sum(counts) / len(counts) if counts else 0.0

        # Mark session back to active (ready for end-session call)
        session.status = "active"
        db.commit()

        logger.info("[Session %d] Processed %d frames in %.1fs",
                    session_id, len(all_results), elapsed)

        return ProcessingStatus(
            session_id      = session_id,
            status          = "processed",
            frames_processed= len(all_results),
            rows_saved      = saved_rows,
            avg_engagement  = round(avg_eng,  1),
            peak_engagement = round(peak_eng, 1),
            min_engagement  = round(min_eng,  1),
            avg_students    = round(avg_stu,  1),
            duration_secs   = round(elapsed,  1),
            message         = f"Processed {len(all_results)} frames in {elapsed:.1f}s",
        )

    except HTTPException:
        session.status = "active"
        db.commit()
        raise
    except Exception as exc:
        session.status = "error"
        db.commit()
        logger.error("[Session %d] Video processing failed: %s", session_id, exc,
                     exc_info=True)
        raise HTTPException(status_code=500,
                            detail=f"Processing failed: {str(exc)}")
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


# ══════════════════════════════════════════════════════════════
# SINGLE IMAGE UPLOAD
# ══════════════════════════════════════════════════════════════

@router.post("/{session_id}/upload-image",
             response_model=ImageAnalysisResult,
             summary="Upload a single classroom image and analyse it")
async def upload_and_process_image(
    session_id: int,
    file      : UploadFile = File(...),
    db        : DBSession  = Depends(get_db),
    user      : TokenData  = Depends(get_current_user),
):
    """
    Analyse a single classroom photo.
    Each image is processed independently — no cross-image tracking.
    The result is saved as one FrameAnalytic row.
    """
    session = _get_session_or_404(session_id, db)

    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_IMAGE_EXT:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported image type '{ext}'. Allowed: {sorted(ALLOWED_IMAGE_EXT)}",
        )

    image_bytes = await file.read()
    if len(image_bytes) > MAX_IMAGE_MB * 1_000_000:
        raise HTTPException(
            status_code=413,
            detail=f"Image too large. Limit: {MAX_IMAGE_MB} MB",
        )

    result = ml_runner.process_image_bytes(image_bytes)
    eng    = result.get("engagement", {})

    # Save to DB if students were detected
    if eng.get("student_count", 0) > 0:
        db.add(FrameAnalytic(
            session_id    = session_id,
            engagement_pct= eng.get("engagement_pct", 0.0),
            student_count = eng.get("student_count",  0),
            distribution  = eng.get("distribution",   {}),
        ))
        db.commit()

    dist = eng.get("distribution", {})
    tot  = eng.get("student_count", 0) or 1

    return ImageAnalysisResult(
        session_id      = session_id,
        filename        = file.filename,
        engagement_pct  = eng.get("engagement_pct", 0.0),
        student_count   = eng.get("student_count",  0),
        distribution    = dist,
        distribution_pct= {
            k: round(100 * v / tot, 1) for k, v in dist.items()
        },
        student_details = result.get("student_details", []),
    )


# ══════════════════════════════════════════════════════════════
# END SESSION
# ══════════════════════════════════════════════════════════════

@router.post("/{session_id}/end",
             summary="End session and compute summary statistics")
def end_session(
    session_id: int,
    db        : DBSession = Depends(get_db),
    user      : TokenData = Depends(get_current_user),
):
    """
    Mark the session as ended and compute aggregated summary stats
    (avg, peak, min engagement; emotion totals; duration).
    These stats power the Session Summary screen and PDF report.
    """
    session = _get_session_or_404(session_id, db)
    if session.status == "ended":
        raise HTTPException(status_code=400,
                            detail=f"Session {session_id} is already ended.")

    frames = (
        db.query(FrameAnalytic)
          .filter(FrameAnalytic.session_id == session_id)
          .order_by(FrameAnalytic.timestamp.asc())
          .all()
    )

    if not frames:
        raise HTTPException(
            status_code=400,
            detail="No frame analytics found for this session. "
                   "Upload a video first (POST /{id}/upload-video).",
        )

    # ── Compute stats ─────────────────────────────────────────
    pcts   = [f.engagement_pct  for f in frames]
    counts = [f.student_count   for f in frames]
    att    = sum(f.distribution.get("attentive",  0) for f in frames)
    con    = sum(f.distribution.get("confused",   0) for f in frames)
    dis    = sum(f.distribution.get("distracted", 0) for f in frames)

    # Duration from first to last frame timestamp
    duration_mins = None
    if frames[0].timestamp and frames[-1].timestamp:
        delta         = frames[-1].timestamp - frames[0].timestamp
        duration_mins = round(delta.total_seconds() / 60, 1)

    # Upsert SessionSummary
    summary = (
        db.query(SessionSummary)
          .filter_by(session_id=session_id)
          .first()
    )
    if not summary:
        summary = SessionSummary(session_id=session_id)
        db.add(summary)

    summary.avg_engagement   = round(sum(pcts)   / len(pcts),   2)
    summary.peak_engagement  = round(max(pcts),                 2)
    summary.min_engagement   = round(min(pcts),                 2)
    summary.avg_students     = round(sum(counts) / len(counts), 1)
    summary.duration_mins    = duration_mins
    summary.frames_processed = len(frames)
    summary.total_attentive  = att
    summary.total_confused   = con
    summary.total_distracted = dis

    # Mark session ended
    from sqlalchemy.sql import func as sqlfunc
    session.status   = "ended"
    session.ended_at = sqlfunc.now()

    db.commit()

    logger.info("[Session %d] Ended — avg=%.1f%% peak=%.1f%%",
                session_id, summary.avg_engagement, summary.peak_engagement)

    return {
        "status"    : "ended",
        "session_id": session_id,
        "summary"   : {
            "avg_engagement" : summary.avg_engagement,
            "peak_engagement": summary.peak_engagement,
            "min_engagement" : summary.min_engagement,
            "avg_students"   : summary.avg_students,
            "duration_mins"  : summary.duration_mins,
            "frames_analysed": len(frames),
            "emotion_totals" : {
                "attentive" : att,
                "confused"  : con,
                "distracted": dis,
            },
        },
    }


# ══════════════════════════════════════════════════════════════
# REAL-TIME & EVALUATION CHANNELS (Phase 6 / 14 Requirements)
# ══════════════════════════════════════════════════════════════

@router.post("/start", summary="Start session alias (Phase 6)")
def start_session_alias(course: str, time_slot: str, db: DBSession = Depends(get_db)):
    """
    Alias starting endpoint matching the FYP implementation plan specifications exactly.
    """
    session = SessionModel(
        instructor_id = 1,
        course_name   = course,
        time_slot     = time_slot,
        status        = "active",
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    ml_runner.start_session(session.id)
    return {"session_id": session.id, "status": "started"}

@router.post("/{session_id}/process-video", summary="Process video alias (Phase 6)")
async def process_video_alias(
    session_id: int,
    file      : UploadFile = File(...),
    db        : DBSession  = Depends(get_db),
):
    """
    Alias processing endpoint matching the FYP implementation plan specifications exactly.
    """
    session = _get_session_or_404(session_id, db)
    ext = os.path.splitext(file.filename or "")[1].lower()
    if not ext:
        ext = ".mp4"
    tmp_path = os.path.join(TMP_DIR, f"session_{session_id}_alias{ext}")
    try:
        with open(tmp_path, "wb") as fp:
            shutil.copyfileobj(file.file, fp)
        
        session.status = "processing"
        db.commit()

        # Run pipeline
        all_results = list(ml_runner.process_video(tmp_path, session_id))

        # Save analytics
        _bulk_save_frame_analytics(session_id, all_results, db)

        # Mark session active so it can be ended
        session.status = "active"
        db.commit()
    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass
    
    return {"frames_processed": len(all_results), "session_id": session_id}

@router.websocket("/{session_id}/stream")
async def websocket_stream(
    websocket : WebSocket,
    session_id: int,
    db        : DBSession = Depends(get_db),
):
    """
    Real-time WebSocket connection to receive live frames, run engagement
    scoring, persist database frame analytics, and return live feedback.
    """
    await websocket.accept()
    logger.info("[WebSocket] Connection accepted for session %d", session_id)
    
    # Track frame count for index insertion
    frame_counter = 0
    try:
        while True:
            # Receive frame bytes
            frame_bytes = await websocket.receive_bytes()
            frame_counter += 1
            
            # Run ML pipeline in worker thread to prevent blocking event loop
            result = await asyncio.to_thread(ml_runner.process_bytes, frame_bytes)
            
            # Save frame analytic row to DB
            eng = result.get("engagement", {})
            db_analytic = FrameAnalytic(
                session_id    = session_id,
                frame_number  = frame_counter,
                engagement_pct= eng.get("engagement_pct", 0.0),
                student_count = eng.get("student_count", 0),
                distribution  = eng.get("distribution", {}),
            )
            db.add(db_analytic)
            db.commit()
            
            # Return live analytics back to browser/client
            await websocket.send_text(json.dumps(eng))
    except WebSocketDisconnect:
        logger.info("[WebSocket] Connection disconnected cleanly for session %d", session_id)
    except Exception as exc:
        logger.error("[WebSocket] Error in stream: %s", exc, exc_info=True)

