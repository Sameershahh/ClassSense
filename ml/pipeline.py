# ml/pipeline.py
# ClassSensePipeline — full inference pipeline.
#
# Stack:
#   Face detection  : MediaPipe FaceDetection (fast, CPU-friendly)
#   Tracking        : DeepSORT (deep-sort-realtime)
#   Emotion         : MobileNetV2 fine-tuned on FER-2013 + ClassSense labels
#   Engagement score: weighted mean of CLASS_SCORES per tracked student
#
# This file is imported by backend/services/ml_runner.py at startup.
# Do NOT import FastAPI or SQLAlchemy here — keep ML and web layers separate.

import cv2
import logging
import numpy as np
from collections import deque, defaultdict
from typing import Generator, Optional, List, Dict

logger = logging.getLogger(__name__)

# Emotion class constants (re-exported so ml_runner has one import point)
CLASS_NAMES  = ["attentive", "confused", "distracted"]
CLASS_SCORES = {"attentive": 1.0, "confused": 0.5, "distracted": 0.0}

# Annotation colours (BGR) for export_annotated_video
_COLOURS = {
    "attentive" : (0, 200, 0),
    "confused"  : (0, 165, 255),
    "distracted": (0, 0, 220),
}


# ── Tracker wrapper ───────────────────────────────────────────────────────────

class _TrackerWrapper:
    """
    Thin wrapper around DeepSort so we can expose reset() cleanly.
    ml_runner calls self._pipeline.tracker.reset() for per-image processing.
    """

    def __init__(self, max_age: int = 30, n_init: int = 2):
        self._max_age = max_age
        self._n_init  = n_init
        self._tracker = self._make()

    def _make(self):
        from deep_sort_realtime.deepsort_tracker import DeepSort
        return DeepSort(max_age=self._max_age, n_init=self._n_init)

    def update(self, detections: list, frame: np.ndarray) -> list:
        """
        detections: list of ([x, y, w, h], confidence, class_id)
        Returns list of active tracks.
        """
        return self._tracker.update_tracks(detections, frame=frame)

    def reset(self) -> None:
        """Re-create tracker to clear all track history."""
        self._tracker = self._make()


# ── Face detector ─────────────────────────────────────────────────────────────

class _FaceDetector:
    """
    MediaPipe FaceDetection wrapper.
    Falls back to OpenCV Haar cascade if MediaPipe is unavailable.
    """

    def __init__(self, min_confidence: float = 0.5):
        self._min_conf = min_confidence
        self._detector = None
        self._fallback = False
        self._init()

    def _init(self) -> None:
        try:
            import mediapipe as mp
            self._mp_fd    = mp.solutions.face_detection
            self._detector = self._mp_fd.FaceDetection(
                model_selection=1,              # full-range model (>2m)
                min_detection_confidence=self._min_conf,
            )
            logger.info("FaceDetector: MediaPipe loaded.")
        except Exception as exc:
            logger.warning(
                "FaceDetector: MediaPipe unavailable (%s). "
                "Falling back to OpenCV Haar cascade.", exc
            )
            self._fallback = True
            self._detector = cv2.CascadeClassifier(
                cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            )

    def detect(self, frame_bgr: np.ndarray) -> List[tuple]:
        """
        Returns list of (x, y, w, h) face bounding boxes.
        Coordinates are pixel-absolute, clipped to frame bounds.
        """
        if frame_bgr is None or frame_bgr.size == 0:
            return []
        h, w = frame_bgr.shape[:2]

        if self._fallback:
            return self._detect_haar(frame_bgr, w, h)
        return self._detect_mediapipe(frame_bgr, w, h)

    def _detect_mediapipe(self, frame_bgr, w, h):
        rgb     = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        results = self._detector.process(rgb)
        boxes   = []
        if not results.detections:
            return boxes
        for det in results.detections:
            bb = det.location_data.relative_bounding_box
            x  = max(0, int(bb.xmin  * w))
            y  = max(0, int(bb.ymin  * h))
            bw = min(int(bb.width  * w), w - x)
            bh = min(int(bb.height * h), h - y)
            if bw > 10 and bh > 10:
                boxes.append((x, y, bw, bh))
        return boxes

    def _detect_haar(self, frame_bgr, w, h):
        gray  = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        faces = self._detector.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
        )
        if len(faces) == 0:
            return []
        return [(int(x), int(y), int(fw), int(fh)) for x, y, fw, fh in faces]


# ── Main pipeline ─────────────────────────────────────────────────────────────

class ClassSensePipeline:
    """
    End-to-end classroom engagement pipeline.

    Instantiated once by ml_runner (singleton) at FastAPI startup.

    Args:
        weights_path      : Path to classsense_mobilenetv2.pth (or None).
        emotion_skip_every: Run emotion classifier every N frames (saves CPU).
        smoothing_window  : Rolling window size for engagement % smoothing.
    """

    def __init__(
        self,
        weights_path      : Optional[str] = None,
        emotion_skip_every: int            = 3,
        smoothing_window  : int            = 10,
    ):
        self._emotion_skip_every = max(1, emotion_skip_every)
        self._smoothing_window   = max(1, smoothing_window)

        # ── Sub-components ────────────────────────────────────
        from ml.emotion.classifier import EmotionClassifier
        self.classifier = EmotionClassifier(weights_path)
        self.tracker    = _TrackerWrapper(max_age=30, n_init=2)
        self._detector  = _FaceDetector(min_confidence=0.5)

        # ── Session state (reset per session) ─────────────────
        self._frame_id          : int                    = 0
        self._track_emotions    : Dict[int, dict]        = {}
        self._session_results   : list                   = []
        self._engagement_history: deque                  = deque(maxlen=self._smoothing_window)

        logger.info(
            "ClassSensePipeline ready | model_loaded=%s | "
            "emotion_skip=%d | smoothing=%d",
            self.classifier.is_ready,
            self._emotion_skip_every,
            self._smoothing_window,
        )

    # ── Session lifecycle ─────────────────────────────────────

    def reset_session(self) -> None:
        """Reset all per-session accumulators. Call before processing a new video."""
        self._frame_id           = 0
        self._track_emotions     = {}
        self._session_results    = []
        self._engagement_history = deque(maxlen=self._smoothing_window)
        self.tracker.reset()
        logger.debug("Pipeline: session reset.")

    def get_session_summary(self) -> dict:
        """
        Aggregate engagement metrics across all processed frames.
        Called by ml_runner.end_session() after video processing.
        """
        if not self._session_results:
            return {}

        all_eng = [
            r["engagement"]["engagement_pct"]
            for r in self._session_results
            if r["engagement"]["student_count"] > 0
        ]
        all_stu = [
            r["engagement"]["student_count"]
            for r in self._session_results
            if r["engagement"]["student_count"] > 0
        ]
        att = sum(r["engagement"]["distribution"].get("attentive",  0)
                  for r in self._session_results)
        con = sum(r["engagement"]["distribution"].get("confused",   0)
                  for r in self._session_results)
        dis = sum(r["engagement"]["distribution"].get("distracted", 0)
                  for r in self._session_results)

        return {
            "avg_engagement"  : round(sum(all_eng) / len(all_eng), 2) if all_eng else 0.0,
            "peak_engagement" : round(max(all_eng),                 2) if all_eng else 0.0,
            "min_engagement"  : round(min(all_eng),                 2) if all_eng else 0.0,
            "avg_students"    : round(sum(all_stu) / len(all_stu),  1) if all_stu else 0.0,
            "frames_processed": len(self._session_results),
            "total_attentive" : att,
            "total_confused"  : con,
            "total_distracted": dis,
        }

    # ── Core frame processing ─────────────────────────────────

    def process_frame(self, frame: np.ndarray, accumulate: bool = True) -> dict:
        """
        Run full pipeline on one BGR frame.

        Args:
            frame      : BGR uint8 numpy array.
            accumulate : If True, append result to session history
                         (set False for single-image API calls).

        Returns:
            Result dict matching the shape expected by ml_runner / sessions router.
        """
        self._frame_id += 1

        # 1. Detect faces
        face_boxes = self._detector.detect(frame)

        # 2. Build detection list for DeepSORT: ([x,y,w,h], conf, class_id)
        detections = [([x, y, w, h], 0.9, 0) for x, y, w, h in face_boxes]

        # 3. Update tracker
        try:
            tracks = self.tracker.update(detections, frame)
        except Exception as exc:
            logger.warning("Tracker update failed (frame %d): %s", self._frame_id, exc)
            tracks = []

        # 4. Determine which objects to analyze (Tracks for Video, Detections for Image)
        targets = []
        
        if accumulate:
            # VIDEO MODE: Use tracks (handles occlusion and smoothing)
            for track in tracks:
                if not track.is_confirmed():
                    continue
                ltrb = track.to_ltrb()
                targets.append({
                    "id": track.track_id,
                    "bbox": [max(0, int(ltrb[0])), max(0, int(ltrb[1])), 
                             min(frame.shape[1], int(ltrb[2])), min(frame.shape[0], int(ltrb[3]))]
                })
        else:
            # SINGLE IMAGE MODE: Use raw detections (tracker won't confirm in 1 frame)
            for i, (box, conf, cls) in enumerate(detections):
                x, y, w, h = box
                targets.append({
                    "id": i + 1,
                    "bbox": [x, y, x + w, y + h]
                })

        run_emotion = (
            (self._frame_id % self._emotion_skip_every == 0)
            or (self._frame_id == 1)
            or (not accumulate) # Always run for single images
        )

        distribution    = {cls: 0 for cls in CLASS_NAMES}
        student_details = []

        for target in targets:
            x1, y1, x2, y2 = target["bbox"]
            track_id = target["id"]

            if x2 <= x1 or y2 <= y1:
                continue

            # Run emotion classifier (or reuse cached)
            if run_emotion:
                face_crop = frame[y1:y2, x1:x2]
                pred = self.classifier.predict(face_crop)
                self._track_emotions[track_id] = pred

            pred  = self._track_emotions.get(track_id) or self.classifier._neutral()
            label = pred["label"]
            distribution[label] = distribution.get(label, 0) + 1

            student_details.append({
                "track_id"  : track_id,
                "bbox"      : [x1, y1, x2, y2],
                "emotion"   : label,
                "confidence": pred["confidence"],
                "score"     : pred["score"],
            })

        # 5. Engagement score = mean(individual scores) * 100
        student_count = len(student_details)
        scores = [d["score"] for d in student_details]
        raw_pct = (sum(scores) / len(scores) * 100) if scores else 0.0

        # Rolling smooth
        self._engagement_history.append(raw_pct)
        smoothed_pct = sum(self._engagement_history) / len(self._engagement_history)

        # Distribution percentages
        total = student_count or 1
        dist_pct = {k: round(100.0 * v / total, 1) for k, v in distribution.items()}

        result = {
            "frame_id": self._frame_id,
            "engagement": {
                "engagement_pct"  : round(smoothed_pct, 1),
                "student_count"   : student_count,
                "distribution"    : distribution,
                "distribution_pct": dist_pct,
            },
            "tracked_count" : student_count,
            "faces"         : [d["bbox"] for d in student_details],
            "student_details": student_details,
        }

        if accumulate:
            self._session_results.append(result)

        return result

    # ── Video processing ──────────────────────────────────────

    def process_video(
        self,
        video_path    : str,
        progress_every: int = 60,
    ) -> Generator[dict, None, None]:
        """
        Process a video file frame by frame and yield result dicts.
        Caller: ml_runner.process_video() → list(generator).
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logger.error("Cannot open video: %s", video_path)
            return

        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps   = cap.get(cv2.CAP_PROP_FPS) or 30.0
        logger.info("Video: %s | %d frames @ %.1f fps", video_path, total, fps)

        frame_idx = 0
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                result = self.process_frame(frame, accumulate=True)
                yield result

                frame_idx += 1
                if progress_every > 0 and frame_idx % progress_every == 0:
                    pct = 100.0 * frame_idx / total if total > 0 else 0.0
                    logger.info(
                        "Video progress: %d/%d (%.1f%%)", frame_idx, total, pct
                    )
        finally:
            cap.release()
            logger.info("Video processing complete: %d frames", frame_idx)

    # ── Annotated video export (FYP demo) ─────────────────────

    def export_annotated_video(self, input_path: str, output_path: str) -> dict:
        """
        Process a video and write an annotated copy with bounding boxes,
        emotion labels, and engagement overlay. Used for FYP demo.
        """
        cap = cv2.VideoCapture(input_path)
        if not cap.isOpened():
            logger.error("Cannot open video for annotation: %s", input_path)
            return {}

        fps    = cap.get(cv2.CAP_PROP_FPS) or 30.0
        width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out    = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        self.reset_session()
        frame_count = 0

        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                result = self.process_frame(frame, accumulate=True)

                # Draw bounding boxes + emotion labels
                for det in result.get("student_details", []):
                    x1, y1, x2, y2 = det["bbox"]
                    label  = det["emotion"]
                    colour = _COLOURS.get(label, (255, 255, 255))
                    cv2.rectangle(frame, (x1, y1), (x2, y2), colour, 2)
                    text = f"#{det['track_id']} {label} {det['confidence']:.2f}"
                    cv2.putText(
                        frame, text, (x1, max(y1 - 8, 12)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, colour, 1,
                    )

                # HUD overlay (top-left)
                eng_pct = result["engagement"]["engagement_pct"]
                hud     = (
                    f"Engagement: {eng_pct:.1f}%  "
                    f"Students: {result['engagement']['student_count']}"
                )
                cv2.putText(
                    frame, hud, (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2,
                )

                out.write(frame)
                frame_count += 1
        finally:
            cap.release()
            out.release()

        summary              = self.get_session_summary()
        summary["output_path"] = output_path
        summary["frame_count"] = frame_count
        logger.info("Annotated video saved: %s (%d frames)", output_path, frame_count)
        return summary
