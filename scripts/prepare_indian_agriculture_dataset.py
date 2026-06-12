#!/usr/bin/env python3
"""
Prepare unified Indian agriculture dataset from multiple sources.

Place raw datasets under datasets/sources/:
  - PlantVillage/          (class folders)
  - rice_diseases/         (Kaggle — optional)
  - wheat_diseases/        (optional)
  - invalid_objects/       (faces, bottles, phones, backgrounds)

Output:
  datasets/indian_agriculture/stage1_crop/
  datasets/indian_agriculture/stage2_disease/

Usage:
  python scripts/prepare_indian_agriculture_dataset.py
  python scripts/prepare_indian_agriculture_dataset.py --copy --max-per-class 800
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from app.utils.dataset_builder import IndianAgricultureDatasetBuilder
from config import DATA_PATHS

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Indian agriculture training dataset")
    parser.add_argument("--copy", action="store_true", help="Copy files instead of symlinks")
    parser.add_argument("--max-per-class", type=int, default=None)
    parser.add_argument("--invalid-count", type=int, default=500)
    parser.add_argument("--no-synthetic-invalid", action="store_true")
    args = parser.parse_args()

    builder = IndianAgricultureDatasetBuilder(
        base_dir=DATA_PATHS["indian_agriculture"],
        sources_dir=DATA_PATHS["dataset_sources"],
    )
    manifest = builder.build(
        symlink=not args.copy,
        max_per_class=args.max_per_class,
        generate_invalid=not args.no_synthetic_invalid,
        invalid_count=args.invalid_count,
    )

    logger.info("=" * 60)
    logger.info("Dataset preparation complete")
    logger.info("Stage-1 classes: %d", len(manifest["stage1_classes"]))
    logger.info("Stage-2 classes: %d", len(manifest["stage2_classes"]))
    logger.info("Total images — stage1: %d, stage2: %d", manifest["total_stage1"], manifest["total_stage2"])
    if manifest["skipped"]:
        logger.info("Skipped folders: %s", manifest["skipped"][:10])
    logger.info("Manifest: %s", DATA_PATHS["indian_agriculture"] / "dataset_manifest.json")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
