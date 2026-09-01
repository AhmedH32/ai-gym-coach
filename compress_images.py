#!/usr/bin/env python3
"""
compress_images.py — Phase 1 Image Compression Pipeline

Recursively scans raw_data/images/ for exercise images (.jpg, .jpeg, .png),
resizes to max 500px width (maintaining aspect ratio), converts to WebP at
quality 60, and saves to client/src/assets/exercises/ with deterministic
snake_case naming: <exercise_id>_<index>.webp
"""

import os
import sys
import json
import re
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("ERROR: Pillow is not installed. Run: python -m pip install Pillow tqdm")
    sys.exit(1)

try:
    from tqdm import tqdm
except ImportError:
    print("ERROR: tqdm is not installed. Run: python -m pip install Pillow tqdm")
    sys.exit(1)

# --- Configuration ---
RAW_IMAGES_DIR = Path("raw_data/images")
OUTPUT_DIR = Path("client/src/assets/exercises")
MAX_WIDTH = 500
WEBP_QUALITY = 60
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png"}


def to_snake_case(name: str) -> str:
    """Convert an exercise directory name to snake_case ID."""
    # Replace hyphens and spaces with underscores
    s = name.replace("-", "_").replace(" ", "_")
    # Insert underscores before uppercase letters (camelCase handling)
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s)
    # Replace multiple underscores with single
    s = re.sub(r"_+", "_", s)
    # Lowercase and strip leading/trailing underscores
    s = s.lower().strip("_")
    return s


def collect_images() -> list[tuple[Path, str, int]]:
    """
    Collect all valid images from raw_data/images/.
    
    The directory structure is:
        raw_data/images/<ExerciseId>/0.jpg
        raw_data/images/<ExerciseId>/1.jpg
    
    Returns list of (image_path, snake_case_exercise_id, image_index).
    """
    images = []

    if not RAW_IMAGES_DIR.exists():
        print(f"ERROR: Source directory '{RAW_IMAGES_DIR}' does not exist.")
        sys.exit(1)

    for exercise_dir in sorted(RAW_IMAGES_DIR.iterdir()):
        if not exercise_dir.is_dir():
            continue

        exercise_id = to_snake_case(exercise_dir.name)

        # Collect image files in this exercise directory
        image_files = sorted(
            f
            for f in exercise_dir.iterdir()
            if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
        )

        for idx, img_file in enumerate(image_files):
            images.append((img_file, exercise_id, idx))

    return images


def compress_image(src_path: Path, dest_path: Path) -> None:
    """
    Open an image, resize to max width 500px maintaining aspect ratio,
    convert to RGB if necessary, and save as WebP at quality 60.
    """
    with Image.open(src_path) as img:
        # Handle RGBA -> RGB conversion for WebP compatibility
        if img.mode == "RGBA":
            # Create white background
            background = Image.new("RGB", img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3])  # Use alpha channel as mask
            img = background
        elif img.mode != "RGB":
            img = img.convert("RGB")

        # Resize if width exceeds MAX_WIDTH
        if img.width > MAX_WIDTH:
            ratio = MAX_WIDTH / img.width
            new_height = int(img.height * ratio)
            img = img.resize((MAX_WIDTH, new_height), Image.LANCZOS)

        # Save as WebP
        img.save(dest_path, format="WEBP", quality=WEBP_QUALITY)


def main():
    print("=" * 60)
    print("  Phase 1 — Image Compression Pipeline")
    print("=" * 60)
    print()

    # Collect all source images
    print("Scanning for images...")
    images = collect_images()
    source_count = len(images)
    print(f"Found {source_count} source images.")
    print()

    if source_count == 0:
        print("ERROR: No images found. Check raw_data/images/ directory.")
        sys.exit(1)

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Process images with progress bar
    success_count = 0
    fail_count = 0
    failures = []

    print("Compressing images to WebP...")
    for src_path, exercise_id, idx in tqdm(images, desc="Converting", unit="img"):
        dest_filename = f"{exercise_id}_{idx}.webp"
        dest_path = OUTPUT_DIR / dest_filename

        try:
            compress_image(src_path, dest_path)
            success_count += 1
        except Exception as e:
            fail_count += 1
            failures.append((str(src_path), str(e)))

    # Count output files and calculate size
    webp_files = list(OUTPUT_DIR.glob("*.webp"))
    webp_count = len(webp_files)
    total_size_bytes = sum(f.stat().st_size for f in webp_files)
    total_size_mb = total_size_bytes / (1024 * 1024)

    # Report
    print()
    print("=" * 60)
    print("  Compression Report")
    print("=" * 60)
    print(f"  Source image count:      {source_count}")
    print(f"  Successful conversions:  {success_count}")
    print(f"  Failed conversions:      {fail_count}")
    print(f"  WebP files created:      {webp_count}")
    print(f"  Total output size:       {total_size_mb:.2f} MB")
    print("=" * 60)

    if failures:
        print()
        print("FAILURES:")
        for path, error in failures:
            print(f"  {path}: {error}")

    if total_size_mb >= 40:
        print()
        print(f"WARNING: Output size ({total_size_mb:.2f} MB) exceeds 40 MB limit!")

    print()
    print("Done.")


if __name__ == "__main__":
    main()
