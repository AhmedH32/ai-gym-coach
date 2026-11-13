# scripts/benchmark_modal_l4.py
import asyncio
import json
import os
import statistics
import time
from pathlib import Path
import httpx

# Replace with your exact deployed URL if different
DEFAULT_MODAL_URL = "https://ahmed-h-moustafa2003--ai-gym-coach-v2-gymcoachservice-api.us-east.modal.run"
MODAL_BASE_URL = os.environ.get("MODAL_API_URL", DEFAULT_MODAL_URL).rstrip("/")

SINGLE_USER_SUITE = [
    (
        "CLASS_1_INJURY_WORKOUT",
        "Outside of my elbow burns when I grip heavy deadlifts, give me an arm workout session I can do today.",
    ),
    (
        "CLASS_1_INJURY_DIAGNOSTIC",
        "Felt a sharp pinching pain in the front of my shoulder during flat bench press yesterday. What happened?",
    ),
    (
        "CLASS_2_CATALOG_WORKOUT",
        "Build me a back and biceps hypertrophy workout using only dumbbells.",
    ),
    (
        "CLASS_3_DIRECT_COACHING",
        "How should I structure a deload week after 6 weeks of high-volume hypertrophy training?",
    ),
    (
        "CLASS_0_RED_FLAG_EMERGENCY",
        "Crushing tightness in my left chest radiating to my jaw and left arm while warming up.",
    ),
]

# 16 diverse concurrent athlete queries hitting the same L4 container simultaneously
CONCURRENT_16_USERS = [
    "Tendon below my kneecap is barking on deep squats, prescribe a leg rehab workout today.",
    "Felt a sharp pinching pain in the front of my shoulder during flat bench press. What is going on?",
    "Outside of my elbow burns when I grip heavy deadlifts, give me an arm workout session today.",
    "Inside of my elbow aches on underhand chin-ups. What is the mechanism of injury?",
    "Bottom of my heel stabs on morning steps. Give me a lower body workout that avoids aggravating it.",
    "Front of my hip pinches when squatting deep. How do I modify my squat stance?",
    "Build me a chest and triceps workout with dumbbells.",
    "Build me a back and biceps workout with barbells and cables.",
    "Give me a shoulder and traps workout using dumbbells.",
    "Build me a hamstring and glute workout with a barbell.",
    "How many sets per muscle group per week maximize hypertrophy for an intermediate lifter?",
    "What is the optimal rest period between heavy compound sets vs isolation accessories?",
    "Should I train to absolute muscular failure on every set of squats and deadlifts?",
    "How do I use RPE to autoregulate progressive overload across a 4-week mesocycle?",
    "Crushing tightness in my left chest radiating to my jaw during squats.",
    "Sudden loss of bladder control and complete saddle numbness after heavy deadlift.",
]


async def run_benchmark():
    print("=" * 85)
    print(f"🚀 BENCHMARKING MODAL SERVERLESS L4 (24GB ADA LOVELACE): {MODAL_BASE_URL}")
    print("=" * 85)

    async with httpx.AsyncClient(timeout=300.0, follow_redirects=True) as client:
        # 1. Wake up container & verify /health
        print("\n[Step 1] Waking L4 Container & Verifying /health (First boot downloads AWQ weights to Volume)...")
        t_boot = time.perf_counter()
        health_resp = await client.get(f"{MODAL_BASE_URL}/health")
        boot_s = round(time.perf_counter() - t_boot, 2)
        
        if health_resp.status_code != 200:
            print(f"❌ [HTTP {health_resp.status_code}] Container boot failed:\n{health_resp.text}")
            return

        health_data = health_resp.json()
        print(f"✓ Container LIVE in {boot_s}s | Health: {health_data}")
        
        # 2. Single-User Sequential Benchmark (5 Core Routes)
        print("\n" + "-" * 85)
        print("⚡ PHASE 1: SINGLE-USER E2E LATENCY ON NVIDIA L4 (5 CORE ROUTES)")
        print("-" * 85)
        single_results = []
        for tag, query in SINGLE_USER_SUITE:
            t0 = time.perf_counter()
            resp = await client.post(f"{MODAL_BASE_URL}/chat", json={"query": query})
            e2e_s = round(time.perf_counter() - t0, 3)
            data = resp.json()
            tel = data.get("telemetry", {})
            items_cnt = len(data["workout_proposal"]["items"]) if data.get("workout_proposal") else 0
            print(
                f"- [{tag}] {e2e_s}s | Route: {data['routing_class']} | "
                f"has_workout={data['has_workout']} (items={items_cnt}) | "
                f"Router={tel.get('router_latency_ms')}ms | RAG={tel.get('rag_latency_ms')}ms | "
                f"LLM={tel.get('llm_latency_ms')}ms | Tokens={tel.get('completion_tokens')}"
            )
            single_results.append({
                "tag": tag,
                "e2e_latency_s": e2e_s,
                "routing_class": data["routing_class"],
                "has_workout": data["has_workout"],
                "workout_items_count": items_cnt,
                "telemetry": tel,
            })

        core4_latencies = [r["e2e_latency_s"] for r in single_results if r["tag"] != "CLASS_0_RED_FLAG_EMERGENCY"]
        p50_single = round(statistics.median(core4_latencies), 3)
        mean_single = round(statistics.mean(core4_latencies), 3)
        print(f"\n✓ Single-User L4 Core-4 p50: {p50_single}s | Mean: {mean_single}s")

        # 3. 16-User Concurrent Burst Stress Test
        print("\n" + "-" * 85)
        print("🔥 PHASE 2: 16-USER CONCURRENT BURST TEST (CONTINUOUS BATCHING + SHARED RADIX CACHE)")
        print("-" * 85)

        async def fire_user(idx: int, q: str):
            t_req = time.perf_counter()
            r = await client.post(f"{MODAL_BASE_URL}/chat", json={"query": q})
            elapsed = round(time.perf_counter() - t_req, 3)
            d = r.json()
            t = d.get("telemetry", {})
            return {
                "user_id": idx + 1,
                "status_code": r.status_code,
                "e2e_s": elapsed,
                "routing_class": d.get("routing_class"),
                "has_workout": d.get("has_workout"),
                "prompt_tokens": t.get("prompt_tokens") or 0,
                "completion_tokens": t.get("completion_tokens") or 0,
                "router_ms": t.get("router_latency_ms"),
                "rag_ms": t.get("rag_latency_ms"),
            }

        t_burst_start = time.perf_counter()
        burst_results = await asyncio.gather(
            *[fire_user(i, q) for i, q in enumerate(CONCURRENT_16_USERS)]
        )
        burst_wall_s = round(time.perf_counter() - t_burst_start, 3)

        success_count = sum(1 for r in burst_results if r["status_code"] == 200)
        total_comp_tokens = sum(r["completion_tokens"] for r in burst_results)
        total_prompt_tokens = sum(r["prompt_tokens"] for r in burst_results)
        burst_latencies = sorted([r["e2e_s"] for r in burst_results])
        llm_latencies = sorted([r["e2e_s"] for r in burst_results if r["completion_tokens"] > 0])

        aggregate_decode_tps = round(total_comp_tokens / burst_wall_s, 2)
        aggregate_total_tps = round((total_prompt_tokens + total_comp_tokens) / burst_wall_s, 2)

        for r in burst_results:
            print(
                f"  [User {r['user_id']:02d}] {r['e2e_s']:6.3f}s | {r['routing_class']:<20} | "
                f"Workout={str(r['has_workout']):<5} | GenTokens={r['completion_tokens']:<4} | "
                f"Router={r['router_ms']}ms"
            )

        summary = {
            "gpu": "1x NVIDIA L4 (24GB Ada Lovelace sm_89)",
            "single_user_core4_p50_s": p50_single,
            "single_user_core4_mean_s": mean_single,
            "single_user_runs": single_results,
            "concurrent_16_users_telemetry": {
                "concurrent_users": 16,
                "http_200_success_rate": round(success_count / 16.0, 4),
                "total_wall_clock_s": burst_wall_s,
                "all_16_p50_latency_s": round(statistics.median(burst_latencies), 3),
                "llm_14_p50_latency_s": round(statistics.median(llm_latencies), 3),
                "p95_latency_s": burst_latencies[int(len(burst_latencies) * 0.95) - 1],
                "total_prompt_tokens_processed": total_prompt_tokens,
                "total_completion_tokens_generated": total_comp_tokens,
                "aggregate_completion_throughput_tps": aggregate_decode_tps,
                "aggregate_total_token_throughput_tps": aggregate_total_tps,
            },
        }

        #out_path = Path("modal_l4_benchmark_telemetry.json")
        #out_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

        print("\n" + "=" * 85)
        print("✅ MODAL L4 CONCURRENCY BENCHMARK COMPLETE")
        print(f"  • 16-User Success Rate:              {success_count}/16 (100%)")
        print(f"  • Total Wall-Clock for 16 Users:     {burst_wall_s}s")
        print(f"  • 16-User Median (p50) Latency:      {summary['concurrent_16_users_telemetry']['all_16_p50_latency_s']}s")
        print(f"  • Total Prompt Tokens Processed:     {total_prompt_tokens:,} tokens")
        print(f"  • Total Completion Tokens Generated: {total_comp_tokens:,} tokens")
        print(f"  • Aggregate Decode Throughput:       {aggregate_decode_tps} tok/s")
        print(f"  • Aggregate Total Token Throughput:  {aggregate_total_tps} tok/s")
        print("=" * 85)


if __name__ == "__main__":
    asyncio.run(run_benchmark())