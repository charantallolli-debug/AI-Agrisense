#!/usr/bin/env python3
"""
Stage 2: Crop-conditioned disease classifier (EfficientNet + crop one-hot).

Usage:
  python scripts/train_stage2_disease_classifier.py
"""
from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

import numpy as np
import tensorflow as tf
from tensorflow.keras.utils import Sequence

from app.ml.model_factory import (
    build_disease_classifier,
    get_architecture,
    get_preprocess_fn,
    standard_callbacks,
)
from app.utils.indian_crops import get_indian_crops, get_invalid_class_name
from config import DATA_PATHS, MODEL_PATHS

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class CropConditionedSequence(Sequence):
    """Batch generator with crop one-hot conditioning for stage-2."""

    def __init__(
        self,
        directory: Path,
        crop_to_index: dict,
        batch_size: int,
        image_size: tuple,
        preprocess_fn,
        shuffle: bool = True,
        augment: bool = False,
    ):
        self.directory = Path(directory)
        self.crop_to_index = crop_to_index
        self.num_crops = len(crop_to_index)
        self.batch_size = batch_size
        self.image_size = image_size
        self.preprocess_fn = preprocess_fn
        self.shuffle = shuffle
        self.augment = augment

        self.samples = []
        self.class_indices = {}
        idx = 0
        for class_dir in sorted(self.directory.iterdir()):
            if not class_dir.is_dir():
                continue
            self.class_indices[class_dir.name] = idx
            crop = self._extract_crop(class_dir.name)
            for img in class_dir.iterdir():
                if img.suffix.lower() in {".jpg", ".jpeg", ".png", ".bmp", ".webp"}:
                    self.samples.append((str(img), idx, crop))
            idx += 1

        self.on_epoch_end()

    @staticmethod
    def _extract_crop(class_name: str) -> str:
        if "___" in class_name:
            return class_name.split("___", 1)[0]
        if "__" in class_name:
            return class_name.split("__", 1)[0]
        return class_name.split("_")[0]

    def __len__(self):
        return max(1, int(np.ceil(len(self.samples) / self.batch_size)))

    def on_epoch_end(self):
        if self.shuffle:
            np.random.shuffle(self.samples)

    def __getitem__(self, index):
        from PIL import Image

        batch = self.samples[index * self.batch_size : (index + 1) * self.batch_size]
        images = []
        crop_oh = []
        labels = []

        for path, label, crop in batch:
            img = Image.open(path).convert("RGB").resize(self.image_size)
            arr = np.asarray(img, dtype=np.float32)
            arr = self.preprocess_fn(arr)
            if self.augment:
                arr = self._augment(arr)
            images.append(arr)
            oh = np.zeros(self.num_crops, dtype=np.float32)
            cidx = self.crop_to_index.get(crop, 0)
            oh[cidx] = 1.0
            crop_oh.append(oh)
            labels.append(label)

        return (
            [np.stack(images), np.stack(crop_oh)],
            tf.keras.utils.to_categorical(labels, num_classes=len(self.class_indices)),
        )

    @staticmethod
    def _augment(arr: np.ndarray) -> np.ndarray:
        if np.random.rand() > 0.5:
            arr = np.fliplr(arr)
        if np.random.rand() > 0.6:
            factor = np.random.uniform(0.7, 1.3)
            arr = np.clip(arr * factor, -128, 128)
        return arr


def train_stage2(architecture: str = "efficientnetb0", epochs: int = 35, batch_size: int = 32) -> None:
    dataset_dir = DATA_PATHS["indian_agriculture"] / "stage2_disease"
    if not dataset_dir.is_dir():
        raise FileNotFoundError(
            f"Stage-2 dataset not found at {dataset_dir}. "
            "Run: python scripts/prepare_indian_agriculture_dataset.py"
        )

    arch = get_architecture(architecture)
    input_size = arch["input_size"]
    preprocess = get_preprocess_fn(architecture)

    stage1_dir = DATA_PATHS["indian_agriculture"] / "stage1_crop"
    invalid = get_invalid_class_name()
    crops = sorted(
        d.name for d in stage1_dir.iterdir()
        if d.is_dir() and d.name != invalid
    )
    if not crops:
        raise FileNotFoundError(f"No crop folders found in {stage1_dir}")

    crop_to_index = {c: i for i, c in enumerate(crops)}
    logger.info("Stage-2 crop conditioning: %d crops", len(crops))

    train_seq = CropConditionedSequence(
        dataset_dir, crop_to_index, batch_size, input_size, preprocess, shuffle=True, augment=True
    )
    val_seq = CropConditionedSequence(
        dataset_dir, crop_to_index, batch_size, input_size, preprocess, shuffle=False, augment=False
    )

    split = int(len(train_seq.samples) * 0.8)
    val_seq.samples = train_seq.samples[split:]
    train_seq.samples = train_seq.samples[:split]

    model = build_disease_classifier(
        len(train_seq.class_indices),
        len(crop_to_index),
        architecture,
        (*input_size, 3),
    )
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )
    model.summary()

    callbacks = standard_callbacks(str(MODEL_PATHS["disease_classifier"]))
    history = model.fit(train_seq, validation_data=val_seq, epochs=epochs, callbacks=callbacks)

    model.save(str(MODEL_PATHS["disease_classifier"]))
    friendly = []
    for name in sorted(train_seq.class_indices.keys()):
        from app.utils.indian_crops import friendly_label
        friendly.append(friendly_label(name))

    labels = {
        "stage": 2,
        "architecture": architecture,
        "image_size": list(input_size),
        "classes": sorted(train_seq.class_indices.keys()),
        "friendly_classes": friendly,
        "class_indices": train_seq.class_indices,
        "crop_to_index": crop_to_index,
        "invalid_class": invalid,
    }
    with open(MODEL_PATHS["disease_classifier_labels"], "w", encoding="utf-8") as f:
        json.dump(labels, f, indent=2)

    logger.info("Stage-2 saved: %s", MODEL_PATHS["disease_classifier"])
    logger.info("Classes: %d | Val accuracy: %.4f", len(train_seq.class_indices), history.history["val_accuracy"][-1])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--architecture", default="efficientnetb0", choices=["efficientnetb0", "mobilenetv2"])
    parser.add_argument("--epochs", type=int, default=35)
    parser.add_argument("--batch-size", type=int, default=32)
    args = parser.parse_args()
    train_stage2(args.architecture, args.epochs, args.batch_size)
