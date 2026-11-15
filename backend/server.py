# backend/server.py
import os
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

import httpx
import torch
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.agent_core.orchestrator import GymCoachOrchestrator
from backend.agent_core.vela_router import VelaSystemOneRouter
from backend.rag_engine.tools import ClinicalRAGTools
from backend.rag_engine.vector_store import RAGVectorStore

PROJECT_ROOT = Path(os.environ.get("PROJECT_ROOT", Path(__file__).resolve().parents[1]))
CHROMA_DB_DIR = os.environ.get("CHROMA_DB_DIR", str(PROJECT_ROOT / "data" / "chroma_db"))
COPROCESSOR_DEVICE = os.environ.get(
    "COPROCESSOR_DEVICE", "cuda:0" if torch.cuda.is_available() else "cpu"
)
VLLM_BASE_URL = os.environ.get("VLLM_BASE_URL", "http://127.0.0.1:8001/v1")
BASE_MODEL_NAME = os.environ.get("BASE_MODEL_NAME", "Qwen/Qwen2.5-7B-Instruct-AWQ")


class AppState:
    orchestrator: Optional[GymCoachOrchestrator] = None
    gpu_name: str = "cpu"
    sm_cap: tuple[int, int] = (0, 0)


state = AppState()


@asynccontextmanager
async def lifespan(app: FastAPI):
    t0 = time.perf_counter()
    os.makedirs(CHROMA_DB_DIR, exist_ok=True)

    if torch.cuda.is_available():
        state.gpu_name = torch.cuda.get_device_name(0)
        state.sm_cap = torch.cuda.get_device_capability(0)

    print(
        f"🚀 [Gateway Lifespan] Loading Co-Processor Suite on device='{COPROCESSOR_DEVICE}' "
        f"(Host GPU: {state.gpu_name})..."
    )

    store = RAGVectorStore(persist_directory=CHROMA_DB_DIR, device=COPROCESSOR_DEVICE)
    if store.collection.count() != 40:
        print("📦 Reconciling 40 clinical injury protocols into ChromaDB...")
        store.reconcile_and_index([
            (str(PROJECT_ROOT / "rag_corpus" / "injuries"), "clinical_injury"),
        ])

    rag_tools = ClinicalRAGTools(vector_store=store, device=COPROCESSOR_DEVICE)
    router = VelaSystemOneRouter(device=COPROCESSOR_DEVICE)

    state.orchestrator = GymCoachOrchestrator(
        vllm_base_url=VLLM_BASE_URL,
        base_model_name=BASE_MODEL_NAME,
        project_root=PROJECT_ROOT,
        rag_tools=rag_tools,
        router=router,
        coprocessor_device=COPROCESSOR_DEVICE,
        router_concurrency=3,
        rag_concurrency=2,
    )

    # Attempt Radix Prefix Cache & Triton Sampler Warmup if vLLM upstream is reachable
    try:
        warmup_msgs = state.orchestrator.build_tiered_messages(
            dynamic_turn_prompt="Warmup probe."
        )
        r = httpx.post(
            f"{VLLM_BASE_URL}/chat/completions",
            json={
                "model": BASE_MODEL_NAME,
                "messages": warmup_msgs,
                "max_tokens": 2,
                "temperature": 0.1,
            },
            timeout=30.0,
        )
        if r.status_code == 200:
            print("🔥 Pre-warmed upstream vLLM Tier-1 Radix Prefix Cache & Sampling Kernels.")
    except Exception as exc:
        print(f"ℹ️ Upstream vLLM warmup skipped during gateway boot ({exc}).")

    boot_s = round(time.perf_counter() - t0, 2)
    print(f"✅ [Gateway Ready] Co-Processor & Orchestrator live in {boot_s}s.")
    yield


app = FastAPI(title="AI Gym Coach v2.5 Gateway", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    query: str
    session_user_profile: Optional[str] = None


@app.get("/health")
async def health():
    use_cuda = torch.cuda.is_available() and COPROCESSOR_DEVICE.startswith("cuda")
    alloc_mb = round(torch.cuda.memory_allocated(0) / (1024**2), 2) if use_cuda else 0.0
    res_mb = round(torch.cuda.memory_reserved(0) / (1024**2), 2) if use_cuda else 0.0
    return {
        "status": "healthy",
        "host_gpu": state.gpu_name,
        "compute_capability": f"sm_{state.sm_cap[0]}{state.sm_cap[1]}",
        "coprocessor_device": COPROCESSOR_DEVICE,
        "router_precision": f"fp32_master_{state.orchestrator.router.autocast_dtype}_autocast",
        "coprocessor_allocated_mb": alloc_mb,
        "coprocessor_reserved_mb": res_mb,
        "router_concurrency_limit": 3,
        "rag_concurrency_limit": 2,
        "indexed_clinical_cards": state.orchestrator.tools.store.collection.count(),
        "catalog_size": len(state.orchestrator.catalog_lookup),
        "vllm_upstream": VLLM_BASE_URL,
    }


@app.post("/chat")
async def chat_endpoint(req: ChatRequest):
    res = await state.orchestrator.execute(
        user_query=req.query,
        session_user_profile=req.session_user_profile,
    )
    return res.model_dump()