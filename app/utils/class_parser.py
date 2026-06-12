"""
Parse model class labels into crop and disease names.

Supports PlantVillage folder format (Crop___Disease_name) and friendly labels.
"""
from __future__ import annotations

import re
from typing import Tuple


def parse_class_label(label: str) -> Tuple[str, str, bool]:
    """
    Parse a model class label into (crop, disease, is_healthy).

    Examples:
        Tomato___Late_blight -> (Tomato, Late Blight, False)
        Tomato Early Blight -> (Tomato, Early Blight, False)
        Tomato Healthy -> (Tomato, Healthy, True)
        Potato___healthy -> (Potato, Healthy, True)
    """
    raw = (label or "").strip()
    if not raw:
        return "Unknown", "Unknown", False

    if "___" in raw:
        crop_part, disease_part = raw.split("___", 1)
        crop = _title_words(crop_part.replace("_", " "))
        disease = _title_words(disease_part.replace("_", " "))
    else:
        tokens = raw.split()
        if len(tokens) < 2:
            return _title_words(raw), "Unknown", False
        crop = tokens[0]
        disease = " ".join(tokens[1:])

    crop = _normalize_crop(crop)
    disease = _title_words(disease)
    is_healthy = _is_healthy_label(disease)
    return crop, disease, is_healthy


def normalize_disease_key(crop: str, disease: str) -> str:
    """Build a lookup key for the disease solutions database."""
    crop_slug = re.sub(r"[^a-z0-9]+", "_", crop.lower()).strip("_")
    disease_slug = re.sub(r"[^a-z0-9]+", "_", disease.lower()).strip("_")
    if disease_slug in ("healthy", "no_disease"):
        return f"{crop_slug}_healthy"
    return f"{crop_slug}_{disease_slug}"


def _is_healthy_label(disease: str) -> bool:
    d = disease.lower().strip().replace("_", " ")
    healthy = ("healthy", "no disease", "no_disease", "normal", "none", "fresh", "fresh leaf")
    return d in healthy or d.endswith(" healthy")


def _normalize_crop(crop: str) -> str:
    aliases = {
        "maize": "Maize",
        "corn": "Maize",
        "bell_pepper": "Chilli",
        "bell pepper": "Chilli",
        "capsicum": "Chilli",
        "chili": "Chilli",
        "bottle gourd": "Bottle Gourd",
    }
    key = crop.lower().replace("_", " ").strip()
    return aliases.get(key, _title_words(crop))


def _title_words(text: str) -> str:
    return " ".join(word.capitalize() for word in text.split())
