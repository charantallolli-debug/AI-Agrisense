"""
Optional LLM integration for personalized treatment advice (OpenAI-compatible API).
Falls back to rule-based text when no API key is configured.
"""
from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional

from config import INTEGRATION_CONFIG

logger = logging.getLogger(__name__)


class LLMService:
    """Thin wrapper around OpenAI-compatible chat completions."""

    def __init__(self) -> None:
        self.api_key = INTEGRATION_CONFIG.get("openai_api_key", "")
        self.base_url = INTEGRATION_CONFIG.get("openai_base_url", "").rstrip("/")
        self.model = INTEGRATION_CONFIG.get("openai_model", "gpt-4o-mini")

    @property
    def is_available(self) -> bool:
        return bool(self.api_key)

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.4,
        max_tokens: int = 900,
    ) -> Dict[str, Any]:
        if not self.is_available:
            return {
                "status": "unavailable",
                "message": "LLM not configured. Set OPENAI_API_KEY in your environment.",
                "content": None,
            }

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        req = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                body = json.loads(resp.read().decode("utf-8"))
            content = body["choices"][0]["message"]["content"].strip()
            return {"status": "success", "content": content, "model": self.model}
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            logger.warning("LLM HTTP error %s: %s", exc.code, detail[:200])
            return {
                "status": "error",
                "message": f"LLM request failed ({exc.code})",
                "content": None,
            }
        except Exception as exc:
            logger.exception("LLM request failed")
            return {"status": "error", "message": str(exc), "content": None}

    def generate_treatment(
        self,
        crop: str,
        disease: str,
        confidence: float,
        solution: Optional[Dict[str, Any]] = None,
        weather: Optional[Dict[str, Any]] = None,
        language: str = "en",
    ) -> Dict[str, Any]:
        """Personalized treatment plan — LLM when available, else structured fallback."""
        solution = solution or {}
        if not self.is_available:
            return {
                "status": "fallback",
                "source": "database",
                "content": _fallback_treatment(crop, disease, solution, weather),
            }

        weather_note = ""
        if weather and weather.get("description"):
            weather_note = (
                f"\nCurrent local weather: {weather.get('temp_c')}°C, "
                f"{weather.get('humidity')}% humidity, {weather.get('description')}."
            )

        system = (
            "You are AgriSense, an expert agricultural advisor for Indian farmers. "
            "Give practical, low-cost treatment advice using locally available inputs when possible. "
            "Structure: Immediate actions, Organic option, Chemical option (if needed), Prevention, "
            "When to consult an extension officer. Keep language simple. "
            f"Respond in {'Hindi' if language == 'hi' else 'English'}."
        )
        user = (
            f"Crop: {crop}\nDisease: {disease}\nModel confidence: {confidence}%\n"
            f"Known database info: {json.dumps(solution, ensure_ascii=False)[:1200]}"
            f"{weather_note}\n\nProvide a farmer-friendly treatment plan."
        )
        result = self.chat_completion(
            [{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=0.35,
            max_tokens=800,
        )
        if result.get("status") == "success":
            return {"status": "success", "source": "llm", "content": result["content"], "model": self.model}
        return {
            "status": "fallback",
            "source": "database",
            "content": _fallback_treatment(crop, disease, solution, weather),
            "llm_error": result.get("message"),
        }


def _fallback_treatment(
    crop: str,
    disease: str,
    solution: Dict[str, Any],
    weather: Optional[Dict[str, Any]],
) -> str:
    """Rule-based treatment text from the JSON disease database."""
    parts = [f"Treatment plan for {crop} — {disease}:\n"]
    if solution.get("cause"):
        parts.append(f"Cause: {solution['cause']}\n")
    for key, title in (
        ("recommended_actions", "Immediate actions"),
        ("organic_solutions", "Organic options"),
        ("pesticides", "Chemical control"),
        ("fertilizers", "Fertilizer support"),
        ("prevention", "Prevention"),
    ):
        items = solution.get(key)
        if not items:
            continue
        if isinstance(items, str):
            parts.append(f"{title}: {items}")
        else:
            parts.append(f"{title}:")
            parts.extend(f"  • {item}" for item in items[:5])
    if weather and weather.get("farming_tip"):
        parts.append(f"\nWeather tip: {weather['farming_tip']}")
    parts.append(
        "\nTip: Set OPENAI_API_KEY for AI-personalized advice tailored to your field conditions."
    )
    return "\n".join(parts)
