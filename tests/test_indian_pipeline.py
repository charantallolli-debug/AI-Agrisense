"""Tests for Indian agriculture utilities and pipeline selection."""
import json
from pathlib import Path

import pytest

from app.services.disease_detection import DiseaseDetectionService, MSG_HEALTHY, MSG_INVALID
from app.services.two_stage_detection import TwoStageDetectionService
from app.utils.indian_crops import (
    get_indian_crops,
    normalize_crop_name,
    parse_disease_folder_name,
    stage2_class_name,
)
from config import MODEL_PATHS


def test_indian_crops_count():
    crops = get_indian_crops()
    assert len(crops) >= 24
    assert "Rice" in crops
    assert "Sugarcane" in crops
    assert "Chilli" in crops


def test_normalize_maize_aliases():
    assert normalize_crop_name("Corn") == "Maize"
    assert normalize_crop_name("bell_pepper") == "Chilli"


def test_stage2_class_name():
    assert stage2_class_name("Rice", "Bacterial Leaf Blight", False) == "Rice___bacterial_leaf_blight"
    assert stage2_class_name("Wheat", "", True) == "Wheat___healthy"


def test_parse_plantvillage_folder():
    crop, disease, healthy = parse_disease_folder_name("Tomato___Late_blight")
    assert crop == "Tomato"
    assert healthy is False


def test_pipeline_mode_is_legacy_without_stage_models():
    """Without trained two-stage artifacts, legacy mode is used."""
    if TwoStageDetectionService.is_available():
        pytest.skip("Two-stage models present — legacy fallback not tested")
    svc = DiseaseDetectionService()
    assert svc.pipeline_mode == "legacy"


def test_disease_service_messages_constants():
    assert "Healthy" in MSG_HEALTHY
    assert "valid crop" in MSG_INVALID.lower()


def test_class_labels_json_valid():
    path = MODEL_PATHS["class_labels"]
    assert path.is_file()
    data = json.loads(path.read_text())
    assert "classes" in data
