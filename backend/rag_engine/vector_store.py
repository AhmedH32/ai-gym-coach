# backend/rag_engine/vector_store.py
import glob
import hashlib
import math
import os
import re
import time
from typing import Any

import chromadb
import torch
from sentence_transformers import CrossEncoder, SentenceTransformer


class RAGVectorStore:
    """
    Two-Stage Clinical Vector Store:
      - Stage 1 (Bi-Encoder Wide Recall): BAAI/bge-base-en-v1.5 over HNSW Inner-Product space (K=10, tau_dense=0.58)
      - Stage 2 (Cross-Encoder Reranker & Safety Gate): BAAI/bge-reranker-base joint query-document scoring
    Automatically binds to GPU co-processor (cuda:1 on dual-T4 setups) in FP16.
    """

    QUERY_INSTRUCTION = "Represent this sentence for searching relevant passages: "

    _RE_ID = re.compile(r"^#\s*ID:\s*([A-Za-z0-9_]+)", re.MULTILINE)
    _RE_CATEGORY = re.compile(r"^\*\*Category:\*\*\s*(.+)$", re.MULTILINE)
    _RE_TOPIC = re.compile(r"^\*\*(?:Condition Name|Topic):\*\*\s*(.+)$", re.MULTILINE)
    _RE_SOURCES_SECTION = re.compile(r"\n##\s*Sources[\s\S]*$", re.MULTILINE)

    def __init__(
        self,
        persist_directory: str = "backend/rag_engine/chroma_db",
        model_name: str = "BAAI/bge-base-en-v1.5",
        reranker_name: str | None = "BAAI/bge-reranker-base",
        device: str | None = None,
        batch_size: int = 64,
    ) -> None:
        self.persist_directory = persist_directory
        self.batch_size = batch_size

        # Resolve target compute device: env override -> cuda:1 (if dual GPU) -> cuda:0 -> cpu
        env_device = os.environ.get("COPROCESSOR_DEVICE")
        if device is not None:
            self.device = device
        elif env_device:
            self.device = env_device
        elif torch.cuda.is_available():
            self.device = "cuda:1" if torch.cuda.device_count() > 1 else "cuda:0"
        else:
            self.device = "cpu"

        os.makedirs(self.persist_directory, exist_ok=True)
        self.client = chromadb.PersistentClient(path=self.persist_directory)

        # 1. Stage-1 Bi-Encoder (FP16 on CUDA for sub-10ms encoding)
        model_kwargs = {"torch_dtype": torch.float16} if "cuda" in self.device else {}
        self.model = SentenceTransformer(
            model_name,
            device=self.device,
            model_kwargs=model_kwargs,
        )
        self.model.max_seq_length = 512

      # 2. Stage-2 Cross-Encoder Reranker (FP16 on CUDA for joint query-document attention)
        self.reranker: CrossEncoder | None = None
        if reranker_name:
            rerank_kwargs = {"torch_dtype": torch.float16} if "cuda" in self.device else {}
            self.reranker = CrossEncoder(
                reranker_name,
                device=self.device,
                max_length=512,
                model_kwargs=rerank_kwargs,
            )

        self.collection = self.client.get_or_create_collection(
            name="gym_coach_knowledge",
            metadata={"hnsw:space": "ip"},
        )

    @classmethod
    def strip_sources_footer(cls, markdown_text: str) -> str:
        """Strips trailing '## Sources' URL blocks to save ~45 prompt tokens per retrieved card."""
        return cls._RE_SOURCES_SECTION.sub("", markdown_text).strip()

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        embeddings = self.model.encode(
            texts,
            batch_size=self.batch_size,
            normalize_embeddings=True,
            show_progress_bar=False,
            convert_to_numpy=True,
        )
        return embeddings.tolist()

    def embed_query(self, query: str) -> list[float]:
        prefixed_query = f"{self.QUERY_INSTRUCTION}{query}"
        embedding = self.model.encode(
            prefixed_query,
            normalize_embeddings=True,
            show_progress_bar=False,
            convert_to_numpy=True,
        )
        return embedding.tolist()

    @classmethod
    def parse_markdown_document(cls, file_path: str, source_type: str) -> dict[str, Any] | None:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except OSError:
            return None

        id_match = cls._RE_ID.search(content)
        raw_id = (
            id_match.group(1).strip().upper()
            if id_match
            else os.path.splitext(os.path.basename(file_path))[0].upper()
        )

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
                "sha256": content_hash,
            },
        }

    def reconcile_and_index(self, directory_configs: list[tuple[str, str]]) -> dict[str, int]:
        disk_docs: dict[str, dict[str, Any]] = {}
        for dir_path, source_type in directory_configs:
            for fpath in glob.glob(os.path.join(dir_path, "*.md")):
                parsed = self.parse_markdown_document(fpath, source_type=source_type)
                if parsed:
                    disk_docs[parsed["id"]] = parsed

        existing = self.collection.get(include=["metadatas"])
        existing_ids = set(existing["ids"])
        existing_hashes = {
            doc_id: meta.get("sha256")
            for doc_id, meta in zip(existing["ids"], existing["metadatas"] or [])
            if meta
        }

        disk_ids = set(disk_docs.keys())
        to_delete = list(existing_ids - disk_ids)
        to_upsert_ids = [
            doc_id
            for doc_id, doc in disk_docs.items()
            if doc_id not in existing_hashes or existing_hashes[doc_id] != doc["metadata"]["sha256"]
        ]
        unchanged_count = len(disk_ids) - len(to_upsert_ids)

        if to_delete:
            self.collection.delete(ids=to_delete)

        if to_upsert_ids:
            for i in range(0, len(to_upsert_ids), self.batch_size):
                chunk_ids = to_upsert_ids[i : i + self.batch_size]
                chunk_docs = [disk_docs[doc_id]["document"] for doc_id in chunk_ids]
                chunk_metas = [disk_docs[doc_id]["metadata"] for doc_id in chunk_ids]
                chunk_embeddings = self.embed_documents(chunk_docs)
                self.collection.upsert(
                    ids=chunk_ids,
                    embeddings=chunk_embeddings,
                    documents=chunk_docs,
                    metadatas=chunk_metas,
                )

        return {
            "upserted": len(to_upsert_ids),
            "deleted": len(to_delete),
            "unchanged": unchanged_count,
            "total_active": self.collection.count(),
        }

    def ingest_all_corpora(
        self,
        injuries_dir: str = "rag_corpus/injuries",
        periodization_dir: str = "rag_corpus/periodization",
    ) -> dict[str, int]:
        return self.reconcile_and_index([
            (injuries_dir, "clinical_injury"),
            (periodization_dir, "periodization"),
        ])

    def query(
        self,
        query_text: str,
        n_results: int = 2,
        candidate_pool_size: int = 10,
        distance_threshold: float = 0.58,
        rerank_prob_threshold: float = 0.12,
        use_reranker: bool = True,
        where_filter: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Executes Two-Stage Retrieval:
          1. Dense HNSW lookup fetches top `candidate_pool_size` (K=10) with lenient tau_dense = 0.58.
          2. Cross-Encoder scores all (query, candidate_doc) pairs in a single FP16 batch and
             enforces a calibrated sigmoid probability safety gate (`rerank_prob_threshold`).
        """
        t0 = time.perf_counter()
        query_vector = self.embed_query(query_text)

        fetch_k = max(n_results, candidate_pool_size) if (use_reranker and self.reranker) else n_results
        raw_results = self.collection.query(
            query_embeddings=[query_vector],
            n_results=fetch_k,
            where=where_filter,
            include=["documents", "metadatas", "distances"],
        )
        t_hnsw = time.perf_counter()

        ids = raw_results.get("ids")
        distances = raw_results.get("distances")
        documents = raw_results.get("documents")
        metadatas = raw_results.get("metadatas")

        if not ids or not distances or not documents or not metadatas or not ids[0]:
            latency_ms = round((time.perf_counter() - t0) * 1000.0, 2)
            return {
                "status": "OUT_OF_DOMAIN",
                "min_distance": 2.0,
                "max_rerank_prob": 0.0,
                "latency_ms": latency_ms,
                "stage1_ms": round((t_hnsw - t0) * 1000.0, 2),
                "rerank_ms": 0.0,
                "results": [],
            }

        min_distance = float(distances[0][0])

        # Stage-1 Lenient Bi-Encoder Filter
        candidates = [
            {
                "id": doc_id,
                "document": self.strip_sources_footer(doc_text),
                "metadata": meta,
                "distance": round(float(dist), 4),
                "rerank_prob": 0.0,
            }
            for doc_id, doc_text, meta, dist in zip(ids[0], documents[0], metadatas[0], distances[0])
            if float(dist) <= distance_threshold
        ]

        if not candidates:
            latency_ms = round((time.perf_counter() - t0) * 1000.0, 2)
            return {
                "status": "OUT_OF_DOMAIN",
                "min_distance": round(min_distance, 4),
                "max_rerank_prob": 0.0,
                "latency_ms": latency_ms,
                "stage1_ms": round((t_hnsw - t0) * 1000.0, 2),
                "rerank_ms": 0.0,
                "results": [],
            }

       # Stage-2 Cross-Encoder Reranking & Calibrated OOD Safety Circuit Breaker
        t_rerank_start = time.perf_counter()
        if use_reranker and self.reranker is not None:
            pairs = [[query_text, c["document"]] for c in candidates]
            # Force raw logits via Identity() to avoid double-sigmoid compression
            raw_logits = self.reranker.predict(
                pairs,
                batch_size=len(pairs),
                show_progress_bar=False,
                activation_fn=torch.nn.Identity(),
                convert_to_numpy=True,
            )
            for c, logit in zip(candidates, raw_logits):
                val = float(logit)
                prob = 1.0 / (1.0 + math.exp(-max(min(val, 20.0), -20.0)))
                c["rerank_logit"] = round(val, 4)
                c["rerank_prob"] = round(prob, 4)

            candidates.sort(key=lambda x: x["rerank_prob"], reverse=True)
            max_rerank_prob = candidates[0]["rerank_prob"]
            rerank_ms = round((time.perf_counter() - t_rerank_start) * 1000.0, 2)

            if max_rerank_prob < rerank_prob_threshold:
                latency_ms = round((time.perf_counter() - t0) * 1000.0, 2)
                return {
                    "status": "OUT_OF_DOMAIN",
                    "min_distance": round(min_distance, 4),
                    "max_rerank_prob": max_rerank_prob,
                    "latency_ms": latency_ms,
                    "stage1_ms": round((t_hnsw - t0) * 1000.0, 2),
                    "rerank_ms": rerank_ms,
                    "results": [],
                }

            top_matches = [
                c for c in candidates[:n_results]
                if c["rerank_prob"] >= (rerank_prob_threshold * 0.5)
            ]
        else:
            top_matches = candidates[:n_results]
            max_rerank_prob = round(1.0 - min_distance, 4)
            rerank_ms = 0.0

        latency_ms = round((time.perf_counter() - t0) * 1000.0, 2)
        return {
            "status": "MATCH_FOUND",
            "min_distance": round(min_distance, 4),
            "max_rerank_prob": round(max_rerank_prob, 4),
            "latency_ms": latency_ms,
            "stage1_ms": round((t_hnsw - t0) * 1000.0, 2),
            "rerank_ms": rerank_ms,
            "results": top_matches,
        }