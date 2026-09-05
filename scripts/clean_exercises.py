#!/usr/bin/env python3
"""
clean_exercises.py — Phase 1 Exercise Data Cleaning Pipeline

Reads raw_data/exercises.json, filters and normalizes exercise data,
validates image references against actual WebP files, and outputs
a clean JSON dataset to client/src/assets/data/exercises.json.

Every output object conforms to the required schema:
{
    "id": "string (snake_case)",
    "name": "string (Title Case)",
    "aliases": ["string"],
    "primary_muscles": ["string"],
    "secondary_muscles": ["string"],
    "equipment": "string",
    "mechanics": "compound | isolation",
    "instructions": ["string"],
    "images": ["assets/exercises/<exercise_id>_<index>.webp"]
}
"""

import json
import re
import sys
from pathlib import Path

# --- Configuration ---
RAW_JSON_PATH = Path("raw_data/exercises.json")
OUTPUT_JSON_PATH = Path("client/src/assets/data/exercises.json")
IMAGES_DIR = Path("client/src/assets/exercises")


def to_snake_case(name: str) -> str:
    """Convert an exercise ID/name to snake_case."""
    s = name.replace("-", "_").replace(" ", "_")
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s)
    s = re.sub(r"_+", "_", s)
    s = s.lower().strip("_")
    return s


def to_title_case(name: str) -> str:
    """Convert a name to Title Case, handling special characters."""
    # Split on spaces and capitalize each word
    words = name.split()
    return " ".join(w.capitalize() if w.islower() or w.isupper() else w for w in words)


def find_exercise_images(exercise_id: str) -> list[str]:
    """
    Find all WebP images for an exercise ID in the output directory.
    Returns relative paths suitable for the client app.
    """
    images = []
    idx = 0
    while True:
        filename = f"{exercise_id}_{idx}.webp"
        filepath = IMAGES_DIR / filename
        if filepath.exists():
            images.append(f"assets/exercises/{filename}")
            idx += 1
        else:
            break
    return images


def normalize_mechanics(mechanic: str | None, raw: dict | None = None) -> str | None:
    """
    Normalize mechanics field to 'compound' or 'isolation'.
    
    When mechanic is None (common for stretching, cardio, plyometrics),
    infer from category and muscle group count:
    - Cardio/plyometrics → compound (multi-joint by nature)
    - Stretching with 1 primary muscle → isolation
    - Stretching with 2+ primary muscles → compound
    - Strength with 1 primary muscle → isolation  
    - Strength with 2+ primary muscles → compound
    """
    if mechanic is not None:
        m = mechanic.strip().lower()
        if m == "compound":
            return "compound"
        elif m == "isolation":
            return "isolation"
        else:
            return None
    
    # Mechanic is None — infer from available data
    if raw is None:
        return None
    
    category = (raw.get("category") or "").strip().lower()
    primary_muscles = [m for m in raw.get("primaryMuscles", []) if m and m.strip()]
    
    if category in ("cardio", "plyometrics"):
        return "compound"
    
    # For stretching and strength with null mechanic, infer from muscle count
    if len(primary_muscles) >= 2:
        return "compound"
    elif len(primary_muscles) == 1:
        return "isolation"
    
    return None


def clean_exercise(raw: dict) -> dict | None:
    """
    Clean and validate a single exercise record.
    Returns None if the exercise should be filtered out.
    """
    # Extract raw fields
    raw_id = raw.get("id", "")
    raw_name = raw.get("name", "")
    raw_mechanic = raw.get("mechanic")
    raw_equipment = raw.get("equipment", "")
    raw_primary = raw.get("primaryMuscles", [])
    raw_secondary = raw.get("secondaryMuscles", [])
    raw_instructions = raw.get("instructions", [])

    # --- Validation: skip if missing critical data ---

    # Must have instructions
    if not raw_instructions or not isinstance(raw_instructions, list):
        return None
    # Filter out empty instruction strings
    instructions = [s.strip() for s in raw_instructions if isinstance(s, str) and s.strip()]
    if not instructions:
        return None

    # Must have at least one primary muscle target
    if not raw_primary or not isinstance(raw_primary, list):
        return None
    primary_muscles = [m.strip().lower() for m in raw_primary if isinstance(m, str) and m.strip()]
    if not primary_muscles:
        return None

    # Generate snake_case ID
    exercise_id = to_snake_case(raw_id) if raw_id else to_snake_case(raw_name)
    if not exercise_id:
        return None

    # Find corresponding images
    images = find_exercise_images(exercise_id)
    if not images:
        return None

    # Normalize mechanics
    mechanics = normalize_mechanics(raw_mechanic, raw)
    if mechanics is None:
        return None

    # Normalize other fields
    name = to_title_case(raw_name) if raw_name else exercise_id.replace("_", " ").title()

    secondary_muscles = [m.strip().lower() for m in raw_secondary if isinstance(m, str) and m.strip()]

    equipment = raw_equipment.strip().lower() if raw_equipment else "none"

    # Aliases: empty array since the raw data doesn't have aliases
    aliases = []

    return {
        "id": exercise_id,
        "name": name,
        "aliases": aliases,
        "primary_muscles": primary_muscles,
        "secondary_muscles": secondary_muscles,
        "equipment": equipment,
        "mechanics": mechanics,
        "instructions": instructions,
        "images": images,
    }


def validate_output(exercises: list[dict]) -> list[str]:
    """Validate the cleaned exercise dataset. Returns list of issues."""
    issues = []

    # Check unique IDs
    ids = [e["id"] for e in exercises]
    if len(ids) != len(set(ids)):
        dupes = [i for i in ids if ids.count(i) > 1]
        issues.append(f"Duplicate IDs found: {set(dupes)}")

    # Validate each exercise
    snake_case_pattern = re.compile(r"^[a-z0-9]+(_[a-z0-9]+)*$")

    for ex in exercises:
        eid = ex["id"]

        # snake_case ID
        if not snake_case_pattern.match(eid):
            issues.append(f"ID '{eid}' is not valid snake_case")

        # Required fields
        for field in ["name", "equipment", "mechanics"]:
            if not ex.get(field):
                issues.append(f"Exercise '{eid}' missing '{field}'")

        # Mechanics values
        if ex.get("mechanics") not in ("compound", "isolation"):
            issues.append(f"Exercise '{eid}' has invalid mechanics: {ex.get('mechanics')}")

        # Non-empty arrays
        if not ex.get("instructions"):
            issues.append(f"Exercise '{eid}' has empty instructions")
        if not ex.get("primary_muscles"):
            issues.append(f"Exercise '{eid}' has empty primary_muscles")
        if not ex.get("images"):
            issues.append(f"Exercise '{eid}' has empty images")

        # Image file existence
        for img_path in ex.get("images", []):
            # img_path is like "assets/exercises/xxx.webp"
            # Resolve relative to client/src/
            full_path = Path("client/src") / img_path
            if not full_path.exists():
                issues.append(f"Exercise '{eid}' references missing image: {img_path}")

    return issues


def main():
    print("=" * 60)
    print("  Phase 1 — Exercise Data Cleaning Pipeline")
    print("=" * 60)
    print()

    # Load raw data
    if not RAW_JSON_PATH.exists():
        print(f"ERROR: {RAW_JSON_PATH} not found.")
        sys.exit(1)

    with open(RAW_JSON_PATH, "r", encoding="utf-8") as f:
        raw_exercises = json.load(f)

    print(f"Raw exercises loaded: {len(raw_exercises)}")

    # Process exercises
    cleaned = []
    skipped_reasons = {
        "no_instructions": 0,
        "no_muscles": 0,
        "no_images": 0,
        "no_mechanics": 0,
        "other": 0,
    }

    seen_ids = set()

    for raw in raw_exercises:
        result = clean_exercise(raw)
        if result is None:
            # Determine skip reason for reporting
            if not raw.get("instructions") or not [s for s in raw.get("instructions", []) if s and s.strip()]:
                skipped_reasons["no_instructions"] += 1
            elif not raw.get("primaryMuscles") or not [m for m in raw.get("primaryMuscles", []) if m and m.strip()]:
                skipped_reasons["no_muscles"] += 1
            elif normalize_mechanics(raw.get("mechanic")) is None:
                skipped_reasons["no_mechanics"] += 1
            else:
                skipped_reasons["no_images"] += 1
            continue

        # Handle duplicate IDs by appending a suffix
        original_id = result["id"]
        if original_id in seen_ids:
            suffix = 2
            while f"{original_id}_{suffix}" in seen_ids:
                suffix += 1
            result["id"] = f"{original_id}_{suffix}"

        seen_ids.add(result["id"])
        cleaned.append(result)

    print(f"Cleaned exercises: {len(cleaned)}")
    print("Skipped:")
    for reason, count in skipped_reasons.items():
        if count > 0:
            print(f"  {reason}: {count}")

    # Validate
    print()
    print("Validating output...")
    issues = validate_output(cleaned)

    if issues:
        print(f"VALIDATION ISSUES ({len(issues)}):")
        for issue in issues[:20]:
            print(f"  {issue}")
        if len(issues) > 20:
            print(f"  ... and {len(issues) - 20} more")
    else:
        print("VALIDATION: ALL PASS")

    # Write output
    OUTPUT_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(cleaned, f, indent=2, ensure_ascii=False)

    print()
    print("=" * 60)
    print("  Cleaning Report")
    print("=" * 60)
    print(f"  Raw exercises:     {len(raw_exercises)}")
    print(f"  Clean exercises:   {len(cleaned)}")
    print(f"  Filtered out:      {len(raw_exercises) - len(cleaned)}")
    print(f"  Output file:       {OUTPUT_JSON_PATH}")
    print(f"  Output size:       {OUTPUT_JSON_PATH.stat().st_size / 1024:.1f} KB")
    print(f"  800+ exercises:    {'PASS' if len(cleaned) >= 800 else 'FAIL'}")
    print("=" * 60)
    print()
    print("Done.")


if __name__ == "__main__":
    main()
