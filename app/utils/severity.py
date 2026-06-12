"""
Disease severity and harmfulness analysis.
"""
from __future__ import annotations

from typing import Any, Dict


HARMFULNESS_LEVELS = ("Low", "Medium", "High", "Critical")


def build_severity_info(
    is_healthy: bool,
    disease_meta: Dict[str, Any] | None,
    confidence: float,
) -> Dict[str, Any]:
    """
    Build severity block for API responses.

    Uses disease database metadata when available; otherwise derives from confidence.
    """
    if is_healthy:
        return {
            "severity_percent": 0,
            "harmfulness": "Low",
            "impact": "The crop leaf appears healthy. Continue regular monitoring and good agronomic practices.",
        }

    if disease_meta:
        severity = int(disease_meta.get("severity_percent", 50))
        harmfulness = str(disease_meta.get("harmfulness", "Medium"))
        impact = str(
            disease_meta.get(
                "impact",
                "This disease may affect crop health and yield if left untreated.",
            )
        )
    else:
        severity = _confidence_to_severity(confidence)
        harmfulness = _severity_to_harmfulness(severity)
        impact = _default_impact(harmfulness)

    harmfulness = harmfulness if harmfulness in HARMFULNESS_LEVELS else "Medium"
    return {
        "severity_percent": max(0, min(100, severity)),
        "harmfulness": harmfulness,
        "impact": impact,
    }


def _confidence_to_severity(confidence: float) -> int:
    """Higher model confidence on a disease class suggests stronger signal."""
    return int(min(95, max(35, confidence * 0.85)))


def _severity_to_harmfulness(severity: int) -> str:
    if severity >= 85:
        return "Critical"
    if severity >= 65:
        return "High"
    if severity >= 40:
        return "Medium"
    return "Low"


def _default_impact(harmfulness: str) -> str:
    impacts = {
        "Low": "Minor impact expected; monitor the field and maintain preventive care.",
        "Medium": "This disease may reduce crop quality and yield if not treated early.",
        "High": "This disease can reduce crop yield significantly if untreated.",
        "Critical": "Severe yield loss and crop failure are possible without immediate treatment.",
    }
    return impacts.get(harmfulness, impacts["Medium"])
