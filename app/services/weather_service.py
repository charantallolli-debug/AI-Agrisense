"""
Weather integration for farming context.

Priority:
  1. OpenWeatherMap (if OPENWEATHER_API_KEY is set)
  2. Open-Meteo (free, no API key)
  3. Static demo profiles (offline fallback)
"""
from __future__ import annotations

import json
import logging
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, Optional, Tuple

from config import INTEGRATION_CONFIG

logger = logging.getLogger(__name__)

# WMO weather code → short description
_WMO_DESCRIPTIONS = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    80: "Rain showers",
    95: "Thunderstorm",
}

_DEMO_CITIES: Dict[str, Dict[str, Any]] = {
    "mumbai": {
        "location": "Mumbai",
        "country": "IN",
        "temp_c": 31.0,
        "feels_like_c": 35.0,
        "humidity": 82,
        "rain_mm": 0.0,
        "wind_ms": 4.2,
        "description": "Humid, partly cloudy",
    },
    "delhi": {
        "location": "Delhi",
        "country": "IN",
        "temp_c": 34.0,
        "feels_like_c": 37.0,
        "humidity": 55,
        "rain_mm": 0.0,
        "wind_ms": 3.5,
        "description": "Hot and dry",
    },
    "bangalore": {
        "location": "Bengaluru",
        "country": "IN",
        "temp_c": 26.0,
        "feels_like_c": 27.0,
        "humidity": 70,
        "rain_mm": 2.0,
        "wind_ms": 2.8,
        "description": "Mild with light rain",
    },
}


class WeatherService:
    """Fetch current weather and derive simple farming advisories."""

    OWM_BASE = "https://api.openweathermap.org/data/2.5/weather"
    METEO_FORECAST = "https://api.open-meteo.com/v1/forecast"
    METEO_GEOCODE = "https://geocoding-api.open-meteo.com/v1/search"

    def __init__(self) -> None:
        self.api_key = INTEGRATION_CONFIG.get("openweather_api_key", "")

    @property
    def is_configured(self) -> bool:
        """True when a paid OpenWeather key is set (Open-Meteo works without it)."""
        return bool(self.api_key)

    @property
    def is_available(self) -> bool:
        """Weather can always be served (live via Open-Meteo or demo fallback)."""
        return True

    def get_weather(
        self,
        lat: Optional[float] = None,
        lon: Optional[float] = None,
        city: Optional[str] = None,
    ) -> Dict[str, Any]:
        if lat is None and lon is None and not city:
            return {"status": "error", "message": "Provide lat/lon or city."}

        if self.is_configured:
            result = self._fetch_openweather(lat, lon, city)
            if result.get("status") == "success":
                result["source"] = "openweathermap"
                return result
            logger.warning("OpenWeather failed, falling back to Open-Meteo: %s", result.get("message"))

        coords = self._resolve_coordinates(lat, lon, city)
        if coords:
            lat_r, lon_r, place_name = coords
            result = self._fetch_open_meteo(lat_r, lon_r, place_name)
            if result.get("status") == "success":
                return result

        return self._demo_weather(city, lat, lon)

    def _resolve_coordinates(
        self,
        lat: Optional[float],
        lon: Optional[float],
        city: Optional[str],
    ) -> Optional[Tuple[float, float, str]]:
        if lat is not None and lon is not None:
            return float(lat), float(lon), city or "Your location"

        if not city:
            return None

        params = urllib.parse.urlencode({"name": city, "count": 1, "language": "en", "format": "json"})
        url = f"{self.METEO_GEOCODE}?{params}"
        try:
            with urllib.request.urlopen(url, timeout=12) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            results = data.get("results") or []
            if not results:
                return None
            r = results[0]
            name = r.get("name", city)
            admin = r.get("admin1")
            place = f"{name}, {admin}" if admin else name
            return float(r["latitude"]), float(r["longitude"]), place
        except Exception as exc:
            logger.warning("Geocoding failed for %s: %s", city, exc)
            return None

    def _fetch_open_meteo(self, lat: float, lon: float, place_name: str) -> Dict[str, Any]:
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m,precipitation",
            "timezone": "auto",
        }
        url = f"{self.METEO_FORECAST}?{urllib.parse.urlencode(params)}"
        try:
            with urllib.request.urlopen(url, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception as exc:
            logger.warning("Open-Meteo request failed: %s", exc)
            return {"status": "error", "message": str(exc)}

        current = data.get("current") or {}
        temp = float(current.get("temperature_2m", 25))
        humidity = int(current.get("relative_humidity_2m", 60))
        wind = float(current.get("wind_speed_10m", 0)) / 3.6  # km/h → m/s approx
        rain_mm = float(current.get("precipitation", 0) or 0)
        code = int(current.get("weather_code", 0))
        desc = _WMO_DESCRIPTIONS.get(code, "Current conditions")

        return {
            "status": "success",
            "source": "open_meteo",
            "location": place_name,
            "country": None,
            "temp_c": round(temp, 1),
            "feels_like_c": round(temp, 1),
            "humidity": humidity,
            "rain_mm": round(rain_mm, 1),
            "wind_ms": round(wind, 1),
            "description": desc,
            "farming_tip": _farming_tip(temp, humidity, rain_mm, desc),
        }

    def _fetch_openweather(
        self,
        lat: Optional[float],
        lon: Optional[float],
        city: Optional[str],
    ) -> Dict[str, Any]:
        params: Dict[str, str] = {"appid": self.api_key, "units": "metric"}
        if lat is not None and lon is not None:
            params["lat"] = str(lat)
            params["lon"] = str(lon)
        elif city:
            params["q"] = city
        else:
            return {"status": "error", "message": "Provide lat/lon or city."}

        url = f"{self.OWM_BASE}?{urllib.parse.urlencode(params)}"
        try:
            with urllib.request.urlopen(url, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            logger.warning("OpenWeather API error %s: %s", exc.code, detail[:200])
            return {"status": "error", "message": "Could not fetch weather data."}
        except Exception as exc:
            return {"status": "error", "message": str(exc)}

        temp = data["main"]["temp"]
        humidity = data["main"]["humidity"]
        rain_mm = data.get("rain", {}).get("1h", 0) or data.get("rain", {}).get("3h", 0)
        desc = (data["weather"][0]["description"] or "").title()
        wind = data.get("wind", {}).get("speed", 0)
        location = data.get("name", city or "Your location")

        return {
            "status": "success",
            "location": location,
            "country": data.get("sys", {}).get("country"),
            "temp_c": round(temp, 1),
            "feels_like_c": round(data["main"].get("feels_like", temp), 1),
            "humidity": humidity,
            "rain_mm": round(float(rain_mm), 1),
            "wind_ms": round(float(wind), 1),
            "description": desc,
            "icon": data["weather"][0].get("icon"),
            "farming_tip": _farming_tip(temp, humidity, rain_mm, desc),
        }

    def _demo_weather(
        self,
        city: Optional[str],
        lat: Optional[float],
        lon: Optional[float],
    ) -> Dict[str, Any]:
        key = (city or "mumbai").lower().strip()
        profile = _DEMO_CITIES["mumbai"]
        for alias, candidate in _DEMO_CITIES.items():
            if alias in key or key in alias:
                profile = candidate
                break

        location = profile["location"]
        if lat is not None and lon is not None and not city:
            location = f"Near ({lat:.2f}, {lon:.2f})"

        return {
            "status": "success",
            "source": "demo",
            "location": location,
            "country": profile.get("country"),
            "temp_c": profile["temp_c"],
            "feels_like_c": profile["feels_like_c"],
            "humidity": profile["humidity"],
            "rain_mm": profile["rain_mm"],
            "wind_ms": profile["wind_ms"],
            "description": profile["description"],
            "farming_tip": _farming_tip(
                profile["temp_c"],
                profile["humidity"],
                profile["rain_mm"],
                profile["description"],
            ),
            "demo_notice": "Offline demo data — connect to the internet for live weather.",
        }


def _farming_tip(temp: float, humidity: float, rain_mm: float, description: str) -> str:
    tips = []
    if humidity > 85:
        tips.append("High humidity — avoid evening irrigation; monitor for fungal leaf spots.")
    elif humidity < 35:
        tips.append("Low humidity — irrigate early morning; mulch to retain soil moisture.")
    if rain_mm > 5:
        tips.append("Recent rain — delay pesticide spray until leaves dry.")
    if temp > 38:
        tips.append("Heat stress risk — irrigate lightly in evening; avoid midday field work.")
    elif temp < 12:
        tips.append("Cool conditions — slow fungal spread but watch for dew-related blights.")
    if "rain" in description.lower():
        tips.append("Rainy weather — ensure drainage; scout for bacterial and fungal diseases.")
    if not tips:
        tips.append("Conditions look moderate — good time for scouting and balanced NPK application.")
    return " ".join(tips)
