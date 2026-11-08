# backend/agent_core/orchestrator.py
import asyncio
import json
import os
import re
import time
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import httpx
from pydantic import BaseModel, Field, model_validator

from backend.agent_core.vela_router import RouterDecision, VelaSystemOneRouter
from backend.analytics_engine.recovery import AnalyticsEngine
from backend.rag_engine.tools import ClinicalRAGTools


# ------------------------------------------------------------------------------
# 1. Pydantic Schemas with Type Coercion
# ------------------------------------------------------------------------------
class WorkoutItem(BaseModel):
    name: str
    existsInCatalog: bool = False
    catalogId: Optional[str] = None
    category: str = Field(default="accessory", description="warmup_rehab | compound | accessory")
    sets: int = Field(default=3)
    reps: str = Field(default="8-12")
    targetRpe: Optional[int] = Field(default=7)
    tempo: Optional[str] = Field(default="3-0-1-0")
    customInstructions: Optional[List[str]] = Field(default_factory=list)
    coachingCue: Optional[str] = Field(default="")

    @model_validator(mode="before")
    @classmethod
    def coerce_llm_types(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        # Coerce reps to string
        if "reps" in data and data["reps"] is not None:
            data["reps"] = str(data["reps"]).strip()
        # Coerce sets to integer
        if "sets" in data and data["sets"] is not None:
            try:
                data["sets"] = int(float(str(data["sets"]).split("-")[0].strip()))
            except Exception:
                data["sets"] = 3
        # Coerce targetRpe to integer
        if "targetRpe" in data and data["targetRpe"] is not None:
            try:
                data["targetRpe"] = int(float(str(data["targetRpe"]).split("-")[0].strip()))
            except Exception:
                data["targetRpe"] = 7
        # Coerce single string instructions to list
        if "customInstructions" in data and isinstance(data["customInstructions"], str):
            data["customInstructions"] = [data["customInstructions"]]
        return data


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
    # Exemplar 1: Clinical Injury with Workout (Custom Protocols)
    {
        "role": "user",
        "content": (
            "### CLINICAL PROTOCOL: Patellar Tendinopathy (Knee) [ID: COND_PATELLAR_TENDINOPATHY]\n"
            "**Mechanism of Irritation:** Overload in patellar tendon provoked by deep knee flexion.\n"
            "## Absolute Contraindications: Deep knees-over-toes squats, plyometrics.\n"
            "## Biomechanical Modifications: Maintain vertical shin angle.\n"
            "## Recommended Substitutions: Spanish squats, Romanian deadlifts.\n\n"
            "Athlete Query: 'Tendon below my kneecap is barking on deep squats, but I have dumbbells. Can I still train legs?'\n\n"
            "EXECUTION DIRECTIVE: Prescribe a clinical explanation in Markdown followed by a 3-exercise custom rehab workout inside <!-- WORKOUT_PAYLOAD_START --> and <!-- WORKOUT_PAYLOAD_END -->. All items must have existsInCatalog: false, catalogId: null."
        ),
    },
    {
        "role": "assistant",
        "content": (
            "Your patellar tendon is reacting to high compressive shear forces at deep knee angles. We will eliminate deep squats and perform tendon-desensitizing isometrics and posterior chain hinges.\n\n"
            "<!-- WORKOUT_PAYLOAD_START -->\n"
            "{\n"
            '  "title": "Patellar-Sparing Dumbbell Session",\n'
            '  "targetFocus": "Lower Body Tendon Rehab",\n'
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
            '      "customInstructions": ["Sit back to 60 degrees knee flexion with strap behind knees.", "Maintain vertical shins."],\n'
            '      "coachingCue": "Do not let knees drift forward."\n'
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
            '      "customInstructions": ["Hinge at hips with soft knees.", "Lower dumbbells to mid-shin."],\n'
            '      "coachingCue": "Keep shins vertical to spare the patellar tendon."\n'
            "    }\n"
            "  ]\n"
            "}\n"
            "<!-- WORKOUT_PAYLOAD_END -->"
        ),
    },
    # Exemplar 2: Clinical Diagnostic ONLY (No Workout Payload)
    {
        "role": "user",
        "content": (
            "### CLINICAL PROTOCOL: Subacromial Impingement Syndrome (Shoulder) [ID: COND_SUBACROMIAL_IMPINGEMENT]\n"
            "**Mechanism of Irritation:** Compression of supraspinatus tendon under acromion during flared abduction.\n\n"
            "Athlete Query: 'Felt a sharp pinching pain in the front of my shoulder during flat bench press yesterday. What happened?'\n\n"
            "EXECUTION DIRECTIVE: Diagnostic question ONLY. Provide clinical coaching in Markdown ONLY. Do NOT emit <!-- WORKOUT_PAYLOAD_START --> or any JSON."
        ),
    },
    {
        "role": "assistant",
        "content": (
            "A sharp anterior pinch at the bottom of a flat bench press indicates **Subacromial Impingement Syndrome**. "
            "Flared elbows (>70°) compress the supraspinatus tendon beneath the acromion bone.\n\n"
            "### Immediate Action Plan:\n"
            "1. **Pause Flat Barbell Benching:** Switch to neutral-grip dumbbell pressing in the scapular plane.\n"
            "2. **Implement Wall Isometrics:** Perform 3 sets of 30-second external rotation holds against a wall to depressive the humeral head."
        ),
    },
    # Exemplar 3: Pain-Free Catalog Workout (Verified Catalog IDs)
    {
        "role": "user",
        "content": (
            "Catalog Search Results:\n"
            "Target Muscles: back, biceps\n"
            "Equipment Available: dumbbell\n"
            "Candidate Catalog Exercises:\n"
            '[\n  {"catalogId": "Bent_Over_Two-Dumbbell_Row", "name": "Bent Over Two-Dumbbell Row"},\n  {"catalogId": "Incline_Dumbbell_Curl", "name": "Incline Dumbbell Curl"}\n]\n\n'
            "Athlete Query: 'Build me a back and biceps workout with dumbbells.'\n\n"
            "EXECUTION DIRECTIVE: Prescribe a coaching rationale in Markdown followed by a 2-to-3 exercise routine using the verified catalogId values above (existsInCatalog: true) inside <!-- WORKOUT_PAYLOAD_START --> and <!-- WORKOUT_PAYLOAD_END -->."
        ),
    },
    {
        "role": "assistant",
        "content": (
            "Here is a targeted dumbbell pull session hitting the lats and elbow flexors with optimal resistance curves.\n\n"
            "<!-- WORKOUT_PAYLOAD_START -->\n"
            "{\n"
            '  "title": "Dumbbell Back & Biceps Hypertrophy",\n'
            '  "targetFocus": "Back & Biceps",\n'
            '  "estimatedMinutes": 40,\n'
            '  "items": [\n'
            "    {\n"
            '      "name": "Bent Over Two-Dumbbell Row",\n'
            '      "existsInCatalog": true,\n'
            '      "catalogId": "Bent_Over_Two-Dumbbell_Row",\n'
            '      "category": "compound",\n'
            '      "sets": 3,\n'
            '      "reps": "8-10",\n'
            '      "targetRpe": 8,\n'
            '      "tempo": "3-0-1-0",\n'
            '      "customInstructions": ["Hinge torso to 45 degrees.", "Row dumbbells toward hip pockets."],\n'
            '      "coachingCue": "Drive elbows back rather than pulling with wrists."\n'
            "    },\n"
            "    {\n"
            '      "name": "Incline Dumbbell Curl",\n'
            '      "existsInCatalog": true,\n'
            '      "catalogId": "Incline_Dumbbell_Curl",\n'
            '      "category": "accessory",\n'
            '      "sets": 3,\n'
            '      "reps": "10-12",\n'
            '      "targetRpe": 8,\n'
            '      "tempo": "3-0-1-1",\n'
            '      "customInstructions": ["Set bench to 60 degrees.", "Curl dumbbells while keeping upper arms fixed."],\n'
            '      "coachingCue": "Maximize stretch at the bottom without swinging."\n'
            "    }\n"
            "  ]\n"
            "}\n"
            "<!-- WORKOUT_PAYLOAD_END -->"
        ),
    },
]


# ------------------------------------------------------------------------------
# 3. Core Orchestrator
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

        self.http_client = httpx.AsyncClient(
            timeout=90.0,
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=50),
        )

        self.tools = rag_tools or ClinicalRAGTools(device=coprocessor_device)
        self.router = router or VelaSystemOneRouter(device=coprocessor_device)

        self.catalog_lookup: Dict[str, Dict[str, Any]] = {}
        for candidate_rel in ["raw_data/exercises.json", "client/src/assets/data/exercises.json"]:
            p = self.project_root / candidate_rel
            if p.exists():
                with open(p, "r", encoding="utf-8") as f:
                    raw_exercises = json.load(f)
                    exercises_list = raw_exercises if isinstance(raw_exercises, list) else raw_exercises.get("exercises", [])
                    for ex in exercises_list:
                        self.catalog_lookup[ex["id"]] = ex
                print(f"✓ Orchestrator indexed {len(self.catalog_lookup)} catalog exercises.")
                break

        periodization_corpus = load_periodization_corpus(self.project_root)
        self.synthesizer_system_prompt = (
            "You are an elite Sports Medicine & Strength Conditioning Coach AI.\n"
            "You synthesize clinical diagnostic findings with evidence-based resistance training programming.\n\n"
            "=== PERIODIZATION GUIDELINES (Radix Cached) ===\n"
            f"{periodization_corpus}\n\n"
            "=== OUTPUT SPECIFICATION (DUAL-PAYLOAD CONTRACT) ===\n"
            "1. Conversational Coaching: Address the user in Markdown (1 to 2 paragraphs). Explain pathology, rationale, and form cues.\n"
            "2. Workout Payload Gate:\n"
            "   - Follow the EXECUTION DIRECTIVE strictly.\n"
            "   - When instructed to prescribe a workout, output a valid JSON object matching the WorkoutProposal schema wrapped inside `<!-- WORKOUT_PAYLOAD_START -->` and `<!-- WORKOUT_PAYLOAD_END -->`.\n"
            "   - When instructed NOT to prescribe a workout, emit Markdown ONLY and NEVER output the delimiters.\n"
            "3. Exercise Prescription Standards:\n"
            "   - Prescribe 2 to 4 exercises per session with concise 1-sentence customInstructions.\n"
            "   - For CLINICAL sessions: existsInCatalog=false, catalogId=null.\n"
            "   - For CATALOG sessions: existsInCatalog=true, catalogId=verified ID from candidates."
        )

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
        max_tokens: int = 1024,
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

        json_str = self._RE_CODE_FENCE.sub("", json_str).strip()

        try:
            parsed_json = json.loads(json_str)
            proposal = WorkoutProposal(**parsed_json)
            proposal = self._sanitize_workout_items(proposal, is_clinical=is_clinical)
            return chat_text, proposal
        except Exception as e:
            print("\n❌ [PARSE ERROR] WorkoutProposal deserialization failed!")
            print(f"Error: {e}")
            print(f"Raw JSON payload:\n{json_str[:400]}")
            traceback.print_exc()
            return chat_text, None

    def build_tiered_messages(
        self,
        dynamic_turn_prompt: str,
        session_user_profile: Optional[str] = None,
    ) -> List[Dict[str, str]]:
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

        # 1. System-1 Decision Encoder Router
        decision: RouterDecision = await asyncio.to_thread(self.router.route, user_query)

        # Class 0: Acute Emergency Circuit Breaker
        if decision.intent == "CLASS_0_RED_FLAG":
            total_ms = round((time.perf_counter() - t_start) * 1000.0, 2)
            return OrchestratorResponse(
                routing_class="CLASS_A_OUT_OF_SCOPE",
                chat_text=(
                    "### URGENT CLINICAL TRIAGE ALERT\n"
                    "Your reported symptoms indicate an acute medical or neurological red flag. "
                    "Cease all physical training immediately and seek urgent medical evaluation."
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

        # 2. Tool Execution
        is_clinical = decision.intent == "CLASS_1_CLINICAL_RAG"
        rag_latency_ms = 0.0

        if is_clinical:
            medical_res = await asyncio.to_thread(self.tools.search_medical_db, user_query)
            rag_latency_ms = medical_res.latency_ms

            if medical_res.triage_required or medical_res.status != "MATCH_FOUND":
                total_ms = round((time.perf_counter() - t_start) * 1000.0, 2)
                return OrchestratorResponse(
                    routing_class="CLASS_A_OUT_OF_SCOPE",
                    chat_text=(
                        "Your query describes symptoms that fall outside our verified musculoskeletal sports "
                        "rehabilitation database. For acute or unverified pathology, please consult a physician."
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

            equip_note = f"Equipment Available: {decision.catalog_equipment_arg}\n" if decision.catalog_equipment_arg else ""
            if decision.wants_workout_program:
                directive = (
                    "EXECUTION DIRECTIVE: Prescribe a concise coaching explanation in Markdown, "
                    "then append a 2-to-3 exercise custom rehab workout routine inside "
                    "<!-- WORKOUT_PAYLOAD_START --> and <!-- WORKOUT_PAYLOAD_END -->. "
                    "All items MUST set existsInCatalog: false, catalogId: null."
                )
                max_gen_tokens = 1024
            else:
                directive = (
                    "EXECUTION DIRECTIVE: Diagnostic question ONLY. Provide clinical explanation in Markdown. "
                    "Do NOT emit <!-- WORKOUT_PAYLOAD_START --> or any JSON block."
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
            }

        elif decision.intent == "CLASS_2_CATALOG_WORKOUT":
            catalog_res = self.tools.search_exercise_catalog(
                muscle=decision.catalog_muscle_arg,
                equipment=decision.catalog_equipment_arg,
                exclude_mechanics=decision.catalog_exclude_arg,
                limit=5,
            )
            rag_latency_ms = catalog_res.latency_ms
            candidate_list = [
                {
                    "catalogId": cid,
                    "name": self.catalog_lookup.get(cid, {}).get("name", cid),
                }
                for cid in catalog_res.matched_ids[:5]
            ]
            dynamic_turn_prompt = (
                f"Catalog Search Results:\n"
                f"Target Muscles: {decision.catalog_muscle_arg or 'General'}\n"
                f"Equipment Available: {decision.catalog_equipment_arg or 'Commercial Gym'}\n"
                f"Candidate Catalog Exercises:\n{json.dumps(candidate_list, indent=2)}\n\n"
                f"Athlete Query: '{user_query}'\n\n"
                f"EXECUTION DIRECTIVE: Write a concise coaching rationale in Markdown, "
                f"then append a 2-to-3 exercise workout using the verified catalogId values above (existsInCatalog: true) "
                f"inside <!-- WORKOUT_PAYLOAD_START --> and <!-- WORKOUT_PAYLOAD_END -->."
            )
            max_gen_tokens = 1024
            routing_tag = "CLASS_C_CATALOG"
            tool_name = "search_exercise_catalog"
            tool_meta = {
                "matched_ids": catalog_res.matched_ids,
            }

        else:
            dynamic_turn_prompt = (
                f"Athlete Query: '{user_query}'\n\n"
                f"EXECUTION DIRECTIVE: Answer the athlete's coaching/periodization question directly in Markdown. "
                f"Do NOT emit <!-- WORKOUT_PAYLOAD_START --> or any JSON block."
            )
            max_gen_tokens = 400
            routing_tag = "DIRECT_COACHING"
            tool_name = None
            tool_meta = {}

        # 3. Single-Pass Tiered Prefix-Cached Synthesis
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