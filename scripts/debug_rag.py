from backend.rag_engine.vector_store import RAGVectorStore

# In debug_rag.py
store = RAGVectorStore(
    persist_directory="backend/rag_engine/chroma_db",
    model_name="BAAI/bge-base-en-v1.5"
)
store.ingest_all_corpora()

print("=" * 70)
print("1. SHOULDER BENCH QUERY (Top 3)")
print("=" * 70)
r1 = store.query(
    "sharp pinch in anterior shoulder when bench pressing heavy barbell",
    n_results=3,
    distance_threshold=2.0
)
for r in r1["results"]:
    print(f"  [{r['distance']:.4f}] {r['id']} ({r['metadata']['category']})")

print("\n" + "=" * 70)
print("2. KNEE VALGUS / LATERAL HIP QUERY (Top 3)")
print("=" * 70)
r2 = store.query(
    "knees caving inward during deep squats with lateral hip aching and weakness",
    n_results=3,
    distance_threshold=2.0
)
for r in r2["results"]:
    print(f"  [{r['distance']:.4f}] {r['id']} ({r['metadata']['category']})")

print("\n" + "=" * 70)
print("3. OUT-OF-DOMAIN / SYSTEMIC EMERGENCY QUERIES")
print("=" * 70)
ood_queries = [
    "severe lower right abdominal pain with nausea and high fever",
    "how to bake a sourdough bread loaf with active yeast",
    "quantum computing Shor algorithm for RSA encryption"
]

for q in ood_queries:
    res = store.query(q, n_results=1, distance_threshold=2.0)
    top_hit = res["results"][0] if res["results"] else None
    top_id = top_hit["id"] if top_hit else "None"
    dist = top_hit["distance"] if top_hit else 999.0
    print(f"  Query: '{q[:40]}...'")
    print(f"    -> Min Distance: {dist:.4f} | Top Hit: {top_id}")
print("=" * 70)