# backend/agent_core/orchestrator.py
import asyncio
import json
import os
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import httpx
from pydantic import BaseModel, Field

from backend.agent_core.vela_router import RouterDecision, VelaSystemOneRouter
from backend.analytics_engine.recovery import AnalyticsEngine
from backend.rag_engine.tools import ClinicalRAGTools


# ------------------------------------------------------------------------------
# 1. Pydantic Schemas for Dual-Payload Frontend Contract ("Add Workout" Button)
# ------------------------------------------------------------------------------
class WorkoutItem(BaseModel):
    name: str
    existsInCatalog: bool
    catalogId: Optional[str] = None
    category: str = Field(default="accessory", description="warmup_rehab | compound | accessory")
    sets: int = Field(default=3)
    reps: str = Field(default="8-12")
    targetRpe: Optional[int] = Field(default=7)
    tempo: Optional[str] = Field(default="3-0-1-0")
    customInstructions: Optional[List[str]] = Field(default_factory=list)
    coachingCue: Optional[str] = Field(default="")


class WorkoutProposal(BaseModel):
    title: str
    targetFocus: str
    estimatedMinutes: int = Field(default=45)
    items: List[WorkoutItem]


class OrchestratorResponse(BaseModel):
    routing_class: str
    chat_text: str
    has_workout: bool
    workout_proposal: Optional[WorkoutProposal] = None
    telemetry: Dict[str, Any] = Field(default_factory=dict)


# ------------------------------------------------------------------------------
# 2. Tier-1 Static Assets (Global Radix Prefix Cache)
# ------------------------------------------------------------------------------
def load_periodization_corpus(project_root: Path) -> str:
    """Loads and concatenates the 5 static periodization Markdown files for Tier-1 Radix caching."""
    candidates = [
        project_root / "prompt_assets" / "periodization",
        project_root / "rag_corpus" / "periodization",
    ]
    periodization_dir = next((d for d in candidates if d.exists()), None)
    if not periodization_dir:
        return ""

    docs = []
    for md_file in sorted(periodization_dir.glob("*.md")):
        try:
            docs.append(
                f"### {md_file.stem.replace('_', ' ').title()}\n"
                f"{md_file.read_text(encoding='utf-8').strip()}"
            )
        except Exception as e:
            print(f"Warning: Failed to read {md_file}: {e}")
    return "\n\n".join(docs)


CONTRASTIVE_FEW_SHOTS = [
    # Positive Anchor: Injury + Wants to Train -> Explanatory Markdown + Delimited JSON for "Add Workout" UI
    {
        "role": "user",
        "content": (
            "### CLINICAL PROTOCOL: Patellar Tendinopathy (Jumper's Knee) (Knee) [ID: COND_PATELLAR_TENDINOPATHY]\n"
            "**Mechanism of Irritation:** Overload in patellar tendon provoked by deep knee flexion and rapid deceleration.\n"
            "## Absolute Contraindications (Exercises to Avoid)\n"
            "* High-impact plyometric depth jumps or bounding\n"
            "* Heavy deep knees-over-toes squats\n"
            "## Biomechanical Modifications (Rules)\n"
            "* Use slow heavy resistance (isometric or 3-4s tempo)\n"
            "* Maintain vertical shin angle to reduce patellar tendon shear\n"
            "## Recommended Substitutions\n"
            "* Spanish squats (isometric patellar loading)\n"
            "* Romanian deadlifts (posterior chain emphasis)\n\n"
            "Athlete Query: 'Tendon below my kneecap is barking on deep squats, but I have dumbbells. Can I still get a leg workout in today?'\n\n"
            "EXECUTION DIRECTIVE: Provide a clear clinical coaching explanation in Markdown for the athlete to read, "
            "then append a 3-exercise workout routine wrapped inside <!-- WORKOUT_PAYLOAD_START --> and <!-- WORKOUT_PAYLOAD_END -->."
        ),
    },
    {
        "role": "assistant",
        "content": (
            "Your patellar tendon is reacting to high compressive and shear forces at deep knee flexion angles. "
            "We are pulling out deep forward-knee squats and all jumping/plyometrics today to offload the extensor mechanism.\n\n"
            "Instead, we will desensitize the tendon with heavy isometric quad holds, followed by vertical-tibia hip hinges "
            "and glute bridges using your dumbbells so your lower body gets trained with zero anterior knee shear.\n\n"
            "<!-- WORKOUT_PAYLOAD_START -->\n"
            "{\n"
            '  "title": "Patellar-Sparing Dumbbell Session",\n'
            '  "targetFocus": "Lower Body (Tendon Rehab Focus)",\n'
            '  "estimatedMinutes": 40,\n'
            '  "items": [\n'
            "    {\n"
            '      "name": "Spanish Squat Isometric Hold",\n'
            '      "existsInCatalog": false,\n'
            '      "catalogId": null,\n'
            '      "category": "warmup_rehab",\n'
            '      "sets": 5,\n'
            '      "reps": "45s hold",\n'
            '      "targetRpe": 6,\n'
            '      "tempo": "Static",\n'
            '      "customInstructions": [\n'
            '        "Anchor a heavy resistance band or strap behind both knees to a secure post.",\n'
            '        "Sit back to 60 degrees knee flexion while keeping shins strictly vertical."\n'
            "      ],\n"
            '      "coachingCue": "Maintain constant quad tension without letting knees drift forward over toes."\n'
            "    },\n"
            "    {\n"
            '      "name": "Dumbbell Romanian Deadlift",\n'
            '      "existsInCatalog": false,\n'
            '      "catalogId": null,\n'
            '      "category": "compound",\n'
            '      "sets": 3,\n'
            '      "reps": "10-12",\n'
            '      "targetRpe": 7,\n'
            '      "tempo": "3-0-1-0",\n'
            '      "customInstructions": [\n'
            '        "Hold dumbbells in front of thighs with a soft 15-degree knee bend.",\n'
            '        "Push hips straight back until hamstrings are loaded, then squeeze glutes to stand."\n'
            "      ],\n"
            '      "coachingCue": "Keep the tibia vertical; hinge purely at the hips to spare the patellar tendon."\n'
            "    },\n"
            "    {\n"
            '      "name": "Dumbbell Glute Bridge",\n'
            '      "existsInCatalog": false,\n'
            '      "catalogId": null,\n'
            '      "category": "accessory",\n'
            '      "sets": 3,\n'
            '      "reps": "12-15",\n'
            '      "targetRpe": 7,\n'
            '      "tempo": "2-0-1-1",\n'
            '      "customInstructions": [\n'
            '        "Lie on your back with feet flat and a dumbbell resting across your hips.",\n'
            '        "Drive through heels and hold peak glute contraction for 1 second at the top."\n'
            "      ],\n"
            '      "coachingCue": "Keep ribs braced down to prevent lumbar hyperextension."\n'
            "    }\n"
            "  ]\n"
            "}\n"
            "<!-- WORKOUT_PAYLOAD_END -->"
        ),
    },
    # Negative Anchor: Diagnostic Query Only -> Pure Markdown, NO Delimiters
    {
        "role": "user",
        "content": (
            "### CLINICAL PROTOCOL: Subacromial Impingement Syndrome (Shoulder) [ID: COND_SUBACROMIAL_IMPINGEMENT]\n"
            "**Mechanism of Irritation:** Compression of supraspinatus tendon and subacromial bursa beneath the acromion during abduction and internal rotation.\n"
            "## Absolute Contraindications (Exercises to Avoid)\n"
            "* Overhead pressing with internal rotation\n"
            "* Upright rows above chest height\n"
            "## Biomechanical Modifications (Rules)\n"
            "* Press in the scapular plane (30-45 degrees anterior) with neutral grip\n\n"
            "Athlete Query: 'Felt a sharp pinching pain in the front of my shoulder during flat bench press yesterday. What happened?'\n\n"
            "EXECUTION DIRECTIVE: The athlete is asking a diagnostic question ONLY. Provide clinical analysis and rehab action steps in Markdown ONLY. Do NOT emit workout JSON or delimiters."
        ),
    },
    {
        "role": "assistant",
        "content": (
            "A sharp anterior pinching sensation at the bottom turnaround of a flat bench press is classic for **Subacromial Impingement Syndrome**. "
            "In this position, the supraspinatus tendon and subacromial bursa are compressed beneath the acromion bone, "
            "typically triggered by flared elbows (abduction > 70 degrees) or an overly wide grip.\n\n"
            "### Immediate Action Plan:\n"
            "1. **Cease Flat Barbell Pressing:** Deload wide-grip horizontal pressing until resting irritation subsides.\n"
            "2. **Implement Wall Isometrics:** Perform 3 sets of 30-second external rotation holds against a wall to recruit the infraspinatus without joint shear.\n"
            "3. **Monitor Red Flags:** If you develop radiating numbness down the arm, severe night pain, or inability to raise the arm unassisted, seek evaluation from a physical therapist."
        ),
    },
]


# ------------------------------------------------------------------------------
# 3. Core Orchestrator Implementation
# ------------------------------------------------------------------------------
class GymCoachOrchestrator:
    _RE_CODE_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE)

    def __init__(
        self,
        vllm_base_url: str = "http://localhost:8001/v1",
        base_model_name: str = "Qwen/Qwen2.5-7B-Instruct-AWQ",
        adapter_model_name: str = "unused_in_system1",
        project_root: Optional[Path] = None,
        rag_tools: Optional[ClinicalRAGTools] = None,
        router: Optional[VelaSystemOneRouter] = None,
        coprocessor_device: Optional[str] = None,
    ):
        self.vllm_base_url = os.environ.get("VLLM_BASE_URL", vllm_base_url).rstrip("/")
        self.base_model = os.environ.get("BASE_MODEL_NAME", base_model_name)
        self.adapter_model = os.environ.get("ADAPTER_NAME", adapter_model_name)
        self.project_root = project_root or Path(__file__).resolve().parent.parent.parent

        # Persistent HTTP/1.1 Keep-Alive connection pool to vLLM
        self.http_client = httpx.AsyncClient(
            timeout=90.0,
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=50),
        )

        # 1. Initialize Co-Processor Stack (Two-Stage RAG + Vela 3.0 Fast on GPU 1)
        self.tools = rag_tools or ClinicalRAGTools(device=coprocessor_device)
        self.router = router or VelaSystemOneRouter(device=coprocessor_device)

        # 2. Build In-Memory Fast Lookup for Catalog ID Verification
        self.catalog_lookup: Dict[str, Dict[str, Any]] = {}
        for candidate_rel in ["raw_data/exercises.json", "client/src/assets/data/exercises.json"]:
            p = self.project_root / candidate_rel
            if p.exists():
                with open(p, "r", encoding="utf-8") as f:
                    raw_exercises = json.load(f)
                    exercises_list = (
                        raw_exercises
                        if isinstance(raw_exercises, list)
                        else raw_exercises.get("exercises", [])
                    )
                    for ex in exercises_list:
                        self.catalog_lookup[ex["id"]] = ex
                print(f"✓ Orchestrator indexed {len(self.catalog_lookup)} catalog exercises.")
                break

        # 3. Assemble Tier-1 Global Static Prefix (100% Radix Cache Hit Across All Requests)
        periodization_corpus = load_periodization_corpus(self.project_root)
        self.synthesizer_system_prompt = (
            "You are an elite Sports Medicine & Strength Conditioning Coach AI.\n"
            "You synthesize clinical diagnostic findings with evidence-based resistance training programming.\n\n"
            "=== PERIODIZATION GUIDELINES (Radix Cached) ===\n"
            f"{periodization_corpus}\n\n"
            "=== OUTPUT SPECIFICATION (DUAL-PAYLOAD CONTRACT) ===\n"
            "1. Conversational Coaching (Part 1 - Read by Athlete): Address the user directly in clear Markdown (2 concise paragraphs). Explain the pathology or training rationale, biomechanical faults to avoid, and why the selected movements are safe.\n"
            "2. Structured Workout Payload (Part 2 - Parsed by App 'Add Workout' Button):\n"
            "   - Follow the EXECUTION DIRECTIVE at the end of the user prompt strictly.\n"
            "   - When instructed to prescribe a workout, you MUST append a valid JSON object matching the WorkoutProposal schema wrapped strictly inside `<!-- WORKOUT_PAYLOAD_START -->` and `<!-- WORKOUT_PAYLOAD_END -->`.\n"
            "   - When instructed NOT to prescribe a workout (diagnostic or deload advice only), output ONLY the conversational Markdown text and NEVER emit the workout delimiters.\n"
            "3. Exercise Prescription Standards (CRITICAL):\n"
            "   - Prescribe 3 to 4 high-impact exercises per session.\n"
            "   - For CLINICAL/INJURY sessions: All prescribed exercises MUST be set as custom movements (`existsInCatalog: false`, `catalogId: null`) with explicit `sets`, `reps`, `targetRpe`, `tempo`, 2 concise `customInstructions` steps, and a `coachingCue`.\n"
            "   - For PAIN-FREE CATALOG sessions: Use verified `catalogId` values from the candidate list (`existsInCatalog: true`) with explicit `sets`, `reps`, `targetRpe`, `tempo`, `customInstructions`, and `coachingCue`."
        )

        # Default Session Biometric Profile (Tier-2 Session Prefix Cache)
        self.default_session_profile = AnalyticsEngine.build_system_context(
            muscle_states=[
                AnalyticsEngine.evaluate_muscle_recovery("Quadriceps", hours_elapsed=48.0, weekly_sets=12),
                AnalyticsEngine.evaluate_muscle_recovery("Pectorals", hours_elapsed=72.0, weekly_sets=14),
                AnalyticsEngine.evaluate_muscle_recovery("Lats", hours_elapsed=60.0, weekly_sets=12),
            ],
            stalled_exercises=[],
        )

    async def _post_vllm_chat(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 768,
    ) -> Tuple[str, Dict[str, Any]]:
        url = f"{self.vllm_base_url}/chat/completions"
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }
        t0 = time.perf_counter()
        resp = await self.http_client.post(url, json=payload)
        llm_ms = round((time.perf_counter() - t0) * 1000.0, 2)
        if resp.status_code != 200:
            raise RuntimeError(f"vLLM API rejected request [HTTP {resp.status_code}]: {resp.text}")
        data = resp.json()
        content = data["choices"][0]["message"]["content"].strip()
        usage = data.get("usage", {})
        usage["llm_latency_ms"] = llm_ms
        return content, usage

    def _sanitize_workout_items(self, proposal: WorkoutProposal, is_clinical: bool) -> WorkoutProposal:
        """Enforces schema integrity so the mobile app's 'Add Workout' button never crashes."""
        for item in proposal.items:
            if is_clinical:
                item.existsInCatalog = False
                item.catalogId = None
            else:
                if item.existsInCatalog:
                    if not item.catalogId or item.catalogId not in self.catalog_lookup:
                        item.existsInCatalog = False
                        item.catalogId = None
            if not item.customInstructions:
                item.customInstructions = [f"Perform {item.name} with controlled {item.tempo} tempo."]
            if not item.coachingCue:
                item.coachingCue = "Focus on controlled execution and maintain proper form throughout."
        return proposal

    def _parse_synthesis_output(
        self, raw_output: str, is_clinical: bool
    ) -> Tuple[str, Optional[WorkoutProposal]]:
        """
        Splits the LLM response into:
          1. `chat_text`: Explanatory Markdown displayed in the user's chat bubble.
          2. `proposal`: Validated `WorkoutProposal` object powering the app's 'Add Workout' button.
        """
        delimiter_start = "<!-- WORKOUT_PAYLOAD_START -->"
        delimiter_end = "<!-- WORKOUT_PAYLOAD_END -->"

        if delimiter_start not in raw_output:
            return raw_output.strip(), None

        parts = raw_output.split(delimiter_start, 1)
        chat_text = parts[0].strip()
        remaining = parts[1]

        if delimiter_end in remaining:
            json_str = remaining.split(delimiter_end, 1)[0].strip()
        else:
            json_str = remaining.strip()

        # Strip optional ```json ... ``` markdown fences if emitted inside the HTML delimiters
        json_str = self._RE_CODE_FENCE.sub("", json_str).strip()

        try:
            parsed_json = json.loads(json_str)
            proposal = WorkoutProposal(**parsed_json)
            proposal = self._sanitize_workout_items(proposal, is_clinical=is_clinical)
            return chat_text, proposal
        except Exception as e:
            print(f"Warning: Failed to parse workout JSON payload: {e}")
            return chat_text, None

    def build_tiered_messages(
        self,
        dynamic_turn_prompt: str,
        session_user_profile: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        """
        Enforces strict 3-Tier Prompt Ordering for vLLM Radix Prefix Caching:
          - Tier 1 (Messages 0..4): Static System Prompt + Periodization Corpus + Contrastive Few-Shots
          - Tier 2 (Start of Msg 5): Session User Biometric/Recovery Profile (cached across user turns)
          - Tier 3 (End of Msg 5):   Dynamic Turn RAG Context + Athlete Query
        """
        profile_block = session_user_profile or self.default_session_profile
        return [
            {"role": "system", "content": self.synthesizer_system_prompt},
            *CONTRASTIVE_FEW_SHOTS,
            {
                "role": "user",
                "content": f"{profile_block}\n\n{dynamic_turn_prompt}",
            },
        ]

    async def execute(
        self,
        user_query: str,
        session_user_profile: Optional[str] = None,
    ) -> OrchestratorResponse:
        t_start = time.perf_counter()

        # --- STAGE 1: System-1 Batched Vela 3.0 Fast Router (~25-35ms on GPU 1) ---
        decision: RouterDecision = await asyncio.to_thread(self.router.route, user_query)

        # Hard Stop Circuit Breaker for Class 0 Acute Medical Red Flags (Zero LLM Calls)
        if decision.intent == "CLASS_0_RED_FLAG":
            total_ms = round((time.perf_counter() - t_start) * 1000.0, 2)
            return OrchestratorResponse(
                routing_class="CLASS_A_OUT_OF_SCOPE",
                chat_text=(
                    "### URGENT CLINICAL TRIAGE ALERT\n"
                    "Your reported symptoms indicate a potential acute medical or neurological red flag "
                    "(such as severe nerve compression, complete tissue rupture, or systemic cardiovascular distress).\n\n"
                    "**Immediate Action:** Cease all physical training immediately and seek urgent evaluation "
                    "from an emergency physician or qualified healthcare professional."
                ),
                has_workout=False,
                workout_proposal=None,
                telemetry={
                    "router": "vela3-fast",
                    "router_intent": decision.intent,
                    "router_confidence": decision.intent_confidence,
                    "router_latency_ms": decision.latency_ms,
                    "total_e2e_ms": total_ms,
                },
            )

        # --- STAGE 2: Tool Execution (Two-Stage Clinical RAG or Catalog Filter) ---
        is_clinical = decision.intent == "CLASS_1_CLINICAL_RAG"
        rag_latency_ms = 0.0

        if is_clinical:
            medical_res = await asyncio.to_thread(
                self.tools.search_medical_db,
                user_query,
            )
            rag_latency_ms = medical_res.latency_ms

            # Fixed Circuit Breaker: properly checks Pydantic `triage_required` / `OUT_OF_DOMAIN`
            if medical_res.triage_required or medical_res.status != "MATCH_FOUND":
                total_ms = round((time.perf_counter() - t_start) * 1000.0, 2)
                return OrchestratorResponse(
                    routing_class="CLASS_A_OUT_OF_SCOPE",
                    chat_text=(
                        "Your query describes symptoms that fall outside our verified musculoskeletal sports "
                        "rehabilitation database (Cross-Encoder safety threshold not met). "
                        "For non-orthopedic symptoms or acute pathology, please consult a qualified healthcare professional."
                    ),
                    has_workout=False,
                    workout_proposal=None,
                    telemetry={
                        "router": "vela3-fast",
                        "router_latency_ms": decision.latency_ms,
                        "tool_executed": "search_medical_db",
                        "rag_latency_ms": rag_latency_ms,
                        "min_distance": medical_res.min_distance,
                        "max_rerank_prob": medical_res.max_rerank_prob,
                        "total_e2e_ms": total_ms,
                    },
                )

            equip_note = (
                f"Available Equipment Constraint: {decision.catalog_equipment_arg}\n"
                if decision.catalog_equipment_arg
                else ""
            )
            if decision.wants_workout_program:
                directive = (
                    "EXECUTION DIRECTIVE: The athlete wants to train around this injury. "
                    "First, write a clear 2-paragraph clinical coaching explanation in Markdown for the user to read. "
                    "Second, append a 3-to-4 exercise custom rehab/modified workout routine wrapped inside "
                    "<!-- WORKOUT_PAYLOAD_START --> and <!-- WORKOUT_PAYLOAD_END --> so the app can populate the 'Add Workout' button. "
                    "All items MUST set existsInCatalog: false, catalogId: null, and include explicit sets, reps, targetRpe, tempo, customInstructions, and coachingCue."
                )
                max_gen_tokens = 768
            else:
                directive = (
                    "EXECUTION DIRECTIVE: The athlete is asking a diagnostic/symptom question ONLY and did NOT "
                    "ask for a workout session. Provide a concise clinical explanation and 3 bulleted rehab cues "
                    "in pure Markdown. Do NOT emit <!-- WORKOUT_PAYLOAD_START --> or any JSON block."
                )
                max_gen_tokens = 384

            dynamic_turn_prompt = (
                f"{medical_res.context_block}\n\n"
                f"{equip_note}"
                f"Athlete Query: '{user_query}'\n\n"
                f"{directive}"
            )
            routing_tag = "CLASS_A_INJURY"
            tool_name = "search_medical_db"
            tool_meta = {
                "matched_ids": medical_res.matched_ids,
                "min_distance": medical_res.min_distance,
                "max_rerank_prob": medical_res.max_rerank_prob,
                "stage1_ms": medical_res.stage1_ms,
                "rerank_ms": medical_res.rerank_ms,
            }

        elif decision.intent == "CLASS_2_CATALOG_WORKOUT":
            catalog_res = self.tools.search_exercise_catalog(
                muscle=decision.catalog_muscle_arg,
                equipment=decision.catalog_equipment_arg,
                exclude_mechanics=decision.catalog_exclude_arg,
                limit=6,
            )
            rag_latency_ms = catalog_res.latency_ms
            candidate_list = [
                {
                    "catalogId": cid,
                    "name": self.catalog_lookup.get(cid, {}).get("name", cid),
                    "equipment": self.catalog_lookup.get(cid, {}).get("equipment", ""),
                }
                for cid in catalog_res.matched_ids[:6]
            ]
            dynamic_turn_prompt = (
                f"Catalog Search Results:\n"
                f"Target Muscles: {decision.catalog_muscle_arg or 'General'}\n"
                f"Equipment Available: {decision.catalog_equipment_arg or 'Commercial Gym'}\n"
                f"Excluded Constraints: {decision.catalog_exclude_arg or 'None'}\n"
                f"Candidate Catalog Exercises:\n{json.dumps(candidate_list, indent=2)}\n\n"
                f"Athlete Query: '{user_query}'\n\n"
                f"EXECUTION DIRECTIVE: First, write a concise 1-paragraph coaching rationale in Markdown for the user to read. "
                f"Second, append a 3-to-4 exercise workout routine using the verified catalogId values above (`existsInCatalog: true`), "
                f"including explicit sets, reps, targetRpe, tempo, customInstructions, and coachingCue, wrapped inside "
                f"<!-- WORKOUT_PAYLOAD_START --> and <!-- WORKOUT_PAYLOAD_END -->."
            )
            max_gen_tokens = 768
            routing_tag = "CLASS_C_CATALOG"
            tool_name = "search_exercise_catalog"
            tool_meta = {
                "muscle": decision.catalog_muscle_arg,
                "equipment": decision.catalog_equipment_arg,
                "exclude_mechanics": decision.catalog_exclude_arg,
                "matched_ids": catalog_res.matched_ids,
            }

        else:
            # CLASS_3_DIRECT_COACHING (Periodization, plateaus, deloads, technique)
            dynamic_turn_prompt = (
                f"Athlete Query: '{user_query}'\n\n"
                f"EXECUTION DIRECTIVE: Answer the athlete's periodization, plateau, recovery, or technique "
                f"question directly and concisely in Markdown using the Periodization Guidelines above. "
                f"Do NOT emit <!-- WORKOUT_PAYLOAD_START --> or any JSON block."
            )
            max_gen_tokens = 400
            routing_tag = "DIRECT_COACHING"
            tool_name = None
            tool_meta = {}

        # --- STAGE 3: Single-Pass Tiered Prefix-Cached LLM Synthesis (GPU 0) ---
        messages = self.build_tiered_messages(
            dynamic_turn_prompt=dynamic_turn_prompt,
            session_user_profile=session_user_profile,
        )
        raw_output, usage = await self._post_vllm_chat(
            model=self.base_model,
            messages=messages,
            temperature=0.1,
            max_tokens=max_gen_tokens,
        )

        chat_text, proposal = self._parse_synthesis_output(raw_output, is_clinical=is_clinical)
        total_ms = round((time.perf_counter() - t_start) * 1000.0, 2)

        return OrchestratorResponse(
            routing_class=routing_tag,
            chat_text=chat_text,
            has_workout=(proposal is not None),
            workout_proposal=proposal,
            telemetry={
                "router": "vela3-fast",
                "router_intent": decision.intent,
                "router_confidence": decision.intent_confidence,
                "wants_workout_program": decision.wants_workout_program,
                "router_latency_ms": decision.latency_ms,
                "tool_executed": tool_name,
                "rag_latency_ms": rag_latency_ms,
                "tool_meta": tool_meta,
                "llm_latency_ms": usage.get("llm_latency_ms"),
                "prompt_tokens": usage.get("prompt_tokens"),
                "completion_tokens": usage.get("completion_tokens"),
                "total_e2e_ms": total_ms,
            },
        )