"""Tests for assistant services (no TensorFlow / API keys required)."""
from app.services.chatbot_service import ChatbotService
from app.services.prediction_explainer import build_explanation, top_predictions
from app.services.weather_service import _farming_tip


def test_top_predictions():
    preds = {"Tomato Late Blight": 85.0, "Tomato Healthy": 10.0, "Potato Early Blight": 5.0}
    top = top_predictions(preds, k=2)
    assert len(top) == 2
    assert top[0]["label"] == "Tomato Late Blight"
    assert top[0]["confidence"] == 85.0


def test_build_explanation_healthy():
    exp = build_explanation(
        crop="Tomato",
        disease="Healthy",
        confidence=92.5,
        is_healthy=True,
        all_predictions={"Tomato Healthy": 92.5, "Tomato Late Blight": 3.0},
    )
    assert "healthy" in exp["summary"].lower()
    assert len(exp["top_predictions"]) >= 1
    assert len(exp["reasoning"]) >= 3


def test_build_explanation_diseased():
    exp = build_explanation(
        crop="Wheat",
        disease="Brown Rust",
        confidence=88.0,
        is_healthy=False,
        all_predictions={"Wheat Brown Rust": 88.0, "Wheat Healthy": 8.0},
        confidence_warning=False,
    )
    assert "Brown Rust" in exp["summary"]
    assert exp["confidence_gap"] == 80.0


def test_chatbot_rule_based_greeting():
    svc = ChatbotService()
    result = svc.chat("Hello")
    assert result["status"] == "success"
    assert result["source"] == "rules"
    assert "AgriSense" in result["reply"] or "Namaste" in result["reply"]


def test_chatbot_with_detection_context():
    svc = ChatbotService()
    result = svc.chat(
        "What treatment should I use?",
        context={"crop": "Tomato", "disease": "Late Blight", "confidence": 90},
    )
    assert result["status"] == "success"
    assert "Tomato" in result["reply"]


def test_farming_tip_high_humidity():
    tip = _farming_tip(temp=28, humidity=90, rain_mm=0, description="Cloudy")
    assert "humidity" in tip.lower() or "fungal" in tip.lower()
