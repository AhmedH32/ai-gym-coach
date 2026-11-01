# backend/server.py
import os
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.agent_core.orchestrator import GymCoachOrchestrator, OrchestratorResponse

app = FastAPI(title="AI Gym Coach Agent Gateway (Vela-3 + AWQ)", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    query: str
    session_user_profile: Optional[str] = None


# Instantiate Orchestrator singleton
orchestrator = GymCoachOrchestrator(
    vllm_base_url=os.getenv("VLLM_BASE_URL", "http://127.0.0.1:8001/v1"),
    base_model_name=os.getenv("BASE_MODEL_NAME", "Qwen/Qwen2.5-7B-Instruct-AWQ"),
    adapter_model_name=os.getenv("ADAPTER_NAME", "unused_in_system1"),
    project_root=Path(__file__).resolve().parent.parent,
    coprocessor_device=os.getenv("COPROCESSOR_DEVICE", None),
)


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "catalog_size": len(orchestrator.catalog_lookup),
        "router_model": "vllm-sr/vela3-fast",
        "coprocessor_device": orchestrator.router.device,
        "rag_device": orchestrator.tools.store.device,
        "base_model": orchestrator.base_model,
        "adapter_model": orchestrator.adapter_model,
    }


@app.post("/api/v1/chat", response_model=OrchestratorResponse)
async def chat_endpoint(request: QueryRequest):
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
    try:
        return await orchestrator.execute(
            user_query=request.query,
            session_user_profile=request.session_user_profile,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)