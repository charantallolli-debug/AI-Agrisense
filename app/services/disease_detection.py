"""
Disease detection facade — routes to two-stage Indian pipeline or legacy single model.
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from app.services.two_stage_detection import TwoStageDetectionService
from config import MODEL_CONFIG, MODEL_PATHS

logger = logging.getLogger(__name__)

# User-facing messages (Indian agriculture requirements)
MSG_INVALID = "Please upload a valid crop image."
MSG_LOW_CONF = "Unable to confidently predict disease. Please try another image."
MSG_UNSUPPORTED = "Crop currently not supported."
MSG_HEALTHY = "Healthy Crop Detected"


class _LegacyDiseaseDetectionService:
    """Original single-model path (128x128 tomato CNN fallback)."""

    def __init__(self) -> None:
        import json
        from typing import List, Tuple

        import numpy as np

        from app.services.disease_solutions import DiseaseSolutionsService
        from app.utils.crop_registry import parse_label_with_model_crops
        from app.utils.image_processing import ImageProcessor
        from app.utils.leaf_detection import detect_leaf, pil_to_rgb_array, validate_image_quality
        from app.utils.model_loader import ModelLoader
        from app.utils.severity import build_severity_info

        self._np = np
        self._ImageProcessor = ImageProcessor
        self._detect_leaf = detect_leaf
        self._pil_to_rgb_array = pil_to_rgb_array
        self._validate = validate_image_quality
        self._parse = parse_label_with_model_crops
        self._solutions = DiseaseSolutionsService
        self._severity = build_severity_info
        self._loader = ModelLoader
        self._paths = MODEL_PATHS
        self._config = MODEL_CONFIG

        self.model = None
        self.classes: List[str] = []
        self.folder_classes: List[str] = []
        self.image_size: Tuple[int, int] = tuple(MODEL_CONFIG.get("legacy_image_size", (128, 128)))
        self._load_model()
        self._load_metadata()

    def _load_model(self) -> None:
        self.model = self._loader.load_disease_detection_model(MODEL_PATHS["disease_detection"])

    def _load_metadata(self) -> None:
        labels_path = MODEL_PATHS.get("class_labels")
        if labels_path and labels_path.is_file():
            import json
            with open(labels_path, encoding="utf-8") as f:
                meta = json.load(f)
            self.classes = list(meta.get("classes", MODEL_CONFIG["disease_classes"]))
            self.folder_classes = list(meta.get("folder_classes", self.classes))
            size = meta.get("image_size", list(self.image_size))
            self.image_size = (int(size[0]), int(size[1]))

        n_out = int(self.model.output_shape[-1])
        if len(self.classes) != n_out:
            logger.warning(
                "Class labels (%d) != model outputs (%d). Run training to sync.",
                len(self.classes),
                n_out,
            )

    def _predict_probs(self, pil_img) -> Any:
        """Run inference with optional test-time augmentation (horizontal flip average)."""
        from PIL import Image as PILImage

        from config import INTEGRATION_CONFIG

        batch = self._ImageProcessor.preprocess_image(pil_img, self.image_size)
        probs = self.model.predict(batch, verbose=0)[0]
        if not INTEGRATION_CONFIG.get("enable_tta", True):
            return probs

        flipped = pil_img.transpose(PILImage.FLIP_LEFT_RIGHT)
        batch_flip = self._ImageProcessor.preprocess_image(flipped, self.image_size)
        probs_flip = self.model.predict(batch_flip, verbose=0)[0]
        return (probs + probs_flip) / 2.0

    def _enrich_success(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        from app.services.prediction_explainer import build_explanation

        payload["explanation"] = build_explanation(
            crop=payload.get("crop", ""),
            disease=payload.get("disease", ""),
            confidence=float(payload.get("confidence", 0)),
            is_healthy=bool(payload.get("is_healthy")),
            all_predictions=payload.get("all_predictions", {}),
            confidence_warning=bool(payload.get("confidence_warning")),
        )
        return payload

        if self.folder_classes and index < len(self.folder_classes):
            return self.folder_classes[index]
        if index < len(self.classes):
            return self.classes[index]
        return f"Class_{index}"

    def predict_from_base64(self, base64_image: str) -> Dict[str, Any]:
        high_threshold = float(MODEL_CONFIG.get("confidence_threshold", 70.0))
        min_threshold = float(MODEL_CONFIG.get("min_prediction_threshold", 35.0))
        try:
            pil_img = self._ImageProcessor.decode_base64_image(base64_image)
            pil_img = self._ImageProcessor.convert_to_rgb(pil_img)
        except ValueError:
            return _err("invalid_image", MSG_INVALID)

        rgb = self._pil_to_rgb_array(pil_img)
        valid, _ = self._validate(rgb)
        if not valid:
            return _err("invalid_image", MSG_INVALID)

        has_leaf, _ = self._detect_leaf(rgb)
        if not has_leaf:
            return _err("no_leaf", MSG_INVALID)

        probs = self._predict_probs(pil_img)
        n_out = len(probs)
        idx = int(self._np.argmax(probs))
        conf = float(probs[idx]) * 100

        all_preds = {}
        for i in range(n_out):
            label = self._label_at(i)
            display = self.classes[i] if i < len(self.classes) else label
            all_preds[display] = round(float(probs[i]) * 100, 2)

        if conf < min_threshold:
            return _err(
                "low_confidence",
                MSG_LOW_CONF,
                confidence=round(conf, 2),
                all_predictions=all_preds,
            )

        raw_label = self._label_at(idx)
        crop, disease, is_healthy = self._parse(raw_label)
        confidence_warning = conf < high_threshold

        if is_healthy:
            sol = self._solutions.lookup(crop, "Healthy", True)
            return self._enrich_success({
                "status": "success",
                "pipeline": "legacy",
                "crop": crop,
                "disease": "Healthy",
                "prediction": MSG_HEALTHY,
                "is_healthy": True,
                "confidence": round(conf, 2),
                "confidence_warning": confidence_warning,
                "severity_percent": 0,
                "harmfulness": "Low",
                "impact": "No disease detected.",
                "message": MSG_HEALTHY,
                "all_predictions": all_preds,
                "solution": sol or {},
            })

        meta = self._solutions.get_disease_metadata(crop, disease, False)
        sol = self._solutions.lookup(crop, disease, False)
        sev = self._severity(False, meta, conf)
        name = sol.get("disease_name") if sol else f"{crop} {disease}"
        msg = f"Crop: {crop} | Disease: {name}"
        if confidence_warning:
            msg += f" (confidence {round(conf, 1)}% — consider a clearer leaf photo)"

        return self._enrich_success({
            "status": "success",
            "pipeline": "legacy",
            "crop": crop,
            "disease": disease,
            "disease_full_name": name,
            "prediction": name,
            "is_healthy": False,
            "confidence": round(conf, 2),
            "confidence_warning": confidence_warning,
            "severity_percent": sev["severity_percent"],
            "harmfulness": sev["harmfulness"],
            "impact": sev["impact"],
            "message": msg,
            "all_predictions": all_preds,
            "solution": sol or self._solutions.get_default_solution(name),
        })


def _err(error_type: str, message: str, **extra: Any) -> Dict[str, Any]:
    return {"status": "error", "error_type": error_type, "message": message, **extra}


class DiseaseDetectionService:
    """
    Auto-selects two-stage Indian agriculture pipeline when trained models exist,
    otherwise falls back to legacy single CNN.
    """

    def __init__(self) -> None:
        self._version = 5
        self._delegate = None
        if TwoStageDetectionService.is_available():
            logger.info("Using two-stage Indian agriculture detection pipeline")
            self._delegate = TwoStageDetectionService()
        else:
            logger.info("Two-stage models not found — using legacy disease model")
            self._delegate = _LegacyDiseaseDetectionService()

    def predict_from_base64(self, base64_image: str) -> Dict[str, Any]:
        return self._delegate.predict_from_base64(base64_image)

    @property
    def pipeline_mode(self) -> str:
        return "two_stage" if TwoStageDetectionService.is_available() else "legacy"
