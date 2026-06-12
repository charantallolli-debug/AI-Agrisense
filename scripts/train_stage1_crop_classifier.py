#!/usr/bin/env python3
"""
Stage 1: Indian crop type classifier + invalid_non_crop rejection.

Usage:
  python scripts/prepare_indian_agriculture_dataset.py
  python scripts/train_stage1_crop_classifier.py
  python scripts/train_stage1_crop_classifier.py --architecture mobilenetv2 --epochs 30
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

import tensorflow as tf

from app.ml.model_factory import (
    augmenting_datagen,
    build_crop_classifier,
    get_architecture,
    get_preprocess_fn,
    standard_callbacks,
)
from config import DATA_PATHS, MODEL_PATHS

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def train_stage1(architecture: str = "efficientnetb0", epochs: int = 30, batch_size: int = 32) -> None:
    dataset_dir = DATA_PATHS["indian_agriculture"] / "stage1_crop"
    if not dataset_dir.is_dir():
        raise FileNotFoundError(
            f"Stage-1 dataset not found at {dataset_dir}. "
            "Run: python scripts/prepare_indian_agriculture_dataset.py"
        )

    arch = get_architecture(architecture)
    input_size = arch["input_size"]
    preprocess = get_preprocess_fn(architecture)

    train_gen = augmenting_datagen(preprocess, validation_split=0.2)
    val_gen = tf.keras.preprocessing.image.ImageDataGenerator(
        preprocessing_function=preprocess, validation_split=0.2
    )

    train_data = train_gen.flow_from_directory(
        str(dataset_dir),
        target_size=input_size,
        batch_size=batch_size,
        class_mode="categorical",
        subset="training",
        shuffle=True,
    )
    val_data = val_gen.flow_from_directory(
        str(dataset_dir),
        target_size=input_size,
        batch_size=batch_size,
        class_mode="categorical",
        subset="validation",
        shuffle=False,
    )

    model = build_crop_classifier(train_data.num_classes, architecture, (*input_size, 3))
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )
    model.summary()

    callbacks = standard_callbacks(str(MODEL_PATHS["crop_classifier"]))
    history = model.fit(train_data, validation_data=val_data, epochs=epochs, callbacks=callbacks)

    model.save(str(MODEL_PATHS["crop_classifier"]))
    labels = {
        "stage": 1,
        "architecture": architecture,
        "image_size": list(input_size),
        "classes": sorted(train_data.class_indices.keys()),
        "class_indices": train_data.class_indices,
    }
    with open(MODEL_PATHS["crop_classifier_labels"], "w", encoding="utf-8") as f:
        json.dump(labels, f, indent=2)

    logger.info("Stage-1 saved: %s", MODEL_PATHS["crop_classifier"])
    logger.info("Val accuracy: %.4f", history.history["val_accuracy"][-1])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--architecture", default="efficientnetb0", choices=["efficientnetb0", "mobilenetv2"])
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--batch-size", type=int, default=32)
    args = parser.parse_args()
    train_stage1(args.architecture, args.epochs, args.batch_size)
