"""
Two-stage Indian agriculture detection:
  Stage 1 — crop type (+ invalid_non_crop rejection)
  Stage 2 — crop-conditioned disease classification
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from app.services.disease_solutions import DiseaseSolutionsService
from app.utils.crop_registry import get_model_crop_names, parse_label_with_model_crops
from app.utils.image_processing import ImageProcessor
from app.utils.indian_crops import (
    friendly_label,
    get_invalid_class_name,
)
from app.utils.leaf_detection import detect_leaf, pil_to_rgb_array, validate_image_quality
from app.utils.model_loader import ModelLoader
from app.utils.severity import build_severity_info
from config import MODEL_CONFIG, MODEL_PATHS

logger = logging.getLogger(__name__)

CROP_CONF_THRESHOLD = float(MODEL_CONFIG.get("crop_confidence_threshold", 70.0))
DISEASE_CONF_THRESHOLD = float(MODEL_CONFIG.get("confidence_threshold", 70.0))


class TwoStageDetectionService:
    """Indian multi-crop disease detection pipeline."""

    def __init__(self) -> None:
        self.crop_model = None
        self.disease_model = None
        self.crop_classes: List[str] = []
        self.disease_classes: List[str] = []
        self.crop_to_index: Dict[str, int] = {}
        self.image_size: Tuple[int, int] = tuple(MODEL_CONFIG["image_size"])
        self.invalid_class = get_invalid_class_name()
        self._load_models()

    def _load_models(self) -> None:
        self.crop_model = ModelLoader.load_crop_classifier(MODEL_PATHS["crop_classifier"])
        self.disease_model = ModelLoader.load_disease_classifier(MODEL_PATHS["disease_classifier"])

        with open(MODEL_PATHS["crop_classifier_labels"], encoding="utf-8") as f:
            crop_meta = json.load(f)
        with open(MODEL_PATHS["disease_classifier_labels"], encoding="utf-8") as f:
            disease_meta = json.load(f)

        self.crop_classes = list(crop_meta["classes"])
        self.disease_classes = list(disease_meta["classes"])
        self.crop_to_index = disease_meta.get("crop_to_index", {})
        size = disease_meta.get("image_size", list(self.image_size))
        self.image_size = (int(size[0]), int(size[1]))

        if not self.crop_to_index:
            stage1_crops = [
                c for c in self.crop_classes if c != self.invalid_class
            ]
            self.crop_to_index = {c: i for i, c in enumerate(stage1_crops)}

        logger.info(
            "Two-stage pipeline ready: %d crops, %d disease classes, size=%s",
            len(self.crop_classes),
            len(self.disease_classes),
            self.image_size,
        )

    @staticmethod
    def is_available() -> bool:
        return (
            MODEL_PATHS["crop_classifier"].is_file()
            and MODEL_PATHS["disease_classifier"].is_file()
            and MODEL_PATHS["crop_classifier_labels"].is_file()
            and MODEL_PATHS["disease_classifier_labels"].is_file()
        )

    def predict_from_base64(self, base64_image: str) -> Dict[str, Any]:
        try:
            pil_img = ImageProcessor.decode_base64_image(base64_image)
            pil_img = ImageProcessor.convert_to_rgb(pil_img)
        except ValueError:
            return self._error(
                "invalid_image",
                "Please upload a valid crop image.",
            )

        rgb = pil_to_rgb_array(pil_img)
        valid, msg = validate_image_quality(rgb)
        if not valid:
            return self._error("invalid_image", "Please upload a valid crop image.")

        has_leaf, leaf_msg = detect_leaf(rgb)
        if not has_leaf:
            return self._error("no_leaf", "Please upload a valid crop image.")

        processed = ImageProcessor.preprocess_image(pil_img, self.image_size)
        return self._predict_two_stage(processed)

    def _predict_two_stage(self, img_array: np.ndarray) -> Dict[str, Any]:
        # --- Stage 1: crop ---
        crop_probs = self.crop_model.predict(img_array, verbose=0)[0]
        crop_idx = int(np.argmax(crop_probs))
        crop_conf = float(crop_probs[crop_idx]) * 100
        crop_raw = self.crop_classes[crop_idx]

        crop_predictions = {
            self.crop_classes[i]: round(float(crop_probs[i]) * 100, 2)
            for i in range(len(self.crop_classes))
        }

        if crop_raw == self.invalid_class:
            return self._error(
                "invalid_image",
                "Please upload a valid crop image.",
                confidence=round(crop_conf, 2),
                crop_predictions=crop_predictions,
            )

        if crop_conf < CROP_CONF_THRESHOLD:
            return self._error(
                "low_confidence",
                "Unable to confidently predict disease. Please try another image.",
                confidence=round(crop_conf, 2),
                crop_predictions=crop_predictions,
            )

        crop = self._resolve_crop(crop_raw)

        # --- Stage 2: disease (crop-conditioned) ---
        crop_oh = np.zeros((1, len(self.crop_to_index)), dtype=np.float32)
        cidx = self._crop_index(crop, crop_raw)
        crop_oh[0, cidx] = 1.0

        disease_probs = self.disease_model.predict([img_array, crop_oh], verbose=0)[0]
        masked_probs = self._mask_diseases_for_crop(disease_probs, crop)
        disease_idx = int(np.argmax(masked_probs))
        disease_conf = float(masked_probs[disease_idx]) * 100

        all_disease_preds = {
            friendly_label(self.disease_classes[i]): round(float(masked_probs[i]) * 100, 2)
            for i in range(len(self.disease_classes))
            if masked_probs[i] > 0.001
        }

        if disease_conf < DISEASE_CONF_THRESHOLD:
            return self._error(
                "low_confidence",
                "Unable to confidently predict disease. Please try another image.",
                crop=crop,
                confidence=round(disease_conf, 2),
                crop_confidence=round(crop_conf, 2),
                all_predictions=all_disease_preds,
                crop_predictions=crop_predictions,
            )

        raw_label = self.disease_classes[disease_idx]
        parsed_crop, disease, is_healthy = parse_label_with_model_crops(raw_label)
        if parsed_crop != "Unknown":
            crop = parsed_crop

        if is_healthy:
            return self._healthy(crop, disease_conf, crop_conf, all_disease_preds, crop_predictions)

        solution = DiseaseSolutionsService.lookup(crop, disease, False)
        meta = DiseaseSolutionsService.get_disease_metadata(crop, disease, False)
        severity = build_severity_info(False, meta, disease_conf)
        disease_full = solution.get("disease_name") if solution else f"{crop} {disease}"

        payload = {
            "status": "success",
            "pipeline": "two_stage",
            "crop": crop,
            "disease": disease,
            "disease_full_name": disease_full,
            "prediction": disease_full,
            "is_healthy": False,
            "confidence": round(disease_conf, 2),
            "crop_confidence": round(crop_conf, 2),
            "severity_percent": severity["severity_percent"],
            "harmfulness": severity["harmfulness"],
            "impact": severity["impact"],
            "message": f"Crop: {crop} | Disease: {disease_full}",
            "all_predictions": all_disease_preds,
            "crop_predictions": crop_predictions,
            "solution": solution or DiseaseSolutionsService.get_default_solution(disease_full),
        }
        return self._enrich(payload)

    def _resolve_crop(self, crop_raw: str) -> str:
        from app.utils.indian_crops import normalize_crop_name

        resolved = normalize_crop_name(crop_raw) or crop_raw
        for mc in get_model_crop_names():
            if mc.lower() == resolved.lower() or mc.lower() == crop_raw.lower():
                return mc
        return resolved

    def _crop_index(self, crop: str, crop_raw: str) -> int:
        if crop in self.crop_to_index:
            return self.crop_to_index[crop]
        if crop_raw in self.crop_to_index:
            return self.crop_to_index[crop_raw]
        for name, idx in self.crop_to_index.items():
            if name.lower() == crop.lower():
                return idx
        return 0

    @staticmethod
    def _enrich(payload: Dict[str, Any]) -> Dict[str, Any]:
        from app.services.prediction_explainer import build_explanation

        payload["explanation"] = build_explanation(
            crop=payload.get("crop", ""),
            disease=payload.get("disease", ""),
            confidence=float(payload.get("confidence", 0)),
            is_healthy=bool(payload.get("is_healthy")),
            all_predictions=payload.get("all_predictions", {}),
            confidence_warning=float(payload.get("confidence", 100)) < DISEASE_CONF_THRESHOLD,
        )
        return payload

    def _mask_diseases_for_crop(self, probs: np.ndarray, crop: str) -> np.ndarray:
        """Zero out disease classes that do not belong to the predicted crop."""
        masked = np.zeros_like(probs)
        crop_lower = crop.lower()
        for i, cls in enumerate(self.disease_classes):
            if cls.lower().startswith(crop_lower + "___") or cls.lower().startswith(crop_lower + "_"):
                masked[i] = probs[i]
        if masked.sum() <= 0:
            return probs
        return masked

    def _healthy(
        self,
        crop: str,
        disease_conf: float,
        crop_conf: float,
        all_preds: dict,
        crop_preds: dict,
    ) -> Dict[str, Any]:
        solution = DiseaseSolutionsService.lookup(crop, "Healthy", True)
        return self._enrich({
            "status": "success",
            "pipeline": "two_stage",
            "crop": crop,
            "disease": "Healthy",
            "disease_full_name": f"{crop} — Healthy",
            "prediction": "Healthy Crop Detected",
            "is_healthy": True,
            "confidence": round(disease_conf, 2),
            "crop_confidence": round(crop_conf, 2),
            "severity_percent": 0,
            "harmfulness": "Low",
            "impact": "No disease detected. Continue regular field monitoring.",
            "message": "Healthy Crop Detected",
            "all_predictions": all_preds,
            "crop_predictions": crop_preds,
            "solution": solution or {},
        })

    @staticmethod
    def _error(error_type: str, message: str, **extra: Any) -> Dict[str, Any]:
        return {"status": "error", "error_type": error_type, "message": message, **extra}
