"""
HTTP routes for crop disease detection (web UI + /predict API).
"""
from __future__ import annotations

import logging

from flask import Blueprint, jsonify, render_template, request

from app.services.disease_detection import DiseaseDetectionService

logger = logging.getLogger(__name__)

disease_bp = Blueprint("disease", __name__)

# Lazy singleton — avoids loading TensorFlow at import time
_service: DiseaseDetectionService | None = None
_SERVICE_VERSION = 5  # bump when inference logic changes (forces reload)


def get_disease_service() -> DiseaseDetectionService:
    global _service
    if _service is None or getattr(_service, "_version", 0) < _SERVICE_VERSION:
        from app.utils.model_loader import ModelLoader

        ModelLoader.clear_cache()
        _service = DiseaseDetectionService()
        _service._version = _SERVICE_VERSION
    return _service


@disease_bp.route("/", methods=["GET"])
def index():
    """Main page: camera capture and disease detection UI."""
    return render_template("index.html")


@disease_bp.route("/api/pipeline", methods=["GET"])
def pipeline_info():
    """Return active ML pipeline (two_stage vs legacy) and supported Indian crops."""
    from app.services.disease_detection import DiseaseDetectionService
    from app.utils.indian_crops import get_indian_crops

    svc = DiseaseDetectionService()
    from app.utils.crop_registry import get_model_crop_names

    return jsonify({
        "pipeline": svc.pipeline_mode,
        "supported_crops": list(get_model_crop_names()),
        "confidence_threshold": 70.0,
        "service_version": _SERVICE_VERSION,
    }), 200


@disease_bp.route("/predict", methods=["POST"])
def predict():
    """
    POST JSON: {"image": "data:image/png;base64,..."}
    Returns prediction, confidence, and per-class scores.
    """
    try:
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 400

        data = request.get_json() or {}
        if "image" not in data:
            return jsonify({"error": "Missing image field"}), 400

        result = get_disease_service().predict_from_base64(data["image"])
        status_code = 200 if result.get("status") == "success" else 422
        return jsonify(result), status_code

    except ValueError as exc:
        logger.warning("Validation error: %s", exc)
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        logger.exception("Prediction failed")
        return jsonify({"error": "Prediction failed", "details": str(exc)}), 500
