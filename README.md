# AI Gym Coach (v2.5) — Compound AI Biomechanical RAG & High-Throughput GPU Serving Engine

[![Live Web Demo](https://img.shields.io/badge/Live_Web_App-Vercel_(Zero--Install_Demo)-000000?logo=vercel&logoColor=white)](https://ai-gym-coach-nine.vercel.app)
[![Live API Gateway](https://img.shields.io/badge/Modal_Serverless_API-Swagger_UI_(/docs)-00D26A?logo=fastapi&logoColor=white)](https://ahmed-h-moustafa2003--ai-gym-coach-v2-gymcoachservice-api.us-east.modal.run/docs)
[![LLM Engine](https://img.shields.io/badge/vLLM_v0.22+-AWQ_Marlin_%7C_FlashAttention--2-7B3FE4)](https://github.com/vllm-project/vllm)
[![System-1 Router](https://img.shields.io/badge/System--1_Router-Vela--3_Fast_(380M_BF16)-FF6B00)](https://huggingface.co/vllm-sr/vela3-fast)
[![Hybrid RAG](https://img.shields.io/badge/Clinical_RAG-BGE_Bi--Encoder_%2B_Cross--Encoder-009688)](https://huggingface.co/BAAI/bge-reranker-base)
[![Containerization](https://img.shields.io/badge/Docker_Compose-8GB_Local_%7C_24GB%2B_Cloud-2496ED?logo=docker&logoColor=white)](docker-compose.yml)
[![CI/CD Gate](https://img.shields.io/badge/GitHub_Actions-4--Gate_Hardware_SLO_Pipeline-2088FF?logo=githubactions&logoColor=white)](.github/workflows/main_cd.yml)
[![v1 LoRA Artifact](https://img.shields.io/badge/Hugging_Face-v1_QLoRA_Adapter_(r%3D32)-FFD21E?logo=huggingface&logoColor=black)](https://huggingface.co/ahmedhassanM/qwen2.5-7b-gym-coach-lora)
[![License](https://img.shields.io/badge/License-MIT-lightgrey.svg)](LICENSE)

An end-to-end, clinical-grade strength and conditioning **Compound AI System** combining a **380M-parameter System-1 Decision Encoder (`Vela-3`)**, a **Two-Stage Hybrid Clinical RAG Engine (`BGE-base` + `BGE-reranker` + `ChromaDB`)**, a **4-bit `AWQ-Marlin` LLM Synthesizer (`Qwen2.5-7B-Instruct-AWQ`)**, an **876-movement in-memory mechanical catalog**, and a **cross-platform React Native (Android & Web) client**.

Engineered to eliminate generative hallucinations, acute medical triage failures, and multi-user GPU out-of-memory (OOM) crashes, **v2.5** consolidates a 4-model neural pipeline (`~7.97B` total parameters) onto a single serverless GPU (`NVIDIA L4 / A10G / L40S`) using stage-decoupled `asyncio` admission semaphores, 3-tier Radix prefix caching, and automated hardware SLO gating—cutting end-to-end `p50` latency by **`23.5× – 34.0×` (`105.4s` $\rightarrow$ `3.10s–4.49s`)** and boosting cluster burst throughput to **`3,902.5 tok/s` (`100%` pass rate across 16 concurrent users)**.

---

## Live Interactive Endpoints & Instant Verification

* **🌐 Live Interactive Web Application (Vercel):** [**`https://ai-gym-coach-nine.vercel.app`**](https://ai-gym-coach-nine.vercel.app) *(Automatically triggers speculative GPU pre-warming on page load).*
* **⚡ Interactive OpenAPI / Swagger Playground (`/docs`):** [**`https://ahmed-h-moustafa2003--ai-gym-coach-v2-gymcoachservice-api.us-east.modal.run/docs`**](https://ahmed-h-moustafa2003--ai-gym-coach-v2-gymcoachservice-api.us-east.modal.run/docs)
* **🩺 Live GPU Hardware & VRAM Health Probe (`GET /health`):** [**`https://ahmed-h-moustafa2003--ai-gym-coach-v2-gymcoachservice-api.us-east.modal.run/health`**](https://ahmed-h-moustafa2003--ai-gym-coach-v2-gymcoachservice-api.us-east.modal.run/health)
* **📱 Standalone Android Release APK:** Available under [**GitHub Releases**](https://github.com/AhmedH32/ai-gym-coach/releases)

### 1-Line Terminal Smoke Test (`curl`)
```bash
curl -X POST "[https://ahmed-h-moustafa2003--ai-gym-coach-v2-gymcoachservice-api.us-east.modal.run/chat](https://ahmed-h-moustafa2003--ai-gym-coach-v2-gymcoachservice-api.us-east.modal.run/chat)" \
  -H "Content-Type: application/json" \
  -d '{"query": "Tendon below my kneecap is barking on deep squats, but I have dumbbells. Can I get a leg workout in today?"}'
```

---

## v2.5 Compound AI Architecture (System-1 / System-2 DAG)

Rather than forcing a 7B generative LLM to act as both classifier and generator, `v2.5` decouples **System-1 deterministic routing & hybrid retrieval** from **System-2 prefix-cached synthesis**:

```text
                        [ Athlete Mobile / Web Client ]
                       (Two-Edge Speculative Pre-Warming)
                                       │
                                       ▼  HTTPS POST /chat
┌──────────────────────────────────────────────────────────────────────────────┐
│                 FASTAPI ASYNC ORCHESTRATOR (`orchestrator.py`)               │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │ Stage 1: System-1 Decision Encoder (`vllm-sr/vela3-fast`, 380M BERT)   │  │
│  │  • Bounded Admission: `asyncio.Semaphore(3)` on `cuda:0` (`bfloat16`)  │  │
│  │  • Single-Pass 7-Head Extraction (`42–56 ms` p50):                     │  │
│  │    1. Primary Intent (4-Way)        5. Available Equipment (Multi)     │  │
│  │    2. Workout Program Gate (Bool)   6. Explicit Exclusion Gate (Bool)  │  │
│  │    3. Target Muscles (Multi-Label)  7. Excluded Mechanics / Gear       │  │
│  │    4. Equipment Constraint Gate                                        │  │
│  └─────┬──────────────────────┬───────────────────────┬───────────────────┘  │
│        │                      │                       │                      │
│        ▼ [CLASS_0_RED_FLAG]   ▼ [CLASS_1_CLINICAL]    ▼ [CLASS_2_CATALOG]    │
│  ┌───────────┐        ┌───────────────┐       ┌──────────────────────┐       │
│  │ Hard-Stop │        │ 2-Stage RAG   │       │ In-Memory Catalog    │       │
│  │ Triage    │        │ Semaphore(2)  │       │ Inverted Index (876) │       │
│  │ Circuit   │        │ 1. BGE-Base   │       │ • Target Muscle Hit  │       │
│  │ Breaker   │        │   (K=10,τ=.58)│       │ • Equipment Filter   │       │
│  │ (0 LLM    │        │ 2. Reranker   │       │ • Negative Mechanics │       │
│  │  Tokens,  │        │   (T=2.5,     │       │   Exclusion Pruning  │       │
│  │ ~108ms)   │        │    p >= 0.12) │       │   (`~1.0 ms`)        │       │
│  └─────┬─────┘        └───────┬───────┘       └──────────┬───────────┘       │
│        │                      │                          │                   │
│        │                      └────────────┬─────────────┘                   │
│        │                                   ▼ Context + Execution Directive   │
│        │              ┌─────────────────────────────────────────┐            │
│        │              │ Stage 2: System-2 LLM Synthesis (`vLLM`)│            │
│        │              │  • Model: `Qwen2.5-7B-Instruct-AWQ`     │            │
│        │              │  • Kernel: `awq_marlin` + `FlashAttn-2` │            │
│        │              │  • 3-Tier Radix Prefix Cache (`~50ms`   │            │
│        │              │    TTFT; `89.7–130.5 tok/s` decode)     │            │
│        │              └────────────────────┬────────────────────┘            │
│        │                                   ▼                                 │
│        │              ┌─────────────────────────────────────────┐            │
│        │              │ Stage 3: Referential Integrity Barrier  │            │
│        │              │  • Delimiter Split & Pydantic Coercion  │            │
│        │              │  • 876 Catalog Foreign-Key Verification │            │
│        │              │  • Custom Rehab Demotion (`null` ID)    │            │
│        │              └────────────────────┬────────────────────┘            │
└────────┼───────────────────────────────────┼─────────────────────────────────┘
         └───────────────────────────────────┴─────────────────► JSON Response
```

### The 4-Class Mutually Exclusive Routing Taxonomy
| Route Class | Target Execution Path | Output Contract | Clinical / Coaching Trigger |
|---|---|---|---|
| **`CLASS_0_RED_FLAG`** | Deterministic Circuit Breaker (`0` LLM tokens) | Urgent Triage Markdown (`has_workout: false`) | Acute medical/neurological trauma: radiating chest tightness, cauda equina (saddle numbness), audible tendon rupture with retraction. |
| **`CLASS_1_CLINICAL_RAG`** | `search_medical_db` (2-Stage Hybrid RAG) | Clinical Rationale + Custom Rehab JSON (`wants_workout=True`) or Diagnostic Markdown (`False`) | Musculoskeletal joint/tendon pain, pinching, burning, or lift-provoked irritation (overrides equipment keywords). |
| **`CLASS_2_CATALOG_WORKOUT`** | `search_exercise_catalog` (876 Inverted Index) | Biomechanical Rationale + Verified Catalog Workout JSON (`has_workout: true`) | Pain-free hypertrophy, strength, or equipment-constrained routine generation for healthy athletes. |
| **`CLASS_3_DIRECT_COACHING`** | Direct Tier-1 Prefix-Cached Synthesis | Pure Periodization / Technique Markdown (`has_workout: false`) | Periodization theory (MEV/MAV/MRV), deload structure, rest intervals, plateau management, or lifting form cues. |

---

## Core Systems Engineering & First-Principles Architecture

### 1. Replacing 7B QLoRA Routing with a 380M System-1 Decision Encoder (`278×` Speedup)
* **The `v1` Baseline Bottleneck:** In `v1.0`, routing relied on a fine-tuned `Qwen2.5-7B-Instruct` Rank-32 QLoRA adapter ([`ahmedhassanM/qwen2.5-7b-gym-coach-lora`](https://huggingface.co/ahmedhassanM/qwen2.5-7b-gym-coach-lora)) trained via Unsloth on 967 LLM-judged synthetic examples. Generating routing JSON autoregressively required **`15,779.5 ms p50` (`31,360.2 ms p95`)** before retrieval could even begin.
* **The `v2.5` System-1 Solution:** Replaced generative LLM routing with `vllm-sr/vela3-fast` (`380M` UltraBERT backbone, pinned to immutable commit `fa60e3aa`), which evaluates **7 parallel classification and multi-label slot heads in a single bidirectional forward pass** (`42.0 ms – 56.7 ms p50`).
* **Hardware-Adaptive Mixed Precision:** Retains `float32` master weights for numerical stability while dynamically dispatching `torch.bfloat16` Tensor Core autocast on Ampere/Ada GPUs (`sm_86`/`sm_89`) and `torch.float16` on Turing (`sm_75`). Eliminating lexical overlap between `CLASS_1` and `CLASS_2` criteria achieved **`100.0%` (`16/16`) intent and workout-gate accuracy**.

### 2. Resolving Vector Space Distribution Collapse & Two-Stage Cross-Encoder Calibration
#### A. Decoupling Periodization Theory from ChromaDB
Indexing broad periodization Markdown documents alongside specific musculoskeletal injury cards in `768`-dimensional `BAAI/bge-base-en-v1.5` space caused severe geometric distortion:
$$\text{Distance}(\text{OOD: Sourdough Recipe}, \text{Periodization}) < \text{Distance}(\text{In-Domain: Biceps Overuse}, \text{Corpus}) \quad \text{[Distribution Collapse]}$$
Purging the 5 periodization documents from ChromaDB and relocating them to `prompt_assets/periodization/` (where they are cached in GPU VRAM via `vLLM` RadixAttention) restored embedding homogeneity across the 40 canonical injury cards.

#### B. Overcoming Vocabulary Mismatch with Two-Stage Hybrid RAG ($T = 2.5$)
Even in a homogeneous injury store, single-stage bi-encoder cosine distance ($\tau \le 0.38$) suffered a **`33.33%` (`8/24`) false rejection rate** when athletes described clinical conditions using gym slang (*"tendon below kneecap is barking out of the hole"* vs. *"Patellar Tendinopathy"*).
1. **Stage 1 (Colloquial-Enriched Bi-Encoder Recall):** Enriched all 40 clinical cards with colloquial symptom descriptors and relaxed `bge-base-en-v1.5` candidate retrieval to $K = 10$ at $\tau \le 0.58$.
2. **Stage 2 (Cross-Encoder Reranking & Sigmoid Calibration):** `BAAI/bge-reranker-base` (`278M`) performs full cross-attention over all 10 `(query, protocol)` pairs and applies a temperature-scaled sigmoid gate ($P = \sigma(\text{logit} / T)$ with $T = 2.5$, cutoff $p \ge 0.12$):

```text
 0.00   0.002 (Cardiac/OOD)     0.12 (Cutoff)                          0.964 (Patellar Hit)  1.00
  ├───────●──────────────────────┰──────────────────────────────────────●──────────────────────┤
  │  OUT-OF-DOMAIN REJECTION     ┃            VERIFIED MUSCULOSKELETAL REHAB ZONE              │
  │  (Emergency Triage Refusal)  ┃     Recall@1: 91.67% | Recall@3: 100.0% | MRR: 0.9583       │
  └──────────────────────────────┸─────────────────────────────────────────────────────────────┘
```

### 3. Single-GPU Co-Location via Stage-Decoupled Admission Semaphores
In `v2.0`, running `vLLM` alongside the 3 co-processor models (`Vela-3` + `BGE-base` + `BGE-reranker`) required **two separate physical GPUs (`cuda:0` + `cuda:1`)** because co-locating them on one GPU under unbounded `asyncio` concurrency caused dynamic encoder activation graphs to spike to **`5,918 MB` (`5.78 GiB`)**, colliding with `vLLM` and crashing 37.5% of requests (`6/16`) with `CUDA out of memory`.
* **Triton `instance_group` Bulkhead Pattern:** `GymCoachOrchestrator` wraps GPU co-processor execution in stage-decoupled semaphores (`_router_sem = asyncio.Semaphore(3)`, `_rag_sem = asyncio.Semaphore(2)`).
* **Result:** Caps peak co-processor reserved VRAM at **`2,496 MB` (`2.44 GiB`, `-57.8%`)**, allowing the entire 4-model stack to run on **1 GPU** while feeding `vLLM` continuous batching (`16/16` pass rate, **`3,902.5 tok/s`** aggregate throughput).

### 4. First-Principles GQA KV-Cache Math & Multi-Profile Hardware Scaling
`Qwen2.5-7B-Instruct-AWQ` uses **Grouped Query Attention (GQA)** with $L = 28$ layers, $H_{kv} = 4$ Key-Value heads, and head dimension $D = 128$ in `FP16` (`2 bytes`):
$$\text{KV Cache per Token} = 2 \times 28 \text{ layers} \times 4 \text{ KV heads} \times 128 \text{ dim} \times 2 \text{ bytes} = 57,344 \text{ bytes} = \mathbf{56 \text{ KiB/token}}$$

This compact `56 KiB/token` footprint drives our **Single-Image, Multi-Profile Hardware Architecture**:
* **8 GB Consumer GPU (`RTX 4060` — `local-8gb` Docker Profile):** Offloads the `767M` co-processor suite to System RAM (`COPROCESSOR_DEVICE=cpu`, `0 MB` VRAM) and runs `vLLM` in eager mode (`4,096` context = only **`224 MiB` KV cache** + `5.20 GiB` weights = **`~6.3 GiB` total VRAM**).
* **24 GB Datacenter GPU (`L4` / `A10G` — `0.75` Pool):** Allocates `11.17 GiB` strictly to the KV block pool = **`204,336` tokens** (**`24.94×` concurrency** at full `8,192` context).
* **48 GB Datacenter GPU (`L40S` — `0.75` Pool):** Allocates `27.65 GiB` to the KV block pool = **`517,808` tokens** (**`63.21×` concurrency** at full `8,192` context).

---

## Architectural & Telemetry Progression (`v1.0` $\rightarrow$ `v2.0` $\rightarrow$ `v2.5`)

### 1. Subsystem Evolution Matrix

| Subsystem | `v1.0` Legacy (`1× T4` + Pass-1 QLoRA) | `v2.0` Pre-Modal (Kaggle `2× T4` Disaggregated) | `v2.5` Production (Modal Serverless + Docker Compose) |
|---|---|---|---|
| **Compute Topology** | Ephemeral Kaggle Notebook (`T4 16GB`, `sm_75`) + manual `pyngrok` tunnel. | Disaggregated Dual-T4 (`vLLM` on `cuda:0`, Co-Processor on `cuda:1`). | **Unified Serverless GPU Pool (`L4` / `A10G` / `L40S`, 24–48GB)** + **2-Container Docker Compose** (`local-8gb` & `cloud-24gb`). |
| **Intent & Slot Router** | `Qwen2.5-7B` Rank-32 QLoRA adapter (`15.78s p50` autoregressive JSON pass). | `Vela-3` (`380M`) on `cuda:1` (`127.3ms p50`, `83.3%–91.7%` gate accuracy). | **Hardware-Adaptive `Vela-3` (`380M`) on `cuda:0`** (`bfloat16`, **`42–56ms p50`**, **`100%` intent & workout-gate accuracy**). |
| **LLM Quantization & Kernel** | `BitsAndBytes` 4-bit `NF4` (Eager mode, no CUDA graphs, no FlashAttention-2). | `vLLM` `auto_awq` (CUDA graphs enabled; `FA-2` unsupported on `sm_75` T4). | **`vLLM` `awq_marlin` + `FlashAttention-2`** (`sm_86`/`sm_89`), `9P` weight prefetch (`1.45s`), pre-compiled Triton sampler (`max_tokens=2, temp=0.1`). |
| **Clinical RAG Engine** | 1-Stage CPU `bge-base` ($\tau \le 0.38$; `33.3%` false rejects; `100%` drop bug). | 2-Stage `bge-base` + `bge-reranker` on `cuda:1` ($T=2.5, p \ge 0.12$). | **Transactional Persistent ChromaDB** with SHA-256 delta sync (`Recall@3 = 100%`, `MRR = 0.9583`). |
| **Multi-User Concurrency** | 1-user sequential blocking (`93.7%` VRAM saturation). | Required 2 physical GPUs; crashed on single GPU under 16-user burst (`5.78 GiB` spike). | **Single-GPU Co-Location via Bounded Semaphores (`3` Router / `2` RAG)**: `2.44 GiB` ceiling, **`16/16` (`100%`) burst pass**. |
| **CI/CD & Quality Gates** | Manual notebook execution & local unit tests. | Embedded notebook benchmark script. | **4-Gate GitHub Actions Pipeline** (Corpus Contract $\rightarrow$ GPU ChromaDB Gate $\rightarrow$ Staging SSE `TTFT`/`ITL` & 8-User Burst $\rightarrow$ Deploy). |

### 2. Empirical Hardware Benchmark & Roofline Matrix

| Metric / Hardware Probe | `v1.0` Baseline (`T4` 16GB `sm_75`) | `v2.0` Dual-GPU (`2× T4` 16GB `sm_75`) | `v2.5` on `NVIDIA L4` (`24GB`, `300 GB/s`) | `v2.5` on `NVIDIA A10G` (`24GB`, `600 GB/s`) | `v2.5` on `NVIDIA L40S` (`48GB`, `864 GB/s`) | Net Gain (`v1.0` $\rightarrow$ `v2.5`) |
|---|---|---|---|---|---|---|
| **E2E Pipeline Latency (`p50`)** | `105.391 s` | `9.131 s` (`18.08s` Run 1) | `~6.80 s` | **`4.490 s`** | **`~3.10 s`** | **`23.5× – 34.0×` faster** |
| **E2E Pipeline Latency (`p95`)** | `115.101 s` | `15.296 s` (`25.33s` Run 1) | `12.69 s` (8-user burst) | **`4.85 s`** (`8.95s` burst) | **`3.21 s`** (8-user burst) | **`35.8×` faster** |
| **Red-Flag Triage E2E (`CLASS_0`)** | `> 100.0 s` | `175.0 ms` | `204.2 ms` (burst) | **`135.0 ms`** (`183ms` burst) | **`108.25 ms`** (burst) | **`> 900×` faster hard-stop** |
| **Router Latency (`p50` / `p95`)** | `15,779.5 ms` / `31,360.2 ms` | `127.25 ms` / `133.54 ms` | `~68.0 ms` / `82.0 ms` | **`56.7 ms` / `73.7 ms`** | **`~42.0 ms` / `54.0 ms`** | **`278× – 375×` faster** |
| **Router Intent / Gate Accuracy** | `~75.0%` | `91.67%` / `83.33%` | **`100.0%` / `100.0%`** | **`100.0%` / `100.0%`** | **`100.0%` / `100.0%`** | **`100%` deterministic** |
| **Cold Prefix TTFT (`~3.8K` tok)** | `27,108.51 ms` | `8,040.76 ms` | `~520 ms` | **`~380 ms`** | **`~310 ms`** | **`71× – 87×` faster** |
| **Warm Tier-1 Prefix TTFT** | `646.13 ms` | `62.51 ms – 207.18 ms` | `164.48 ms` | **`52.85 ms`** | **`48.52 ms`** | **`13.3×` faster (`559×` vs cold)** |
| **Single-Stream Decode (`ITL` p50)** | `8.28 tok/s` (`124.75 ms`) | `35.83 tok/s` (`28.13 ms`) | `44.8 tok/s` (`22.34 ms`) | **`89.7 tok/s` (`11.15 ms`)** | **`130.5 tok/s` (`7.66 ms`)** | **`10.8× – 15.8×` higher tok/s** |
| **Clinical RAG `Recall@1` / `@3`** | `54.17%` / `58.33%` | `87.5%–91.7%` / `100.0%` | **`91.67%` / `100.0%`** | **`91.67%` / `100.0%`** | **`91.67%` / `100.0%`** | **`+37.5%` R@1, `100%` R@3** |
| **Clinical RAG `MRR` / Drop Rate** | `0.5625` / `100.0%` dropped | `0.9583` / `0.0%` | **`0.9583` / `0.0%`** | **`0.9583` / `0.0%`** | **`0.9583` / `0.0%`** | **`+70.4%` MRR, `0%` drops** |
| **16-User Burst Throughput** | Failed (Sequential) | Crashed (`6/16` OOM on 1 GPU) | `100%` Pass (`~2,100 tok/s`) | **`16/16` Pass (`3,902.5 tok/s`)** | **`100%` Pass (`~5,600+ tok/s`)** | **`471×` cluster throughput** |
| **Allocated KV Cache Pool (`0.75`)** | `~1.84 GB` (32K eager) | `81,648` tokens (`9.97×`) | `204,336` tokens (`24.94×`) | **`204,336` tokens (`24.94×`)** | **`517,808` tokens (`63.21×`)** | **`6.3×` larger KV capacity** |

---

## Client Systems Engineering (React Native Mobile & Web)

* **Two-Edge Speculative Container Pre-Warming (`client/src/api/coachApi.ts`):** Eliminates perceived serverless cold-start latency by firing a non-blocking, in-flight-deduplicated `GET /health` wakeup probe on `CoachScreen` mount and `TextInput` focus (`120s` cooldown guard matching Modal's container `scaledown_window`).
* **4-Stage Progressive Coaching Status Indicator (`client/src/screens/CoachScreen.tsx`):** Transitions smoothly across 4 contextual analysis stages (`0s`, `4s`, `10s`, `18s`) if a request intersects a cold container boot.
* **Hermes Static Asset Pre-Compiler (`1,746` WebP Frames, `0` Fallbacks):** React Native's Hermes bytecode engine forbids dynamic runtime strings inside `require()`. `client/src/assets/exerciseImages.ts` maps all **1,746 snake-cased `.webp` demonstration frames** (`876 exercises × 2 states`) to static asset references with a `1.1s` asynchronous flipbook cadence.
* **Referential Integrity & Custom Rehab Demotion:** The backend orchestrator cross-verifies every generated `catalogId` against the 876 indexed movements. Non-catalog physical therapy drills (e.g., *Spanish Squats*) are automatically demoted to `existsInCatalog: false, catalogId: null`, preventing client image lookup crashes.

---

## Automated 4-Gate MLOps CI/CD Pipeline (`.github/workflows/main_cd.yml`)

Every push to `main` touching backend, corpus, or infrastructure code must clear four sequential verification gates on an pinned `ubuntu-24.04` runner before production rollout:

1. **Gate 1 — CPU Corpus & Catalog Contract Verification (`~1s`):** Verifies all 40 clinical injury Markdown cards are non-empty and validates the 876-exercise JSON catalog schema (`id`, `name`, `primaryMuscles`, `equipment`).
2. **Gate 2 — Transactional GPU ChromaDB Reconciliation & OOD Regression Gate (`~8s`):** Computes SHA-256 content hashes to perform differential ChromaDB upserts on the persistent Modal Volume, verifies in-domain recall (`COND_PATELLAR_TENDINOPATHY`, $P = 0.964$), and enforces out-of-domain cardiac emergency rejection ($P = 0.002$).
3. **Gate 3 — Isolated Staging Hardware SLO & Multi-User Burst Gate (`~45s`):** Boots an isolated staging GPU container, measures true SSE streaming `TTFT` ($< 250\text{ ms}$) and `p50 ITL` ($< 18\text{ ms}$ on `A10G`/`L40S`; $< 30\text{ ms}$ on `L4`), fires an **8-user concurrent burst** across all 4 routing classes (requiring `100%` route and workout-gate accuracy), and asserts post-burst co-processor VRAM remains below `3,200 MB`.
4. **Gate 4 — Zero-Downtime Atomic Production Rollout (`modal deploy`):** Promotes the verified container image and persistent volume state to the live `us-east` ASGI gateway.

---

## Deployment & Reproduction Guide

### Option 1: Serverless GPU Cloud Deployment (Modal)
```bash
pip install modal pydantic
modal token new

# Run the corpus verification gate, staging SLO gate, and production deployment
modal run deploy_modal.py::ingest_and_verify_corpus
modal run deploy_modal.py::verify_system_slos
modal deploy deploy_modal.py
```

### Option 2: Self-Hosted Containerized Deployment (`Docker Compose`)
A single immutable OCI image ([`Dockerfile`](Dockerfile), `pytorch:2.15.0-cuda13.2-cudnn9-runtime`) adapts across consumer and enterprise GPUs via three declarative hardware profiles in [`docker-compose.yml`](docker-compose.yml):

```bash
# Profile A: Fast Co-Processor & RAG Gateway Verification (~2.25 GB VRAM on 8GB RTX 4060)
docker compose --profile gateway-only up --build

# Profile B: Full 4-Model Stack on 8GB Consumer GPU (CPU Co-Processor + GPU Eager vLLM)
docker compose --profile local-8gb up --build

# Profile C: Production 24GB+ Datacenter GPU Stack (Full GPU Co-Location + AWQ-Marlin CUDAGraphs)
docker compose --profile cloud-24gb up --build -d
```

### Option 3: Mobile (Android) & Web Client Execution
```bash
cd client
npm install

# Launch interactive Web App locally
npx expo start --web

# Export static production Web bundle & deploy to Vercel
npx expo export --platform web
npx vercel deploy dist --prod

# Launch on physical Android device via USB Debugging / Expo Go (SDK 51)
npx expo start --tunnel -c
```

---

## Repository Structure

```text
ai-gym-coach/
├── .github/workflows/
│   └── main_cd.yml                 # 4-Gate MLOps CI/CD pipeline (Corpus -> RAG -> Staging SLOs -> Deploy)
├── backend/
│   ├── agent_core/
│   │   ├── orchestrator.py         # Async DAG orchestrator, semaphore bulkheads & 3-tier prompt builder
│   │   └── vela_router.py          # Vela-3 (380M) System-1 router with adaptive BF16/FP16 autocast
│   ├── analytics_engine/
│   │   └── recovery.py             # Volume landmarks (MEV/MAV/MRV) & muscular recovery state engine
│   ├── rag_engine/
│   │   ├── exercise_catalog.py     # In-memory inverted index (876 movements) & negative mechanical filters
│   │   ├── tools.py                # 2-Stage Hybrid Clinical RAG (BGE Bi-Encoder + Cross-Encoder Reranker)
│   │   └── vector_store.py         # Transactional ChromaDB store with SHA-256 delta reconciliation
│   └── server.py                   # Standalone FastAPI ASGI gateway with lifespan warmup & CORS
├── client/                         # Cross-platform React Native (Expo SDK 51) Mobile & Web application
│   └── src/
│       ├── api/coachApi.ts         # Modal gateway client with deduplicated speculative pre-warming
│       ├── screens/                # CoachScreen (4-stage progressive status), WorkoutScreen, Routines
│       └── assets/                 # 876 exercises JSON + 1,746 pre-compiled WebP demonstration frames
├── notebooks/
│   └── serve_backend.ipynb         # Historical v2.0 Dual-T4 disaggregation & ablation benchmark suite
├── prompt_assets/periodization/    # 5 Markdown sports-science documents cached in Tier-1 Radix prefix
├── rag_corpus/injuries/            # 40 colloquial-enriched clinical musculoskeletal protocols
├── raw_data/exercises.json         # Canonical 876-exercise mechanical dataset
├── Dockerfile                      # Production CUDA 13.2 + cuDNN 9 + PyTorch 2.15 gateway container image
├── docker-compose.yml              # Multi-profile orchestrator (gateway-only, local-8gb, cloud-24gb)
└── deploy_modal.py                 # Serverless multi-SKU GPU infrastructure & CI/CD verification functions
```

---

## Contributors

* **[Ahmed Hassan](https://github.com/AhmedH32)** — Lead ML Systems Architect, Compound AI Orchestration, GPU Inference Optimization & MLOps Infrastructure
* **[Ahmed Samy](https://github.com/Ahmedsamy2003)** — Synthetic Dataset Pipelines & Baseline Tooling
* **[Mohamed Salem](https://github.com/ms467154-coder)** — Mobile Client Engineering & Clinical Knowledge Base

## License

Distributed under the MIT License. See [LICENSE](LICENSE) for details.