"""
Assistant routes: farmer chatbot, LLM treatment, weather, crop catalog.
"""
from __future__ import annotations

import logging

from flask import Blueprint, jsonify, request

from app.services.chatbot_service import ChatbotService
from app.services.llm_service import LLMService
from app.services.weather_service import WeatherService
from app.utils.crop_registry import get_model_crop_names, load_model_labels

logger = logging.getLogger(__name__)

assistant_bp = Blueprint("assistant", __name__, url_prefix="/api/assistant")


@assistant_bp.route("/crops", methods=["GET"])
def crop_catalog():
    """Model-trained crops plus roadmap crops for expansion."""
    meta = load_model_labels()
    model_crops = list(get_model_crop_names())
    return jsonify({
        "model_crops": model_crops,
        "model_class_count": len(meta.get("classes", [])),
        "architecture": meta.get("architecture", "unknown"),
        "roadmap_note": (
            "Add new crop folders under datasets/sources/dataset/ and retrain "
            "to expand beyond current model crops."
        ),
    }), 200


@assistant_bp.route("/weather", methods=["GET"])
def weather():
    """GET ?lat=&lon= or ?city=Mumbai"""
    lat = request.args.get("lat", type=float)
    lon = request.args.get("lon", type=float)
    city = request.args.get("city", type=str)
    result = WeatherService().get_weather(lat=lat, lon=lon, city=city)
    code = 200 if result.get("status") == "success" else 400
    return jsonify(result), code


@assistant_bp.route("/chat", methods=["POST"])
def chat():
    """
    POST JSON: {"message": "...", "history": [...], "context": {...}}
    """
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    data = request.get_json() or {}
    message = data.get("message", "")
    history = data.get("history", [])
    context = data.get("context", {})
    result = ChatbotService().chat(message, history=history, context=context)
    return jsonify(result), 200


@assistant_bp.route("/treatment", methods=["POST"])
def llm_treatment():
    """
    POST JSON: {"crop", "disease", "confidence", "solution", "weather"}
    """
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    data = request.get_json() or {}
    crop = data.get("crop", "")
    disease = data.get("disease", "")
    if not crop or not disease:
        return jsonify({"error": "crop and disease are required"}), 400

    result = LLMService().generate_treatment(
        crop=crop,
        disease=disease,
        confidence=float(data.get("confidence", 0)),
        solution=data.get("solution"),
        weather=data.get("weather"),
        language=data.get("language", "en"),
    )
    return jsonify(result), 200


@assistant_bp.route("/status", methods=["GET"])
def integration_status():
    """Which optional integrations are active."""
    from config import INTEGRATION_CONFIG

    llm = LLMService()
    weather = WeatherService()
    return jsonify({
        "llm_available": llm.is_available,
        "llm_model": llm.model if llm.is_available else None,
        "weather_available": weather.is_available,
        "weather_live_provider": "openweathermap" if weather.is_configured else "open_meteo",
        "tta_enabled": bool(INTEGRATION_CONFIG.get("enable_tta", True)),
    }), 200
