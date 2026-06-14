# backend/models/schemas.py
# Pydantic v2 schemas for all API request bodies and response shapes.

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, List
from datetime import datetime


# ══════════════════════════════════════════════════════════════
# Auth schemas
# ══════════════════════════════════════════════════════════════

class Token(BaseModel):
    access_token: str
    token_type:   str = "bearer"

class TokenData(BaseModel):
    username: Optional[str] = None
    role:     Optional[str] = None


# ══════════════════════════════════════════════════════════════
# Session schemas
# ══════════════════════════════════════════════════════════════

class SessionCreate(BaseModel):
    course_slot_id: int
    mode         : str = "video"  # live | video
    instructor_id: Optional[int] = 1


class SessionResponse(BaseModel):
    session_id  : int
    course_name : str
    time_slot   : Optional[str]
    status      : str
    started_at  : Optional[datetime]
    ended_at    : Optional[datetime] = None
    semester_sessions_count: Optional[int] = None
    start_date_time: Optional[str] = None
    end_date_time: Optional[str] = None
    mode: Optional[str] = "video"

    model_config = {"from_attributes": True}


class SessionListItem(BaseModel):
    id          : int
    course_name : Optional[str]
    time_slot   : Optional[str]
    status      : str
    started_at  : Optional[datetime]
    ended_at    : Optional[datetime]
    start_date_time: Optional[str] = None
    end_date_time: Optional[str] = None

    model_config = {"from_attributes": True}


# ══════════════════════════════════════════════════════════════
# Processing / upload schemas
# ══════════════════════════════════════════════════════════════

class ProcessingStatus(BaseModel):
    """Returned after a video or image is processed."""
    session_id      : int
    status          : str        # "processed" | "error"
    frames_processed: int
    rows_saved      : int
    avg_engagement  : float
    peak_engagement : float
    min_engagement  : float
    avg_students    : float
    duration_secs   : Optional[float] = None
    message         : Optional[str]   = None


class ImageAnalysisResult(BaseModel):
    """Returned after a single classroom image is processed."""
    session_id     : int
    filename       : Optional[str]
    engagement_pct : float
    student_count  : int
    distribution   : Dict[str, int]
    distribution_pct: Dict[str, float]
    student_details: List[dict]


# ══════════════════════════════════════════════════════════════
# Analytics schemas
# ══════════════════════════════════════════════════════════════

class EngagementPoint(BaseModel):
    """One data point in the engagement time-series chart."""
    frame_number  : Optional[int]
    timestamp     : datetime
    engagement_pct: float
    student_count : int
    attentive     : int
    confused      : int
    distracted    : int
    time_str      : Optional[str] = None


class AnalyticsTimeSeries(BaseModel):
    session_id: int
    total_frames: int
    points    : List[EngagementPoint]


class SessionSummaryResponse(BaseModel):
    session_id      : int
    course_name     : Optional[str]
    time_slot       : Optional[str]
    avg_engagement  : float
    peak_engagement : float
    min_engagement  : float
    avg_students    : float
    duration_mins   : Optional[float]
    frames_processed: Optional[int]
    total_attentive : int
    total_confused  : int
    total_distracted: int
    emotion_totals  : Optional[Dict[str, int]] = None
    pdf_report_path : Optional[str]
    csv_report_path : Optional[str]
    semester_sessions_count: Optional[int] = None

    model_config = {"from_attributes": True}


class CourseSessionItem(BaseModel):
    session_id    : int
    started_at    : Optional[datetime]
    avg_engagement: float
    peak_engagement: float
    avg_students  : float
    duration_mins : Optional[float]


class CourseAnalytics(BaseModel):
    course_name    : str
    session_count  : int
    overall_avg    : float
    trend_direction: str    # "improving" | "declining" | "stable"
    sessions       : List[CourseSessionItem]


class ModelStatusResponse(BaseModel):
    model_loaded : bool
    message      : str
    weights_path : Optional[str] = None


# ══════════════════════════════════════════════════════════════
# Semester Analytics schemas
# ══════════════════════════════════════════════════════════════

class SemesterStatusResponse(BaseModel):
    unlocked     : bool
    session_count: int
    required     : int = 14
    course_name  : str
    time_slot    : str


class SemesterSessionItem(BaseModel):
    session_id     : int
    started_at     : datetime
    avg_engagement : float
    peak_engagement: float
    min_engagement : float
    avg_students   : float
    duration_mins  : float


class SemesterReportResponse(BaseModel):
    course_name           : str
    time_slot             : str
    session_count         : int
    overall_avg_engagement: float
    peak_engagement       : float
    min_engagement        : float
    avg_students          : float
    total_duration_mins   : float
    total_attentive       : int
    total_confused        : int
    total_distracted      : int
    sessions              : List[SemesterSessionItem]
