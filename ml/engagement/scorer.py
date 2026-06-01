# ml/engagement/scorer.py
# Computes per-student and class-wide engagement scores.
#
# Formula (as per the ClassSense Implementation Plan, Phase 4):
#   engagement_per_student = (0.6 × gaze_score) + (0.4 × emotion_score)
#   class_engagement_pct   = mean(all student scores) × 100
#
# A rolling average (smoothing_window frames) is applied to prevent
# sudden spikes in the dashboard number.

from dataclasses import dataclass, field
from typing import List
from collections import deque


# ── Engagement class scores (must match ml/emotion/classifier.py) ──────────────
EMOTION_SCORES = {
    "attentive" : 1.0,
    "confused"  : 0.5,
    "distracted": 0.0,
}


@dataclass
class StudentEngagement:
    """
    Holds the engagement signals for one tracked student in one frame.

    Fields:
        track_id     : Anonymous integer ID assigned by DeepSORT.
        emotion      : 'attentive' | 'confused' | 'distracted'
        emotion_score: Float score from EMOTION_SCORES (1.0 / 0.5 / 0.0)
        gaze_score   : Float score from GazeEstimator  (1.0 → 0.0)
                       Defaults to 1.0 (forward-looking) if gaze is unavailable.
    """
    track_id     : int
    emotion      : str
    emotion_score: float
    gaze_score   : float = 1.0   # default: assume looking forward

    @property
    def engagement_score(self) -> float:
        """
        Weighted combination:
            60 % gaze attention  +  40 % emotion state
        Range: 0.0 (fully disengaged) → 1.0 (fully engaged)
        """
        return (0.6 * self.gaze_score) + (0.4 * self.emotion_score)


@dataclass
class ClassEngagement:
    """
    Aggregated engagement metrics for the entire class in one frame.
    This is the object sent to the WebSocket / REST response.
    """
    engagement_pct  : float          # e.g. 87.3 (already × 100)
    student_count   : int
    attentive_count : int
    confused_count  : int
    distracted_count: int
    student_details : List[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Return a JSON-serialisable dict matching the API response schema."""
        total = self.student_count or 1
        return {
            "engagement_pct": round(self.engagement_pct, 1),
            "student_count" : self.student_count,
            "distribution"  : {
                "attentive" : self.attentive_count,
                "confused"  : self.confused_count,
                "distracted": self.distracted_count,
            },
            "distribution_pct": {
                "attentive" : round(100.0 * self.attentive_count  / total, 1),
                "confused"  : round(100.0 * self.confused_count   / total, 1),
                "distracted": round(100.0 * self.distracted_count / total, 1),
            },
            "student_details": self.student_details,
        }


class EngagementScorer:
    """
    Converts a list of StudentEngagement objects into a ClassEngagement result.

    Uses a rolling average over the last `smoothing_window` frames to smooth out
    per-frame noise before the number is displayed on the dashboard.

    Usage:
        scorer  = EngagementScorer(smoothing_window=10)
        result  = scorer.score_frame(students)
        payload = result.to_dict()      # ready for JSON / WebSocket send
    """

    def __init__(self, smoothing_window: int = 10):
        self._history: deque = deque(maxlen=max(1, smoothing_window))

    def score_frame(self, students: List[StudentEngagement]) -> ClassEngagement:
        """
        Compute class engagement for one frame.

        Args:
            students: List of StudentEngagement objects (one per tracked face).

        Returns:
            ClassEngagement with smoothed engagement_pct and distribution counts.
        """
        if not students:
            self._history.append(0.0)
            return ClassEngagement(
                engagement_pct  =0.0,
                student_count   =0,
                attentive_count =0,
                confused_count  =0,
                distracted_count=0,
            )

        scores  = [s.engagement_score for s in students]
        raw_pct = (sum(scores) / len(scores)) * 100.0

        self._history.append(raw_pct)
        smoothed_pct = sum(self._history) / len(self._history)

        details = [
            {
                "id"   : s.track_id,
                "emotion": s.emotion,
                "score": round(s.engagement_score, 3),
            }
            for s in students
        ]

        return ClassEngagement(
            engagement_pct  =round(smoothed_pct, 1),
            student_count   =len(students),
            attentive_count =sum(1 for s in students if s.emotion == "attentive"),
            confused_count  =sum(1 for s in students if s.emotion == "confused"),
            distracted_count=sum(1 for s in students if s.emotion == "distracted"),
            student_details =details,
        )

    def reset(self) -> None:
        """Clear history — call at the start of each new session."""
        self._history.clear()


# ── Quick unit test ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    scorer = EngagementScorer(smoothing_window=5)

    # 3 attentive (looking forward) + 1 distracted (looking away)
    test_students = [
        StudentEngagement(track_id=1, emotion="attentive",  emotion_score=1.0, gaze_score=1.0),
        StudentEngagement(track_id=2, emotion="attentive",  emotion_score=1.0, gaze_score=0.9),
        StudentEngagement(track_id=3, emotion="attentive",  emotion_score=1.0, gaze_score=1.0),
        StudentEngagement(track_id=4, emotion="distracted", emotion_score=0.0, gaze_score=0.0),
    ]

    result = scorer.score_frame(test_students)
    print("Class engagement:", result.to_dict())
    # Expected: engagement_pct ~= 75  (3/4 attentive, one fully disengaged)
