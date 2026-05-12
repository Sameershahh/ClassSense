# ml/emotion/classifier.py
# Wraps the ClassSense MobileNetV2 emotion model.
#
# Architecture mirrors Colab build_model() exactly — so state_dict keys match.
# Loads from the .pth checkpoint produced by save_best_model() in the notebook.
# Falls back to neutral (score=0.5) if weights file is missing or corrupt.

import logging
from pathlib import Path
from typing import Optional

import numpy as np
import torch
import torch.nn as nn
import torchvision.models as models
import torchvision.transforms as T

logger = logging.getLogger(__name__)

# ── Constants (must match Colab Cell 6 & Cell 7 val_transform) ────────────────
IMG_SIZE      = 224
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD  = [0.229, 0.224, 0.225]

CLASS_NAMES  = ["attentive", "confused", "distracted"]
CLASS_TO_IDX = {c: i for i, c in enumerate(CLASS_NAMES)}
CLASS_SCORES = {"attentive": 1.0, "confused": 0.5, "distracted": 0.0}

# ── Inference transform (matches Colab val_transform, no albumentations needed)
_infer_transform = T.Compose([
    T.ToPILImage(),
    T.Resize((IMG_SIZE, IMG_SIZE)),
    T.ToTensor(),
    T.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
])


# ── Model architecture — identical to Colab build_model() ─────────────────────

def _build_model(num_classes: int = 3, dropout: float = 0.4) -> nn.Module:
    """
    Exact replica of Colab build_model().
    weights=None because we load fine-tuned weights from the .pth checkpoint.
    """
    model = models.mobilenet_v2(weights=None)
    in_feat = model.classifier[1].in_features
    model.classifier = nn.Sequential(
        nn.Dropout(p=dropout),
        nn.Linear(in_feat, 512),
        nn.BatchNorm1d(512),
        nn.ReLU(inplace=True),
        nn.Dropout(p=dropout * 0.5),
        nn.Linear(512, num_classes),
    )
    return model


# ── Classifier wrapper ────────────────────────────────────────────────────────

class EmotionClassifier:
    """
    CPU inference wrapper around the ClassSense MobileNetV2 model.

    Usage:
        clf = EmotionClassifier("ml/emotion/model_weights/classsense_mobilenetv2.pth")
        result = clf.predict(face_bgr_array)
        # result = {label, confidence, score, probs}
    """

    def __init__(self, weights_path: Optional[str] = None):
        self._model        : Optional[nn.Module] = None
        self._ready        : bool                = False
        self._class_names  : list                = CLASS_NAMES
        self._class_scores : dict                = CLASS_SCORES

        if weights_path and Path(weights_path).exists():
            self._load(weights_path)
        else:
            logger.warning(
                "EmotionClassifier: weights not found at '%s'. "
                "Returning neutral defaults until you drop the .pth file.",
                weights_path,
            )

    # ── Internal ─────────────────────────────────────────────

    def _load(self, path: str) -> None:
        try:
            # weights_only=False required: checkpoint contains Python dicts
            ckpt = torch.load(path, map_location="cpu", weights_only=False)

            num_classes = ckpt.get("num_classes", 3)
            dropout     = ckpt.get("dropout", 0.4)

            # Prefer metadata baked into checkpoint over hardcoded defaults
            self._class_names  = ckpt.get("class_names",  CLASS_NAMES)
            self._class_scores = ckpt.get("class_scores", CLASS_SCORES)

            model = _build_model(num_classes=num_classes, dropout=dropout)
            model.load_state_dict(ckpt["model_state_dict"])
            model.eval()

            self._model = model
            self._ready = True
            logger.info(
                "EmotionClassifier: loaded '%s'  classes=%s",
                Path(path).name, self._class_names,
            )
        except Exception as exc:
            logger.error(
                "EmotionClassifier: failed to load weights — %s", exc, exc_info=True
            )
            self._ready = False

    # ── Public API ────────────────────────────────────────────

    @property
    def is_ready(self) -> bool:
        return self._ready

    def predict(self, face_bgr: np.ndarray) -> dict:
        """
        Classify emotion for one face crop (BGR uint8 numpy array).

        Returns:
            {
                "label"     : str,   # attentive | confused | distracted
                "confidence": float, # softmax probability of winner
                "score"     : float, # engagement score (1.0 / 0.5 / 0.0)
                "probs"     : dict,  # {class_name: prob} for all classes
            }
        """
        if not self._ready or self._model is None:
            return self._neutral()

        if face_bgr is None or face_bgr.size == 0:
            return self._neutral()

        try:
            # BGR → RGB, then apply val_transform
            rgb    = face_bgr[:, :, ::-1].copy()
            tensor = _infer_transform(rgb).unsqueeze(0)   # (1, 3, 224, 224)

            with torch.no_grad():
                probs = torch.softmax(self._model(tensor), dim=1)[0].numpy()

            idx   = int(np.argmax(probs))
            label = self._class_names[idx]
            conf  = float(probs[idx])
            score = self._class_scores.get(label, 0.5)

            return {
                "label"     : label,
                "confidence": round(conf, 3),
                "score"     : score,
                "probs"     : {
                    n: round(float(p), 3)
                    for n, p in zip(self._class_names, probs)
                },
            }
        except Exception as exc:
            logger.warning("EmotionClassifier.predict error: %s", exc)
            return self._neutral()

    def _neutral(self) -> dict:
        """Default when model is unavailable — neutral mid-point score."""
        return {
            "label"     : "attentive",
            "confidence": 0.0,
            "score"     : 0.5,
            "probs"     : {n: round(1.0 / len(self._class_names), 3)
                           for n in self._class_names},
        }
