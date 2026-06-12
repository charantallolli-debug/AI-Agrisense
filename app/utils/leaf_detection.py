"""
OpenCV-based validation: detect whether an image likely contains a crop leaf.
"""
from __future__ import annotations

import logging
from typing import Tuple

import numpy as np

logger = logging.getLogger(__name__)

MIN_WIDTH = 80
MIN_HEIGHT = 80
MIN_BLUR_VARIANCE = 35.0
MIN_GREEN_RATIO = 0.05
MIN_LEAF_AREA_RATIO = 0.04


def validate_image_quality(rgb_array: np.ndarray) -> Tuple[bool, str]:
    """
    Check if the image is clear enough for analysis.

    Returns:
        (is_valid, error_message)
    """
    if rgb_array is None or rgb_array.size == 0:
        return False, "Invalid Image. Please capture a clear crop leaf image."

    h, w = rgb_array.shape[:2]
    if w < MIN_WIDTH or h < MIN_HEIGHT:
        return False, "Invalid Image. Please capture a clear crop leaf image."

    gray = _to_gray(rgb_array)
    blur_score = cv2_laplacian_variance(gray)
    if blur_score < MIN_BLUR_VARIANCE:
        return False, "Invalid Image. Please capture a clear crop leaf image."

    brightness = float(np.mean(gray))
    if brightness < 25 or brightness > 245:
        return False, "Invalid Image. Please capture a clear crop leaf image."

    return True, ""


def detect_leaf(rgb_array: np.ndarray) -> Tuple[bool, str]:
    """
    Detect plant/leaf-like content using color and contour analysis.

    Returns:
        (has_leaf, message)
    """
    valid, msg = validate_image_quality(rgb_array)
    if not valid:
        return False, msg

    try:
        import cv2
    except ImportError:
        logger.warning("OpenCV not installed; skipping strict leaf detection")
        return True, ""

    hsv = cv2.cvtColor(rgb_array, cv2.COLOR_RGB2HSV)

    # Green plant tissue (tuned for foliage; excludes very dark background)
    lower_green = np.array([25, 30, 30])
    upper_green = np.array([95, 255, 255])
    green_mask = cv2.inRange(hsv, lower_green, upper_green)

    # Yellow/brown diseased leaf regions
    lower_yellow = np.array([15, 30, 40])
    upper_yellow = np.array([35, 255, 255])
    yellow_mask = cv2.inRange(hsv, lower_yellow, upper_yellow)

    plant_mask = cv2.bitwise_or(green_mask, yellow_mask)
    plant_ratio = float(np.count_nonzero(plant_mask)) / plant_mask.size

    if plant_ratio < MIN_GREEN_RATIO:
        return False, "Please upload a valid crop leaf image."

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    cleaned = cv2.morphologyEx(plant_mask, cv2.MORPH_CLOSE, kernel)
    cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, kernel)

    contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return False, "Please upload a valid crop leaf image."

    largest = max(contours, key=cv2.contourArea)
    area = cv2.contourArea(largest)
    image_area = rgb_array.shape[0] * rgb_array.shape[1]
    area_ratio = area / image_area

    if area_ratio < MIN_LEAF_AREA_RATIO:
        return False, "Please upload a valid crop leaf image."

    return True, ""


def pil_to_rgb_array(img) -> np.ndarray:
    """Convert PIL Image to RGB uint8 numpy array."""
    import numpy as np
    from PIL import Image

    if img.mode != "RGB":
        img = img.convert("RGB")
    return np.asarray(img, dtype=np.uint8)


def cv2_laplacian_variance(gray: np.ndarray) -> float:
    try:
        import cv2
        return float(cv2.Laplacian(gray, cv2.CV_64F).var())
    except ImportError:
        # Fallback without OpenCV
        return float(np.var(gray.astype(np.float64)))


def _to_gray(rgb_array: np.ndarray) -> np.ndarray:
    try:
        import cv2
        return cv2.cvtColor(rgb_array, cv2.COLOR_RGB2GRAY)
    except ImportError:
        return (
            0.299 * rgb_array[:, :, 0]
            + 0.587 * rgb_array[:, :, 1]
            + 0.114 * rgb_array[:, :, 2]
        ).astype(np.uint8)
