"""
Farmer chatbot — answers agriculture questions with optional LLM backend.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.services.llm_service import LLMService
from app.utils.crop_registry import get_model_crop_names
from config import INTEGRATION_CONFIG


class ChatbotService:
    """Context-aware farming assistant."""

    SYSTEM_PROMPT = (
        "You are AgriSense Farmer Assistant for Indian agriculture. "
        "Help smallholder farmers with crop diseases, soil, irrigation, weather-aware advice, "
        "and low-cost organic options. Be concise, practical, and safe — recommend consulting "
        "local Krishi Vigyan Kendra (KVK) for severe outbreaks. "
        "If unsure, say so. Use bullet points for action steps."
    )

    def __init__(self) -> None:
        self.llm = LLMService()
        self.max_history = int(INTEGRATION_CONFIG.get("chat_max_history", 12))

    def chat(
        self,
        message: str,
        history: Optional[List[Dict[str, str]]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        message = (message or "").strip()
        if not message:
            return {"status": "error", "message": "Empty message."}

        history = list(history or [])
        context = context or {}

        if self.llm.is_available:
            return self._llm_chat(message, history, context)
        return self._rule_based_chat(message, context)

    def _llm_chat(
        self,
        message: str,
        history: List[Dict[str, str]],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        ctx_block = _format_context(context)
        messages: List[Dict[str, str]] = [
            {"role": "system", "content": self.SYSTEM_PROMPT + ctx_block},
        ]
        for turn in history[-self.max_history :]:
            role = turn.get("role", "user")
            content = turn.get("content", "")
            if role in ("user", "assistant") and content:
                messages.append({"role": role, "content": content})
        messages.append({"role": "user", "content": message})

        result = self.llm.chat_completion(messages, temperature=0.5, max_tokens=700)
        if result.get("status") == "success":
            return {
                "status": "success",
                "reply": result["content"],
                "source": "llm",
            }
        fallback = self._rule_based_chat(message, context)
        fallback["llm_error"] = result.get("message")
        return fallback

    def _rule_based_chat(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Offline fallback when no LLM API key."""
        lower = message.lower()
        crops = ", ".join(get_model_crop_names())

        if any(w in lower for w in ("hello", "hi", "namaste", "help")):
            reply = (
                f"Namaste! I am AgriSense. I can help with disease detection on: {crops}. "
                "Upload a leaf photo in the Detect tab, or ask about irrigation, NPK, or weather."
            )
        elif "weather" in lower or "rain" in lower:
            reply = (
                "Open the Weather tab and allow location access for local conditions. "
                "High humidity increases fungal disease risk — scout leaves after rain."
            )
        elif "npk" in lower or "fertilizer" in lower or "soil" in lower:
            reply = (
                "For crop choice from soil/climate, use POST /api/recommendation/recommend-crop "
                "with N, P, K, temperature, humidity, pH, and rainfall. "
                "Typical NPK varies by crop — e.g. rice needs more N, legumes fix their own N."
            )
        elif "disease" in lower or "treatment" in lower or "pest" in lower:
            crop_ctx = context.get("crop", "")
            disease_ctx = context.get("disease", "")
            if crop_ctx and disease_ctx:
                reply = (
                    f"Your last scan: {crop_ctx} — {disease_ctx}. "
                    "See treatment details in the Detect results, or tap 'Get AI Treatment Plan' "
                    "when OPENAI_API_KEY is configured."
                )
            else:
                reply = (
                    "Upload a clear leaf photo in the Detect tab for AI disease identification. "
                    f"Supported crops: {crops}."
                )
        elif "organic" in lower:
            reply = (
                "Organic options: neem oil spray, Trichoderma for soil fungi, "
                "cow urine + garlic for some leaf spots, crop rotation, and resistant varieties."
            )
        else:
            reply = (
                f"I can help with crop diseases ({crops}), weather tips, and soil advice. "
                "Try: 'How to treat tomato blight?' or use the leaf scanner. "
                "For full AI chat, set OPENAI_API_KEY on the server."
            )

        return {"status": "success", "reply": reply, "source": "rules"}


def _format_context(context: Dict[str, Any]) -> str:
    parts = []
    if context.get("crop"):
        parts.append(f"Last detected crop: {context['crop']}.")
    if context.get("disease"):
        parts.append(f"Last detected disease: {context['disease']}.")
    if context.get("confidence"):
        parts.append(f"Detection confidence: {context['confidence']}%.")
    if context.get("weather"):
        w = context["weather"]
        parts.append(
            f"Local weather: {w.get('temp_c')}°C, {w.get('humidity')}% humidity, {w.get('description')}."
        )
    if not parts:
        return ""
    return "\n\nFarmer session context:\n" + " ".join(parts)
