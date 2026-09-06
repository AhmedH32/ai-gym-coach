import pytest
from backend.rag_engine.tools import ClinicalRAGTools


@pytest.fixture(scope="module")
def tools():
    instance = ClinicalRAGTools()
    assert instance.store.collection.count() == 40, (
        f"ChromaDB at {instance.store.persist_directory} does not contain exactly 40 injury cards!"
    )
    return instance


# =====================================================================
# MEDICAL DB RETRIEVAL TESTS (Clinical Injuries & Hard Circuit Breaker)
# =====================================================================

def test_search_medical_db_injury_match(tools: ClinicalRAGTools):
    """Case 1: Acute orthopedic query matches clinical cards safely under tau=0.38."""
    query = "sharp pinch in anterior shoulder when bench pressing heavy barbell"
    res = tools.search_medical_db(query, n_results=3)

    assert res["triage_required"] is False
    assert len(res["matched_ids"]) == 3
    assert res["min_distance"] < 0.38
    assert res["latency_ms"] > 0.0

    assert "### CLINICAL PROTOCOL:" in res["context_block"]
    assert "Contraindications" in res["context_block"]
    assert "Substitutions" in res["context_block"]


def test_search_medical_db_circuit_breaker_emergency(tools: ClinicalRAGTools):
    """Case 2: Acute medical emergency trips the tau=0.38 circuit breaker."""
    query = "severe lower right abdominal pain with nausea chills and high fever"
    res = tools.search_medical_db(query, n_results=3)

    assert res["triage_required"] is True
    assert res["matched_ids"] == []
    assert res["min_distance"] > 0.38
    assert "CLINICAL ALERT" in res["context_block"]
    assert "Do NOT prescribe exercise modifications" in res["context_block"]


def test_search_medical_db_circuit_breaker_sourdough_ood(tools: ClinicalRAGTools):
    """Case 3: Unrelated open-domain query trips the tau=0.38 circuit breaker."""
    query = "how long should I bulk ferment sourdough bread with high hydration"
    res = tools.search_medical_db(query, n_results=3)

    assert res["triage_required"] is True
    assert res["matched_ids"] == []
    assert res["min_distance"] > 0.38
    assert "CLINICAL ALERT" in res["context_block"]


def test_search_medical_db_empty_or_whitespace_query(tools: ClinicalRAGTools):
    """Case 4: Empty string or whitespace triggers defensive rejection without crashing."""
    res_empty = tools.search_medical_db("", n_results=3)
    assert res_empty["triage_required"] is True
    assert res_empty["matched_ids"] == []

    res_spaces = tools.search_medical_db("   \n\t  ", n_results=3)
    assert res_spaces["triage_required"] is True
    assert res_spaces["matched_ids"] == []


# =====================================================================
# EXERCISE CATALOG TESTS (In-Memory Filtering & Negative Constraints)
# =====================================================================

def test_search_exercise_catalog_candidates_found(tools: ClinicalRAGTools):
    """Case 5: Multi-attribute matching with defensive negative constraint handling."""
    res = tools.search_exercise_catalog(
        muscle="quads",
        equipment="kettlebell, resistance bands",
        exclude_mechanics="barbell",
        limit=5
    )

    assert res["found"] is True
    assert res["count"] > 0
    assert len(res["matched_ids"]) == res["count"]
    assert res["latency_ms"] < 10.0

    assert "### CANDIDATE EXERCISES:" in res["context_block"]
    assert "- [" in res["context_block"]
    assert "Target: quadriceps" in res["context_block"]


def test_search_exercise_catalog_empty_fallback(tools: ClinicalRAGTools):
    """Case 6: Non-existent equipment returns safe fallback context rather than an error."""
    res = tools.search_exercise_catalog(
        muscle="quads",
        equipment="anti_gravity_boots",
        limit=5
    )

    assert res["found"] is False
    assert res["count"] == 0
    assert res["matched_ids"] == []
    assert "No matching exercises found in catalog" in res["context_block"]


def test_search_exercise_catalog_all_none_arguments(tools: ClinicalRAGTools):
    """Case 7: Calling with no arguments returns valid default candidates without crashing."""
    res = tools.search_exercise_catalog(muscle=None, equipment=None, exclude_mechanics=None, limit=3)

    assert res["found"] is True
    assert res["count"] == 3
    assert len(res["matched_ids"]) == 3


def test_search_exercise_catalog_whitespace_and_casing(tools: ClinicalRAGTools):
    """Case 8: Handles messy LLM input with excessive whitespace and uppercase letters."""
    res = tools.search_exercise_catalog(
        muscle="  CHEST  ",
        equipment="  DUMBBELLS  ",
        limit=3
    )

    assert res["found"] is True
    assert res["count"] > 0
    for ex in tools.catalog.search(muscle="  CHEST  ", equipment="  DUMBBELLS  ", limit=3):
        assert "chest" in ex["primary_muscles"]
        assert "dumbbell" in ex["equipment"]


def test_search_exercise_catalog_back_biomechanical_isolation(tools: ClinicalRAGTools):
    """Case 9: Querying 'back' must never leak 'lower back' axial loading movements."""
    res = tools.search_exercise_catalog(muscle="back", limit=10)

    assert res["found"] is True
    for doc_id in res["matched_ids"]:
        assert "deadlift" not in doc_id.lower()
        assert "hyperextension" not in doc_id.lower()