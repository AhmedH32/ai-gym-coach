import time
from pathlib import Path
from typing import Any

from backend.rag_engine.exercise_catalog import ExerciseCatalog
from backend.rag_engine.vector_store import RAGVectorStore

DEFAULT_CHROMA_DIR = Path(__file__).resolve().parent / "chroma_db"


class ClinicalRAGTools:
    """
    Unified Tool Layer for the AI Gym Coach ReAct agent.
    Bridges fine-tuned Qwen 2.5 tool calls to RAGVectorStore (40 Clinical Injury Cards)
    and ExerciseCatalog (876 in-memory exercises).
    """

    def __init__(
        self,
        vector_store: RAGVectorStore | None = None,
        catalog: ExerciseCatalog | None = None
    ) -> None:
        self.store = vector_store or RAGVectorStore(persist_directory=str(DEFAULT_CHROMA_DIR))
        self.catalog = catalog or ExerciseCatalog()

    def search_medical_db(
        self,
        query: str,
        n_results: int = 3,
        distance_threshold: float = 0.38  # Calibrated boundary: in-domain ~0.33, OOD >= 0.48
    ) -> dict[str, Any]:
        """
        Retrieves clinical orthopedic injury protocols and biomechanical contraindications.
        Enforces a hard safety circuit breaker (tau = 0.38).
        """
        t0 = time.perf_counter()

        # Guard: Reject empty or whitespace-only queries immediately
        if not query or not str(query).strip():
            latency_ms = round((time.perf_counter() - t0) * 1000, 2)
            return {
                "triage_required": True,
                "matched_ids": [],
                "min_distance": 1.0,
                "latency_ms": latency_ms,
                "context_block": (
                    "### CLINICAL ALERT: EMPTY QUERY / UNVERIFIED SYMPTOM\n"
                    "No valid symptom or injury query was provided. "
                    "SAFETY ACTION: Prompt the athlete for specific symptoms and pain location."
                )
            }

        query_res = self.store.query(
            query_text=query.strip(),
            n_results=n_results,
            distance_threshold=distance_threshold
        )

        latency_ms = round((time.perf_counter() - t0) * 1000, 2)

        # -------------------------------------------------------------
        # HARD CIRCUIT BREAKER: Out-of-domain or acute medical emergency
        # -------------------------------------------------------------
        if query_res["status"] == "OUT_OF_DOMAIN" or not query_res["results"]:
            return {
                "triage_required": True,
                "matched_ids": [],
                "min_distance": query_res["min_distance"],
                "latency_ms": latency_ms,
                "context_block": (
                    "### CLINICAL ALERT: OUT OF DOMAIN / POTENTIAL MEDICAL EMERGENCY\n"
                    "The reported symptoms do not match indexed musculoskeletal sports injuries.\n"
                    "SAFETY ACTION: Do NOT prescribe exercise modifications. Instruct the athlete to seek "
                    "formal evaluation from a licensed medical professional or physical therapist immediately."
                )
            }

        # -------------------------------------------------------------
        # NORMAL FLOW: Format matched injury cards into verbatim Markdown context
        # -------------------------------------------------------------
        matched_ids: list[str] = []
        context_sections: list[str] = []

        for card in query_res["results"]:
            doc_id = card["id"]
            topic = card["metadata"].get("topic", doc_id)
            category = card["metadata"].get("category", "General")
            matched_ids.append(doc_id)

            formatted_card = (
                f"### CLINICAL PROTOCOL: {topic} ({category})\n"
                f"{card['document'].strip()}"
            )
            context_sections.append(formatted_card)

        context_block = "\n\n---\n\n".join(context_sections)

        return {
            "triage_required": False,
            "matched_ids": matched_ids,
            "min_distance": query_res["min_distance"],
            "latency_ms": latency_ms,
            "context_block": context_block
        }

    def search_exercise_catalog(
        self,
        muscle: str | None = None,
        equipment: str | None = None,
        exclude_mechanics: str | None = None,
        limit: int = 5
    ) -> dict[str, Any]:
        """
        Retrieves candidate exercises from the in-memory catalog matching equipment,
        target muscles, and defensive negative constraints.
        """
        t0 = time.perf_counter()

        clean_muscle = muscle.strip() if isinstance(muscle, str) else None
        clean_equip = equipment.strip() if isinstance(equipment, str) else None
        clean_exclude = exclude_mechanics.strip() if isinstance(exclude_mechanics, str) else None

        candidates = self.catalog.search(
            muscle=clean_muscle,
            equipment=clean_equip,
            exclude_mechanics=clean_exclude,
            limit=limit
        )

        latency_ms = round((time.perf_counter() - t0) * 1000, 2)
        matched_ids = [ex["id"] for ex in candidates]

        if not candidates:
            return {
                "found": False,
                "count": 0,
                "matched_ids": [],
                "latency_ms": latency_ms,
                "context_block": (
                    "### CANDIDATE EXERCISES:\n"
                    "No matching exercises found in catalog. Consider broadening equipment constraints "
                    "or using bodyweight alternatives."
                )
            }

        formatted_summary = self.catalog.format_for_prompt(candidates)
        context_block = f"### CANDIDATE EXERCISES:\n{formatted_summary}"

        return {
            "found": True,
            "count": len(candidates),
            "matched_ids": matched_ids,
            "latency_ms": latency_ms,
            "context_block": context_block
        }