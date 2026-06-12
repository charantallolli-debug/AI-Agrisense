#!/usr/bin/env python3
"""
Full Indian agriculture AI pipeline: dataset prep → stage1 → stage2.

Usage:
  python scripts/train_indian_agriculture_pipeline.py
  python scripts/train_indian_agriculture_pipeline.py --skip-prepare
"""
from __future__ import annotations

import argparse
import logging
import subprocess
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def run(cmd: list) -> None:
    logger.info("Running: %s", " ".join(cmd))
    subprocess.run(cmd, check=True, cwd=str(project_root))


def main() -> None:
    parser = argparse.ArgumentParser(description="Train full Indian agriculture two-stage pipeline")
    parser.add_argument("--skip-prepare", action="store_true")
    parser.add_argument("--architecture", default="efficientnetb0")
    parser.add_argument("--stage1-epochs", type=int, default=30)
    parser.add_argument("--stage2-epochs", type=int, default=35)
    parser.add_argument("--max-per-class", type=int, default=None)
    args = parser.parse_args()

    py = sys.executable
    scripts = project_root / "scripts"

    if not args.skip_prepare:
        cmd = [py, str(scripts / "prepare_indian_agriculture_dataset.py")]
        if args.max_per_class:
            cmd.extend(["--max-per-class", str(args.max_per_class)])
        run(cmd)

    run([
        py, str(scripts / "train_stage1_crop_classifier.py"),
        "--architecture", args.architecture,
        "--epochs", str(args.stage1_epochs),
    ])
    run([
        py, str(scripts / "train_stage2_disease_classifier.py"),
        "--architecture", args.architecture,
        "--epochs", str(args.stage2_epochs),
    ])

    logger.info("=" * 60)
    logger.info("Indian agriculture pipeline training complete.")
    logger.info("Restart Flask app to load new models.")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
