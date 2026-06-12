"""
Shared Keras model builders for Indian agriculture two-stage pipeline.
"""
from __future__ import annotations

from typing import Callable, Tuple

import tensorflow as tf
from tensorflow.keras import layers, models
from tensorflow.keras.applications import EfficientNetB0, MobileNetV2


ARCHITECTURES = {
    "efficientnetb0": {
        "class": EfficientNetB0,
        "input_size": (224, 224),
    },
    "mobilenetv2": {
        "class": MobileNetV2,
        "input_size": (224, 224),
    },
}


def get_architecture(name: str) -> dict:
    key = name.lower()
    if key not in ARCHITECTURES:
        raise ValueError(f"Unknown architecture: {name}. Choose from {list(ARCHITECTURES)}")
    return ARCHITECTURES[key]


def build_crop_classifier(
    num_classes: int,
    architecture: str = "efficientnetb0",
    input_shape: Tuple[int, int, int] = (224, 224, 3),
) -> tf.keras.Model:
    """Stage 1: crop type + invalid_non_crop rejection."""
    arch = get_architecture(architecture)
    base = arch["class"](include_top=False, weights="imagenet", input_shape=input_shape, pooling="avg")
    base.trainable = False

    inputs = layers.Input(shape=input_shape)
    x = base(inputs, training=False)
    x = layers.Dropout(0.4)(x)
    x = layers.Dense(256, activation="relu")(x)
    x = layers.Dropout(0.3)(x)
    outputs = layers.Dense(num_classes, activation="softmax", name="crop_output")(x)
    return models.Model(inputs, outputs, name="crop_classifier")


def build_disease_classifier(
    num_disease_classes: int,
    num_crops: int,
    architecture: str = "efficientnetb0",
    input_shape: Tuple[int, int, int] = (224, 224, 3),
) -> tf.keras.Model:
    """
    Stage 2: disease prediction conditioned on stage-1 crop (crop one-hot input).
    """
    arch = get_architecture(architecture)
    base = arch["class"](include_top=False, weights="imagenet", input_shape=input_shape, pooling="avg")
    base.trainable = False

    image_input = layers.Input(shape=input_shape, name="image")
    crop_input = layers.Input(shape=(num_crops,), name="crop_condition")

    x = base(image_input, training=False)
    c = layers.Dense(128, activation="relu")(crop_input)
    x = layers.Concatenate()([x, c])
    x = layers.Dropout(0.4)(x)
    x = layers.Dense(512, activation="relu")(x)
    x = layers.Dropout(0.3)(x)
    outputs = layers.Dense(num_disease_classes, activation="softmax", name="disease_output")(x)
    return models.Model([image_input, crop_input], outputs, name="disease_classifier")


def get_preprocess_fn(architecture: str) -> Callable:
    arch = get_architecture(architecture)
    if arch["class"] is EfficientNetB0:
        from tensorflow.keras.applications.efficientnet import preprocess_input
        return preprocess_input
    from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
    return preprocess_input


def standard_callbacks(
    checkpoint_path: str,
    monitor: str = "val_accuracy",
) -> list:
    return [
        tf.keras.callbacks.EarlyStopping(
            patience=6, restore_best_weights=True, monitor=monitor, mode="max"
        ),
        tf.keras.callbacks.ReduceLROnPlateau(
            patience=3, factor=0.5, min_lr=1e-7, monitor=monitor, mode="max"
        ),
        tf.keras.callbacks.ModelCheckpoint(
            checkpoint_path, save_best_only=True, monitor=monitor, mode="max"
        ),
    ]


def augmenting_datagen(preprocess_fn: Callable, validation_split: float = 0.2):
    """Real-world robust augmentation for field/mobile images."""
    return tf.keras.preprocessing.image.ImageDataGenerator(
        preprocessing_function=preprocess_fn,
        validation_split=validation_split,
        rotation_range=35,
        zoom_range=0.35,
        width_shift_range=0.2,
        height_shift_range=0.2,
        shear_range=0.15,
        brightness_range=[0.55, 1.45],
        horizontal_flip=True,
        channel_shift_range=25.0,
        fill_mode="nearest",
    )
