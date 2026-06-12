"""
Crops and labels from the deployed model (class_labels.json).
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import List, Set, Tuple

from config import MODEL_PATHS


@lru_cache(maxsize=1)
def load_model_labels() -> dict:
    path = MODEL_PATHS.get("class_labels")
    if path and path.is_file():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {}


@lru_cache(maxsize=1)
def get_model_crop_names() -> Tuple[str, ...]:
    """Unique crop names extracted from folder_classes (e.g. Wheat, Bottle_gourd)."""
    meta = load_model_labels()
    crops: Set[str] = set()
    for folder in meta.get("folder_classes", meta.get("classes", [])):
        if "___" in folder:
            crop = folder.split("___", 1)[0]
        elif "__" in folder:
            crop = folder.split("__", 1)[0]
        else:
            crop = folder.split("_")[0]
        crops.add(_friendly_crop(crop))
    return tuple(sorted(crops, key=len, reverse=True))


def _friendly_crop(raw: str) -> str:
    return " ".join(part.capitalize() for part in raw.replace("_", " ").split())


def is_model_crop(crop: str) -> bool:
    """True if crop is in the trained model vocabulary."""
    key = crop.lower().strip()
    aliases = _crop_aliases()
    key = aliases.get(key, key)
    model_crops = {c.lower() for c in get_model_crop_names()}
    model_crops.update(aliases.values())
    return key in model_crops


def _crop_aliases() -> dict:
    return {
        "corn": "corn",
        "maize": "corn",
        "chili": "chili",
        "chilli": "chili",
        "capsicum": "capsicum",
        "bell pepper": "capsicum",
    }


def parse_label_with_model_crops(label: str) -> Tuple[str, str, bool]:
    """
    Parse class label using known model crop names (handles Bottle Gourd, etc.).
    """
    from app.utils.class_parser import _is_healthy_label, _title_words

    raw = (label or "").strip()
    if not raw:
        return "Unknown", "Unknown", False

    if "___" in raw:
        crop_part, disease_part = raw.split("___", 1)
        crop = _friendly_crop(crop_part)
        disease = _title_words(disease_part.replace("_", " "))
        healthy = _is_healthy_label(disease)
        return crop, disease, healthy

    # Dataset folders like Chili__leaf spot or Tomato___healthy
    if "__" in raw:
        crop_part, disease_part = raw.split("__", 1)
        crop = _friendly_crop(crop_part)
        disease = _title_words(disease_part.replace("_", " "))
        healthy = _is_healthy_label(disease)
        return crop, disease, healthy

    raw_norm = " ".join(raw.split())
    lower = raw_norm.lower()

    for crop in get_model_crop_names():
        if lower.startswith(crop.lower()):
            rest = raw_norm[len(crop) :].strip()
            if rest:
                disease = _title_words(rest)
                return crop, disease, _is_healthy_label(disease)

    tokens = raw_norm.split()
    if len(tokens) >= 2:
        crop = _title_words(tokens[0])
        disease = _title_words(" ".join(tokens[1:]))
        return crop, disease, _is_healthy_label(disease)

    return _title_words(raw_norm), "Unknown", False
