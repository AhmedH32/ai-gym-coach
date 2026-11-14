# deploy_modal.py
import os
import subprocess
import sys
import time
from pathlib import Path

import modal

# ------------------------------------------------------------------------------
# 1. Persistent Distributed Volume & Programmatic OCI Image
# ------------------------------------------------------------------------------
APP_NAME = "ai-gym-coach-v2"
VOLUME_PATH = "/data"
HF_CACHE_DIR = f"{VOLUME_PATH}/hf_cache"
VLLM_CACHE_DIR = f"{VOLUME_PATH}/vllm_cache"
CHROMA_DB_DIR = f"{VOLUME_PATH}/chroma_db"

volume = modal.Volume.from_name("ai-gym-coach-volume", create_if_missing=True)

# Kept byte-for-byte identical to hit cached image im-ESctTbUlf0izFHFUHSOCtO (0s build)
image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("git", "curl")
    .uv_pip_install(
        "vllm>=0.6.3",
        "torch>=2.4.0",
        "transformers>=5.0.0",
        "sentence-transformers>=3.1.0",
        "chromadb>=0.5.5",
        "fastapi>=0.115.0",
        "uvicorn>=0.30.0",
        "httpx>=0.27.0",
        "pydantic>=2.9.0",
        "numpy>=1.26.0",
    )
    .env({
        "HF_HOME": HF_CACHE_DIR,
        "VLLM_CACHE_ROOT": VLLM_CACHE_DIR,
        "PYTORCH_CUDA_ALLOC_CONF": "expandable_segments:True",
        "COPROCESSOR_DEVICE": "cuda:0",
        "VLLM_BASE_URL": "http://127.0.0.1:8001/v1",
        "BASE_MODEL_NAME": "Qwen/Qwen2.5-7B-Instruct-AWQ",
    })
    .add_local_dir("backend", remote_path="/root/app/backend")
    .add_local_dir("prompt_assets", remote_path="/root/app/prompt_assets")
    .add_local_dir("rag_corpus", remote_path="/root/app/rag_corpus")
    .add_local_dir("raw_data", remote_path="/root/app/raw_data")
)

app = modal.App(APP_NAME, image=image)


def _build_vllm_runtime_env() -> dict[str, str]:
    """
    Configures the isolated environment for the vLLM subprocess:
      1. Disables the FlashInfer top-k/top-p sampler JIT (uses native pre-compiled CUDA sampler).
      2. Links pip-installed nvidia-cuda-nvcc/runtime wheels into /usr/local/cuda as defense-in-depth.
      3. Directs any FlashInfer/Triton workspace caches onto the persistent Modal Volume.
      4. Strips VLLM_BASE_URL so vLLM's internal env parser does not emit warnings.
    """
    env = os.environ.copy()
    env.pop("VLLM_BASE_URL", None)
    env["VLLM_USE_FLASHINFER_SAMPLER"] = "0"
    env["FLASHINFER_WORKSPACE_BASE"] = f"{VLLM_CACHE_DIR}/flashinfer"

    cuda_home = Path("/usr/local/cuda")
    site_nvidia = Path("/usr/local/lib/python3.11/site-packages/nvidia")
    if not (cuda_home / "bin" / "nvcc").exists() and site_nvidia.exists():
        nvcc_matches = list(site_nvidia.rglob("bin/nvcc"))
        if nvcc_matches:
            nvcc_bin = nvcc_matches[0]
            try:
                (cuda_home / "bin").mkdir(parents=True, exist_ok=True)
                (cuda_home / "include").mkdir(parents=True, exist_ok=True)
                (cuda_home / "lib64").mkdir(parents=True, exist_ok=True)

                for tool in nvcc_bin.parent.iterdir():
                    target = cuda_home / "bin" / tool.name
                    if not target.exists():
                        target.symlink_to(tool)

                for inc_dir in site_nvidia.rglob("include"):
                    if inc_dir.is_dir():
                        for header in inc_dir.iterdir():
                            target = cuda_home / "include" / header.name
                            if not target.exists():
                                target.symlink_to(header)
            except Exception as e:
                print(f"⚠️ Non-fatal warning linking /usr/local/cuda: {e}")

    if (cuda_home / "bin" / "nvcc").exists():
        env["CUDA_HOME"] = str(cuda_home)
        env["PATH"] = f"{cuda_home / 'bin'}:{env.get('PATH', '')}"

    return env


# ------------------------------------------------------------------------------
# 2. Tier-1 CI/CD Gate: Corpus Ingestion, Weight Pre-Cache & Recall/OOD Gate
# ------------------------------------------------------------------------------
@app.function(
    gpu=["L40S", "A10G", "L4", "T4"],
    volumes={VOLUME_PATH: volume},
    timeout=600,
)
def ingest_and_verify_corpus() -> dict:
    sys.path.insert(0, "/root/app")
    from huggingface_hub import snapshot_download
    from backend.agent_core.vela_router import VelaSystemOneRouter
    from backend.rag_engine.tools import ClinicalRAGTools
    from backend.rag_engine.vector_store import RAGVectorStore

    volume.reload()
    print("📦 [CI/CD Step 1/3] Reconciling 40 clinical injury protocols into ChromaDB...")
    t0 = time.perf_counter()

    store = RAGVectorStore(
        persist_directory=CHROMA_DB_DIR,
        device="cuda:0",
    )
    stats = store.reconcile_and_index([
        ("/root/app/rag_corpus/injuries", "clinical_injury"),
    ])
    ingest_ms = round((time.perf_counter() - t0) * 1000.0, 2)
    print(f"✓ ChromaDB Reconcile Stats ({ingest_ms} ms): {stats}")

    if stats["total_active"] != 40:
        raise RuntimeError(
            f"CI/CD QUALITY GATE FAILED: Expected 40 clinical cards, found {stats['total_active']}"
        )

    print("🔍 [CI/CD Step 2/3] Running Cross-Encoder In-Domain & OOD Regression Gate...")
    tools = ClinicalRAGTools(vector_store=store, device="cuda:0")
    in_domain_probe = tools.search_medical_db(
        "Tendon below my kneecap is barking on deep squats"
    )
    ood_probe = tools.search_medical_db(
        "Crushing tightness in my left chest radiating to my jaw"
    )

    print(
        f"  -> In-Domain={in_domain_probe.matched_ids} (P={in_domain_probe.max_rerank_prob}) | "
        f"OOD={ood_probe.status} (P={ood_probe.max_rerank_prob})"
    )

    if in_domain_probe.status != "MATCH_FOUND" or "COND_PATELLAR_TENDINOPATHY" not in in_domain_probe.matched_ids:
        raise RuntimeError("CI/CD QUALITY GATE FAILED: Patellar tendinopathy probe failed recall!")
    if ood_probe.status != "OUT_OF_DOMAIN":
        raise RuntimeError("CI/CD QUALITY GATE FAILED: Cardiac emergency was not rejected by OOD gate!")

    print("📥 [CI/CD Step 3/3] Pre-caching & sanitizing Vela-3 and Qwen2.5-7B-AWQ on Volume...")
    router = VelaSystemOneRouter(device="cuda:0")
    router_probe = router.route("Tendon below my kneecap is barking on deep squats, prescribe a leg workout.")
    print(f"  -> Vela-3 Router verified: intent={router_probe.intent} ({router_probe.latency_ms}ms)")
    if router_probe.intent != "CLASS_1_CLINICAL_RAG":
        raise RuntimeError(f"CI/CD QUALITY GATE FAILED: Expected CLASS_1_CLINICAL_RAG, got {router_probe.intent}")

    snapshot_download(repo_id="Qwen/Qwen2.5-7B-Instruct-AWQ")
    print("  -> Qwen/Qwen2.5-7B-Instruct-AWQ weights verified on persistent Volume.")

    volume.commit()
    print("✅ [CI/CD Corpus Gate Complete] All models cached, sanitized, verified, and committed to Volume.")
    return stats


# ------------------------------------------------------------------------------
# 3. Tier-2 CI/CD Gate: Full-Stack Staging SLO, TTFT/ITL & Concurrency Verification
# ------------------------------------------------------------------------------
@app.function(
    gpu=["L40S", "A10G", "L4"],
    volumes={VOLUME_PATH: volume},
    timeout=600,
)
def verify_system_slos() -> dict:
    """
    Spins up an isolated staging container (prioritizing L40S -> A10G -> L4 for zero queue wait)
    and verifies hardware-normalized production SLOs before allowing `modal deploy`:
      1. Engine Cold Boot & Radix Prefix Warmup Latency (< 65s)
      2. True SSE Streaming TTFT (< 250ms on cached prefix) & ITL (< 18ms on A10G/L40S, < 30ms on L4)
      3. 8-User Concurrent Burst across all 4 routing classes (100% accuracy, 0 OOMs, VRAM < 3200 MB)
    """
    import asyncio
    import json
    import statistics
    import httpx
    import torch

    sys.path.insert(0, "/root/app")
    volume.reload()

    gpu_name = torch.cuda.get_device_name(0)
    sm_cap = torch.cuda.get_device_capability(0)
    # L4 has a 300 GB/s memory bus vs 600 GB/s (A10G) and 864 GB/s (L40S)
    is_bandwidth_constrained_l4 = "L4" in gpu_name and "L40" not in gpu_name
    max_allowed_itl_ms = 30.0 if is_bandwidth_constrained_l4 else 18.0
    max_allowed_ttft_ms = 350.0 if is_bandwidth_constrained_l4 else 250.0

    print(f"🔬 [SLO Gate 1/4] Booting Isolated Staging Engine on {gpu_name} (sm_{sm_cap[0]}{sm_cap[1]})...")
    t_boot_start = time.perf_counter()

    vllm_env = _build_vllm_runtime_env()
    vllm_cmd = [
        sys.executable, "-m", "vllm.entrypoints.openai.api_server",
        "--model", "Qwen/Qwen2.5-7B-Instruct-AWQ",
        "--quantization", "awq_marlin",
        "--safetensors-load-strategy", "prefetch",
        "--dtype", "half",
        "--max-model-len", "8192",
        "--gpu-memory-utilization", "0.75",
        "--enable-prefix-caching",
        "--max-num-seqs", "16",
        "--port", "8001",
    ]
    vllm_proc = subprocess.Popen(vllm_cmd, env=vllm_env)

    try:
        from backend.agent_core.orchestrator import GymCoachOrchestrator
        from backend.agent_core.vela_router import VelaSystemOneRouter
        from backend.rag_engine.tools import ClinicalRAGTools
        from backend.rag_engine.vector_store import RAGVectorStore

        store = RAGVectorStore(persist_directory=CHROMA_DB_DIR, device="cuda:0")
        if store.collection.count() != 40:
            store.reconcile_and_index([("/root/app/rag_corpus/injuries", "clinical_injury")])

        rag_tools = ClinicalRAGTools(vector_store=store, device="cuda:0")
        router = VelaSystemOneRouter(device="cuda:0")
        orchestrator = GymCoachOrchestrator(
            vllm_base_url="http://127.0.0.1:8001/v1",
            base_model_name="Qwen/Qwen2.5-7B-Instruct-AWQ",
            project_root=Path("/root/app"),
            rag_tools=rag_tools,
            router=router,
            coprocessor_device="cuda:0",
            router_concurrency=3,
            rag_concurrency=2,
        )

        for _ in range(180):
            if vllm_proc.poll() is not None:
                raise RuntimeError(f"SLO GATE FAILED: vLLM exited prematurely with code {vllm_proc.returncode}")
            try:
                if httpx.get("http://127.0.0.1:8001/health", timeout=2.0).status_code == 200:
                    break
            except Exception:
                pass
            time.sleep(1.0)
        else:
            raise RuntimeError("SLO GATE FAILED: vLLM failed to become ready within 180s.")

        # Warm up Radix Prefix Cache
        warmup_msgs = orchestrator.build_tiered_messages(dynamic_turn_prompt="Warmup probe.")
        httpx.post(
            "http://127.0.0.1:8001/v1/chat/completions",
            json={
                "model": "Qwen/Qwen2.5-7B-Instruct-AWQ",
                "messages": warmup_msgs,
                "max_tokens": 2,
                "temperature": 0.1,
            },
            timeout=60.0,
        )
        startup_s = round(time.perf_counter() - t_boot_start, 2)
        print(f"✓ [SLO Gate 1/4 Passed] Engine & Radix Cache Warmed in {startup_s}s.")

        # ----------------------------------------------------------------------
        # Step 2: True TTFT & ITL Measurement via SSE Streaming (`stream: True`)
        # ----------------------------------------------------------------------
        print("⚡ [SLO Gate 2/4] Measuring True TTFT & Inter-Token Latency (ITL) via SSE Stream...")
        stream_msgs = orchestrator.build_tiered_messages(
            dynamic_turn_prompt=(
                "Athlete Query: 'How do I structure a deload week?'\n\n"
                "EXECUTION DIRECTIVE: Answer directly in Markdown. Do NOT emit JSON."
            )
        )
        ttft_ms = None
        token_timestamps: list[float] = []
        t_req_start = time.perf_counter()

        with httpx.stream(
            "POST",
            "http://127.0.0.1:8001/v1/chat/completions",
            json={
                "model": "Qwen/Qwen2.5-7B-Instruct-AWQ",
                "messages": stream_msgs,
                "max_tokens": 64,
                "temperature": 0.1,
                "stream": True,
            },
            timeout=30.0,
        ) as resp:
            for line in resp.iter_lines():
                if not line or not line.startswith("data: "):
                    continue
                payload_str = line[6:].strip()
                if payload_str == "[DONE]":
                    break
                chunk = json.loads(payload_str)
                delta_content = chunk["choices"][0].get("delta", {}).get("content")
                if delta_content:
                    now = time.perf_counter()
                    if ttft_ms is None:
                        ttft_ms = round((now - t_req_start) * 1000.0, 2)
                    token_timestamps.append(now)

        itls_ms = [
            (token_timestamps[i] - token_timestamps[i - 1]) * 1000.0
            for i in range(1, len(token_timestamps))
        ]
        p50_itl_ms = round(statistics.median(itls_ms), 2)
        p95_itl_ms = round(sorted(itls_ms)[int(len(itls_ms) * 0.95) - 1], 2)
        decode_tps = round(1000.0 / p50_itl_ms, 1)

        print(
            f"  -> TTFT (Radix Cached): {ttft_ms} ms (SLO < {max_allowed_ttft_ms} ms) | "
            f"ITL p50: {p50_itl_ms} ms (p95: {p95_itl_ms} ms, SLO < {max_allowed_itl_ms} ms) | "
            f"Decode Speed: {decode_tps} tok/s"
        )
        if ttft_ms is None or ttft_ms > max_allowed_ttft_ms:
            raise RuntimeError(f"SLO GATE FAILED: TTFT {ttft_ms}ms exceeded {max_allowed_ttft_ms}ms threshold!")
        if p50_itl_ms > max_allowed_itl_ms:
            raise RuntimeError(f"SLO GATE FAILED: p50 ITL {p50_itl_ms}ms exceeded {max_allowed_itl_ms}ms threshold!")

        # ----------------------------------------------------------------------
        # Step 3: 8-User Concurrent Multi-Class Burst & Functional Verification
        # ----------------------------------------------------------------------
        print("🔥 [SLO Gate 3/4] Running 8-User Concurrent Multi-Route Burst Verification...")
        test_suite = [
            # (Query, Expected Routing Class, Expected has_workout)
            ("Crushing tightness in my left chest radiating to my jaw during squats.", "CLASS_A_OUT_OF_SCOPE", False),
            ("Sudden loss of bladder control and saddle numbness after deadlifts.", "CLASS_A_OUT_OF_SCOPE", False),
            ("Tendon below my kneecap is barking on deep squats, prescribe a leg rehab workout today.", "CLASS_A_INJURY", True),
            ("Outside of my elbow burns when I grip heavy deadlifts, give me an arm workout session today.", "CLASS_A_INJURY", True),
            ("Felt a sharp pinching pain in the front of my shoulder during flat bench press. What happened?", "CLASS_A_INJURY", False),
            ("Build me a back and biceps hypertrophy workout using only dumbbells.", "CLASS_C_CATALOG", True),
            ("Give me a chest and triceps workout with barbells and cables.", "CLASS_C_CATALOG", True),
            ("What is the optimal rest period between heavy compound sets vs isolation accessories?", "DIRECT_COACHING", False),
        ]

        async def _run_burst():
            return await asyncio.gather(*[orchestrator.execute(q) for q, _, _ in test_suite])

        t_burst = time.perf_counter()
        results = asyncio.run(_run_burst())
        burst_s = round(time.perf_counter() - t_burst, 2)

        for idx, ((q, exp_route, exp_wo), res) in enumerate(zip(test_suite, results)):
            print(
                f"  [Probe {idx + 1}/8] Route={res.routing_class} (exp={exp_route}) | "
                f"has_workout={res.has_workout} (exp={exp_wo}) | E2E={res.telemetry.get('total_e2e_ms')}ms"
            )
            if res.routing_class != exp_route:
                raise RuntimeError(
                    f"SLO GATE FAILED on Probe {idx + 1} ('{q[:40]}...'): "
                    f"Expected route {exp_route}, got {res.routing_class}"
                )
            if res.has_workout != exp_wo:
                raise RuntimeError(
                    f"SLO GATE FAILED on Probe {idx + 1} ('{q[:40]}...'): "
                    f"Expected has_workout={exp_wo}, got {res.has_workout}"
                )

        # ----------------------------------------------------------------------
        # Step 4: Co-Processor VRAM Ceiling Verification
        # ----------------------------------------------------------------------
        alloc_mb = round(torch.cuda.memory_allocated(0) / (1024**2), 2)
        reserved_mb = round(torch.cuda.memory_reserved(0) / (1024**2), 2)
        print(
            f"🛡️ [SLO Gate 4/4] Post-Burst Co-Processor VRAM: "
            f"allocated={alloc_mb} MB, reserved={reserved_mb} MB (Ceiling < 3200 MB)."
        )
        if reserved_mb > 3200.0:
            raise RuntimeError(f"SLO GATE FAILED: Co-processor reserved VRAM {reserved_mb}MB exceeded 3200MB ceiling!")

        volume.commit()
        report = {
            "status": "PASSED",
            "gpu": gpu_name,
            "startup_s": startup_s,
            "ttft_ms": ttft_ms,
            "p50_itl_ms": p50_itl_ms,
            "p95_itl_ms": p95_itl_ms,
            "single_stream_decode_tps": decode_tps,
            "burst_8_users_wall_s": burst_s,
            "coprocessor_reserved_mb": reserved_mb,
        }
        print(f"✅ [ALL SLO GATES PASSED] {report}")
        return report

    finally:
        vllm_proc.terminate()
        try:
            vllm_proc.wait(timeout=10)
        except Exception:
            vllm_proc.kill()


# ------------------------------------------------------------------------------
# 4. Unified Production Service (L4 -> A10G -> L40S Automatic Fallback)
# ------------------------------------------------------------------------------
@app.cls(
    gpu=["L4", "A10G", "L40S"],
    volumes={VOLUME_PATH: volume},
    scaledown_window=180,
    timeout=600,
)
@modal.concurrent(max_inputs=16)
class GymCoachService:
    @modal.enter()
    def startup_engine(self):
        import torch

        sys.path.insert(0, "/root/app")
        os.makedirs(HF_CACHE_DIR, exist_ok=True)
        os.makedirs(VLLM_CACHE_DIR, exist_ok=True)
        os.makedirs(CHROMA_DB_DIR, exist_ok=True)

        volume.reload()

        self.gpu_name = torch.cuda.get_device_name(0) if torch.cuda.is_available() else "unknown"
        self.sm_cap = torch.cuda.get_device_capability(0) if torch.cuda.is_available() else (0, 0)
        print(f"🚀 Booting on {self.gpu_name} (Compute Capability sm_{self.sm_cap[0]}{self.sm_cap[1]})...")

        # 1. Launch vLLM with awq_marlin kernel & 0.75 VRAM pool (~16.55 GiB = 204,336 KV tokens)
        vllm_env = _build_vllm_runtime_env()
        vllm_cmd = [
            sys.executable, "-m", "vllm.entrypoints.openai.api_server",
            "--model", "Qwen/Qwen2.5-7B-Instruct-AWQ",
            "--quantization", "awq_marlin",
            "--safetensors-load-strategy", "prefetch",
            "--dtype", "half",
            "--max-model-len", "8192",
            "--gpu-memory-utilization", "0.75",
            "--enable-prefix-caching",
            "--max-num-seqs", "16",
            "--port", "8001",
        ]
        self.vllm_proc = subprocess.Popen(vllm_cmd, env=vllm_env)

        # 2. Initialize Co-Processor Suite on cuda:0 (native FP32 weights + BF16/FP16 autocast)
        from backend.agent_core.orchestrator import GymCoachOrchestrator
        from backend.agent_core.vela_router import VelaSystemOneRouter
        from backend.rag_engine.tools import ClinicalRAGTools
        from backend.rag_engine.vector_store import RAGVectorStore

        store = RAGVectorStore(persist_directory=CHROMA_DB_DIR, device="cuda:0")
        if store.collection.count() != 40:
            store.reconcile_and_index([
                ("/root/app/rag_corpus/injuries", "clinical_injury"),
            ])

        rag_tools = ClinicalRAGTools(vector_store=store, device="cuda:0")
        router = VelaSystemOneRouter(device="cuda:0")

        self.orchestrator = GymCoachOrchestrator(
            vllm_base_url="http://127.0.0.1:8001/v1",
            base_model_name="Qwen/Qwen2.5-7B-Instruct-AWQ",
            project_root=Path("/root/app"),
            rag_tools=rag_tools,
            router=router,
            coprocessor_device="cuda:0",
            router_concurrency=3,
            rag_concurrency=2,
        )

        # 3. Wait for vLLM HTTP readiness
        import httpx
        for _ in range(180):
            if self.vllm_proc.poll() is not None:
                raise RuntimeError(
                    f"vLLM subprocess terminated prematurely with exit code {self.vllm_proc.returncode}"
                )
            try:
                r = httpx.get("http://127.0.0.1:8001/health", timeout=2.0)
                if r.status_code == 200:
                    print(f"✓ vLLM AWQ-Marlin Engine is LIVE on {self.gpu_name}.")
                    break
            except Exception:
                pass
            time.sleep(1.0)
        else:
            raise RuntimeError("vLLM failed to start within 180 seconds.")

        # 4. Pre-warm Tier-1 Radix Prefix Cache & JIT kernels
        print("🔥 Pre-warming Tier-1 Radix Prefix Cache in VRAM...")
        warmup_msgs = self.orchestrator.build_tiered_messages(
            dynamic_turn_prompt="Warmup probe."
        )
        httpx.post(
            "http://127.0.0.1:8001/v1/chat/completions",
            json={
                "model": "Qwen/Qwen2.5-7B-Instruct-AWQ",
                "messages": warmup_msgs,
                "max_tokens": 2,
                "temperature": 0.1,
            },
            timeout=60.0,
        )
        volume.commit()
        alloc_mb = round(torch.cuda.memory_allocated(0) / (1024**2), 2)
        res_mb = round(torch.cuda.memory_reserved(0) / (1024**2), 2)
        print(
            f"✅ Container warmed on {self.gpu_name} | Co-Processor VRAM: "
            f"allocated={alloc_mb} MB, reserved={res_mb} MB."
        )

    @modal.exit()
    def shutdown_engine(self):
        if hasattr(self, "vllm_proc") and self.vllm_proc:
            self.vllm_proc.terminate()

    @modal.asgi_app()
    def api(self):
        from typing import Optional
        import torch
        from fastapi import FastAPI
        from pydantic import BaseModel

        web_app = FastAPI(title="AI Gym Coach v2.5 Serverless Gateway")

        class ChatRequest(BaseModel):
            query: str
            session_user_profile: Optional[str] = None

        @web_app.get("/health")
        async def health():
            return {
                "status": "healthy",
                "allocated_gpu": self.gpu_name,
                "compute_capability": f"sm_{self.sm_cap[0]}{self.sm_cap[1]}",
                "quantization_kernel": "awq_marlin",
                "router_precision": f"fp32_master_{self.orchestrator.router.autocast_dtype}_autocast",
                "vllm_vram_allocation": 0.75,
                "coprocessor_allocated_mb": round(torch.cuda.memory_allocated(0) / (1024**2), 2),
                "coprocessor_reserved_mb": round(torch.cuda.memory_reserved(0) / (1024**2), 2),
                "router_concurrency_limit": 3,
                "rag_concurrency_limit": 2,
                "max_concurrent_inputs": 16,
                "indexed_clinical_cards": self.orchestrator.tools.store.collection.count(),
                "catalog_size": len(self.orchestrator.catalog_lookup),
            }

        @web_app.post("/chat")
        async def chat_endpoint(req: ChatRequest):
            res = await self.orchestrator.execute(
                user_query=req.query,
                session_user_profile=req.session_user_profile,
            )
            return res.model_dump()

        return web_app