# AI Gym Coach — Biomechanical RAG & Strength-and-Conditioning Inference Engine

[![Platform](https://img.shields.io/badge/Platform-Android%20%7C%20Expo%20SDK%2051-blue.svg)](https://expo.dev/)
[![LLM Serving](https://img.shields.io/badge/Serving-vLLM%200.5%2B%20%7C%20BitsAndBytes%204--bit-purple.svg)](https://github.com/vllm-project/vllm)
[![Base Model](https://img.shields.io/badge/Base%20LLM-Qwen2.5--7B--Instruct-red.svg)](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct)
[![LoRA Weights](https://img.shields.io/badge/Hugging%20Face-LoRA%20Adapter%20(Rank%2032)-orange.svg?logo=huggingface)](https://huggingface.co/ahmedhassanM/qwen2.5-7b-gym-coach-lora)
[![Embeddings](https://img.shields.io/badge/Embeddings-BAAI%2Fbge--base--en--v1.5-green.svg)](https://huggingface.co/BAAI/bge-base-en-v1.5)
[![Presentation](https://img.shields.io/badge/Slides-System%20Design%20Deck%20(PDF)-red.svg?logo=adobeacrobatreader&logoColor=white)](docs/AI_Gym_Coach_Presentation.pdf)
[![Reproducible Notebook](https://img.shields.io/badge/Serving-Kaggle%20GPU%20Notebook-blue.svg?logo=kaggle)](notebooks/serve_backend.ipynb)
[![License](https://img.shields.io/badge/License-MIT-lightgrey.svg)](LICENSE)

An end-to-end, clinical-grade strength and conditioning coaching system combining a fine-tuned Large Language Model (`Qwen2.5-7B-Instruct` + LoRA) with an isolated Musculoskeletal Vector Store (BGE-Base + ChromaDB), an in-memory 876-movement inverted index, and an offline-first React Native execution client.

Built to eliminate generative hallucinations and biomechanically unsafe volume prescription in automated fitness software, the platform executes a **2-Stage Deterministic Directed Acyclic Graph (DAG)**. It isolates intent triage from exercise generation, enforces a calibrated safety circuit breaker ($\tau \le 0.38$) on pathological queries, caches periodization theory via RadixAttention prefix caching, and cross-verifies routines against an indexed catalog and dynamic client asset map.

---

## 2-Stage Deterministic DAG Architecture

The engine decouples classification and tool invocation from full program synthesis to guarantee safety precedence and eliminate multi-hop tool hallucination.

```text
                                 [ Athlete Query Input ]
                                            │
                                            ▼
                    ┌───────────────────────────────────────────────┐
                    │      Pass 1: Intent Triage Router (vLLM)       │
                    │         Qwen 2.5 7B LoRA Adapter (r=32)       │
                    │   + Deterministic Safety Precedence Override  │
                    └───────────────────────┬───────────────────────┘
                                            │
         ┌──────────────────────────────────┼──────────────────────────────────┐
         │                                  │                                  │
         ▼ [Pain Indicators / Red Flags]    ▼ [Pain-Free Movement / Gear]      ▼ [Fatigue / Form / Theory]
  ┌──────────────┐                   ┌──────────────┐                   ┌──────────────┐
  │   CLASS A    │                   │   CLASS C    │                   │ CLASS B / D  │
  │ Medical Tool │                   │ Catalog Tool │                   │Direct Coaching│
  └──────┬───────┘                   └──────┬───────┘                   └──────┬───────┘
         │                                  │                                  │
         ▼                                  ▼                                  │
  ┌─────────────────────────────┐    ┌─────────────────────────────┐           │
  │    ChromaDB Vector Store    │    │  In-Memory Inverted Index   │           │
  │   BAAI/bge-base-en-v1.5     │    │   876 Canonical Movements   │           │
  │  40 Musculoskeletal Cards   │    │ Negative Mechanical Filters │           │
  │  Safety Reject: τ <= 0.38   │    │  (e.g., deep_flexion excl.) │           │
  └──────────────┬──────────────┘    └──────────────┬──────────────┘           │
                 │                                  │                          │
                 └─────────────────┬────────────────┘                          │
                                   │ Context Injection                         │
                                   ▼                                           │
                    ┌───────────────────────────────────────────────┐          │
                    │       Pass 2: Grounded Clinical Synthesis      │          │
                    │          Base Qwen 2.5 7B-Instruct            │          │
                    │  Grounding: Radix-Cached Periodization Theory │          │
                    │          + Retrieved Clinical Protocol        │          │
                    └───────────────────────┬───────────────────────┘          │
                                            │                                  │
                                            ▼                                  │
                    ┌───────────────────────────────────────────────┐          │
                    │  Delimiter Parsing & Referential Integrity    │          │
                    │  - In-Catalog Items: verified against 876 IDs │          │
                    │  - Clinical Rehab: demoted to custom items    │          │
                    │    (existsInCatalog: false, catalogId: null)  │          │
                    └───────────────────────┬───────────────────────┘          │
                                            │                                  │
                                            ▼                                  ▼
                    ┌──────────────────────────────────────────────────────────────────┐
                    │                 Final Orchestrator Response Contract             │
                    │          Markdown Clinical Rationale + Structured Pydantic JSON   │
                    └───────────────────────────────┬──────────────────────────────────┘
                                                    │ HTTPS / Secure ngrok Tunnel
                                                    ▼
                                          [ Client Mobile App ]
```

### Execution Lifecycle
1. **Pass 1 (Intent Triage Router):** The query is evaluated by the fine-tuned LoRA router (`r=32`) under a strict 4-class routing contract. A **Deterministic Safety Precedence Interceptor** monitors input tokens: if acute musculoskeletal markers appear (`"pain"`, `"sharp"`, `"tendon"`, `"barking"`, `"tweak"`), the query is forced to `CLASS_A` (`search_medical_db`), preventing equipment keywords from overriding injury triage.
2. **Direct Coaching Bypass:** If classified as `CLASS_B` (fatigue/DOMS/deloads) or `CLASS_D` (technique/warm-up theory), the engine evaluates fatigue markers via `backend/analytics_engine/recovery.py`, returns pure coaching Markdown, enforces `has_workout: false` to suppress empty client UI cards, and completely bypasses Pass 2 synthesis.
3. **Tool Execution & Retrieval:**
   * **Class A:** Queries the isolated ChromaDB vector store. If the nearest-neighbor cosine distance exceeds $\tau = 0.38$, retrieval aborts and triggers an automated out-of-scope medical referral.
   * **Class C:** Queries the in-memory inverted catalog index (876 movements) applying target muscle requirements and negative mechanical exclusion filters (e.g., excluding shear loads or deep knee flexion).
4. **Pass 2 (Grounded Clinical Synthesis):** The **Base `Qwen2.5-7B-Instruct`** model receives the athlete context, retrieved clinical protocols or candidate movements, and the static periodization prompt (reused across requests via RadixAttention prefix caching).
5. **Referential Integrity & Sanitization:** Output tokens are parsed across custom delimiters. Prescribed catalog IDs are verified against the 876 indexed entries. Pathological rehab exercises (e.g., Spanish squats, isometrics) are automatically demoted to `existsInCatalog: false` with `catalogId: null`, protecting the client UI from broken foreign-key lookups.

---

## Executive Demo & Core Artifacts

<p align="center">
  <video src="https://github.com/user-attachments/assets/f7c98283-30f6-496d-8b8c-c7671a494045" width="100%" controls></video>
</p>

* **System Design Presentation:** Engineering defense slide deck detailing architectural trade-offs, clinical safety layers, and serving benchmarks [available here (PDF)](docs/AI_Gym_Coach_Presentation.pdf).
* **Fine-Tuned Adapter Weights:** Public weights and tokenizer artifacts hosted on [Hugging Face Hub (`ahmedhassanM/qwen2.5-7b-gym-coach-lora`)](https://huggingface.co/ahmedhassanM/qwen2.5-7b-gym-coach-lora).
* **Cloud Serving Pipeline:** Self-contained, automated 5-cell serving notebook for Kaggle/Colab T4 runtimes located in [`notebooks/serve_backend.ipynb`](notebooks/serve_backend.ipynb).
* **Local Workstation Serving:** Production CLI inference orchestrator with VRAM autoscaling and dual-mode networking located in [`scripts/serve_local.py`](scripts/serve_local.py).
* **Android Release Binary:** Pre-compiled, standalone release binary available under [GitHub Releases](https://github.com/AhmedH32/ai-gym-coach/releases).

---

## Core Machine Learning & Alignment Overhaul

### 1. The 4-Class Multi-Intent Taxonomy
To eliminate tool-calling compulsion on standard fatigue and soreness, training data was aligned to a 4-class mutually exclusive contract:

| Routing Class | Target Action | Output Schema | Clinical / Coaching Trigger |
|---|---|---|---|
| **Class A** | `search_medical_db` | Strict Tool Call JSON | Musculoskeletal pathology, acute/chronic pain, joint irritation, sharp mechanical tweaks. |
| **Class B** | Direct Coaching | Pure Markdown | Periodization, fatigue management, 5x5 plateaus, programmed deloads, systemic DOMS. |
| **Class C** | `search_exercise_catalog` | Strict Tool Call JSON | Pain-free equipment substitutions, exercise mechanical queries. |
| **Class D** | Direct Coaching | Pure Markdown | General lifting technique, warm-up theory, general strength coaching. |

### 2. Data-Centric Synthetic Engineering & Iterative Hardening
Rather than scraping unstructured web forums—which are rife with biomechanically unsound advice and bro-science—the training distribution was synthetically generated and grounded strictly in sports science literature (Renaissance Periodization volume landmarks: MEV, MAV, MRV, and tempo conventions).

The dataset underwent a three-stage audit and curation pipeline (`ml_pipeline/synthetic_data/`):
* **v1 Initial Draft (`train_data.jsonl` — 907 pairs):** Baseline instruction-tuning split across program generation, recovery, and pain queries. Automated evaluation revealed severe tool-calling compulsion where standard DOMS/fatigue falsely invoked medical tools.
* **v2 Schema Realignment & LLM Judge (`train_data_transformed.jsonl` — 927 pairs):** Audited 663 legacy samples with an automated LLM judge (`ml_pipeline/verify_dataset.py`); 244 queries detailing lifting fatigue and training stalls were stripped of tool calls and transformed into Class B direct-coaching responses.
* **v3 Hardened Production Split (`train_data_final.jsonl` — 967 pairs):** Integrated **40 targeted out-of-domain (OOD) negative anchor examples** (non-orthopedic emergencies like appendicitis/cardiac events, PED inquiries, crash diets, and diagnostic imaging scans) establishing a ~6.4% negative anchor ratio to suppress tool hallucination on unsupported queries.

### 3. Parameter-Efficient Fine-Tuning (PEFT / LoRA)
* **Base Architecture:** `Qwen/Qwen2.5-7B-Instruct` fine-tuned via Unsloth in 4-bit BitsAndBytes quantization on an Nvidia Tesla T4 GPU (16 GB VRAM).
* **Target Modules:** All linear projections across both attention and feed-forward networks (`q_proj`, `k_proj`, `v_proj`, `o_proj`, `gate_proj`, `up_proj`, `down_proj`).
* **Hyperparameters:** LoRA Rank $r=32$, scaling factor $\alpha=64$, Dropout $=0$, learning rate $2 \times 10^{-4}$ with linear warmup, per-device batch size 2 with 4 gradient accumulation steps (effective batch size = 8), sequence length capped at 2,048 tokens.
* **Chat Template Alignment:** Standardized conversation tokenization against the native Qwen2.5 chat template to guarantee deterministic tool-call serialization and eliminate multi-turn role confusion.
* **Artifact Registry:** Decoupled final adapter weights (162 MB) published to [Hugging Face Hub (`ahmedhassanM/qwen2.5-7b-gym-coach-lora`)](https://huggingface.co/ahmedhassanM/qwen2.5-7b-gym-coach-lora).

---

## Clinical RAG Engine & Decoupled Periodization

### 1. Vector Store Architecture & Calibrated Safety Threshold ($\tau = 0.38$)
* **Dense Bi-Encoder:** `BAAI/bge-base-en-v1.5` (768-dimensional embeddings) running on CPU via SIMD AVX2 acceleration.
* **Storage Engine:** ChromaDB persistent storage, strictly populated by the **40 canonical clinical injury cards** from `rag_corpus/injuries/`.
* **Idempotent Synchronization (`scripts/ingest_canonical_chroma.py`):** Computes SHA-256 hashes of each card to ensure deterministic, zero-duplicate synchronization across environments.
* **Calibrated Rejection Threshold:** Nearest-neighbor queries must satisfy $\text{Cosine Distance}(q, c) \le 0.38$.

```text
 0.0                      0.24                0.38             0.53               0.68         1.0
  ├─────────────────────────●───────────────────┰────────────────●──────────────────●───────────┤
  │   IN-DOMAIN ZONE (Rehab Protocol)           ┃      OUT-OF-SCOPE REJECTION ZONE              │
  │   Patellar Tendon (d = 0.24)                ┃      Appendicitis (d = 0.53)   Recipe (d=0.68)│
  │                                             ┃                                               │
  └─────────────────────────────────────────────┸───────────────────────────────────────────────┘
                                                ▲
                                                Rejection Threshold τ = 0.38
                                                Emergency Safety Margin Δ ≈ 0.15
                                                General OOD Margin Δ ≈ 0.30
```

Any query yielding a nearest-neighbor distance $> 0.38$ triggers an automated clinical refusal (*"Your query falls outside our verified musculoskeletal database... consult a physician."*), preventing medical misinformation.

### 2. Decoupling Periodization Theory: Resolving Threshold Collapse
During early development, indexing the 5 periodization theory documents directly in ChromaDB alongside the 40 clinical cards caused severe geometric distortion across the 768-dimensional embedding space:
* **High Intra-Cluster Distance for Real Queries:** Broad markdown theory files produced weak semantic matches for specific athletic inquiries (e.g., *"biceps tendon overworking on pull days"* yielded large distances $d > 0.45 - 0.52$).
* **False Proximity for Out-of-Domain Noise:** Unrelated queries containing procedural tokens (e.g., a sourdough bread recipe with *"rest intervals"*, *"cycles"*, *"volume"*) produced artificially low distances ($d \approx 0.48 - 0.52$) against high-level periodization text.

$$\text{Distance}(\text{OOD: Sourdough}, \text{Periodization}) < \text{Distance}(\text{In-Domain: Biceps Overuse}, \text{Corpus}) \quad \text{[Distribution Collapse]}$$

**The Architectural Solution:** Periodization theory was completely purged from ChromaDB and relocated to 5 markdown documents in `prompt_assets/periodization/` (`exercise_ordering_rules.md`, `progression_and_overload_models.md`, `rep_ranges_and_stimulus.md`, `split_design_and_frequency.md`, `volume_landmarks_table.md`).
1. **Restores Embedding Homogeneity:** ChromaDB indexes strictly musculoskeletal pathologies, creating a clean bimodal distribution that makes the single calibrated threshold ($\tau = 0.38$) mathematically sound.
2. **RadixAttention Prefix Caching:** The 5 periodization assets are concatenated directly into the Pass 2 system prompt. Because these tokens remain static across sessions, vLLM retains the Key-Value (KV) cache in GPU memory, eliminating redundant prefill FLOPs and accelerating generation without consuming retrieval bandwidth.

---

## In-Memory Exercise Catalog (876 Movements)

The catalog (`backend/rag_engine/exercise_catalog.py`) loads 876 movements from `raw_data/exercises.json` into an in-memory inverted index:
* **Multi-Key Inverted Index:** Maps target muscle groups, secondary stabilizers, and equipment availability.
* **Negative Mechanical Filtering:** Dynamically strips contraindicated exercises (e.g., `exclude_mechanics="deep_flexion, plyometrics"`), pruning dangerous movements before candidate generation.
* **Referential Integrity Barrier:** The orchestrator cross-checks generated exercise IDs against the 876 indexed entries. Any hallucinated ID is automatically demoted to a custom item (`existsInCatalog: false`, `catalogId: null`), preventing client-side image lookup crashes.

---

## High-Throughput Serving & Hardware Profiling

The inference backend is optimized to run on a single Nvidia Tesla T4 GPU (16 GB / 15.3 GiB addressable VRAM):

| Component | Footprint | Systems Architecture & Allocation Mechanics |
|---|---|---|
| **Base Model Weights** | ~5.5 GB | `Qwen/Qwen2.5-7B-Instruct` quantized to 4-bit BitsAndBytes (NF4). |
| **LoRA Hot-Swap Adapter** | ~162 MB | Rank $r=32$ linear adapter modules loaded into vLLM runtime. |
| **GQA KV Cache (32,768 Context)** | ~1.84 GB | Pre-allocated block pool for full 32k sequence length. |
| **Execution Workspaces & Buffers**| ~6.1 GB | PyTorch/CUDA runtime, Triton kernels, activation headroom, and PagedAttention memory pool. |
| **Total Peak Allocated VRAM** | **13.6 GiB / 15.3 GiB** | Fits within `--gpu-memory-utilization 0.90` operational budget. |

### Grouped Query Attention (GQA) Memory Calculation
Qwen2.5-7B uses 28 transformer layers, 4 Key-Value heads, and a head dimension of 128. In FP16 precision (2 bytes per parameter):

$$\text{KV Cache per Token} = 2 \times 28 \text{ layers} \times 4 \text{ heads} \times 128 \text{ dim} \times 2 \text{ bytes} = 57,344 \text{ bytes} \approx 56 \text{ KB}$$

At the full 32,768-token context window:

$$32,768 \times 56 \text{ KB} \approx 1.84 \text{ GB VRAM}$$

### Why vLLM Allocates ~13.6 GiB on Startup
When launching with `--gpu-memory-utilization 0.90`, vLLM immediately claims 90% of available GPU memory ($15.36 \text{ GiB} \times 0.90 \approx 13.8 \text{ GiB}$) during engine initialization. Beyond holding the 5.5 GB model weights and the 1.84 GB KV cache, the engine reserves the remaining ~6.2 GB as a static PagedAttention block pool and execution buffer. This design prevents dynamic memory allocation spikes and eliminates out-of-memory errors during multi-user inference.

---

## Client Systems Engineering & Full-Stack Integration

### 1. Static Asset Pre-Compiler (1,746 Frames, 0 Fallbacks)
* **Hermes Engine Compatibility:** React Native's Hermes engine does not support dynamic runtime string evaluation inside `require()` calls. A build-step pre-compilation pipeline (`client/src/assets/exerciseImages.ts`) maps all **1,746 snake-cased `.webp` multi-angle frames** to static require references.
* **100% Asset Resolution:** Achieves a verified **1,746/1,746 match rate** across the 876 catalog movements (2 demonstration frames per movement), eliminating image placeholder fallbacks.
* **1.1s Dual-Frame Cadence Animation:** Exercise detail modals run an asynchronous flipbook loop cycling start and peak contraction states at a 1.1s cadence to convey lifting tempo visually.

### 2. Mobile Architecture & Native Polish
* **Expo SDK 51 & Hermes:** Upgraded the mobile runtime to SDK 51, establishing direct JavaScript Interface (JSI) compatibility and eliminating native C-extension dynamic linking issues.
* **System Surface Palette:** Android window manager configured with `translucent={false}` to prevent system bar overlapping, unified with dark theme surfaces (`#0D1117`).
* **Active Workout Session Engine:** Tracks active session duration, cumulative tonnage, set completion states, and contextual units (`reps` for dynamic resistance vs. `secs` for rehabilitation isometrics).

### 3. Production CI/CD & Gateway Optimization
* **EAS Cloud Packaging:** Streamlined mobile binary creation via EAS Build (`buildType: apk`) for sideloadable distribution.
* **600%+ Upload Size Reduction:** Configured strict `.easignore` compiler filters to isolate source logic from build caches, cutting cloud upload sizes from 231 MB to lightweight source archives.
* **Unbuffered Streaming Logs:** Implemented `PYTHONUNBUFFERED=1` and real-time stdout poll loops in the FastAPI gateway to eliminate 4KB output buffering delays, shortening cold-start verification by ~120 seconds.

---

## Technical Stack Summary

| Domain | Layer | Specification |
|---|---|---|
| **Machine Learning** | Base LLM | `Qwen/Qwen2.5-7B-Instruct` (Native 32k Context Window) |
| | Fine-Tuning | PEFT / LoRA ($r=32$, $\alpha=64$, Unsloth) |
| | Quantization | BitsAndBytes (4-bit NF4) |
| | Inference Engine | vLLM 0.5+, CUDA 12.1+, Triton JIT |
| | Weights Registry | [Hugging Face Hub (`ahmedhassanM/qwen2.5-7b-gym-coach-lora`)](https://huggingface.co/ahmedhassanM/qwen2.5-7b-gym-coach-lora) |
| **Retrieval (RAG)** | Dense Embeddings | `BAAI/bge-base-en-v1.5` (768-dim, CPU AVX2 acceleration) |
| | Vector Database | ChromaDB Persistent Store (Cosine Distance Space) |
| | Safety Barrier | Calibrated $\tau = 0.38$ distance threshold |
| | Clinical Corpus | 40 Canonical Musculoskeletal Injury Cards |
| **Backend Gateway** | Framework | FastAPI, Uvicorn (Port 8000) |
| | Routing DAG | 2-Stage Deterministic DAG Orchestrator |
| | Contract Validation| Pydantic v2 Schema Enforcement |
| | Catalog Index | In-memory inverted index (876 movements) with mechanical exclusion |
| | Ingress Tunnel | pyngrok Static Anycast Edge Tunnel |
| **Mobile Client** | Runtime | React Native (Expo SDK 51), TypeScript |
| | Engine | Hermes Bytecode Engine |
| | Movement Media | 1,746 pre-compiled `.webp` frames (876 exercises $\times$ 2 states) |
| | Persistence | AsyncStorage |

---

## Repository Structure

```text
ai-gym-coach/
├── backend/
│   ├── agent_core/
│   │   └── orchestrator.py         # 2-Stage Deterministic DAG Orchestrator
│   ├── analytics_engine/
│   │   └── recovery.py             # Volume landmarks & algorithmic recovery engine
│   ├── rag_engine/
│   │   ├── chroma_db/              # Persistent canonical clinical vector store
│   │   ├── exercise_catalog.py     # In-memory inverted index for 876 exercises
│   │   ├── tools.py                # ClinicalRAGTools (Medical RAG & Catalog interface)
│   │   └── vector_store.py         # RAGVectorStore (BGE bi-encoder AVX2 SIMD)
│   └── server.py                   # FastAPI production gateway (/api/v1/chat)
├── client/
│   ├── src/
│   │   ├── api/coachApi.ts         # HTTP client with ngrok header bypass
│   │   ├── assets/
│   │   │   ├── data/exercises.json # Canonical 876-movement dataset
│   │   │   ├── exerciseImages.ts   # 1,746 static image require references
│   │   │   └── exercises/          # Snake-cased demonstration frames (.webp)
│   │   ├── components/             # Flipbook modals, set loggers, routine cards
│   │   ├── screens/                # Coach, Routines, Catalog, and Active Workout
│   │   └── utils/imageResolver.ts  # Zero-fallback asset resolver
│   ├── app.json                    # Android manifest, status bar config, and theme
│   └── eas.json                    # EAS Build configuration for standalone APK
├── docs/
│   └── AI_Gym_Coach_Presentation.pdf # Technical engineering defense deck
├── ml_pipeline/
│   ├── qwen2.5_gym_adapter/        # Exported LoRA adapter weights & metadata
│   ├── synthetic_data/             # Curated 967-record dataset (train_data_final.jsonl)
│   ├── training_scripts/           # Unsloth fine-tuning (train_unsloth.py)
│   └── verify_dataset.py           # LLM-as-a-judge dataset curation pipeline
├── notebooks/
│   └── serve_backend.ipynb         # Automated 5-cell Kaggle/Colab vLLM serving pipeline
├── prompt_assets/periodization/    # 5 Markdown documents for Radix prefix caching
├── rag_corpus/injuries/            # 40 canonical musculoskeletal injury cards
├── raw_data/
│   └── exercises.json              # Source movement catalog (876 exercises)
├── scripts/
│   ├── clean_exercises.py          # Data cleaning & taxonomy verification
│   ├── compress_images.py          # Batch asset WebP compression
│   ├── ingest_canonical_chroma.py  # SHA-256 idempotent ChromaDB ingestion
│   └── serve_local.py              # CLI production inference orchestrator
└── tests/                          # Automated verification test suite
    ├── test_agent_orchestrator.py  # E2E DAG routing, Pass 1/2 contracts, referential integrity
    ├── test_analytics.py           # Volume landmarks, recovery algorithms, fatigue scoring
    ├── test_exercise_catalog.py    # Inverted index lookups, equipment & mechanical filters
    ├── test_rag_retrieval.py       # Vector lookups, differential diagnosis, SHA-256 idempotency
    └── test_rag_tools.py           # Tau=0.38 distance enforcement, emergency OOD rejection
```

---

## Reproduction & Serving Guide

### Option A: Cloud GPU Serving (Kaggle / Colab T4)

Open [`notebooks/serve_backend.ipynb`](notebooks/serve_backend.ipynb) on a GPU runtime (Nvidia Tesla T4) and execute the 5-cell lifecycle:
1. **Cell 1 (Sanitation & Pinning):** Removes conflicting packages, disables telemetry, and installs pinned versions of `vllm`, `bitsandbytes`, `sentence-transformers`, `fastapi`, and `pyngrok`.
2. **Cell 2 (Git Sync & Pre-Flight Assertions):** Runs `git reset --hard origin/main`, validates required file paths, and pre-caches `bge-base-en-v1.5` on CPU.
3. **Cell 3 (vLLM Engine):** Starts `vllm.entrypoints.openai.api_server` on port 8001 with BitsAndBytes 4-bit quantization, binds the LoRA adapter, and enables prefix caching.
4. **Cell 4 (FastAPI Gateway):** Starts `backend.server` on port 8000, indexing all 876 catalog movements into memory.
5. **Cell 5 (Ngrok Tunnel & Smoke Test):** Connects the tunnel to your static Anycast domain and runs an end-to-end clinical verification request.

Copy the resulting `https://...ngrok-free.app` URL into `client/src/api/coachApi.ts`.

---

### Option B: Local CUDA Workstation Serving

To serve from a local Linux workstation or Windows WSL2 environment:

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Launch orchestrator (auto-downloads LoRA weights from Hugging Face if not present)
python scripts/serve_local.py --gpu-util 0.85 --max-model-len 16384
```

**Hardware Profiles:**
* **8 GB – 12 GB VRAM (RTX 3060 / 4060):** `--max-model-len 4096 --gpu-util 0.75`
* **16 GB VRAM (Tesla T4 / RTX 4080):** `--max-model-len 16384 --gpu-util 0.85`
* **24 GB+ VRAM (RTX 3090 / 4090):** `--max-model-len 32768 --gpu-util 0.90`

**Networking Modes:**
* **Local LAN Mode (Default):** Prints host LAN IP for physical device testing on local Wi-Fi and routes `10.0.2.2` for Android Studio emulators.
* **Public Anycast Mode (`--ngrok`):** Opens a secure reverse tunnel for remote testing across networks where AP client isolation is enabled:
  ```bash
  python scripts/serve_local.py --ngrok
  ```

---

### Mobile Client Execution

#### Option 1: Standalone Android APK (Recommended)
Download and install the pre-compiled binary directly on an Android device:
* Download `ai-gym-coach.apk` from the [GitHub Releases](https://github.com/AhmedH32/ai-gym-coach/releases) page.
* The release APK embeds its own pre-compiled Hermes runtime and runs without Expo Go or Node.js.

#### Option 2: Local Developer Run (Android Emulator / Studio)
To inspect or run the client source locally:

```bash
cd client
npm install

# Launch on connected Android Studio Emulator
npx expo run:android
```

---

## Verification Suite & Test Coverage

The test suite in `tests/` verifies the safety contracts, routing behavior, and catalog search logic:

```bash
pytest tests/ -v
```

1. **`tests/test_rag_tools.py` (9 Tests):** Validates the $\tau = 0.38$ distance threshold, tests rejection of medical emergencies and non-fitness queries, and checks catalog filter constraints.
2. **`tests/test_rag_retrieval.py` (6 Tests):** Validates canonical injury card integrity (40 cards), differential diagnosis resolution, and SHA-256 ingestion idempotency.
3. **`tests/test_agent_orchestrator.py`:** Validates delimiter parsing, custom rehab demotion (`existsInCatalog: false`), and `OrchestratorResponse` Pydantic schemas.
4. **`tests/test_exercise_catalog.py`:** Tests candidate ranking by muscle group and enforces negative mechanical exclusion rules.
5. **`tests/test_analytics.py`:** Tests training volume landmark tracking and recovery scoring in `backend/analytics_engine/recovery.py`.

---

## Contributors

Built as an end-to-end engineering collaboration by:

* **[Ahmed Hassan](https://github.com/AhmedH32)** — Core Architecture, Machine Learning Systems & Orchestration
* **[Ahmed Samy](https://github.com/Ahmedsamy2003)** — Synthetic Dataset Pipelines & Baseline Tooling
* **[Mohamed Salem](https://github.com/ms467154-coder)** —  Mobile Client Engineering & Clinical Knowledge Base

---

## License

Distributed under the MIT License. See [LICENSE](LICENSE) for details.