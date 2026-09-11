# AI Gym Coach — Biomechanical RAG & Strength-and-Conditioning Inference Engine

[![Platform](https://img.shields.io/badge/Platform-Android%20%7C%20Expo%20SDK%2051-blue.svg)](https://expo.dev/)
[![LLM Serving](https://img.shields.io/badge/Serving-vLLM%200.5%2B%20%7C%20BitsAndBytes%204--bit-purple.svg)](https://github.com/vllm-project/vllm)
[![Base Model](https://img.shields.io/badge/Base%20LLM-Qwen2.5--7B--Instruct-red.svg)](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct)
[![LoRA Weights](https://img.shields.io/badge/Hugging%20Face-LoRA%20Adapter%20(Rank%2016)-orange.svg?logo=huggingface)](https://huggingface.co/ahmedhassanM/qwen2.5-7b-gym-coach-lora)
[![Embeddings](https://img.shields.io/badge/Embeddings-BAAI%2Fbge--base--en--v1.5-green.svg)](https://huggingface.co/BAAI/bge-base-en-v1.5)
[![Presentation](https://img.shields.io/badge/Slides-System%20Design%20Deck%20(PDF)-red.svg?logo=adobeacrobatreader&logoColor=white)](docs/AI_Gym_Coach_Presentation.pdf)
[![Reproducible Notebook](https://img.shields.io/badge/Serving-Kaggle%20GPU%20Notebook-blue.svg?logo=kaggle)](notebooks/serve_backend.ipynb)
[![License](https://img.shields.io/badge/License-MIT-lightgrey.svg)](LICENSE)

An end-to-end, privacy-conscious strength and conditioning coaching system combining a fine-tuned Large Language Model (`Qwen2.5-7B-Instruct` + LoRA) with Clinical Retrieval-Augmented Generation (RAG) and an offline-first mobile execution client.

Built to eliminate generative hallucinations and biomechanically unsafe volume prescription in automated fitness software, the platform integrates multi-class intent triage routing, in-context sports physiotherapy guardrails, recovery analytics, and deterministic JSON-schema workout synthesis tied to a verified 1,746-movement canonical asset catalog.

---

## Detailed System Architecture

```
+===================================================================================================+
|                                    CLIENT LAYER (React Native / Expo SDK 51)                      |
|  - 1,746 Pre-Compiled Static Assets (.webp)          - Dynamic Set Logger (reps vs secs)          |
|  - 1.1s Dual-Frame Cadence Animation Engine          - Offline Local Storage (AsyncStorage)       |
+================================================+==================================================+
                                                 | HTTPS / Secure ngrok Anycast Tunnel
                                                 v
+===================================================================================================+
|                               FASTAPI GATEWAY & ORCHESTRATION LAYER                               |
|                                                                                                   |
|  +---------------------------------------------------------------------------------------------+  |
|  |                        Multi-Class Intent Triage Router (orchestrator.py)                   |  |
|  +--------------------+--------------------------------+--------------------------------+------+  |
|                       |                                |                                |         |
|                       v                                v                                v         |
|     [CLASS A: Pain / Joint Pathology]        [CLASS B: Recovery / DOMS]    [CLASS C: Program Design]
|                       |                                |                                |         |
|                       v                                v                                v         |
|  +-----------------------------------+  +----------------------------+  +----------------------+  |
|  |       ChromaDB Vector Store       |  |  Analytics Recovery Engine |  | Periodization Engine |  |
|  |  - BAAI/bge-base-en-v1.5 (Dense)  |  |  - Sleep Debt & Soreness   |  |  - Volume Landmarks  |  |
|  |  - 40 Clinical Injury Protocols   |  |  - Volume Landmark Intercept| |  - Split Frequency   |  |
|  |  - Kinetic Chain Contraindications|  |  - Suppress Workout UI     |  |  - Movement Ordering|  |
|  |  - Green "CUSTOM REHAB" Injector  |  |    (has_workout: false)    |  |  - Canonical Match  |  |
|  +--------------------+--------------+  +--------------+-------------+  +-----------+----------+  |
|                       |                                |                            |             |
|                       +--------------------------------+----------------------------+             |
|                                                        |                                          |
|                                                        v                                          |
|  +---------------------------------------------------------------------------------------------+  |
|  |               Dynamic In-Context Grounding & Clinical Prompt Assembly Engine                |  |
|  +---------------------------------------------+-----------------------------------------------+  |
+================================================|==================================================+
                                                 | OpenAI-Compatible API Request
                                                 v
+===================================================================================================+
|                               vLLM HIGH-THROUGHPUT INFERENCE ENGINE                               |
|                                                                                                   |
|  +-----------------------------------+     +---------------------------------------------------+  |
|  |    Base: Qwen2.5-7B-Instruct      |     |           Dynamic LoRA Hot-Swap Adapter           |  |
|  |  - BitsAndBytes 4-bit (NF4)       | <== |  - Hugging Face: ahmedhassanM/...-lora (Rank 16)  |  |
|  |  - 13.5 GB Allocated VRAM (T4)    |     |  - Progressive Overload & Tempo (3-0-1-0) Weight  |  |
|  +-----------------------------------+     +---------------------------------------------------+  |
|  |                                                                                     |  |
|  |  - PagedAttention & Prefix Caching (KV Cache hits for static clinical system prompts)          |  |
|  |  - Triton JIT Acceleration & Unbuffered Standard Output Logging Pipeline                      |  |
+================================================+==================================================+
                                                 | Raw Generative Stream
                                                 v
+===================================================================================================+
|                                  OUTPUT CONTRACT & VALIDATION BARRIER                             |
|  - Pydantic v2 Schema Enforcement: Traps missing set arrays, invalid tempos, and hallucinations   |
|  - Exercise Verification Barrier: Validates movement slugs against local canonical taxonomy        |
+================================================+==================================================+
                                                 | Validated JSON Schema Response
                                                 v
                                       [Client Mobile App]
```

---

## Executive Demo & Core Artifacts

<p align="center">
  <video src="https://github.com/user-attachments/assets/f7c98283-30f6-496d-8b8c-c7671a494045" width="100%" controls></video>
</p>

* **System Design Presentation:** Engineering defense slide deck detailing architectural trade-offs, clinical safety layers, and serving benchmarks [available here (PDF)](docs/AI_Gym_Coach_Presentation.pdf).
* **Fine-Tuned Adapter Weights:** Public weights and tokenizer artifacts hosted on [Hugging Face Hub (`ahmedhassanM/qwen2.5-7b-gym-coach-lora`)](https://huggingface.co/ahmedhassanM/qwen2.5-7b-gym-coach-lora).
* **Cloud Serving Pipeline:** Self-contained, automated serving notebook for Kaggle/Colab T4 runtimes located in [`notebooks/serve_backend.ipynb`](notebooks/serve_backend.ipynb).
* **Local Workstation Serving:** Production CLI inference orchestrator with VRAM autoscaling and dual-mode networking located in [`scripts/serve_local.py`](scripts/serve_local.py).
* **Android Release Binary:** Pre-compiled, standalone release binary available under [GitHub Releases](https://github.com/AhmedH32/ai-gym-coach/releases).

---

## Core Machine Learning & Inference Engineering

### 1. Data-Centric Synthetic Engineering & Iterative Hardening
Rather than scraping web forums—which are rife with biomechanically unsound advice, contradictory bro-science, and unformatted syntax—the training distribution was synthetically generated and grounded strictly in sports science literature (Renaissance Periodization volume landmarks: MEV, MAV, MRV, and tempo conventions).

The dataset underwent a three-stage audit and curation pipeline (`ml_pipeline/synthetic_data/`):
* **v1 Initial Draft (`train_data.jsonl` — 907 pairs):** Baseline instruction-tuning split across program generation, recovery, and pain queries. Automated evaluation revealed edge-case classification overlaps between systemic fatigue and localized acute pain.
* **v2 Schema Realignment (`train_data_transformed.jsonl` — 927 pairs):** Standardized intent classification labels, strictly decoupled recovery triage from workout generation, and enforced nested Pydantic set-and-rep JSON contracts.
* **v3 Hardened Production Split (`train_data_final.jsonl` — 967 pairs):** Integrated **40 targeted out-of-domain negative anchor examples** (adversarial prompts, clinical red flags requiring immediate medical referral, and non-fitness queries) to teach the model explicit abstention and rejection boundaries.

### 2. Parameter-Efficient Fine-Tuning (PEFT / LoRA)
* **Base Architecture:** `Qwen/Qwen2.5-7B-Instruct` fine-tuned via Unsloth on an Nvidia T4 GPU (16 GB VRAM).
* **Target Modules:** Targeted all linear projections across both the attention and feed-forward networks (`q_proj`, `k_proj`, `v_proj`, `o_proj`, `gate_proj`, `up_proj`, `down_proj`).
* **Hyperparameters:** LoRA Rank $r=16$, scaling factor $\alpha=16$, learning rate $2\times 10^{-4}$ with linear warmup, per-device batch size 2 with 4 gradient accumulation steps (effective batch size = 8), and sequence length capped at 2,048 tokens.
* **Chat Template Alignment:** Standardized conversation tokenization against the Qwen2.5 chat template to guarantee deterministic output structure and eliminate multi-turn role confusion.
* **Artifact Registry:** Decoupled final adapter weights (162 MB) to [Hugging Face Hub (`ahmedhassanM/qwen2.5-7b-gym-coach-lora`)](https://huggingface.co/ahmedhassanM/qwen2.5-7b-gym-coach-lora).

### 3. High-Throughput Serving & Hardware Profiling (vLLM Engine)
Deployed using `vLLM` with runtime 4-bit `BitsAndBytes` (NF4) quantization, dynamic LoRA module hot-swapping (`--lora-modules gym_adapter=...`), and PagedAttention KV-cache management:

| Metric | Measured Value (Kaggle Nvidia T4 16GB) | Systems Note |
|---|---|---|
| **Base Model Parameters** | 7.61 Billion (`Qwen2.5-7B-Instruct`) | Native instruction-tuned weights |
| **Quantized Weights + LoRA** | ~5.2 GB | 4-bit NF4 base + Rank 16 FP16 adapter weights |
| **PagedAttention KV Cache** | ~8.3 GB | Pre-allocated block pool for 32,768 context window |
| **Total Peak Allocated VRAM** | **~13.5 GB / 15.0 GB** | Matches `--gpu-memory-utilization 0.90` budget |
| **Static Prefix Optimization**| Active (`--enable-prefix-caching`) | Reuses KV cache for static clinical triage system prompts |

### 4. Biomechanical Guardrails & 3-Class Intent Triage
To prevent generic LLM hallucinations and dangerous exercise prescription for injured lifters, incoming queries pass through a multi-class orchestrator (`backend/agent_core/orchestrator.py`):
* **Class A (Clinical Triage & Pain Protocol):** Triggers on anatomical pain cues, tendonitis, or joint impingement. Queries a ChromaDB vector store seeded with 40 clinical sports physiotherapy protocols (`rag_corpus/injuries/`). Automatically injects non-aggravating exercises and attaches a specialized **`CUSTOM REHAB`** UI badge, bypassing standard catalog constraints with explicit clinical modifications (e.g., Spanish squat isometric holds for patellar tendinopathy).
* **Class B (Recovery & Fatigue Management):** Intercepts queries regarding systemic fatigue, DOMS, sleep deficits, or deload planning. Evaluates systemic fatigue markers via `backend/analytics_engine/recovery.py` and enforces `has_workout: false` to suppress empty UI workout cards.
* **Class C (Periodized Workout Generation):** Generates structured workout routines constrained strictly to verified exercise names present in the canonical local database and governed by periodization guidelines (`prompt_assets/periodization/`).

### 5. Deterministic Output Contract & Schema Enforcement
* **Pydantic v2 Validation Barrier:** Built a strict validation layer between raw model tokens and API output. Malformed JSON blocks, missing set arrays, or invalid rep-bracket syntax are caught and remediated before reaching the client layer.
* **Canonical Slug Verification:** Verifies generated exercise titles against canonical entries in `exercises.json`, preventing runtime client image failures.

---

## Client Systems Engineering & Full-Stack Integration

### 1. Static Asset Pre-Compiler (1,746 Movements, 0 Fallbacks)
* **Hermes Bytecode Compatibility:** Because React Native's Hermes engine does not support dynamic runtime string evaluation inside `require()` statements, an automated pre-compilation pipeline (`client/src/assets/exerciseImages.ts`) mapped all 1,746 snake-cased `.webp` multi-angle frames to static references.
* **100% Asset Resolution:** Achieved a verified **1,746/1,746 match rate** across the movement library, eliminating runtime image faults and blueprint fallback placeholders.
* **Dual-Frame Cadence Animation:** Built an asynchronous flipbook animation loop in exercise modals cycling start and peak contraction states at a 1.1s cadence to communicate lifting tempo visually.

### 2. Mobile Architecture & Native Polish
* **Expo SDK 51 Migration:** Upgraded the mobile runtime to SDK 51, establishing direct JavaScript Interface (JSI) compatibility and eliminating native C-extension dynamic linking issues.
* **Unified Surface Palette:** Resolved Android system bar clipping using `translucent={false}` on the native window manager and matched system-level alert dialogues to the application's core dark theme (`#0D1117`).
* **Dynamic Active Workout Engine:** Built an interactive set-logging interface supporting live session timers, volume/tonnage accumulation, set completion toggles, and contextual units (`reps` for dynamic resistance vs. `secs` for rehabilitation isometrics).

### 3. Production CI/CD & Gateway Optimization
* **EAS Cloud Packaging:** Streamlined mobile binary creation via EAS Build (`buildType: apk`) for sideloadable distribution.
* **600%+ Upload Size Reduction:** Engineered strict `.easignore` compiler filters to isolate source logic from build caches, cutting cloud upload sizes from 231 MB to lightweight source archives.
* **Unbuffered Streaming Logs:** Implemented `PYTHONUNBUFFERED=1` and real-time stdout poll loops in the FastAPI gateway to eliminate 4KB output buffering delays, shortening cold-start verification by ~120 seconds.

---

## Technical Stack Summary

| Domain | Layer | Specification |
|---|---|---|
| **Machine Learning** | Base LLM | `Qwen/Qwen2.5-7B-Instruct` (32k Context Window) |
| | Fine-Tuning | PEFT / LoRA ($r=16$, $\alpha=16$, Unsloth) |
| | Quantization | BitsAndBytes (4-bit NF4) |
| | Inference Engine | vLLM 0.5+, CUDA 12.1+, Triton JIT |
| | Weights Registry | [Hugging Face Hub](https://huggingface.co/ahmedhassanM/qwen2.5-7b-gym-coach-lora) |
| **Retrieval (RAG)** | Dense Embeddings | `BAAI/bge-base-en-v1.5` (768-dim Vectors) |
| | Vector Database | ChromaDB (Cosine Distance Space) |
| | Clinical Corpus | 40 Sports Medicine Blueprints + Periodization Rules |
| **Backend Gateway** | Framework | FastAPI, Uvicorn (Unbuffered Async Pipeline) |
| | Contract Validation | Pydantic v2 Schema Enforcement |
| | Tunneling | pyngrok (Static Domain Anycast Routing) |
| **Mobile Client** | Runtime | React Native (Expo SDK 51), TypeScript |
| | JavaScript Engine | Hermes Engine (Bytecode Pre-compiled) |
| | Asset Engine | Static TypeScript Asset Map (1,746 `.webp` frames) |
| | State & Storage | React Navigation, AsyncStorage |

---

## Repository Structure

```text
ai-gym-coach/
├── backend/
│   ├── agent_core/
│   │   └── orchestrator.py        # 3-Class Triage Router & contract validation
│   ├── analytics_engine/
│   │   └── recovery.py            # Fatigue & readiness algorithms
│   ├── rag_engine/
│   │   ├── chroma_db/             # Seeded ChromaDB persistent vector store
│   │   ├── exercise_catalog.py    # Catalog query tools
│   │   └── vector_store.py        # BGE-Base embedding search interface
│   └── server.py                  # FastAPI gateway & application lifecycle
├── client/
│   ├── src/
│   │   ├── api/coachApi.ts        # HTTP client with ngrok header bypass
│   │   ├── assets/
│   │   │   ├── data/exercises.json# Canonical movement catalog
│   │   │   └── exercises/         # 1,746 snake-cased demonstration frames
│   │   ├── components/            # Flipbook modals, set loggers, routine cards
│   │   ├── screens/               # Coach, Routines, Catalog, and Active Workout
│   │   └── utils/imageResolver.ts # Strict zero-fallback asset resolver
│   ├── app.json                   # Android manifest, status bar config, and theme
│   └── eas.json                   # EAS Build profile for standalone APK generation
├── docs/
│   └── AI_Gym_Coach_Presentation.pdf # Engineering defense presentation deck
├── ml_pipeline/
│   ├── qwen2.5_gym_adapter/       # Local adapter weights & tokenizer definitions
│   ├── synthetic_data/            # Training splits & curation checkpoints
│   └── training_scripts/          # Data generation and Unsloth LoRA scripts
├── notebooks/
│   └── serve_backend.ipynb        # Automated Kaggle/Colab vLLM serving pipeline
├── prompt_assets/periodization/   # Volume landmarks & exercise ordering rules
├── rag_corpus/injuries/           # 40 clinical sports physiotherapy protocols
├── scripts/
│   ├── clean_exercises.py         # Data cleaning & schema validation
│   ├── compress_images.py         # Batch asset WebP compression
│   ├── ingest_canonical_chroma.py # ChromaDB vector ingestion pipeline
│   └── serve_local.py             # CLI production inference & gateway runner
└── tests/                         # Pytest test suite (orchestrator, RAG, catalog)
```

---

## Reproduction & Serving Guide

### Option A: Cloud GPU Serving (Zero Setup for Reviewers)

To run the complete inference backend without local Nvidia hardware:

1. Open [`notebooks/serve_backend.ipynb`](notebooks/serve_backend.ipynb) in Kaggle or Google Colab (ensure GPU accelerator is active: T4, P100, or A100).
2. Execute cells 1 through 5:
   * Pulls LoRA weights directly from Hugging Face Hub (`ahmedhassanM/qwen2.5-7b-gym-coach-lora`).
   * Spawns `vLLM` with 4-bit BitsAndBytes quantization.
   * Initializes the FastAPI 3-class intent triage gateway.
   * Exposes an anycast HTTPS endpoint via `ngrok` and streams unbuffered logs.
3. Copy the generated `https://...ngrok-free.app` URL into `client/src/api/coachApi.ts`.

---

### Option B: Local CUDA Workstation Serving

For execution on local Linux workstations or Windows WSL2 environments equipped with an Nvidia GPU:

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Launch the orchestrator (auto-downloads adapter weights from HF Hub if not present locally)
python scripts/serve_local.py --gpu-util 0.85 --max-model-len 16384
```

**Hardware & VRAM Configurations:**
* **8 GB – 12 GB VRAM (RTX 3060 / 4060):** Run with `--max-model-len 4096 --gpu-util 0.75`
* **16 GB VRAM (T4 / RTX 4080):** Run with `--max-model-len 16384 --gpu-util 0.85`
* **24 GB+ VRAM (RTX 3090 / 4090 / A10G):** Run with `--max-model-len 32768 --gpu-util 0.90`

**Dual-Mode Networking Options:**
* **Zero-Tunnel Local Mode (Default):** Runs directly on local IP. The CLI prints your machine's LAN IP for physical device testing on the same Wi-Fi and maps `10.0.2.2` for Android Studio emulators without third-party dependencies.
* **Public Anycast Mode (`--ngrok`):** Adds a secure reverse-tunnel for remote mobile testing or running across university/corporate networks where Access Point (AP) client isolation blocks direct peer connections:
  ```bash
  python scripts/serve_local.py --ngrok
  ```

---

### Mobile Client Execution

#### Option 1: Standalone Android APK (Recommended)
Download and install the pre-compiled binary directly onto any physical Android device:
* Download the standalone build from the [GitHub Releases](https://github.com/AhmedH32/ai-gym-coach/releases) section.
* *Note: The release APK embeds its own native Hermes runtime and does not require Expo Go or Node.js.*

#### Option 2: Local Developer Run (Android Emulator / Studio)
To inspect or run the client source code locally:

```bash
cd client
npm install

# Launch directly on connected Android Studio Emulator
npx expo run:android
```
*(Note: Built on Expo SDK 51. For physical device developer execution without an emulator, use the pre-compiled standalone APK.)*

---

## Test Suite Execution

The backend includes automated test coverage validating intent triage routing, vector retrieval scoring, and catalog consistency:

```bash
# Run the test suite
pytest tests/ -v
```

---

## Contributors

Built as a collaborative engineering project by:
* [Ahmed Hassan](https://github.com/AhmedH32)
* [Ahmed Samy](https://github.com/AhmedSamy5)
* [Youssef Elmegharbel](https://github.com/YoussefElmegharbel)

---

## License

Distributed under the MIT License. See [LICENSE](LICENSE) for details.