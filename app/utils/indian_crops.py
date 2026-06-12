"""
Indian agriculture crop registry and label normalization.
"""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Set

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_INDIAN_CROPS_PATH = _DATA_DIR / "indian_crops.json"
_MAPPING_PATH = _DATA_DIR / "source_dataset_mapping.json"


@lru_cache(maxsize=1)
def load_indian_crop_config() -> dict:
    with open(_INDIAN_CROPS_PATH, encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def load_source_mapping() -> dict:
    with open(_MAPPING_PATH, encoding="utf-8") as f:
        return json.load(f)


def get_indian_crops() -> List[str]:
    return list(load_indian_crop_config()["crops"])


def get_invalid_class_name() -> str:
    return load_indian_crop_config().get("invalid_class", "invalid_non_crop")


def get_crop_aliases() -> Dict[str, Optional[str]]:
    return load_indian_crop_config().get("aliases", {})


def normalize_crop_name(name: str) -> Optional[str]:
    """Map arbitrary dataset crop name to canonical crop or None."""
    if not name:
        return None

    raw = name.strip()
    key = raw.lower().replace("-", "_").replace(" ", "_")

    aliases = get_crop_aliases()
    if key in aliases:
        return aliases[key]

    # Deployed model crops take precedence (62-class dataset vocabulary)
    try:
        from app.utils.crop_registry import get_model_crop_names

        norm_key = key.replace("_", " ")
        for mc in get_model_crop_names():
            mc_key = mc.lower().replace(" ", "_")
            if key == mc_key or norm_key == mc.lower():
                return mc
            if key.replace("_", "") == mc.lower().replace(" ", ""):
                return mc
    except Exception:
        pass

    canonical = {c.lower(): c for c in get_indian_crops()}
    if key in canonical:
        return canonical[key]

    # PlantVillage mapping
    pv_map = load_source_mapping().get("plantvillage_crop_map", {})
    if raw in pv_map:
        return pv_map[raw]
    if raw.title() in pv_map:
        return pv_map[raw.title()]

    title = raw.replace("_", " ").title()
    if title.lower() in canonical:
        return canonical[title.lower()]

    return None


def is_healthy_disease_name(disease: str) -> bool:
    keywords = load_source_mapping().get("healthy_keywords", ["healthy"])
    d = disease.lower().replace("_", " ")
    return any(kw in d for kw in keywords)


def parse_disease_folder_name(folder_name: str) -> tuple[Optional[str], str, bool]:
    """
    Parse dataset folder like Tomato___Late_blight, Chili__leaf spot, or Rice_Bacterial_Leaf_Blight.

    Returns (crop, disease_slug, is_healthy).
    """
    if "___" in folder_name:
        crop_raw, disease_raw = folder_name.split("___", 1)
    elif "__" in folder_name:
        crop_raw, disease_raw = folder_name.split("__", 1)
    elif "_" in folder_name:
        parts = folder_name.split("_")
        crop_raw = parts[0]
        disease_raw = "_".join(parts[1:])
    else:
        tokens = folder_name.split()
        crop_raw = tokens[0]
        disease_raw = " ".join(tokens[1:]) if len(tokens) > 1 else "unknown"

    crop = normalize_crop_name(crop_raw.replace("_", " "))
    disease = disease_raw.replace("_", " ").strip()
    healthy = is_healthy_disease_name(disease)
    return crop, disease, healthy


def stage2_class_name(crop: str, disease: str, is_healthy: bool) -> str:
    """Canonical stage-2 folder/label: Crop___Disease_slug."""
    if is_healthy:
        slug = "healthy"
    else:
        slug = re.sub(r"[^a-z0-9]+", "_", disease.lower()).strip("_")
    return f"{crop}___{slug}"


def friendly_label(stage2_name: str) -> str:
    """Human-readable label from stage2 class name."""
    if "___" not in stage2_name:
        return stage2_name.replace("_", " ").title()
    crop, disease = stage2_name.split("___", 1)
    disease_display = disease.replace("_", " ").title()
    if is_healthy_disease_name(disease):
        return f"{crop} Healthy"
    return f"{crop} {disease_display}"


def supported_crop_set() -> Set[str]:
    return set(get_indian_crops())
