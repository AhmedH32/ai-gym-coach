# backend/server.py

import os
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.agent_core.orchestrator import GymCoachOrchestrator, OrchestratorResponse

app = FastAPI(title="AI Gym Coach Agent Gateway", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    query: str

# Instantiate Orchestrator (singleton)
orchestrator = GymCoachOrchestrator(
    vllm_base_url=os.getenv("VLLM_BASE_URL", "http://localhost:8001/v1"),
    adapter_model_name=os.getenv("ADAPTER_NAME", "gym_adapter"),
    base_model_name=os.getenv("BASE_MODEL_NAME", "Qwen/Qwen2.5-7B-Instruct"),
    project_root=Path(__file__).resolve().parent.parent
)

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "catalog_size": len(orchestrator.catalog_lookup),
        "adapter_model": orchestrator.adapter_model,
        "base_model": orchestrator.base_model
    }

@app.post("/api/v1/chat", response_model=OrchestratorResponse)
async def chat_endpoint(request: QueryRequest):
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
    try:
        response = await orchestrator.execute(request.query)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)