"""
Application configuration: Flask settings, model paths, and ML parameters.

Environment:
    FLASK_ENV=development|production|testing  (default: development)
    SECRET_KEY=<string>                       (required in production)
"""
import os
from pathlib import Path

# Project root (directory containing this file)
BASE_DIR = Path(__file__).parent.resolve()


# ---------------------------------------------------------------------------
# Flask configuration classes
# ---------------------------------------------------------------------------
class Config:
    """Base Flask configuration."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
    DEBUG = False
    TESTING = False


class DevelopmentConfig(Config):
    """Local development."""

    DEBUG = True


class ProductionConfig(Config):
    """Production deployment."""

    DEBUG = False
    SECRET_KEY = os.environ.get("SECRET_KEY")  # Must be set in production


class TestingConfig(Config):
    """Automated tests."""

    TESTING = True
    DEBUG = True


CONFIG_MAP = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}


def get_config(name: str = None) -> Config:
    """Return the config class for the given environment name."""
    env = name or os.environ.get("FLASK_ENV", "development")
    return CONFIG_MAP.get(env, DevelopmentConfig)


# ---------------------------------------------------------------------------
# Artifact paths (trained models and datasets)
# ---------------------------------------------------------------------------
MODEL_PATHS = {
    # Legacy single-stage model (fallback)
    "disease_detection": BASE_DIR / "trained_models" / "crop_disease_model.h5",
    "class_labels": BASE_DIR / "trained_models" / "class_labels.json",
    # Two-stage Indian agriculture pipeline (preferred when present)
    "crop_classifier": BASE_DIR / "trained_models" / "crop_classifier.h5",
    "crop_classifier_labels": BASE_DIR / "trained_models" / "crop_classifier_labels.json",
    "disease_classifier": BASE_DIR / "trained_models" / "disease_classifier.h5",
    "disease_classifier_labels": BASE_DIR / "trained_models" / "disease_classifier_labels.json",
    "crop_recommendation": BASE_DIR / "trained_models" / "npk_rf_pipeline.pkl",
    "crop_options": BASE_DIR / "trained_models" / "crop_options.pkl",
}

DATA_PATHS = {
    "crop_dataset": BASE_DIR / "datasets" / "Crop_recommendationV2.csv",
    "plant_village": BASE_DIR / "datasets" / "PlantVillage",
    # Primary user dataset (PlantVillage-style class folders)
    "crop_disease_dataset": BASE_DIR / "datasets" / "sources" / "dataset",
    "dataset_sources": BASE_DIR / "datasets" / "sources",
    "indian_agriculture": BASE_DIR / "datasets" / "indian_agriculture",
}

# ---------------------------------------------------------------------------
# ML / inference settings
# ---------------------------------------------------------------------------
MODEL_CONFIG = {
    # Default input size (overridden by label JSON when two-stage models are loaded)
    "image_size": (224, 224),
    "batch_size": 32,
    "confidence_threshold": 70.0,
    "min_prediction_threshold": 35.0,
    "crop_confidence_threshold": 70.0,
    "pipeline_mode": "auto",  # auto | two_stage | legacy
    "architecture": "efficientnetb0",
    # Legacy fallback labels (128x128 custom CNN)
    "legacy_image_size": (128, 128),
    "disease_classes": [
        "Tomato Early Blight",
        "Tomato Healthy",
        "Tomato Late Blight",
    ],
}

# Feature column order for the crop recommendation Random Forest
CROP_FEATURE_COLUMNS = ["N", "P", "K", "temperature", "humidity", "ph", "rainfall"]

# ---------------------------------------------------------------------------
# External integrations (optional — set via environment / .env)
# ---------------------------------------------------------------------------
INTEGRATION_CONFIG = {
    "openai_api_key": os.environ.get("OPENAI_API_KEY", ""),
    "openai_base_url": os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
    "openai_model": os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
    "openweather_api_key": os.environ.get("OPENWEATHER_API_KEY", ""),
    "enable_tta": os.environ.get("ENABLE_TTA", "true").lower() in ("1", "true", "yes"),
    "chat_max_history": int(os.environ.get("CHAT_MAX_HISTORY", "12")),
}
