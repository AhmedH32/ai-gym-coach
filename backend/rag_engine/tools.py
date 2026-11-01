# backend/rag_engine/tools.py
import time
from pathlib import Path
from typing import Any, Literal
from pydantic import BaseModel, Field

from backend.rag_engine.exercise_catalog import ExerciseCatalog
from backend.rag_engine.vector_store import RAGVectorStore

DEFAULT_CHROMA_DIR = Path(__file__).resolve().parent / "chroma_db"


class MedicalSearchResult(BaseModel):
    """Strict Pydantic schema preventing silent key mismatches between tools.py and orchestrator.py."""
    status: Literal["MATCH_FOUND", "OUT_OF_DOMAIN", "EMPTY_QUERY"]
    triage_required: bool
    matched_ids: list[str] = Field(default_factory=list)
    min_distance: float = 1.0
    max_rerank_prob: float = 0.0
    latency_ms: float = 0.0
    stage1_ms: float = 0.0
    rerank_ms: float = 0.0
    context_block: str

    def __getitem__(self, item: str) -> Any:
        return getattr(self, item)

    def get(self, item: str, default: Any = None) -> Any:
        return getattr(self, item, default)


class CatalogSearchResult(BaseModel):
    found: bool
    count: int
    matched_ids: list[str] = Field(default_factory=list)
    candidates: list[dict[str, Any]] = Field(default_factory=list)
    latency_ms: float = 0.0
    context_block: str

    def __getitem__(self, item: str) -> Any:
        return getattr(self, item)

    def get(self, item: str, default: Any = None) -> Any:
        return getattr(self, item, default)


class ClinicalRAGTools:
    """
    Unified Tool Layer bridging System-1 Vela Router decisions to
    Two-Stage Clinical RAG (40 Clinical Injury Cards) and ExerciseCatalog (876 movements).
    """

    def __init__(
        self,
        vector_store: RAGVectorStore | None = None,
        catalog: ExerciseCatalog | None = None,
        device: str | None = None,
    ) -> None:
        self.store = vector_store or RAGVectorStore(
            persist_directory=str(DEFAULT_CHROMA_DIR),
            device=device,
        )
        self.catalog = catalog or ExerciseCatalog()

    def search_medical_db(
        self,
        query: str,
        n_results: int = 2,
        candidate_pool_size: int = 10,
        distance_threshold: float = 0.58,
        rerank_prob_threshold: float = 0.12,
        use_reranker: bool = True,
    ) -> MedicalSearchResult:
        t0 = time.perf_counter()

        if not query or not str(query).strip():
            latency_ms = round((time.perf_counter() - t0) * 1000.0, 2)
            return MedicalSearchResult(
                status="EMPTY_QUERY",
                triage_required=True,
                matched_ids=[],
                min_distance=1.0,
                max_rerank_prob=0.0,
                latency_ms=latency_ms,
                context_block=(
                    "### CLINICAL ALERT: EMPTY QUERY / UNVERIFIED SYMPTOM\n"
                    "No valid symptom or injury query was provided. "
                    "SAFETY ACTION: Prompt the athlete for specific symptoms and pain location."
                ),
            )

        query_res = self.store.query(
            query_text=query.strip(),
            n_results=n_results,
            candidate_pool_size=candidate_pool_size,
            distance_threshold=distance_threshold,
            rerank_prob_threshold=rerank_prob_threshold,
            use_reranker=use_reranker,
        )
        latency_ms = round((time.perf_counter() - t0) * 1000.0, 2)

        if query_res["status"] == "OUT_OF_DOMAIN" or not query_res["results"]:
            return MedicalSearchResult(
                status="OUT_OF_DOMAIN",
                triage_required=True,
                matched_ids=[],
                min_distance=query_res["min_distance"],
                max_rerank_prob=query_res.get("max_rerank_prob", 0.0),
                latency_ms=latency_ms,
                stage1_ms=query_res.get("stage1_ms", 0.0),
                rerank_ms=query_res.get("rerank_ms", 0.0),
                context_block=(
                    "### CLINICAL ALERT: OUT OF DOMAIN / POTENTIAL MEDICAL EMERGENCY\n"
                    "The reported symptoms do not match indexed musculoskeletal sports injuries.\n"
                    "SAFETY ACTION: Do NOT prescribe exercise modifications. Instruct the athlete to seek "
                    "formal evaluation from a licensed medical professional or physical therapist immediately."
                ),
            )

        matched_ids: list[str] = []
        context_sections: list[str] = []

        for card in query_res["results"]:
            doc_id = card["id"]
            topic = card["metadata"].get("topic", doc_id)
            category = card["metadata"].get("category", "General")
            matched_ids.append(doc_id)
            formatted_card = (
                f"### CLINICAL PROTOCOL: {topic} ({category}) [ID: {doc_id}]\n"
                f"{card['document'].strip()}"
            )
            context_sections.append(formatted_card)

        context_block = "\n\n---\n\n".join(context_sections)

        return MedicalSearchResult(
            status="MATCH_FOUND",
            triage_required=False,
            matched_ids=matched_ids,
            min_distance=query_res["min_distance"],
            max_rerank_prob=query_res.get("max_rerank_prob", 0.0),
            latency_ms=latency_ms,
            stage1_ms=query_res.get("stage1_ms", 0.0),
            rerank_ms=query_res.get("rerank_ms", 0.0),
            context_block=context_block,
        )

    def search_exercise_catalog(
        self,
        muscle: str | None = None,
        equipment: str | None = None,
        exclude_mechanics: str | None = None,
        limit: int = 6,
    ) -> CatalogSearchResult:
        t0 = time.perf_counter()

        clean_muscle = muscle.strip() if isinstance(muscle, str) and muscle.strip() else None
        clean_equip = equipment.strip() if isinstance(equipment, str) and equipment.strip() else None
        clean_exclude = (
            exclude_mechanics.strip()
            if isinstance(exclude_mechanics, str) and exclude_mechanics.strip()
            else None
        )

        # Balanced multi-muscle candidate retrieval (e.g. "back, biceps" -> 3 back + 3 biceps)
        candidates: list[dict[str, Any]] = []
        seen_ids: set[str] = set()
        if clean_muscle and "," in clean_muscle:
            sub_muscles = [m.strip() for m in clean_muscle.split(",") if m.strip()]
            per_muscle_limit = max(2, limit // len(sub_muscles))
            for sm in sub_muscles:
                sub_hits = self.catalog.search(
                    muscle=sm,
                    equipment=clean_equip,
                    exclude_mechanics=clean_exclude,
                    limit=per_muscle_limit,
                )
                for ex in sub_hits:
                    if ex["id"] not in seen_ids:
                        seen_ids.add(ex["id"])
                        candidates.append(ex)
        else:
            candidates = self.catalog.search(
                muscle=clean_muscle,
                equipment=clean_equip,
                exclude_mechanics=clean_exclude,
                limit=limit,
            )

        latency_ms = round((time.perf_counter() - t0) * 1000.0, 2)
        matched_ids = [ex["id"] for ex in candidates]

        if not candidates:
            return CatalogSearchResult(
                found=False,
                count=0,
                matched_ids=[],
                candidates=[],
                latency_ms=latency_ms,
                context_block=(
                    "### CANDIDATE EXERCISES:\n"
                    "No matching exercises found in catalog. Consider broadening equipment constraints "
                    "or using bodyweight alternatives."
                ),
            )

        formatted_summary = self.catalog.format_for_prompt(candidates)
        context_block = f"### CANDIDATE EXERCISES:\n{formatted_summary}"

        return CatalogSearchResult(
            found=True,
            count=len(candidates),
            matched_ids=matched_ids,
            candidates=candidates,
            latency_ms=latency_ms,
            context_block=context_block,
        )