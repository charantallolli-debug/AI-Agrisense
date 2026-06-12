"""Verify model_crop_solutions covers all deployed classes."""
import json
from pathlib import Path

from app.utils.class_parser import normalize_disease_key
from app.utils.crop_registry import parse_label_with_model_crops
from config import MODEL_PATHS

_SOLUTIONS = Path(__file__).resolve().parent.parent / "app" / "data" / "model_crop_solutions.json"


def test_model_crop_solutions_covers_all_classes():
    with open(MODEL_PATHS["class_labels"], encoding="utf-8") as f:
        meta = json.load(f)
    with open(_SOLUTIONS, encoding="utf-8") as f:
        solutions = json.load(f)

    classes = meta.get("classes", [])
    folder_classes = meta.get("folder_classes", classes)
    missing = []
    for friendly, folder in zip(classes, folder_classes):
        crop, disease, is_healthy = parse_label_with_model_crops(folder or friendly)
        key = normalize_disease_key(crop, disease if not is_healthy else "healthy")
        if key not in solutions:
            missing.append(key)
    assert len(solutions) >= len(classes)
    assert not missing, f"Missing solution keys: {missing[:5]}"
