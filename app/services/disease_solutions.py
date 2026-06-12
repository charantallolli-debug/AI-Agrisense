"""
Disease solution database — causes, treatments, and prevention.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.utils.class_parser import normalize_disease_key

logger = logging.getLogger(__name__)

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_SOLUTIONS_PATH = _DATA_DIR / "disease_solutions.json"
_INDIAN_SOLUTIONS_PATH = _DATA_DIR / "indian_disease_solutions.json"
_MODEL_SOLUTIONS_PATH = _DATA_DIR / "model_crop_solutions.json"
_CROPS_PATH = _DATA_DIR / "supported_crops.json"


class DiseaseSolutionsService:
    """Load and query agronomic advice for predicted diseases."""

    _solutions: Dict[str, Any] | None = None
    _supported_crops: List[str] | None = None

    @classmethod
    def _load_solutions(cls) -> Dict[str, Any]:
        if cls._solutions is None:
            with open(_SOLUTIONS_PATH, encoding="utf-8") as f:
                merged = json.load(f)
            if _INDIAN_SOLUTIONS_PATH.is_file():
                with open(_INDIAN_SOLUTIONS_PATH, encoding="utf-8") as f:
                    merged.update(json.load(f))
            if _MODEL_SOLUTIONS_PATH.is_file():
                with open(_MODEL_SOLUTIONS_PATH, encoding="utf-8") as f:
                    merged.update(json.load(f))
            cls._solutions = merged
            logger.info("Loaded %d disease solution entries", len(cls._solutions))
        return cls._solutions

    @classmethod
    def _load_supported_crops(cls) -> List[str]:
        if cls._supported_crops is None:
            with open(_CROPS_PATH, encoding="utf-8") as f:
                cls._supported_crops = json.load(f)
        return cls._supported_crops

    @classmethod
    def is_crop_supported(cls, crop: str) -> bool:
        """All crops from the trained model are valid for prediction."""
        supported = cls._load_supported_crops()
        return any(c.lower() == crop.lower() for c in supported)

    @classmethod
    def lookup(cls, crop: str, disease: str, is_healthy: bool) -> Optional[Dict[str, Any]]:
        key = normalize_disease_key(crop, disease if not is_healthy else "healthy")
        solutions = cls._load_solutions()
        entry = solutions.get(key)
        if entry:
            return cls._format_solution(entry, crop, disease, is_healthy)

        # Fuzzy: match by crop + partial disease name
        crop_lower = crop.lower()
        disease_lower = disease.lower()
        for db_key, db_val in solutions.items():
            if not db_key.startswith(crop_lower):
                continue
            if is_healthy and "healthy" in db_key:
                return cls._format_solution(db_val, crop, disease, True)
            if disease_lower.replace(" ", "_") in db_key.replace(" ", "_"):
                return cls._format_solution(db_val, crop, disease, is_healthy)
        return None

    @classmethod
    def get_disease_metadata(cls, crop: str, disease: str, is_healthy: bool) -> Optional[Dict[str, Any]]:
        """Return raw DB entry for severity fields."""
        key = normalize_disease_key(crop, disease if not is_healthy else "healthy")
        return cls._load_solutions().get(key)

    @classmethod
    def get_default_solution(cls, disease_full: str) -> Dict[str, Any]:
        entry = dict(cls._load_solutions().get("default_disease", {}))
        entry["disease_name"] = disease_full
        return cls._format_solution(entry, "", disease_full, False)

    @staticmethod
    def _format_solution(
        entry: Dict[str, Any],
        crop: str,
        disease: str,
        is_healthy: bool,
    ) -> Dict[str, Any]:
        name = entry.get("disease_name") or f"{crop} {disease}"
        return {
            "disease_name": name,
            "cause": entry.get("cause", ""),
            "symptoms": entry.get("symptoms", []),
            "fertilizers": entry.get("fertilizers", []),
            "pesticides": entry.get("pesticides", []),
            "organic_solutions": entry.get("organic_solutions", []),
            "prevention": entry.get("prevention", []),
            "recommended_actions": entry.get("recommended_actions", []),
        }
