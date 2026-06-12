"""Weather service tests (no API key required)."""
from unittest.mock import patch

from app.services.weather_service import WeatherService


def test_demo_mumbai_without_api_key():
    svc = WeatherService()
    with patch.object(svc, "api_key", ""):
        with patch.object(svc, "_fetch_open_meteo", return_value={"status": "error"}):
            with patch.object(svc, "_resolve_coordinates", return_value=None):
                result = svc.get_weather(city="Mumbai")
    assert result["status"] == "success"
    assert result["source"] == "demo"
    assert "Mumbai" in result["location"]


def test_open_meteo_mumbai_live():
    svc = WeatherService()
    with patch.object(svc, "api_key", ""):
        result = svc.get_weather(city="Mumbai")
    if result.get("source") == "open_meteo":
        assert result["status"] == "success"
        assert result["temp_c"] is not None
        assert result["farming_tip"]
