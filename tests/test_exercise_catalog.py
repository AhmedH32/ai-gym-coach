from pathlib import Path

import pytest
from backend.rag_engine.exercise_catalog import ExerciseCatalog

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CATALOG_PATH = PROJECT_ROOT / "raw_data" / "exercises.json"


@pytest.fixture(scope="module")
def catalog():
    return ExerciseCatalog(catalog_path=str(CATALOG_PATH))

def test_catalog_ingestion_and_pruning(catalog: ExerciseCatalog):
    assert len(catalog.exercises) == 876
    assert len(catalog.valid_ids) == 876

    # Verify memory footprint: heavy frontend fields must NOT be stored in memory
    sample = catalog.exercises[0]
    assert "id" in sample
    assert "name" in sample
    assert "primary_muscles" in sample
    assert "equipment" in sample
    assert "mechanic" in sample
    assert "images" not in sample
    assert "instructions" not in sample


def test_muscle_synonym_quads(catalog: ExerciseCatalog):
    # Model says "quads", catalog has "quadriceps"
    results = catalog.search(muscle="quads", limit=5)
    assert len(results) > 0
    for ex in results:
        assert "quadriceps" in ex["primary_muscles"]


def test_muscle_back_biomechanical_isolation(catalog: ExerciseCatalog):
    # Querying "back" must pull lats and middle back, but NEVER spinal lower back
    results = catalog.search(muscle="back", limit=10)
    assert len(results) > 0

    allowed_targets = {"lats", "middle back"}
    for ex in results:
        matched = set(ex["primary_muscles"]).intersection(allowed_targets)
        assert len(matched) > 0, f"Exercise {ex['id']} has invalid targets: {ex['primary_muscles']}"
        # Spinal erector movements must never leak into a general back query
        assert "lower back" not in ex["primary_muscles"], (
            f"Spinal erector exercise {ex['id']} leaked into general back query!"
        )


def test_equipment_plural_and_stemming(catalog: ExerciseCatalog):
    # 1. Model emits "dumbbells" -> catalog has "dumbbell"
    results_db = catalog.search(equipment="dumbbells", limit=5)
    assert len(results_db) > 0
    for ex in results_db:
        assert "dumbbell" in ex["equipment"]

    # 2. Model emits "kettlebell" -> catalog has "kettlebells"
    results_kb = catalog.search(equipment="kettlebell", limit=5)
    assert len(results_kb) > 0
    for ex in results_kb:
        assert "kettlebell" in ex["equipment"]


def test_multi_equipment_tokenization(catalog: ExerciseCatalog):
    # Model emits comma-separated string from test C1
    results = catalog.search(muscle="quads", equipment="kettlebell, resistance bands", limit=10)
    assert len(results) > 0

    valid_equipment = {"kettlebell", "kettlebells", "bands"}
    for ex in results:
        assert any(eq in ex["equipment"] for eq in valid_equipment)


def test_negative_constraint_true_mechanic(catalog: ExerciseCatalog):
    # Model asks for chest compound only, excluding isolation
    results = catalog.search(muscle="chest", exclude_mechanics="isolation", limit=5)
    assert len(results) > 0
    for ex in results:
        assert ex["mechanic"] == "compound"
        assert ex["mechanic"] != "isolation"


def test_negative_constraint_equipment_misnomer(catalog: ExerciseCatalog):
    # Model passes equipment ("barbell") inside exclude_mechanics
    results = catalog.search(muscle="chest", equipment="cable", exclude_mechanics="barbell", limit=5)
    assert len(results) > 0
    for ex in results:
        assert "barbell" not in ex["equipment"]
        assert "barbell" not in ex["name"].lower()


def test_negative_constraint_machine_plural(catalog: ExerciseCatalog):
    # Model passes plural "machines" inside exclude_mechanics
    results = catalog.search(muscle="back", equipment="dumbbell", exclude_mechanics="machines", limit=5)
    assert len(results) > 0
    for ex in results:
        assert "machine" not in ex["equipment"]
        assert "machine" not in ex["name"].lower()


def test_result_limit_boundary(catalog: ExerciseCatalog):
    results = catalog.search(muscle="chest", limit=3)
    assert len(results) == 3


def test_format_for_prompt(catalog: ExerciseCatalog):
    candidates = catalog.search(muscle="chest", equipment="dumbbell", limit=2)
    prompt_context = catalog.format_for_prompt(candidates)

    assert len(candidates) == 2
    assert prompt_context.count("- [") == 2
    assert "Equipment: dumbbell" in prompt_context
    assert "Target: chest" in prompt_context

    # Empty fallback test
    empty_context = catalog.format_for_prompt([])
    assert empty_context == "No matching exercises found in catalog."