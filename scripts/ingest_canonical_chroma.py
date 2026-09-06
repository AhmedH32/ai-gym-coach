# ingest_canonical_chroma.py
import shutil
from pathlib import Path

from backend.rag_engine.vector_store import RAGVectorStore

PROJECT_ROOT = Path(__file__).resolve().parent
CANONICAL_CHROMA_DIR = PROJECT_ROOT / "backend" / "rag_engine" / "chroma_db"
SCRATCH_CHROMA_DIR = PROJECT_ROOT / "backend" / "rag_engine" / "chroma_db_base"
INJURIES_DIR = PROJECT_ROOT / "rag_corpus" / "injuries"


def main():
    print("=" * 65)
    print("CANONICAL CHROMADB INGESTION: CLINICAL INJURIES ONLY (40 CARDS)")
    print("=" * 65)

    # Clean existing database to guarantee fresh state
    if SCRATCH_CHROMA_DIR.exists():
        shutil.rmtree(SCRATCH_CHROMA_DIR)

    if CANONICAL_CHROMA_DIR.exists():
        shutil.rmtree(CANONICAL_CHROMA_DIR)

    # Initialize store
    store = RAGVectorStore(
        persist_directory=str(CANONICAL_CHROMA_DIR),
        model_name="BAAI/bge-base-en-v1.5",
        device="cpu"
    )

    # Ingest injuries
    print(f"Ingesting clinical injuries from: {INJURIES_DIR}...")
    sync_results = store.reconcile_and_index([
        (str(INJURIES_DIR), "clinical_injury")
    ])
    print(f"Sync Results: {sync_results}")

    # Verify Count Invariant: exactly 40 documents
    total_count = store.collection.count()
    print(f"\nTotal documents indexed: {total_count}")
    assert total_count == 40, f"Expected 40 injury cards, but found {total_count}!"
    print("✓ Invariant verified: Exactly 40 clinical cards indexed.")

    # Sanity Verification: In-domain vs. Out-of-Domain Separation
    injury_query = "sharp pinch in anterior shoulder when bench pressing heavy barbell"
    res_inj = store.query(injury_query, n_results=3, distance_threshold=0.38)

    ood_query = "severe lower right abdominal pain with nausea chills and high fever"
    res_ood = store.query(ood_query, n_results=3, distance_threshold=0.38)

    sourdough_query = "how long should I bulk ferment sourdough bread with high hydration"
    res_sd = store.query(sourdough_query, n_results=3, distance_threshold=0.38)

    print("\n" + "-" * 65)
    print(f"Injury Match Distance:      {res_inj['min_distance']:.4f}  (Status: {res_inj['status']})")
    print(f"Appendicitis Distance:      {res_ood['min_distance']:.4f}  (Status: {res_ood['status']})")
    print(f"Sourdough Distance:         {res_sd['min_distance']:.4f}  (Status: {res_sd['status']})")
    print("-" * 65)

    assert res_inj["status"] == "MATCH_FOUND", "Injury failed to match under tau=0.38!"
    assert res_ood["status"] == "OUT_OF_DOMAIN", "Appendicitis breached the tau=0.38 safety gate!"
    assert res_sd["status"] == "OUT_OF_DOMAIN", "Sourdough breached the tau=0.38 safety gate!"

    margin_emergency = res_ood["min_distance"] - res_inj["min_distance"]
    margin_sourdough = res_sd["min_distance"] - res_inj["min_distance"]
    print(f"✓ Safety Margin (Appendicitis vs Injury): Δ = {margin_emergency:.4f}")
    print(f"✓ Safety Margin (Sourdough vs Injury):    Δ = {margin_sourdough:.4f}")
    print("=" * 65)
    print("CANONICAL INJURY VECTOR STORE READY.")


if __name__ == "__main__":
    main()