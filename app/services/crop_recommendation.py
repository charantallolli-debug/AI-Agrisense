"""
Crop recommendation service.

- recommend_crop: Random Forest predicts the best crop from env + optional NPK.
- predict_npk: Returns typical N/P/K levels for a crop from the reference dataset.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from app.utils.model_loader import ModelLoader
from config import CROP_FEATURE_COLUMNS, DATA_PATHS, MODEL_PATHS

logger = logging.getLogger(__name__)


class CropRecommendationService:
    """Crop recommendation and NPK lookup backed by sklearn + CSV reference data."""

    def __init__(self) -> None:
        self.model = None
        self.crop_options: Optional[List[str]] = None
        self.dataset: Optional[pd.DataFrame] = None
        self._load_models()

    def _load_models(self) -> None:
        """Load ML pipeline, crop list, and optional reference dataset."""
        self.model = ModelLoader.load_crop_recommendation_model(
            MODEL_PATHS["crop_recommendation"]
        )
        self.crop_options = ModelLoader.load_crop_options(MODEL_PATHS["crop_options"])

        dataset_path = DATA_PATHS["crop_dataset"]
        if dataset_path.is_file():
            self.dataset = pd.read_csv(dataset_path)
            logger.info("Reference dataset loaded (%d rows)", len(self.dataset))
        else:
            logger.warning("Crop dataset not found at %s", dataset_path)

        logger.info("CropRecommendationService initialized")

    def get_available_crops(self) -> List[str]:
        """Return sorted list of crops the model supports."""
        return sorted(self.crop_options) if self.crop_options else []

    def predict_npk(self, crop_name: str, features: Dict[str, float]) -> Dict[str, Any]:
        """
        Return typical N, P, K values for a crop (mean from reference dataset).

        Environmental inputs are validated and echoed in the response; NPK values
        come from historical data for the selected crop, not from the classifier.
        """
        self._validate_crop_name(crop_name)
        self._validate_environment(features)

        npk = self._get_mean_npk_for_crop(crop_name)
        result = {
            "crop": crop_name,
            "N": npk["N"],
            "P": npk["P"],
            "K": npk["K"],
            "features_used": features,
        }
        logger.info("NPK lookup for %s: N=%s P=%s K=%s", crop_name, npk["N"], npk["P"], npk["K"])
        return result

    def recommend_crop(
        self,
        temperature: float,
        humidity: float,
        ph: float,
        rainfall: float,
        n: Optional[float] = None,
        p: Optional[float] = None,
        k: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Recommend a crop using the trained Random Forest classifier.

        Feature order: N, P, K, temperature, humidity, ph, rainfall.
        """
        features = [
            n if n is not None else 50.0,
            p if p is not None else 30.0,
            k if k is not None else 30.0,
            temperature,
            humidity,
            ph,
            rainfall,
        ]
        X = np.array([features])

        prediction = self.model.predict(X)[0]

        result = {
            "recommended_crop": str(prediction),
            "input_conditions": {
                "temperature": temperature,
                "humidity": humidity,
                "ph": ph,
                "rainfall": rainfall,
                "N": n,
                "P": p,
                "K": k,
            },
        }
        logger.info("Recommended crop: %s", prediction)
        return result

    def _validate_crop_name(self, crop_name: str) -> None:
        if crop_name not in self.crop_options:
            sample = ", ".join(self.crop_options[:5])
            raise ValueError(f"Crop '{crop_name}' not found. Examples: {sample}...")

    def _validate_environment(self, features: Dict[str, float]) -> None:
        required = {"temperature", "humidity", "ph", "rainfall"}
        missing = required - features.keys()
        if missing:
            raise ValueError(f"Missing required features: {missing}")

        if not (0 <= features["temperature"] <= 60):
            raise ValueError("Temperature must be between 0–60°C")
        if not (0 <= features["humidity"] <= 100):
            raise ValueError("Humidity must be between 0–100%")
        if not (3 <= features["ph"] <= 9):
            raise ValueError("pH must be between 3–9")
        if features["rainfall"] < 0:
            raise ValueError("Rainfall must be >= 0 mm")

    def _get_mean_npk_for_crop(self, crop_name: str) -> Dict[str, float]:
        """Average N, P, K for a crop from the reference CSV."""
        if self.dataset is None or "label" not in self.dataset.columns:
            return {"N": 0.0, "P": 0.0, "K": 0.0}

        rows = self.dataset[self.dataset["label"] == crop_name]
        if rows.empty:
            return {"N": 0.0, "P": 0.0, "K": 0.0}

        return {
            "N": round(float(rows["N"].mean()), 2),
            "P": round(float(rows["P"].mean()), 2),
            "K": round(float(rows["K"].mean()), 2),
        }
