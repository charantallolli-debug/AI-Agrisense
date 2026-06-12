"""
Train crop disease detection model with transfer learning (EfficientNetB0 or MobileNetV2).

Expects PlantVillage-style folder layout:
    datasets/PlantVillage/<class_name>/*.jpg

Saves:
    trained_models/crop_disease_model.h5
    trained_models/class_labels.json

Usage:
    python scripts/train_disease_detection.py
    python scripts/train_disease_detection.py --architecture mobilenetv2 --epochs 20
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

import tensorflow as tf
from tensorflow.keras import layers, models
from tensorflow.keras.applications import EfficientNetB0, MobileNetV2
from tensorflow.keras.applications.efficientnet import preprocess_input as efficientnet_preprocess
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input as mobilenet_preprocess
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau
from tensorflow.keras.preprocessing.image import ImageDataGenerator

from config import DATA_PATHS, MODEL_PATHS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

ARCHITECTURES = {
    "efficientnetb0": {
        "class": EfficientNetB0,
        "input_size": (224, 224),
        "preprocess": efficientnet_preprocess,
    },
    "mobilenetv2": {
        "class": MobileNetV2,
        "input_size": (224, 224),
        "preprocess": mobilenet_preprocess,
    },
}


def build_transfer_model(
    base_model_class,
    num_classes: int,
    input_shape: tuple,
) -> tf.keras.Model:
    """Build classifier head on frozen ImageNet backbone (inputs preprocessed in datagen)."""
    base = base_model_class(
        include_top=False,
        weights="imagenet",
        input_shape=input_shape,
        pooling="avg",
    )
    base.trainable = False

    inputs = layers.Input(shape=input_shape)
    x = base(inputs, training=False)
    x = layers.Dropout(0.4)(x)
    x = layers.Dense(512, activation="relu")(x)
    x = layers.Dropout(0.3)(x)
    outputs = layers.Dense(num_classes, activation="softmax")(x)
    return models.Model(inputs, outputs)


def friendly_class_name(folder_name: str) -> str:
    """Convert PlantVillage folder name to readable label."""
    if "___" in folder_name:
        crop, disease = folder_name.split("___", 1)
        crop = crop.replace("_", " ").title()
        disease = disease.replace("_", " ").title()
        return f"{crop} {disease}"
    return folder_name.replace("_", " ").title()


def train_disease_detection_model(
    architecture: str = "efficientnetb0",
    epochs: int = 25,
    batch_size: int = 32,
    fine_tune_epochs: int = 10,
    dataset_path: str | None = None,
) -> None:
    arch_key = architecture.lower()
    if arch_key not in ARCHITECTURES:
        raise ValueError(f"Unknown architecture: {architecture}")

    arch = ARCHITECTURES[arch_key]
    input_size = arch["input_size"]
    if dataset_path is None:
        crop_path = DATA_PATHS.get("crop_disease_dataset")
        pv_path = DATA_PATHS["plant_village"]
        if crop_path and crop_path.is_dir():
            dataset_path = str(crop_path)
        elif pv_path.is_dir():
            dataset_path = str(pv_path)
        else:
            dataset_path = str(crop_path or pv_path)

    if not os.path.isdir(dataset_path):
        raise FileNotFoundError(
            f"Dataset not found at {dataset_path}. "
            "Place class folders under datasets/sources/dataset/ or datasets/PlantVillage/"
        )

    logger.info("=" * 60)
    logger.info("Smart Agriculture — Disease Model Training")
    logger.info("Architecture: %s | Input: %s", arch_key, input_size)
    logger.info("=" * 60)

    train_datagen = ImageDataGenerator(
        preprocessing_function=arch["preprocess"],
        rotation_range=25,
        zoom_range=0.25,
        width_shift_range=0.15,
        height_shift_range=0.15,
        brightness_range=[0.7, 1.3],
        horizontal_flip=True,
        fill_mode="nearest",
        validation_split=0.2,
    )

    val_datagen = ImageDataGenerator(
        preprocessing_function=arch["preprocess"],
        validation_split=0.2,
    )

    train_data = train_datagen.flow_from_directory(
        dataset_path,
        target_size=input_size,
        batch_size=batch_size,
        class_mode="categorical",
        subset="training",
    )

    val_data = val_datagen.flow_from_directory(
        dataset_path,
        target_size=input_size,
        batch_size=batch_size,
        class_mode="categorical",
        subset="validation",
    )

    folder_classes = sorted(train_data.class_indices.keys())
    friendly_classes = [friendly_class_name(c) for c in folder_classes]

    logger.info("Classes: %d", train_data.num_classes)
    logger.info("Sample labels: %s", friendly_classes[:5])

    model = build_transfer_model(
        arch["class"],
        train_data.num_classes,
        (*input_size, 3),
    )
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )
    model.summary()

    callbacks = [
        EarlyStopping(patience=5, restore_best_weights=True, monitor="val_accuracy"),
        ReduceLROnPlateau(patience=3, factor=0.5, min_lr=1e-6),
        ModelCheckpoint(
            str(MODEL_PATHS["disease_detection"]),
            save_best_only=True,
            monitor="val_accuracy",
        ),
    ]

    logger.info("Phase 1: training head (frozen base)...")
    history = model.fit(
        train_data,
        validation_data=val_data,
        epochs=epochs,
        callbacks=callbacks,
        verbose=1,
    )

    # Optional fine-tuning: unfreeze top layers of the backbone
    base_layer = None
    for layer in model.layers:
        if hasattr(layer, "layers") and len(getattr(layer, "layers", [])) > 10:
            base_layer = layer
            break
    if base_layer is not None:
        base_layer.trainable = True
        for layer in base_layer.layers[:-30]:
            layer.trainable = False
        model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=1e-5),
            loss="categorical_crossentropy",
            metrics=["accuracy"],
        )
        logger.info("Phase 2: fine-tuning top base layers...")
        model.fit(
            train_data,
            validation_data=val_data,
            epochs=fine_tune_epochs,
            callbacks=callbacks,
            verbose=1,
        )

    os.makedirs(MODEL_PATHS["disease_detection"].parent, exist_ok=True)
    model.save(str(MODEL_PATHS["disease_detection"]))
    logger.info("Model saved: %s", MODEL_PATHS["disease_detection"])

    labels_meta = {
        "image_size": list(input_size),
        "architecture": arch_key,
        "classes": friendly_classes,
        "folder_classes": folder_classes,
        "class_indices": train_data.class_indices,
    }
    labels_path = MODEL_PATHS["class_labels"]
    with open(labels_path, "w", encoding="utf-8") as f:
        json.dump(labels_meta, f, indent=2)
    logger.info("Class labels saved: %s", labels_path)

    logger.info("Final train accuracy: %.4f", history.history["accuracy"][-1])
    logger.info("Final val accuracy: %.4f", history.history["val_accuracy"][-1])
    logger.info("Training complete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train disease detection CNN")
    parser.add_argument(
        "--architecture",
        choices=list(ARCHITECTURES.keys()),
        default="efficientnetb0",
    )
    parser.add_argument("--epochs", type=int, default=25)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--fine-tune-epochs", type=int, default=10)
    parser.add_argument("--dataset", type=str, default=None, help="Path to class-folder dataset")
    parser.add_argument("--no-fine-tune", action="store_true", help="Skip phase-2 fine-tuning (faster)")
    args = parser.parse_args()
    train_disease_detection_model(
        architecture=args.architecture,
        epochs=args.epochs,
        batch_size=args.batch_size,
        fine_tune_epochs=0 if args.no_fine_tune else args.fine_tune_epochs,
        dataset_path=args.dataset,
    )
