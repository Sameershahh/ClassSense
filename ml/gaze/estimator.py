# ml/gaze/estimator.py
# Head pose / gaze estimation using MediaPipe Face Mesh.
# Determines if a student is looking forward (attentive) or looking away.
#
# Algorithm:
#   1. MediaPipe Face Mesh gives 468 3D landmarks for each face in the frame.
#   2. We pick 6 key landmarks matching a known 3D face model.
#   3. cv2.solvePnP() finds the head rotation vector from 2D→3D correspondences.
#   4. We convert to Euler angles and threshold on yaw (left-right) + pitch (up-down).
#   5. Score: 1.0 = looking straight forward, 0.0 = looking fully away.
#
# Integrated into ml/pipeline.py — the pipeline calls estimate(frame) once per
# frame and pairs each gaze score with the nearest tracked face by proximity.

import cv2
import numpy as np
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

# ── 3D face reference model ────────────────────────────────────────────────────
# Generic human face points in 3D space (millimetres).
# These match the LANDMARK_IDS indices below.
FACE_3D_MODEL = np.array([
    [   0.0,    0.0,   0.0],  # Nose tip        (idx 1)
    [   0.0, -330.0, -65.0],  # Chin            (idx 152)
    [-225.0,  170.0,-135.0],  # Left eye corner (idx 226)
    [ 225.0,  170.0,-135.0],  # Right eye corner(idx 446)
    [-150.0, -150.0,-125.0],  # Left mouth      (idx 57)
    [ 150.0, -150.0,-125.0],  # Right mouth     (idx 287)
], dtype=np.float64)

# Corresponding Face Mesh landmark indices
LANDMARK_IDS = [1, 152, 226, 446, 57, 287]


class GazeEstimator:
    """
    Estimates head pose / gaze direction for every face in a frame.

    Usage:
        estimator = GazeEstimator()
        gaze_scores = estimator.estimate(frame_bgr)
        # gaze_scores: list of floats, one per detected face
        # 1.0 = looking forward, 0.0 = looking fully away
    """

    def __init__(self, max_num_faces: int = 15):
        self._ready = False
        self._face_mesh = None
        self._init(max_num_faces)

    def _init(self, max_num_faces: int) -> None:
        try:
            import mediapipe as mp
            self._face_mesh = mp.solutions.face_mesh.FaceMesh(
                max_num_faces=max_num_faces,
                refine_landmarks=True,        # more accurate eye & lip landmarks
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5,
            )
            self._ready = True
            logger.info("GazeEstimator: MediaPipe Face Mesh loaded (max_faces=%d).", max_num_faces)
        except Exception as exc:
            logger.warning(
                "GazeEstimator: could not load Face Mesh — %s. "
                "Gaze scores will default to 1.0 (neutral forward).", exc
            )

    @property
    def is_ready(self) -> bool:
        return self._ready

    def estimate(self, frame_bgr: np.ndarray) -> List[dict]:
        """
        Run head-pose estimation on every face detected by Face Mesh.

        Args:
            frame_bgr: Full classroom frame in BGR format (from OpenCV).

        Returns:
            List of dicts, one per detected face:
                {
                    "score" : float (1.0 to 0.0),
                    "center": (cx, cy) tuple of floats,
                    "bbox"  : (x, y, w, h) bounding box in pixel coords
                              (derived from all 468 landmarks — reused by
                               the pipeline as DeepSORT detections so we
                               never need a separate face-detector call).
                }
        """
        if not self._ready or self._face_mesh is None:
            return []

        if frame_bgr is None or frame_bgr.size == 0:
            return []

        h, w = frame_bgr.shape[:2]
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        results = self._face_mesh.process(rgb)

        if not results.multi_face_landmarks:
            return []

        # Camera intrinsic matrix (estimated from frame dimensions)
        focal      = float(w)
        cam_matrix = np.array([
            [focal, 0,    w / 2.0],
            [0,    focal, h / 2.0],
            [0,    0,    1.0     ],
        ], dtype=np.float64)
        dist_coeffs = np.zeros((4, 1), dtype=np.float64)

        gaze_results: List[dict] = []

        for face_landmarks in results.multi_face_landmarks:
            # ── Bounding box from ALL 468 landmarks ──────────────
            # This is more reliable than any separate detector and
            # gives us multi-face boxes for free from the same pass.
            all_x = [lm.x for lm in face_landmarks.landmark]
            all_y = [lm.y for lm in face_landmarks.landmark]
            margin = 0.02   # 2 % of frame as padding
            x1 = int(max(0,     (min(all_x) - margin) * w))
            y1 = int(max(0,     (min(all_y) - margin) * h))
            x2 = int(min(w - 1, (max(all_x) + margin) * w))
            y2 = int(min(h - 1, (max(all_y) + margin) * h))
            bw = max(1, x2 - x1)
            bh = max(1, y2 - y1)
            bbox = (x1, y1, bw, bh)   # (x, y, w, h) for DeepSORT

            # ── Nose tip as face centre ───────────────────────────
            nose_lm = face_landmarks.landmark[1]
            cx, cy  = nose_lm.x * w, nose_lm.y * h

            # ── Head-pose via 6 key landmarks ────────────────────
            points_2d = np.array(
                [[face_landmarks.landmark[idx].x * w,
                  face_landmarks.landmark[idx].y * h]
                 for idx in LANDMARK_IDS],
                dtype=np.float64,
            )

            success, rot_vec, _ = cv2.solvePnP(
                FACE_3D_MODEL, points_2d, cam_matrix, dist_coeffs,
                flags=cv2.SOLVEPNP_ITERATIVE,
            )
            if not success:
                gaze_results.append({"score": 0.5, "center": (cx, cy), "bbox": bbox})
                continue

            rot_mat, _ = cv2.Rodrigues(rot_vec)
            angles, _, _, _, _, _ = cv2.RQDecomp3x3(rot_mat)

            yaw   = abs(angles[1])   # left-right rotation
            pitch = abs(angles[0])   # up-down rotation

            if yaw < 15 and pitch < 20:
                score = 1.0   # clearly attentive
            elif yaw < 30:
                score = 0.6   # slightly turned
            elif yaw < 45:
                score = 0.3   # significantly turned
            else:
                score = 0.0   # looking fully away

            gaze_results.append({"score": score, "center": (cx, cy), "bbox": bbox})

        return gaze_results


# ── Standalone test ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    estimator = GazeEstimator()
    cap = cv2.VideoCapture(0)   # 0 = default webcam
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        scores = estimator.estimate(frame)
        label = f"Gaze scores: {[round(s,2) for s in scores]}"
        cv2.putText(frame, label, (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 200), 2)
        cv2.imshow("Gaze Estimation Test", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
    cap.release()
    cv2.destroyAllWindows()
