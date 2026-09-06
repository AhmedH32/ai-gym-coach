import shutil
import tempfile

import pytest
from backend.rag_engine.vector_store import RAGVectorStore


@pytest.fixture(scope="module")
def vector_store():
    temp_dir = tempfile.mkdtemp()
    store = RAGVectorStore(
        persist_directory=temp_dir,
        model_name="BAAI/bge-base-en-v1.5",
        device="cpu"
    )
    store.ingest_all_corpora(
        injuries_dir="rag_corpus/injuries",
        periodization_dir="rag_corpus/periodization"
    )
    yield store
    shutil.rmtree(temp_dir, ignore_errors=True)


def test_corpus_ingestion_counts(vector_store: RAGVectorStore):
    total_docs = vector_store.collection.count()
    assert total_docs == 45, f"Expected 45 indexed documents, found {total_docs}"


def test_clinical_injury_semantic_retrieval(vector_store: RAGVectorStore):
    query = "sharp pinch in anterior shoulder when bench pressing heavy barbell"
    # K=2 to capture differential diagnosis
    response = vector_store.query(query, n_results=2, distance_threshold=0.42)

    assert response["status"] == "MATCH_FOUND"
    assert len(response["results"]) >= 1

    top_hit = response["results"][0]
    assert top_hit["metadata"]["source_type"] == "clinical_injury"
    assert top_hit["metadata"]["category"] == "Shoulder"
    # Matches valid anterior shoulder differential cards
    assert any(condition in top_hit["id"] for condition in ["INSTABILITY", "IMPINGEMENT", "AC_JOINT"])
    assert response["min_distance"] < 0.42


def test_kinetic_chain_cross_joint_retrieval(vector_store: RAGVectorStore):
    query = "knees caving inward during deep squats with lateral hip aching and weakness"
    # K=3 captures both the knee symptom and hip stabilizing root cause
    response = vector_store.query(query, n_results=3, distance_threshold=0.42)

    assert response["status"] == "MATCH_FOUND"
    retrieved_ids = [doc["id"] for doc in response["results"]]
    
    # Verifies both hip root dysfunction and knee symptom cards surface simultaneously
    has_hip = any("FEMOROACETABULAR" in doc_id or "GREATER_TROCHANTERIC" in doc_id or "GLUTEAL" in doc_id for doc_id in retrieved_ids)
    has_knee = any("PATELLOFEMORAL" in doc_id or "ILIOTIBIAL" in doc_id for doc_id in retrieved_ids)
    
    assert has_hip, f"Expected hip condition in kinetic chain retrieval, got: {retrieved_ids}"
    assert has_knee, f"Expected knee condition in kinetic chain retrieval, got: {retrieved_ids}"


def test_periodization_retrieval(vector_store: RAGVectorStore):
    query = "optimal hypertrophy rep range and proximity to failure RIR"
    response = vector_store.query(query, n_results=1, distance_threshold=0.42)

    assert response["status"] == "MATCH_FOUND"
    top_hit = response["results"][0]
    assert top_hit["metadata"]["source_type"] == "periodization"
    assert "REP_RANGES" in top_hit["id"]


def test_out_of_domain_clinical_rejection(vector_store: RAGVectorStore):
    irrelevant_query = "severe lower right abdominal pain with nausea and high fever"
    response = vector_store.query(irrelevant_query, n_results=1, distance_threshold=0.42)

    assert response["status"] == "OUT_OF_DOMAIN"
    assert response["results"] == []
    assert response["min_distance"] > 0.42


def test_idempotent_reconciliation(vector_store: RAGVectorStore):
    reconcile_result = vector_store.ingest_all_corpora(
        injuries_dir="rag_corpus/injuries",
        periodization_dir="rag_corpus/periodization"
    )

    assert reconcile_result["upserted"] == 0
    assert reconcile_result["deleted"] == 0
    assert reconcile_result["unchanged"] == 45
    assert reconcile_result["total_active"] == 45