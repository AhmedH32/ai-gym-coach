# syntax=docker/dockerfile:1
# ------------------------------------------------------------------------------
# AI Gym Coach v2.5 — Co-Processor & Orchestrator Gateway Image
# Base: Official PyTorch 2.15.0 + CUDA 13.2 + cuDNN 9 Runtime
# ------------------------------------------------------------------------------
FROM pytorch/pytorch:2.15.0-cuda13.2-cudnn9-runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PROJECT_ROOT=/app \
    HF_HOME=/data/hf_cache \
    CHROMA_DB_DIR=/data/chroma_db \
    PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True"

WORKDIR /app

# Layer 1: System dependencies (chained with apt cache cleanup in a single layer)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Layer 2: Python ML & ASGI dependencies (cached across code edits)
RUN pip install --break-system-packages --upgrade pip && pip install --break-system-packages \
    "transformers>=5.0.0" \
    "sentence-transformers>=3.1.0" \
    "chromadb>=0.5.5" \
    "fastapi>=0.115.0" \
    "uvicorn[standard]>=0.30.0" \
    "httpx>=0.27.0" \
    "pydantic>=2.9.0" \
    "numpy>=1.26.0" \
    "huggingface-hub>=0.25.0"


# Layer 3: Static Domain Corpora & Exercise Catalog
COPY raw_data/ /app/raw_data/
COPY prompt_assets/ /app/prompt_assets/
COPY rag_corpus/ /app/rag_corpus/

# Layer 4: Application Source Code (placed last so code edits rebuild in <1s)
COPY backend/ /app/backend/

ENV HF_HUB_DISABLE_XET=1 \
    HF_HUB_ETAG_TIMEOUT=30 \
    HF_HUB_DOWNLOAD_TIMEOUT=60

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD curl -f http://127.0.0.1:8000/health || exit 1

CMD ["uvicorn", "backend.server:app", "--host", "0.0.0.0", "--port", "8000"]