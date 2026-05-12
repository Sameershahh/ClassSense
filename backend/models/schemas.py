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
    course_name  : str = Field(..., min_length=1, max_length=100,
                               example="CS101 — Data Structures")
    time_slot    : str = Field(default="", max_length=80,
                               example="Monday 10:00 AM – 11:30 AM")
    instructor_id: int = Field(default=1)

    @field_validator("course_name")
    @classmethod
    def course_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("course_name must not be blank")
        return v.strip()


class SessionResponse(BaseModel):
    session_id  : int
    course_name : str
    time_slot   : Optional[str]
    status      : str
    started_at  : Optional[datetime]
    ended_at    : Optional[datetime] = None

    model_config = {"from_attributes": True}


class SessionListItem(BaseModel):
    id          : int
    course_name : Optional[str]
    time_slot   : Optional[str]
    status      : str
    started_at  : Optional[datetime]
    ended_at    : Optional[datetime]

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
    pdf_report_path : Optional[str]
    csv_report_path : Optional[str]

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
