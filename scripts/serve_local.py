"""
AI Gym Coach — Local High-Throughput Inference & Gateway Orchestrator
Spawns quantized vLLM model serving and FastAPI gateway with automated 
weight retrieval, dual-mode networking (LAN / ngrok), and clean CUDA process lifecycle management.
"""

import argparse
import getpass
import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path
import requests

HF_LORA_REPO = "ahmedhassanM/qwen2.5-7b-gym-coach-lora"


def parse_args():
    parser = argparse.ArgumentParser(
        description="Launch local vLLM inference engine and FastAPI gateway."
    )
    # Hardware & VRAM Configuration
    parser.add_argument(
        "--gpu-util",
        type=float,
        default=0.85,
        help="Fraction of GPU VRAM to reserve for vLLM (default: 0.85).",
    )
    parser.add_argument(
        "--max-model-len",
        type=int,
        default=16384,
        help="Max sequence context length (e.g., 4096 for 8-12GB VRAM, 16384 for 16GB, 32768 for 24GB+).",
    )
    parser.add_argument(
        "--quantization",
        type=str,
        default="bitsandbytes",
        choices=["bitsandbytes", "awq", "gptq", "none"],
        help="Quantization backend (default: bitsandbytes 4-bit NF4).",
    )
    # Network Endpoints & Ports
    parser.add_argument(
        "--gateway-port",
        type=int,
        default=8000,
        help="Port for the FastAPI intent triage gateway (default: 8000).",
    )
    parser.add_argument(
        "--vllm-port",
        type=int,
        default=8001,
        help="Internal port for the vLLM OpenAI server (default: 8001).",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Binding IP interface (default: 0.0.0.0).",
    )
    # Public Tunneling
    parser.add_argument(
        "--ngrok",
        action="store_true",
        help="Create a public anycast HTTPS tunnel via ngrok (bypasses Wi-Fi isolation).",
    )
    parser.add_argument(
        "--ngrok-domain",
        type=str,
        default="",
        help="Optional static ngrok domain (leave blank for free random URL).",
    )
    # Model Artifact Paths
    parser.add_argument(
        "--base-model",
        type=str,
        default="Qwen/Qwen2.5-7B-Instruct",
        help="Base model identifier from Hugging Face Hub.",
    )
    parser.add_argument(
        "--adapter-dir",
        type=str,
        default="ml_pipeline/qwen2.5_gym_adapter",
        help="Local path to LoRA adapter weights. Auto-pulls from HF Hub if not present.",
    )
    return parser.parse_args()


def resolve_adapter(target_dir: Path) -> Path:
    """Verifies local LoRA adapter presence or downloads it from Hugging Face Hub."""
    if (target_dir / "adapter_config.json").exists():
        print(f"✓ Found local adapter at: {target_dir.resolve()}")
        return target_dir.resolve()

    print(f"Local adapter not found at '{target_dir}'.")
    print(f"Downloading weights directly from Hugging Face Hub: {HF_LORA_REPO}...")
    from huggingface_hub import snapshot_download

    download_dir = snapshot_download(repo_id=HF_LORA_REPO)
    print(f"✓ Adapter weights cached to: {download_dir}")
    return Path(download_dir).resolve()


def get_local_ip() -> str:
    """Detects local LAN IPv4 address for same-network device routing."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


def main():
    args = parse_args()
    project_root = Path(__file__).resolve().parent.parent
    adapter_path = resolve_adapter(project_root / args.adapter_dir)

    print("\n" + "=" * 78)
    print(" AI GYM COACH — HIGH-THROUGHPUT LOCAL SERVING ENGINE")
    print(f"  * Base Model:       {args.base_model}")
    print(f"  * LoRA Weights:     {adapter_path.name}")
    print(f"  * Quantization:     {args.quantization} (4-bit)")
    print(f"  * Max Context:      {args.max_model_len} tokens")
    print(f"  * VRAM Reserve:     {int(args.gpu_util * 100)}%")
    print(f"  * Gateway Port:     {args.gateway_port}")
    print(f"  * vLLM Port:        {args.vllm_port}")
    print("=" * 78 + "\n")

    # Construct vLLM execution command
    vllm_cmd = [
        sys.executable,
        "-m",
        "vllm.entrypoints.openai.api_server",
        "--model",
        args.base_model,
        "--host",
        "127.0.0.1",
        "--port",
        str(args.vllm_port),
        "--dtype",
        "half",
        "--gpu-memory-utilization",
        str(args.gpu_util),
        "--max-model-len",
        str(args.max_model_len),
        "--enable-prefix-caching",
        "--enable-lora",
        "--max-lora-rank",
        "32",
        "--lora-modules",
        f"gym_adapter={adapter_path}",
        "--enforce-eager",
    ]

    if args.quantization != "none":
        vllm_cmd.extend(["--quantization", args.quantization, "--load-format", args.quantization])

    # Gateway environment configuration
    env = os.environ.copy()
    env["PYTHONPATH"] = str(project_root)
    env["VLLM_BASE_URL"] = f"http://127.0.0.1:{args.vllm_port}/v1"
    env["ADAPTER_NAME"] = "gym_adapter"
    env["BASE_MODEL_NAME"] = args.base_model
    env["ANONYMIZED_TELEMETRY"] = "False"
    env["PYTHONUNBUFFERED"] = "1"

    vllm_proc = None
    gateway_proc = None
    active_tunnel = None

    def shutdown(signum=None, frame=None):
        print("\n\n[SHUTDOWN] Intercepted termination signal. Releasing GPU memory...")
        if active_tunnel:
            try:
                from pyngrok import ngrok
                ngrok.kill()
            except Exception:
                pass
        if gateway_proc and gateway_proc.poll() is None:
            gateway_proc.terminate()
            gateway_proc.wait()
        if vllm_proc and vllm_proc.poll() is None:
            vllm_proc.terminate()
            vllm_proc.wait()
        print("✓ All background services terminated. VRAM cleared successfully.")
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    # 1. Spawn vLLM Engine
    print("[1/2] Initializing vLLM inference engine...")
    vllm_proc = subprocess.Popen(vllm_cmd, cwd=str(project_root))

    print("Polling vLLM engine health status...")
    vllm_ready = False
    for _ in range(120):  # 120 x 2s = 240s maximum startup budget
        try:
            res = requests.get(f"http://127.0.0.1:{args.vllm_port}/v1/models", timeout=2)
            if res.status_code == 200:
                vllm_ready = True
                print("✓ vLLM serving engine online and healthy.\n")
                break
        except Exception:
            pass

        if vllm_proc.poll() is not None:
            print("❌ vLLM process exited unexpectedly. Terminating startup.")
            sys.exit(1)
        time.sleep(2)

    if not vllm_ready:
        print("❌ vLLM failed to report healthy within timeout window.")
        shutdown()

    # 2. Spawn FastAPI Gateway
    print(f"[2/2] Initializing FastAPI Intent Gateway on port {args.gateway_port}...")
    gateway_cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "backend.server:app",
        "--host",
        args.host,
        "--port",
        str(args.gateway_port),
    ]
    gateway_proc = subprocess.Popen(gateway_cmd, cwd=str(project_root), env=env)

    # Health check on FastAPI gateway
    gateway_ready = False
    for _ in range(30):
        try:
            res = requests.get(f"http://127.0.0.1:{args.gateway_port}/health", timeout=2)
            if res.status_code == 200:
                gateway_ready = True
                print("✓ FastAPI triage gateway online.")
                break
        except Exception:
            pass
        time.sleep(1)

    if not gateway_ready:
        print("❌ FastAPI gateway failed to report healthy.")
        shutdown()

    # 3. Connection Routing Setup
    if args.ngrok:
        from pyngrok import ngrok

        token = os.getenv("NGROK_AUTHTOKEN", "")
        if not token:
            token = getpass.getpass("Enter your Ngrok Authtoken: ")
        ngrok.set_auth_token(token)

        if args.ngrok_domain.strip():
            active_tunnel = ngrok.connect(args.gateway_port, domain=args.ngrok_domain.strip())
        else:
            active_tunnel = ngrok.connect(args.gateway_port)

        endpoint_url = active_tunnel.public_url
        print("\n" + "=" * 78)
        print(f"🚀 PUBLIC ANYCAST TUNNEL ACTIVE: {endpoint_url}")
        print(f"👉 Set in client/src/api/coachApi.ts: const BASE_URL = '{endpoint_url}';")
        print("=" * 78 + "\n")
    else:
        lan_ip = get_local_ip()
        print("\n" + "=" * 78)
        print("📍 LOCAL NETWORK READY (Zero-Tunnel Mode)")
        print(f"  * Physical Device (Same Wi-Fi): http://{lan_ip}:{args.gateway_port}")
        print(f"  * Android Studio Emulator:      http://10.0.2.2:{args.gateway_port}")
        print(f"  * Localhost / Dev:              http://127.0.0.1:{args.gateway_port}")
        print(f"👉 Set in client/src/api/coachApi.ts: const BASE_URL = 'http://{lan_ip}:{args.gateway_port}';")
        print("=" * 78 + "\n")

    print("Pipeline running. Press [Ctrl+C] to gracefully stop both servers.\n")

    try:
        gateway_proc.wait()
    except KeyboardInterrupt:
        shutdown()


if __name__ == "__main__":
    main()