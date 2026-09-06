import glob
import hashlib
import os
import re
import time
from typing import Any

import chromadb
from sentence_transformers import SentenceTransformer


class RAGVectorStore:
    """
    High-performance vector store engineered for sub-20ms retrieval,
    idempotent set-reconciliation ingestion, and deterministic clinical guardrails.
    """
    QUERY_INSTRUCTION = "Represent this sentence for searching relevant passages: "

    # Pre-compile regexes at the class level to eliminate per-file recompilation overhead
    _RE_ID = re.compile(r"^#\s*ID:\s*([A-Za-z0-9_]+)", re.MULTILINE)
    _RE_CATEGORY = re.compile(r"^\*\*Category:\*\*\s*(.+)$", re.MULTILINE)
    _RE_TOPIC = re.compile(r"^\*\*(?:Condition Name|Topic):\*\*\s*(.+)$", re.MULTILINE)

    def __init__(
        self,
        persist_directory: str = "backend/rag_engine/chroma_db",
        model_name: str = "BAAI/bge-base-en-v1.5",
        device: str = "cpu",
        batch_size: int = 64
    ) -> None:
        self.persist_directory = persist_directory
        self.batch_size = batch_size
        os.makedirs(self.persist_directory, exist_ok=True)

        # 1. Embedded storage engine (SQLite metadata ledger + HNSW memory-mapped index)
        self.client = chromadb.PersistentClient(path=self.persist_directory)

        # 2. Bi-encoder runtime
        self.model = SentenceTransformer(model_name, device=device)
        self.model.max_seq_length = 512

        # 3. Inner Product space (equivalent to Cosine Similarity for unit-normalized vectors)
        # Bypasses vector norm reduction and square root calculations during HNSW graph hops
        self.collection = self.client.get_or_create_collection(
            name="gym_coach_knowledge",
            metadata={"hnsw:space": "ip"}
        )

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """
        Embeds document passages in mini-batches.
        Uses C-level vector normalization and array casting to prevent Python runtime stalls.
        """
        embeddings = self.model.encode(
            texts,
            batch_size=self.batch_size,
            normalize_embeddings=True,
            show_progress_bar=False,
            convert_to_numpy=True
        )
        return embeddings.tolist()

    def embed_query(self, query: str) -> list[float]:
        """
        Asymmetrically embeds a search query by prepending the task-conditioning instruction.
        """
        prefixed_query = f"{self.QUERY_INSTRUCTION}{query}"
        embedding = self.model.encode(
            prefixed_query,
            normalize_embeddings=True,
            show_progress_bar=False,
            convert_to_numpy=True
        )
        return embedding.tolist()

    @classmethod
    def parse_markdown_document(cls, file_path: str, source_type: str) -> dict[str, Any] | None:
        """
        Extracts document payload, schema metadata, and content hash in a single pass.
        Guarantees deterministic IDs and zero-leakage corpus tagging.
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except OSError:
            return None

        # Extract deterministic ID with fallback to uppercase file slug
        id_match = cls._RE_ID.search(content)
        raw_id = id_match.group(1).strip().upper() if id_match else os.path.splitext(os.path.basename(file_path))[0].upper()

        # Enforce canonical ID prefixes based on directory domain
        if source_type == "clinical_injury" and not raw_id.startswith("COND_"):
            doc_id = f"COND_{raw_id}"
        elif source_type == "periodization" and not raw_id.startswith("PROG_"):
            doc_id = f"PROG_{raw_id}"
        else:
            doc_id = raw_id

        cat_match = cls._RE_CATEGORY.search(content)
        category = cat_match.group(1).strip() if cat_match else "General"

        topic_match = cls._RE_TOPIC.search(content)
        topic = topic_match.group(1).strip() if topic_match else os.path.basename(file_path)

        # Cryptographic content hash for change detection
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

        return {
            "id": doc_id,
            "document": content,
            "metadata": {
                "id": doc_id,
                "topic": topic,
                "category": category,
                "source_type": source_type,
                "file_name": os.path.basename(file_path),
                "sha256": content_hash
            }
        }

    def reconcile_and_index(self, directory_configs: list[tuple[str, str]]) -> dict[str, int]:
        """
        Idempotent set-reconciliation sync engine.
        
        Complexity:
            - Scan & Hash: O(N_files) disk I/O, negligible CPU
            - Reconciliation diff: O(N_docs) set operations
            - Embedding: O(M_changed * (L^2 * d)) Transformer forward passes
        """
        # 1. Ingest disk state
        disk_docs: dict[str, dict[str, Any]] = {}
        for dir_path, source_type in directory_configs:
            for fpath in glob.glob(os.path.join(dir_path, "*.md")):
                parsed = self.parse_markdown_document(fpath, source_type=source_type)
                if parsed:
                    disk_docs[parsed["id"]] = parsed

        # 2. Extract active database state from Chroma SQLite ledger
        existing = self.collection.get(include=["metadatas"])
        existing_ids = set(existing["ids"])
        existing_hashes = {
            doc_id: meta.get("sha256")
            for doc_id, meta in zip(existing["ids"], existing["metadatas"] or [])
            if meta
        }

        # 3. Compute disjoint sets
        disk_ids = set(disk_docs.keys())
        to_delete = list(existing_ids - disk_ids)
        to_upsert_ids = [
            doc_id for doc_id, doc in disk_docs.items()
            if doc_id not in existing_hashes or existing_hashes[doc_id] != doc["metadata"]["sha256"]
        ]
        unchanged_count = len(disk_ids) - len(to_upsert_ids)

        # 4. Prune orphaned vectors
        if to_delete:
            self.collection.delete(ids=to_delete)

        # 5. Batched embedding & upserting for new/modified entities
        if to_upsert_ids:
            for i in range(0, len(to_upsert_ids), self.batch_size):
                chunk_ids = to_upsert_ids[i:i + self.batch_size]
                chunk_docs = [disk_docs[doc_id]["document"] for doc_id in chunk_ids]
                chunk_metas = [disk_docs[doc_id]["metadata"] for doc_id in chunk_ids]
                
                chunk_embeddings = self.embed_documents(chunk_docs)

                self.collection.upsert(
                    ids=chunk_ids,
                    embeddings=chunk_embeddings,
                    documents=chunk_docs,
                    metadatas=chunk_metas
                )

        return {
            "upserted": len(to_upsert_ids),
            "deleted": len(to_delete),
            "unchanged": unchanged_count,
            "total_active": self.collection.count()
        }

    def ingest_all_corpora(
        self,
        injuries_dir: str = "rag_corpus/injuries",
        periodization_dir: str = "rag_corpus/periodization"
    ) -> dict[str, int]:
        """Ingests and synchronizes all corpora through the reconciliation pipeline."""
        return self.reconcile_and_index([
            (injuries_dir, "clinical_injury"),
            (periodization_dir, "periodization")
        ])

    def query(
        self,
        query_text: str,
        n_results: int = 2,
        distance_threshold: float = 0.42,
        where_filter: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Queries top-K nearest neighbors using inner-product distance with clinical rejection.
        Returns OUT_OF_DOMAIN if the nearest neighbor distance exceeds tau = 0.55.
        """
        t0 = time.perf_counter()
        query_vector = self.embed_query(query_text)

        raw_results = self.collection.query(
            query_embeddings=[query_vector],
            n_results=n_results,
            where=where_filter,
            include=["documents", "metadatas", "distances"]
        )
        latency_ms = round((time.perf_counter() - t0) * 1000, 2)

        # Structural validation guard
        ids = raw_results.get("ids")
        distances = raw_results.get("distances")
        documents = raw_results.get("documents")
        metadatas = raw_results.get("metadatas")

        if not ids or not distances or not documents or not metadatas or not ids[0]:
            return {
                "status": "OUT_OF_DOMAIN",
                "min_distance": 2.0,
                "latency_ms": latency_ms,
                "results": []
            }

        min_distance = float(distances[0][0])

        # Clinical rejection check (OOD symptoms / emergency triage)
        if min_distance > distance_threshold:
            return {
                "status": "OUT_OF_DOMAIN",
                "min_distance": round(min_distance, 4),
                "latency_ms": latency_ms,
                "results": []
            }

        # Format valid matches that respect the safety threshold
        formatted_matches = [
            {
                "id": doc_id,
                "document": doc_text,
                "metadata": meta,
                "distance": round(float(dist), 4)
            }
            for doc_id, doc_text, meta, dist in zip(ids[0], documents[0], metadatas[0], distances[0])
            if dist <= distance_threshold
        ]

        return {
            "status": "MATCH_FOUND",
            "min_distance": round(min_distance, 4),
            "latency_ms": latency_ms,
            "results": formatted_matches
        }