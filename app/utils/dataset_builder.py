"""
Build unified Indian agriculture datasets from PlantVillage, Kaggle, and field sources.

Output structure:
  datasets/indian_agriculture/stage1_crop/<CropName>/*.jpg
  datasets/indian_agriculture/stage1_crop/invalid_non_crop/<subdir>/*.jpg
  datasets/indian_agriculture/stage2_disease/<Crop___disease>/*.jpg
"""
from __future__ import annotations

import json
import logging
import random
import re
import shutil
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFilter

from app.utils.indian_crops import (
    friendly_label,
    get_indian_crops,
    get_invalid_class_name,
    load_source_mapping,
    normalize_crop_name,
    parse_disease_folder_name,
    stage2_class_name,
)

logger = logging.getLogger(__name__)

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


class IndianAgricultureDatasetBuilder:
    """Merge multiple sources into stage1/stage2 training folders."""

    def __init__(self, base_dir: Path, sources_dir: Path):
        self.base_dir = Path(base_dir)
        self.sources_dir = Path(sources_dir)
        self.stage1_dir = self.base_dir / "stage1_crop"
        self.stage2_dir = self.base_dir / "stage2_disease"
        self.manifest_path = self.base_dir / "dataset_manifest.json"
        self.mapping = load_source_mapping()

    def build(
        self,
        symlink: bool = True,
        max_per_class: Optional[int] = None,
        generate_invalid: bool = True,
        invalid_count: int = 400,
    ) -> dict:
        """Build full dataset; returns manifest statistics."""
        if self.stage1_dir.exists():
            shutil.rmtree(self.stage1_dir)
        if self.stage2_dir.exists():
            shutil.rmtree(self.stage2_dir)

        stats = {
            "stage1": {},
            "stage2": {},
            "sources_used": [],
            "skipped": [],
        }

        invalid_name = get_invalid_class_name()
        self.stage1_dir.mkdir(parents=True, exist_ok=True)
        (self.stage1_dir / invalid_name).mkdir(parents=True, exist_ok=True)

        # --- Primary user dataset (62-class folders) ---
        user_dataset = self.sources_dir / "dataset"
        if user_dataset.is_dir():
            stats["sources_used"].append("dataset")
            self._ingest_flat_class_folders(user_dataset, symlink, max_per_class, stats)

        # --- PlantVillage ---
        pv_path = self.sources_dir / "PlantVillage"
        if pv_path.is_dir():
            stats["sources_used"].append("PlantVillage")
            self._ingest_plantvillage(pv_path, symlink, max_per_class, stats)
        else:
            stats["skipped"].append(f"PlantVillage not found at {pv_path}")

        # --- Additional Kaggle / Indian sources ---
        for folder_name, crop_hint in self.mapping.get("kaggle_source_folders", {}).items():
            src = self.sources_dir / folder_name
            if not src.is_dir():
                continue
            stats["sources_used"].append(folder_name)
            self._ingest_generic_source(src, crop_hint, symlink, max_per_class, stats)

        # --- invalid_non_crop from sources/invalid_objects ---
        invalid_src = self.sources_dir / "invalid_objects"
        if invalid_src.is_dir():
            stats["sources_used"].append("invalid_objects")
            self._ingest_invalid_objects(invalid_src, symlink, max_per_class, stats)

        if generate_invalid:
            self._generate_synthetic_invalid(invalid_count, stats)

        manifest = {
            "stage1_classes": sorted(stats["stage1"].keys()),
            "stage2_classes": sorted(stats["stage2"].keys()),
            "stage1_counts": stats["stage1"],
            "stage2_counts": stats["stage2"],
            "sources_used": stats["sources_used"],
            "skipped": stats["skipped"],
            "total_stage1": sum(stats["stage1"].values()),
            "total_stage2": sum(stats["stage2"].values()),
        }
        with open(self.manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

        logger.info(
            "Dataset built: stage1=%d images, stage2=%d images, %d stage2 classes",
            manifest["total_stage1"],
            manifest["total_stage2"],
            len(manifest["stage2_classes"]),
        )
        return manifest

    def _ingest_flat_class_folders(
        self,
        src_root: Path,
        symlink: bool,
        max_per_class: Optional[int],
        stats: dict,
    ) -> None:
        """Ingest PlantVillage-style flat class folders (e.g. datasets/sources/dataset/)."""
        for class_dir in sorted(src_root.iterdir()):
            if not class_dir.is_dir():
                continue
            folder_name = class_dir.name
            crop, disease, healthy = parse_disease_folder_name(folder_name)
            if crop is None:
                from app.utils.crop_registry import parse_label_with_model_crops

                crop, disease, healthy = parse_label_with_model_crops(folder_name)
            if crop in (None, "Unknown"):
                stats["skipped"].append(folder_name)
                continue
            self._add_images(
                class_dir, crop, disease, healthy, symlink, max_per_class, stats
            )

    def _ingest_plantvillage(
        self,
        pv_path: Path,
        symlink: bool,
        max_per_class: Optional[int],
        stats: dict,
    ) -> None:
        pv_map = self.mapping.get("plantvillage_crop_map", {})
        for class_dir in sorted(pv_path.iterdir()):
            if not class_dir.is_dir():
                continue
            folder_name = class_dir.name
            crop = None
            disease = folder_name

            if "___" in folder_name:
                crop, disease, healthy = parse_disease_folder_name(folder_name)
            else:
                for pv_crop, mapped in pv_map.items():
                    if folder_name.lower().startswith(pv_crop.lower()):
                        crop = mapped
                        disease = folder_name[len(pv_crop) :].lstrip("_- ")
                        healthy = self._is_healthy_name(disease)
                        break

            if crop is None:
                crop, disease, healthy = parse_disease_folder_name(folder_name)

            if crop is None:
                stats["skipped"].append(folder_name)
                continue

            self._add_images(
                class_dir,
                crop,
                disease,
                healthy,
                symlink,
                max_per_class,
                stats,
            )

    def _ingest_generic_source(
        self,
        src: Path,
        crop_hint: Optional[str],
        symlink: bool,
        max_per_class: Optional[int],
        stats: dict,
    ) -> None:
        """Ingest Kaggle-style folders: either crop/disease hierarchy or flat class folders."""
        subdirs = [d for d in src.iterdir() if d.is_dir()]
        if not subdirs:
            return

        # If top-level folders are crop names
        if crop_hint and normalize_crop_name(subdirs[0].name):
            for crop_dir in subdirs:
                crop = normalize_crop_name(crop_dir.name) or crop_hint
                for disease_dir in crop_dir.iterdir():
                    if disease_dir.is_dir():
                        _, disease, healthy = parse_disease_folder_name(
                            f"{crop}___{disease_dir.name}"
                        )
                        self._add_images(
                            disease_dir, crop, disease, healthy, symlink, max_per_class, stats
                        )
            return

        # Flat class folders: Rice_Blast, wheat_leaf_rust, etc.
        for class_dir in subdirs:
            if "___" in class_dir.name:
                crop, disease, healthy = parse_disease_folder_name(class_dir.name)
            else:
                crop = normalize_crop_name(class_dir.name.split("_")[0]) or crop_hint
                disease = class_dir.name
                healthy = self._is_healthy_name(disease)
            if crop is None:
                stats["skipped"].append(class_dir.name)
                continue
            self._add_images(
                class_dir, crop, disease, healthy, symlink, max_per_class, stats
            )

    def _ingest_invalid_objects(
        self,
        invalid_src: Path,
        symlink: bool,
        max_per_class: Optional[int],
        stats: dict,
    ) -> None:
        invalid_name = get_invalid_class_name()
        subfolders = self.mapping.get("invalid_subfolders", [])
        for sub in invalid_src.iterdir():
            if sub.is_dir():
                dest_sub = self.stage1_dir / invalid_name / sub.name
                dest_sub.mkdir(parents=True, exist_ok=True)
                count = self._copy_images(sub, dest_sub, symlink, max_per_class)
                stats["stage1"].setdefault(invalid_name, 0)
                stats["stage1"][invalid_name] += count

    def _generate_synthetic_invalid(self, count: int, stats: dict) -> None:
        """Bootstrap invalid_non_crop when real non-leaf images are not yet collected."""
        invalid_name = get_invalid_class_name()
        dest = self.stage1_dir / invalid_name / "synthetic"
        dest.mkdir(parents=True, exist_ok=True)
        existing = len(list(dest.glob("*")))
        to_make = max(0, count - existing)
        rng = random.Random(42)

        for i in range(to_make):
            img = Image.new("RGB", (256, 256), self._random_color(rng))
            draw = ImageDraw.Draw(img)
            kind = i % 5
            if kind == 0:
                draw.ellipse([40, 40, 200, 200], fill=self._random_color(rng))
            elif kind == 1:
                draw.rectangle([20, 80, 230, 180], fill=self._random_color(rng))
            elif kind == 2:
                for _ in range(8):
                    draw.line(
                        [rng.randint(0, 255)] * 4,
                        fill=self._random_color(rng),
                        width=rng.randint(2, 8),
                    )
            elif kind == 3:
                img = img.filter(ImageFilter.GaussianBlur(radius=rng.uniform(1, 4)))
            else:
                draw.polygon(
                    [rng.randint(0, 255) for _ in range(8)],
                    fill=self._random_color(rng),
                )
            out = dest / f"synthetic_{existing + i:05d}.jpg"
            img.save(out, quality=85)

        total = len(list(dest.glob("*.jpg")))
        stats["stage1"][invalid_name] = stats["stage1"].get(invalid_name, 0) + total
        logger.info("Synthetic invalid_non_crop samples: %d in %s", total, dest)

    def _add_images(
        self,
        src_dir: Path,
        crop: str,
        disease: str,
        healthy: bool,
        symlink: bool,
        max_per_class: Optional[int],
        stats: dict,
    ) -> None:
        s2_name = stage2_class_name(crop, disease, healthy)
        s1_dir = self.stage1_dir / crop
        s2_dir = self.stage2_dir / s2_name
        s2_dir.mkdir(parents=True, exist_ok=True)

        n1 = self._copy_images(src_dir, s1_dir, symlink, max_per_class)
        n2 = self._copy_images(src_dir, s2_dir, symlink, max_per_class)

        stats["stage1"][crop] = stats["stage1"].get(crop, 0) + n1
        stats["stage2"][s2_name] = stats["stage2"].get(s2_name, 0) + n2

    def _copy_images(
        self,
        src_dir: Path,
        dest_dir: Path,
        symlink: bool,
        max_per_class: Optional[int],
    ) -> int:
        dest_dir.mkdir(parents=True, exist_ok=True)
        files = [
            f
            for f in src_dir.rglob("*")
            if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS
        ]
        if max_per_class and len(files) > max_per_class:
            random.shuffle(files)
            files = files[:max_per_class]

        count = 0
        for src in files:
            dest = dest_dir / f"{src.stem}_{count:06d}{src.suffix.lower()}"
            if dest.exists():
                continue
            try:
                if symlink:
                    dest.symlink_to(src.resolve())
                else:
                    shutil.copy2(src, dest)
                count += 1
            except OSError:
                shutil.copy2(src, dest)
                count += 1
        return count

    @staticmethod
    def _is_healthy_name(name: str) -> bool:
        from app.utils.indian_crops import is_healthy_disease_name
        return is_healthy_disease_name(name)

    @staticmethod
    def _random_color(rng: random.Random) -> Tuple[int, int, int]:
        return (rng.randint(0, 255), rng.randint(0, 255), rng.randint(0, 255))
