# backend/services/ml_runner.py
# Bridge between FastAPI and the ML pipeline.
# Loaded ONCE at startup — singleton pattern.
# Handles: video processing, single-image processing, session lifecycle.

import cv2
import numpy as np
import logging
import os
from pathlib import Path
from typing import Generator, Optional

logger = logging.getLogger(__name__)

# Model weights path — override with MODEL_WEIGHTS_PATH env var if needed.
# Default: <project_root>/ml/emotion/model_weights/classsense_mobilenetv2.pth
_env_override = os.getenv("MODEL_WEIGHTS_PATH", "")
if _env_override:
    WEIGHTS_PATH = Path(_env_override)
else:
    WEIGHTS_PATH = (
        Path(__file__).parents[2]
        / "ml"
        / "emotion"
        / "model_weights"
        / "classsense_mobilenetv2.pth"
    )

# Reports directory — created at import time so report.py never fails on mkdir
REPORTS_DIR = Path(os.getenv("REPORTS_DIR", "reports"))
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


class MLRunner:
    """
    Singleton wrapper around ClassSensePipeline.
    One instance is created at FastAPI startup and shared across all requests.
    Thread-safe for read operations; video processing is CPU-bound so
    each request effectively serialises through the GIL anyway.
    """

    def __init__(self):
        self._pipeline = None
        self._loaded   = False
        self._load_pipeline()

    def _load_pipeline(self):
        try:
            from ml.pipeline import ClassSensePipeline   # noqa — imported at runtime
            weights = str(WEIGHTS_PATH) if WEIGHTS_PATH.exists() else None
            if weights is None:
                logger.warning(
                    "Model weights not found at %s. "
                    "Classifier will return neutral defaults. "
                    "Copy your Colab .pth export to ml/emotion/model_weights/",
                    WEIGHTS_PATH,
                )
            self._pipeline = ClassSensePipeline(
                weights_path=weights,
                emotion_skip_every=3,
                smoothing_window=10,
            )
            self._loaded = True
            logger.info("MLRunner: ClassSensePipeline loaded successfully.")
        except Exception as exc:
            logger.error("MLRunner: Failed to load pipeline — %s", exc, exc_info=True)
            self._pipeline = None
            self._loaded   = False

    # ── Properties ───────────────────────────────────────────

    @property
    def is_ready(self) -> bool:
        return self._loaded and self._pipeline is not None

    @property
    def model_loaded(self) -> bool:
        return self._loaded and self._pipeline is not None and \
               self._pipeline.classifier.is_ready

    @property
    def weights_path(self) -> Optional[str]:
        return str(WEIGHTS_PATH) if WEIGHTS_PATH.exists() else None

    # ── Session lifecycle ─────────────────────────────────────

    def start_session(self, session_id: int):
        """Reset pipeline state for a fresh session."""
        if self._pipeline:
            self._pipeline.reset_session()
        logger.info("[Session %d] Pipeline reset for new session.", session_id)

    def end_session(self, session_id: int) -> dict:
        """Return aggregated session summary and reset."""
        if not self._pipeline:
            return {}
        summary = self._pipeline.get_session_summary()
        logger.info("[Session %d] Ended — summary: %s", session_id, summary)
        return summary

    # ── Video processing ──────────────────────────────────────

    def process_video(self, video_path: str,
                      session_id: int) -> Generator[dict, None, None]:
        """
        Process an uploaded video file frame by frame.
        Yields one result dict per processed frame.
        Each dict matches ClassSensePipeline.process_frame() output.
        """
        if not self._pipeline:
            logger.error("[Session %d] Pipeline not loaded — cannot process video.", session_id)
            return

        logger.info("[Session %d] Processing video: %s", session_id, video_path)
        self._pipeline.reset_session()
        yield from self._pipeline.process_video(video_path, progress_every=60)

    # ── Image processing ─────────────────────────────────────

    def process_image_bytes(self, image_bytes: bytes) -> dict:
        """
        Process a single classroom image from raw upload bytes.
        Tracker is reset — each image is treated independently.
        """
        if not self._pipeline:
            return self._empty_result()

        arr   = np.frombuffer(image_bytes, dtype=np.uint8)
        frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if frame is None:
            logger.warning("Could not decode image bytes.")
            return self._empty_result()

        # Reset session and tracker so each image is independent (no cross-image tracking or emotion leakage)
        self._pipeline.reset_session()
        return self._pipeline.process_frame(frame, accumulate=False)

    # ── Annotated video export (FYP demo) ────────────────────

    def export_annotated_video(self, input_path: str, output_path: str) -> dict:
        """
        Process a video and write an annotated copy with bounding boxes,
        emotion labels, and engagement % overlay.
        Used for generating the FYP demo video.
        """
        if not self._pipeline:
            return {}
        self._pipeline.reset_session()
        return self._pipeline.export_annotated_video(input_path, output_path)

    @staticmethod
    def _empty_result() -> dict:
        return {
            "frame_id"      : 0,
            "engagement"    : {
                "engagement_pct"  : 0.0,
                "student_count"   : 0,
                "distribution"    : {"attentive": 0, "confused": 0, "distracted": 0},
                "distribution_pct": {"attentive": 0.0, "confused": 0.0, "distracted": 0.0},
            },
            "tracked_count" : 0,
            "faces"         : [],
            "student_details": [],
        }


# ── Module-level singleton ────────────────────────────────────
# Imported by routers:
#   from backend.services.ml_runner import ml_runner
ml_runner = MLRunner()
