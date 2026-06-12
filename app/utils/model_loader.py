"""
Model loading utilities with in-memory caching and optimized TensorFlow loading.

Models are loaded once per process and reused for all predictions.
TensorFlow is imported lazily so CLI tools that only need scikit-learn start faster.
"""
from __future__ import annotations

import logging
import os
import threading
from pathlib import Path
from typing import Any, Dict, Optional

import joblib

logger = logging.getLogger(__name__)

# Thread-safe cache: key -> loaded artifact
_cache: Dict[str, Any] = {}
_cache_lock = threading.Lock()


class ModelLoader:
    """Load and cache ML models used by prediction services."""

    @staticmethod
    def _get_cached(key: str) -> Optional[Any]:
        with _cache_lock:
            return _cache.get(key)

    @staticmethod
    def _set_cached(key: str, value: Any) -> None:
        with _cache_lock:
            _cache[key] = value

    @staticmethod
    def _require_file(path: str | Path, label: str) -> Path:
        resolved = Path(path)
        if not resolved.is_file():
            raise FileNotFoundError(f"{label} not found: {resolved}")
        return resolved

    @staticmethod
    def _load_keras_model(model_path: str | Path, cache_key: str, label: str) -> Any:
        cached = ModelLoader._get_cached(cache_key)
        if cached is not None:
            return cached
        resolved = ModelLoader._require_file(model_path, label)
        logger.info("Loading %s from %s", label, resolved)
        from tensorflow.keras.models import load_model
        try:
            model = load_model(str(resolved), compile=False)
        except TypeError:
            model = load_model(str(resolved), compile=False, safe_mode=False)
        ModelLoader._set_cached(cache_key, model)
        return model

    @staticmethod
    def load_crop_classifier(model_path: str | Path) -> Any:
        """Stage-1 Indian crop classifier."""
        return ModelLoader._load_keras_model(model_path, "crop_classifier", "Crop classifier")

    @staticmethod
    def load_disease_classifier(model_path: str | Path) -> Any:
        """Stage-2 crop-conditioned disease classifier."""
        return ModelLoader._load_keras_model(
            model_path, "disease_classifier", "Disease classifier"
        )

    @staticmethod
    def load_disease_detection_model(model_path: str | Path) -> Any:
        """
        Load the Keras disease-detection CNN.

        Uses compile=False for faster loads and Keras 3 compatibility.
        TensorFlow is imported only when this method is first called.
        """
        model = ModelLoader._load_keras_model(
            model_path, "disease_model", "Disease detection model (legacy)"
        )
        logger.info("Legacy disease model ready (output units: %s)", model.output_shape)
        return model

    @staticmethod
    def load_crop_recommendation_model(model_path: str | Path) -> Any:
        """Load the scikit-learn crop recommendation pipeline (.pkl)."""
        cache_key = "crop_model"
        cached = ModelLoader._get_cached(cache_key)
        if cached is not None:
            logger.debug("Crop recommendation model loaded from cache")
            return cached

        resolved = ModelLoader._require_file(model_path, "Crop recommendation model")
        logger.info("Loading crop recommendation model from %s", resolved)
        model = joblib.load(resolved)

        ModelLoader._set_cached(cache_key, model)
        logger.info("Crop recommendation model ready")
        return model

    @staticmethod
    def load_crop_options(options_path: str | Path) -> list:
        """Load the list of supported crop labels."""
        cache_key = "crop_options"
        cached = ModelLoader._get_cached(cache_key)
        if cached is not None:
            return cached

        resolved = ModelLoader._require_file(options_path, "Crop options file")
        logger.info("Loading crop options from %s", resolved)
        options = joblib.load(resolved)

        ModelLoader._set_cached(cache_key, options)
        logger.info("Loaded %d crop options", len(options))
        return options

    @staticmethod
    def clear_cache() -> None:
        """Clear all cached models (useful in tests)."""
        with _cache_lock:
            _cache.clear()
        logger.info("Model cache cleared")
