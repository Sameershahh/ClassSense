# backend/models/session.py
# SQLAlchemy ORM models — maps Python classes to PostgreSQL tables.

from sqlalchemy import (Column, Integer, Float, String,
                        DateTime, JSON, ForeignKey, Text)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from backend.database import Base


class Session(Base):
    """
    One classroom session (a single lecture period).
    Created when instructor clicks "Start Session".
    Closed when they click "End Session".
    """
    __tablename__ = "sessions"

    id            = Column(Integer, primary_key=True, index=True, autoincrement=True)
    instructor_id = Column(Integer, nullable=False, default=1)
    course_name   = Column(String(100), nullable=False)
    time_slot     = Column(String(80),  nullable=True)
    started_at    = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    ended_at      = Column(DateTime(timezone=True), nullable=True)
    status        = Column(String(20), default="active", nullable=False)
    # active | processing | ended | error

    # Relationships
    frame_analytics = relationship("FrameAnalytic", back_populates="session",
                                   cascade="all, delete-orphan")
    summary         = relationship("SessionSummary",  back_populates="session",
                                   uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Session id={self.id} course={self.course_name} status={self.status}>"


class FrameAnalytic(Base):
    """
    Per-frame engagement data stored during video processing.
    One row per processed video frame.
    High volume — up to thousands of rows per session.
    """
    __tablename__ = "frame_analytics"

    id             = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id     = Column(Integer, ForeignKey("sessions.id", ondelete="CASCADE"),
                            nullable=False, index=True)
    timestamp      = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    frame_number   = Column(Integer, nullable=True)         # frame index in the video
    engagement_pct = Column(Float,   nullable=False)
    student_count  = Column(Integer, nullable=False, default=0)
    distribution   = Column(JSON,    nullable=False)
    # {"attentive": N, "confused": N, "distracted": N}

    # Relationship
    session = relationship("Session", back_populates="frame_analytics")


class SessionSummary(Base):
    """
    Aggregated statistics for a completed session.
    One row per session (computed when session ends).
    Used for Session Summary screen and PDF reports.
    """
    __tablename__ = "session_summaries"

    id                = Column(Integer, primary_key=True, autoincrement=True)
    session_id        = Column(Integer, ForeignKey("sessions.id", ondelete="CASCADE"),
                               unique=True, nullable=False, index=True)
    avg_engagement    = Column(Float,   nullable=True)
    peak_engagement   = Column(Float,   nullable=True)
    min_engagement    = Column(Float,   nullable=True)
    avg_students      = Column(Float,   nullable=True)
    duration_mins     = Column(Float,   nullable=True)
    frames_processed  = Column(Integer, nullable=True, default=0)

    # Emotion totals across all frames
    total_attentive   = Column(Integer, default=0)
    total_confused    = Column(Integer, default=0)
    total_distracted  = Column(Integer, default=0)

    # PDF/CSV report file paths (stored after download is triggered)
    pdf_report_path   = Column(String(300), nullable=True)
    csv_report_path   = Column(String(300), nullable=True)

    created_at        = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    session = relationship("Session", back_populates="summary")

    def __repr__(self):
        return (f"<SessionSummary session={self.session_id} "
                f"avg={self.avg_engagement:.1f}%>")
