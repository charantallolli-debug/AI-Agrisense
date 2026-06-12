"""
HTTP routes for crop recommendation REST API.
"""
from __future__ import annotations

import logging

from flask import Blueprint, jsonify, request

from app.services.crop_recommendation import CropRecommendationService

logger = logging.getLogger(__name__)

recommendation_bp = Blueprint("recommendation", __name__, url_prefix="/api/recommendation")

_service: CropRecommendationService | None = None


def get_recommendation_service() -> CropRecommendationService:
    global _service
    if _service is None:
        _service = CropRecommendationService()
    return _service


@recommendation_bp.route("/available-crops", methods=["GET"])
def available_crops():
    """List all crops supported by the recommendation model."""
    try:
        crops = get_recommendation_service().get_available_crops()
        return jsonify({"crops": crops, "count": len(crops)}), 200
    except Exception as exc:
        logger.exception("Failed to fetch crops")
        return jsonify({"error": "Failed to fetch crops", "details": str(exc)}), 500


@recommendation_bp.route("/predict-npk", methods=["POST"])
def predict_npk():
    """
    POST JSON: crop, temperature, humidity, ph, rainfall
    Returns typical N/P/K for that crop from the reference dataset.
    """
    try:
        data = request.get_json() or {}
        required = ["crop", "temperature", "humidity", "ph", "rainfall"]
        missing = [f for f in required if f not in data]
        if missing:
            return jsonify({"error": f"Missing fields: {missing}"}), 400

        features = {
            "temperature": float(data["temperature"]),
            "humidity": float(data["humidity"]),
            "ph": float(data["ph"]),
            "rainfall": float(data["rainfall"]),
        }
        result = get_recommendation_service().predict_npk(data["crop"], features)
        return jsonify(result), 200

    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        logger.exception("NPK lookup failed")
        return jsonify({"error": "NPK prediction failed", "details": str(exc)}), 500


@recommendation_bp.route("/recommend-crop", methods=["POST"])
def recommend_crop():
    """
    POST JSON: temperature, humidity, ph, rainfall (+ optional N, P, K)
    Returns the Random Forest crop recommendation.
    """
    try:
        data = request.get_json() or {}
        required = ["temperature", "humidity", "ph", "rainfall"]
        missing = [f for f in required if f not in data]
        if missing:
            return jsonify({"error": f"Missing fields: {missing}"}), 400

        result = get_recommendation_service().recommend_crop(
            temperature=float(data["temperature"]),
            humidity=float(data["humidity"]),
            ph=float(data["ph"]),
            rainfall=float(data["rainfall"]),
            n=float(data["N"]) if "N" in data else None,
            p=float(data["P"]) if "P" in data else None,
            k=float(data["K"]) if "K" in data else None,
        )
        return jsonify(result), 200

    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        logger.exception("Crop recommendation failed")
        return jsonify({"error": "Crop recommendation failed", "details": str(exc)}), 500
