#!/usr/bin/env python3
"""
Generate model_crop_solutions.json entries for every class in class_labels.json.

Merges existing disease_solutions, indian_disease_solutions, and model_crop_solutions,
then fills gaps with agronomic templates keyed by disease type.

Usage:
  python scripts/generate_model_crop_solutions.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from app.utils.class_parser import normalize_disease_key
from app.utils.crop_registry import parse_label_with_model_crops
from config import MODEL_PATHS

DATA_DIR = project_root / "app" / "data"
OUT_PATH = DATA_DIR / "model_crop_solutions.json"


def load_merged_sources() -> dict:
    merged = {}
    for name in ("disease_solutions.json", "indian_disease_solutions.json", "model_crop_solutions.json"):
        path = DATA_DIR / name
        if path.is_file():
            with open(path, encoding="utf-8") as f:
                merged.update(json.load(f))
    return merged


def fuzzy_find(key: str, crop: str, disease: str, pool: dict) -> dict | None:
    if key in pool:
        return pool[key]
    crop_l = crop.lower()
    dis_l = disease.lower().replace(" ", "_")
    for k, v in pool.items():
        if k == "default_disease":
            continue
        if not k.startswith(crop_l.replace(" ", "_")):
            continue
        if dis_l in k or k.endswith(dis_l.split("_")[0]):
            return v
    return None


def disease_category(disease: str) -> str:
    d = disease.lower()
    if any(x in d for x in ("healthy", "fresh")):
        return "healthy"
    if any(x in d for x in ("virus", "virosis", "mosaic", "curl")):
        return "virus"
    if any(x in d for x in ("aphid", "whitefly", "mite", "minner", "hispa")):
        return "pest"
    if any(x in d for x in ("bacterial", "wilt")):
        return "bacterial"
    if any(x in d for x in ("rust", "mildew", "blight", "spot", "rot", "anthracnose", "septoria", "blast")):
        return "fungal"
    return "general"


def template_entry(crop: str, disease: str, is_healthy: bool, friendly: str) -> dict:
    if is_healthy:
        return {
            "disease_name": f"{crop} — Healthy",
            "severity_percent": 0,
            "harmfulness": "Low",
            "impact": "No disease detected. Continue regular scouting and balanced nutrition.",
            "cause": "N/A",
            "symptoms": ["Green healthy foliage", "Normal growth"],
            "fertilizers": ["Balanced NPK per growth stage", "Micronutrients if soil test shows deficiency"],
            "pesticides": ["None required"],
            "organic_solutions": ["Mulching", "Drip irrigation", "Crop rotation"],
            "prevention": ["Certified seed", "Field sanitation", "Avoid water stress"],
            "recommended_actions": [f"Monitor {crop} weekly for early disease signs"],
        }

    cat = disease_category(disease)
    if cat == "healthy":
        return template_entry(crop, disease, True, friendly)
    name = friendly.strip()
    base = {
        "disease_name": name,
        "severity_percent": {"fungal": 65, "bacterial": 70, "virus": 75, "pest": 55, "general": 60}[cat],
        "harmfulness": {"fungal": "Medium", "bacterial": "High", "virus": "High", "pest": "Medium", "general": "Medium"}[cat],
        "impact": f"This condition can reduce {crop} yield if left untreated. Early action improves recovery.",
    }

    templates = {
        "fungal": {
            "cause": f"Fungal pathogen affecting {crop} foliage or fruit.",
            "symptoms": ["Leaf spots or lesions", "Yellowing or wilting", "Spread in humid weather"],
            "fertilizers": ["Balanced NPK", "Avoid excess nitrogen during infection"],
            "pesticides": ["Mancozeb", "Propiconazole", "Copper oxychloride"],
            "organic_solutions": ["Neem oil spray", "Trichoderma", "Remove infected plant parts"],
            "prevention": ["Crop rotation", "Proper spacing", "Avoid wet foliage at night"],
            "recommended_actions": [
                "Remove heavily infected leaves",
                "Apply fungicide at first symptoms",
                "Improve air circulation in the field",
            ],
        },
        "bacterial": {
            "cause": f"Bacterial infection on {crop}, often spread by rain splash and tools.",
            "symptoms": ["Water-soaked lesions", "Yellow halos", "Wilting in advanced stages"],
            "fertilizers": ["Reduce nitrogen during outbreak", "Potassium support for recovery"],
            "pesticides": ["Copper bactericides", "Streptocycline where approved"],
            "organic_solutions": ["Certified disease-free seed", "Field sanitation"],
            "prevention": ["Avoid overhead irrigation", "Disinfect tools", "Use resistant varieties"],
            "recommended_actions": [
                "Remove infected plants",
                "Apply copper spray early",
                "Consult local KVK for severe outbreaks",
            ],
        },
        "virus": {
            "cause": f"Viral disease on {crop}, often vector-transmitted (whitefly, aphid, mites).",
            "symptoms": ["Mosaic or mottled leaves", "Leaf curl or distortion", "Stunted growth"],
            "fertilizers": ["Balanced nutrition", "Micronutrient foliar spray"],
            "pesticides": ["Control vector insects", "Imidacloprid for whitefly (as per label)"],
            "organic_solutions": ["Neem oil for vectors", "Remove infected plants", "Reflective mulch"],
            "prevention": ["Vector control", "Resistant varieties", "Rogue infected plants early"],
            "recommended_actions": [
                "Remove and destroy infected plants",
                "Control whitefly/aphid population",
                "Plant virus-free seedlings",
            ],
        },
        "pest": {
            "cause": f"Insect or mite pest damage on {crop}.",
            "symptoms": ["Visible insects or eggs", "Leaf mining or curling", "Honeydew or sooty mold"],
            "fertilizers": ["Maintain plant vigor with balanced NPK"],
            "pesticides": ["Neem-based spray", "Spinosad", "Abamectin for mites (label rates)"],
            "organic_solutions": ["Yellow sticky traps", "Neem oil", "Predatory insects"],
            "prevention": ["Regular scouting", "Remove weed hosts", "Intercropping with repellent plants"],
            "recommended_actions": [
                "Identify pest correctly before spraying",
                "Apply targeted insecticide at economic threshold",
                "Monitor after treatment",
            ],
        },
        "general": {
            "cause": f"Stress or pathogen affecting {crop} — confirm with local extension officer.",
            "symptoms": ["Discolored or damaged leaves", "Reduced vigor"],
            "fertilizers": ["Balanced NPK per soil test"],
            "pesticides": ["Consult local agri officer for approved products"],
            "organic_solutions": ["Field sanitation", "Crop rotation"],
            "prevention": ["Certified seed", "Timely irrigation"],
            "recommended_actions": ["Scout field weekly", "Take clear leaf photo for re-analysis"],
        },
    }
    entry = {**base, **templates[cat]}
    entry["disease_name"] = name
    return entry


def main() -> None:
    labels_path = MODEL_PATHS["class_labels"]
    with open(labels_path, encoding="utf-8") as f:
        meta = json.load(f)

    pool = load_merged_sources()
    existing_model = {}
    model_path = OUT_PATH
    if model_path.is_file():
        with open(model_path, encoding="utf-8") as f:
            existing_model = json.load(f)

    classes = meta.get("classes", [])
    folder_classes = meta.get("folder_classes", classes)
    output = dict(existing_model)
    added = 0

    for friendly, folder in zip(classes, folder_classes):
        label = folder if folder else friendly
        crop, disease, is_healthy = parse_label_with_model_crops(label)
        if crop == "Unknown" and friendly:
            crop, disease, is_healthy = parse_label_with_model_crops(friendly)

        key = normalize_disease_key(crop, disease if not is_healthy else "healthy")
        if key in output:
            continue

        found = fuzzy_find(key, crop, disease, pool)
        if found:
            output[key] = {k: v for k, v in found.items() if k != "disease_name"}
            output[key]["disease_name"] = found.get("disease_name", friendly)
        else:
            output[key] = template_entry(crop, disease, is_healthy or disease_category(disease) == "healthy", friendly)
            added += 1

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"Wrote {len(output)} entries to {OUT_PATH} ({added} new templates, {len(classes)} model classes)")


if __name__ == "__main__":
    main()
