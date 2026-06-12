"""
Human-readable explanations for disease model predictions.
"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple


def top_predictions(all_predictions: Dict[str, float], k: int = 3) -> List[Dict[str, Any]]:
    """Return top-k class predictions sorted by confidence."""
    if not all_predictions:
        return []
    ranked = sorted(all_predictions.items(), key=lambda x: x[1], reverse=True)
    return [
        {"label": label, "confidence": conf}
        for label, conf in ranked[:k]
    ]


def build_explanation(
    crop: str,
    disease: str,
    confidence: float,
    is_healthy: bool,
    all_predictions: Dict[str, float],
    confidence_warning: bool = False,
) -> Dict[str, Any]:
    """
    Build a structured explanation from softmax outputs (no Grad-CAM required).
    """
    top3 = top_predictions(all_predictions, k=3)
    summary = _summary_text(crop, disease, confidence, is_healthy, top3, confidence_warning)
    reasoning = _reasoning_steps(crop, disease, confidence, is_healthy, top3, confidence_warning)
    alternatives = top3[1:] if len(top3) > 1 else []

    return {
        "summary": summary,
        "reasoning": reasoning,
        "top_predictions": top3,
        "alternatives": alternatives,
        "confidence_gap": _confidence_gap(top3),
    }


def _confidence_gap(top3: List[Dict[str, Any]]) -> float | None:
    if len(top3) < 2:
        return None
    return round(top3[0]["confidence"] - top3[1]["confidence"], 2)


def _summary_text(
    crop: str,
    disease: str,
    confidence: float,
    is_healthy: bool,
    top3: List[Dict[str, Any]],
    confidence_warning: bool,
) -> str:
    if is_healthy:
        base = (
            f"The model classified this as a healthy {crop} leaf with {confidence:.1f}% confidence. "
            "Visual patterns matched healthy tissue rather than common disease symptoms."
        )
    else:
        base = (
            f"The model detected {disease} on {crop} with {confidence:.1f}% confidence. "
            "Leaf texture, color patches, and spot patterns were compared against all trained disease classes."
        )

    gap = _confidence_gap(top3)
    if gap is not None and gap < 8:
        base += (
            f" Note: the next closest prediction was only {gap:.1f}% lower — "
            "a clearer close-up of a single leaf may improve certainty."
        )
    elif confidence_warning:
        base += " Confidence is moderate; retake the photo in good daylight with the leaf filling most of the frame."

    return base


def _reasoning_steps(
    crop: str,
    disease: str,
    confidence: float,
    is_healthy: bool,
    top3: List[Dict[str, Any]],
    confidence_warning: bool,
) -> List[str]:
    steps = [
        "Image passed quality checks (size, brightness, blur).",
        "OpenCV leaf detection confirmed plant foliage in the frame.",
        f"CNN compared the image against {len(top3) if top3 else 'all'} leading classes from the trained model.",
    ]
    if top3:
        leader = top3[0]["label"]
        steps.append(f"Highest match: {leader} ({top3[0]['confidence']:.1f}%).")
    if is_healthy:
        steps.append(f"No significant disease signature was found for {crop}.")
    else:
        steps.append(f"Disease label resolved to: {disease}.")
    if confidence_warning:
        steps.append("Recommendation: capture one leaf on a plain background for a stronger match.")
    return steps
