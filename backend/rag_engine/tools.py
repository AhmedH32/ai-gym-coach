from typing import Any

from backend.rag_engine.vector_store import RAGVectorStore


class ClinicalRAGTools:
    """
    Agent tool abstraction over RAGVectorStore.
    Translates raw vector retrieval into prompt-ready context blocks
    and deterministic clinical triage boundaries.
    """

    def __init__(self, vector_store: RAGVectorStore | None = None) -> None:
        # Allow injecting an existing store instance or instantiating default singleton
        self.store = vector_store or RAGVectorStore()

    def get_injury_protocol(
        self,
        symptom_description: str,
        n_results: int = 2,
        distance_threshold: float = 0.42
    ) -> dict[str, Any]:
        """
        Retrieves clinical injury protocols based on user-described symptoms.
        
        Returns:
            dict containing:
              - 'triage_required' (bool): True if symptoms exceed safe distance boundary.
              - 'context_block' (str): Token-efficient formatted Markdown for LLM prompt.
              - 'matched_conditions' (list[str]): Retrieved condition IDs.
        """
        query_res = self.store.query(
            query_text=symptom_description,
            n_results=n_results,
            distance_threshold=distance_threshold,
            where_filter={"source_type": "clinical_injury"}
        )

        if query_res["status"] == "OUT_OF_DOMAIN":
            return {
                "triage_required": True,
                "matched_conditions": [],
                "min_distance": query_res["min_distance"],
                "context_block": (
                    "### CLINICAL ALERT: OUT OF DOMAIN / POTENTIAL MEDICAL EMERGENCY\n"
                    "The athlete's reported symptoms do not match indexed musculoskeletal sports injuries.\n"
                    "SAFETY ACTION: Do NOT prescribe exercise modifications. Instruct the user to seek "
                    "formal evaluation from a licensed medical professional immediately."
                )
            }

        # Format retrieved cards into a clean prompt context block
        context_sections: list[str] = []
        matched_ids: list[str] = []

        for card in query_res["results"]:
            doc_id = card["id"]
            topic = card["metadata"].get("topic", doc_id)
            category = card["metadata"].get("category", "General")
            matched_ids.append(doc_id)

            formatted_card = (
                f"### CLINICAL PROTOCOL: {topic} ({category})\n"
                f"{card['document'].strip()}\n"
            )
            context_sections.append(formatted_card)

        context_block = "\n---\n".join(context_sections)

        return {
            "triage_required": False,
            "matched_conditions": matched_ids,
            "min_distance": query_res["min_distance"],
            "context_block": context_block
        }

    def get_programming_protocol(
        self,
        training_focus: str,
        n_results: int = 1,
        distance_threshold: float = 0.42
    ) -> dict[str, Any]:
        """
        Retrieves scientific periodization, load prescription, or exercise order rules.
        """
        query_res = self.store.query(
            query_text=training_focus,
            n_results=n_results,
            distance_threshold=distance_threshold,
            where_filter={"source_type": "periodization"}
        )

        if query_res["status"] == "OUT_OF_DOMAIN" or not query_res["results"]:
            return {
                "found": False,
                "matched_protocols": [],
                "context_block": "Standard progressive overload principles apply."
            }

        matched_ids = [doc["id"] for doc in query_res["results"]]
        context_block = "\n---\n".join(
            f"### PROGRAMMING RULE: {doc['metadata'].get('topic', doc['id'])}\n{doc['document'].strip()}"
            for doc in query_res["results"]
        )

        return {
            "found": True,
            "matched_protocols": matched_ids,
            "context_block": context_block
        }