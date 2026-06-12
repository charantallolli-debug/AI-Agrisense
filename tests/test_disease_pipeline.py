"""Tests for disease detection pipeline helpers (no TensorFlow required)."""
import json
from pathlib import Path

import numpy as np
import pytest

from app.services.disease_solutions import DiseaseSolutionsService
from app.utils.class_parser import normalize_disease_key, parse_class_label
from app.utils.leaf_detection import detect_leaf, validate_image_quality
from app.utils.severity import build_severity_info


def _green_leaf_array(width=200, height=200):
    """Synthetic green leaf-like image for OpenCV tests."""
    arr = np.zeros((height, width, 3), dtype=np.uint8)
    arr[:, :] = [30, 30, 30]
    cy, cx = height // 2, width // 2
    y, x = np.ogrid[:height, :width]
    mask = ((x - cx) ** 2 + (y - cy) ** 2) < (min(width, height) // 3) ** 2
    arr[mask] = [40, 180, 60]
    return arr


def test_parse_plant_village_label():
    crop, disease, healthy = parse_class_label("Tomato___Late_blight")
    assert crop == "Tomato"
    assert disease == "Late Blight"
    assert healthy is False


def test_parse_friendly_label():
    crop, disease, healthy = parse_class_label("Tomato Healthy")
    assert crop == "Tomato"
    assert healthy is True


def test_normalize_disease_key():
    assert normalize_disease_key("Tomato", "Late Blight") == "tomato_late_blight"


def test_supported_crop():
    assert DiseaseSolutionsService.is_crop_supported("Tomato")
    assert not DiseaseSolutionsService.is_crop_supported("UnknownCropXYZ")


def test_tomato_late_blight_solution():
    sol = DiseaseSolutionsService.lookup("Tomato", "Late Blight", False)
    assert sol is not None
    assert "fungicide" in " ".join(sol.get("recommended_actions", [])).lower()


def test_severity_healthy():
    info = build_severity_info(True, None, 95.0)
    assert info["severity_percent"] == 0
    assert info["harmfulness"] == "Low"


def test_severity_from_metadata():
    meta = {"severity_percent": 85, "harmfulness": "High", "impact": "Test impact"}
    info = build_severity_info(False, meta, 90.0)
    assert info["severity_percent"] == 85
    assert info["harmfulness"] == "High"


def test_validate_image_quality_rejects_tiny():
    tiny = np.zeros((10, 10, 3), dtype=np.uint8)
    valid, _ = validate_image_quality(tiny)
    assert valid is False


def test_detect_leaf_on_synthetic_green():
    arr = _green_leaf_array()
    has_leaf, _ = detect_leaf(arr)
    assert has_leaf is True


def test_class_labels_file_exists():
    path = Path(__file__).resolve().parent.parent / "trained_models" / "class_labels.json"
    assert path.is_file()
    data = json.loads(path.read_text())
    assert "classes" in data
    assert len(data["classes"]) >= 3
