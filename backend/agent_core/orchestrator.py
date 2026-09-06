# backend/agent_core/orchestrator.py

import json
import os
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import httpx
from pydantic import BaseModel, Field

# Support flexible project layouts
try:
    from backend.rag_engine.tools import ClinicalRAGTools
except ImportError:
    try:
        from backend.agent_core.rag_engine.clinical_rag import ClinicalRAGTools
    except ImportError:
        from backend.agent_core.rag_engine.tools import ClinicalRAGTools

# ------------------------------------------------------------------------------
# 1. Pydantic Schemas for Dual-Payload Contract
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
# 2. System Prompts & Dynamic Asset Loaders
# ------------------------------------------------------------------------------
ROUTER_SYSTEM_PROMPT = (
    "You are an elite Gym Coach AI. You manage user programming, injuries, and progressive overload. "
    "You have access to tools: 'search_medical_db(query)', 'search_exercise_catalog(muscle, equipment, exclude_mechanics)', "
    "and 'generate_workout(workout_json)'.\n\n"
    "CRITICAL PRECEDENCE RULE - MEDICAL FIRST:\n"
    "If the athlete mentions ANY pain, sharp sensations, tendon irritation, joint ache, tweak, or injury symptoms—"
    "EVEN IF THEY ASK TO TRAIN, SUBSTITUTE EXERCISES, OR LIST SPECIFIC EQUIPMENT IN THE SAME SENTENCE—"
    "you MUST call 'search_medical_db'. Medical safety takes absolute priority over exercise selection or catalog search.\n\n"
    "ROUTING RULES:\n"
    "1. Orthopedic Injuries & Musculoskeletal Pathology: Physical discomfort, joint/tendon irritation, acute pain -> MUST call 'search_medical_db'.\n"
    "2. Periodization, Plateaus & Fatigue: Lifting stalls, deloads, fatigue management, DOMS -> Respond directly with coaching text (no tools).\n"
    "3. Exercise Selection (Pain-Free Only): Requesting exercise options matching equipment or mechanics when NO pain is reported -> Call 'search_exercise_catalog'.\n"
    "4. Technique & General Coaching: General lifting form, warm-ups, or cues without pain -> Respond directly with coaching text (no tools)."
)


def load_periodization_corpus(project_root: Path) -> str:
    """Dynamically loads and concatenates the 5 periodization markdown docs for Radix caching."""
    periodization_dir = project_root / "prompt_assets" / "periodization"
    if not periodization_dir.exists():
        return ""

    docs = []
    for md_file in sorted(periodization_dir.glob("*.md")):
        try:
            docs.append(f"### {md_file.stem.replace('_', ' ').title()}\n{md_file.read_text(encoding='utf-8')}")
        except Exception as e:
            print(f"Warning: Failed to read {md_file}: {e}")

    return "\n\n".join(docs)


CONTRASTIVE_FEW_SHOTS = [
    # Positive Anchor: Injury + Wants to Train -> Emits Markdown + Delimited JSON (Custom rehab items, no catalog IDs)
    {
        "role": "user",
        "content": (
            "Clinical Reference Data:\n"
            "Condition: Patellar Tendinopathy (Jumper's Knee)\n"
            "Contraindicated Mechanics: Deep knee flexion past 90 degrees under load, forward knee shear, plyometrics, jumping.\n"
            "Acute Rehab Protocol: Spanish Squat Isometric Hold: 5 sets x 45s.\n"
            "Clinical Safe Alternatives:\n"
            "- Spanish Squat Isometric Hold\n"
            "- Dumbbell Romanian Deadlift (Hip Hinge Focus)\n"
            "- Seated Dumbbell Leg Extension Isometric (45-60 deg)\n\n"
            "Athlete Query: 'Tendon below my kneecap is barking on deep squats, but I have dumbbells. Can I still get a leg workout in today?'"
        )
    },
    {
        "role": "assistant",
        "content": (
            "Your patellar tendon is reacting to high compressive and shear forces at deep knee flexion angles. "
            "We are completely pulling out deep free-weight squats and all jumping/plyometrics today to give the extensor mechanism a rest.\n\n"
            "Instead, we will perform a specialized clinical routine: desensitizing the tendon with isometric quad loading, "
            "then loading the posterior chain via hip hinges with your dumbbells where the tibia stays vertical.\n\n"
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
            '        "Loop a heavy resistance band or towel behind both knees anchored to a secure post.",\n'
            '        "Squat to approximately 60 degrees of knee flexion, maintaining a vertical shin angle.",\n'
            '        "Hold statically against the tension while keeping quads engaged."\n'
            "      ],\n"
            '      "coachingCue": "Maintain constant quad tension without letting the knees migrate forward over toes."\n'
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
            '        "Hold dumbbells in front of thighs with soft, unlocked knees.",\n'
            '        "Push hips straight back toward the wall behind you with minimal additional knee flexion.",\n'
            '        "Hinge until hamstrings are fully loaded, then squeeze glutes to stand."\n'
            "      ],\n"
            '      "coachingCue": "Keep the tibia vertical. The movement happens at the hips, sparing the patellar tendon."\n'
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
            '        "Lie on back with feet flat and dumbbells resting securely on your hips.",\n'
            '        "Drive through heels and squeeze glutes hard at the top for a 1-second pause."\n'
            "      ],\n"
            '      "coachingCue": "Keep ribs down to prevent lower back hyperextension."\n'
            "    }\n"
            "  ]\n"
            "}\n"
            "<!-- WORKOUT_PAYLOAD_END -->"
        )
    },
    # Negative Anchor: Diagnostic Query Only -> Pure Markdown, NO Delimiters
    {
        "role": "user",
        "content": (
            "Clinical Reference Data:\n"
            "Condition: Subacromial Impingement Syndrome\n"
            "Contraindicated Mechanics: Flared elbows > 70 deg, internal rotation under horizontal abduction.\n"
            "Acute Rehab Protocol: Shoulder External Rotation Wall Isometric: 3 sets x 30s.\n"
            "Clinical Safe Alternatives:\n"
            "- Shoulder External Rotation Wall Isometric\n"
            "- Scapular Retraction Holds\n\n"
            "Athlete Query: 'Felt a sharp pinching pain in the front of my shoulder during flat bench press yesterday. What happened?'"
        )
    },
    {
        "role": "assistant",
        "content": (
            "A sharp anterior pinching sensation during the bottom turnaround of a flat bench press is classic for **subacromial impingement syndrome**. "
            "In this position, the supraspinatus tendon and the subacromial bursa become compressed beneath the acromion bone, "
            "most commonly caused by flared elbows (abduction > 70 degrees) or pressing with an excessively wide grip.\n\n"
            "### Immediate Action Plan:\n"
            "1. **Cease Flat Barbell Pressing:** Deload horizontal pressing until resting inflammation subsides.\n"
            "2. **Implement Wall Isometrics:** Perform 3 sets of 30-second external rotation holds against a wall to recruit the infraspinatus without shearing the joint.\n"
            "3. **Monitor Red Flags:** If you develop numbness radiating down the arm, severe night pain, or inability to raise your arm unassisted, seek prompt clinical evaluation from a physical therapist."
        )
    }
]


# ------------------------------------------------------------------------------
# 3. Core Orchestrator Implementation
# ------------------------------------------------------------------------------
class GymCoachOrchestrator:
    def __init__(
        self,
        vllm_base_url: str = "http://localhost:8001/v1",
        adapter_model_name: str = "gym_adapter",
        base_model_name: str = "Qwen/Qwen2.5-7B-Instruct",
        project_root: Optional[Path] = None,
        rag_tools: Optional[ClinicalRAGTools] = None
    ):
        self.vllm_base_url = os.environ.get("VLLM_BASE_URL", vllm_base_url).rstrip("/")
        self.adapter_model = os.environ.get("ADAPTER_NAME", adapter_model_name)
        self.base_model = os.environ.get("BASE_MODEL_NAME", base_model_name)

        if project_root is None:
            self.project_root = Path(__file__).resolve().parent.parent.parent
        else:
            self.project_root = project_root

        # 1. Initialize RAG Tools (ChromaDB + Inverted Index)
        self.tools = rag_tools if rag_tools else ClinicalRAGTools()

        # 2. Build In-Memory Fast Lookup for Catalog ID Verification
        self.catalog_lookup: Dict[str, Dict[str, Any]] = {}
        exercises_path = self.project_root / "raw_data" / "exercises.json"
        if not exercises_path.exists():
            exercises_path = self.project_root / "client" / "src" / "assets" / "data" / "exercises.json"

        if exercises_path.exists():
            with open(exercises_path, "r", encoding="utf-8") as f:
                raw_exercises = json.load(f)
                exercises_list = raw_exercises if isinstance(raw_exercises, list) else raw_exercises.get("exercises", [])
                for ex in exercises_list:
                    self.catalog_lookup[ex["id"]] = ex
            print(f"✓ Orchestrator indexed {len(self.catalog_lookup)} catalog exercises.")
        else:
            print(f"Warning: exercises.json not found at {exercises_path}")

        # 3. Assemble Radix-Cached Synthesizer System Prompt
        periodization_corpus = load_periodization_corpus(self.project_root)
        self.synthesizer_system_prompt = (
            "You are an elite Sports Medicine & Strength Conditioning Coach AI.\n"
            "You synthesize clinical diagnostic findings with evidence-based resistance training programming.\n\n"
            "=== PERIODIZATION GUIDELINES (Radix Cached) ===\n"
            f"{periodization_corpus}\n\n"
            "=== OUTPUT SPECIFICATION ===\n"
            "1. Conversational Coaching: Address the user directly in Markdown. Explain the pathology, biomechanical faults to avoid, and training rationale.\n"
            "2. Workout Intent Gate:\n"
            "   - IF the user asks to train, work out, or substitute exercises: You MUST append a complete structured workout proposal wrapped inside `<!-- WORKOUT_PAYLOAD_START -->` and `<!-- WORKOUT_PAYLOAD_END -->`.\n"
            "   - IF the user ONLY asks a diagnostic or symptom question without expressing intent to train: Provide clinical analysis and rehab cues in text ONLY. Do not emit the workout delimiters or payload.\n"
            "3. Exercise Prescription Standards (CRITICAL):\n"
            "   - For CLINICAL/INJURY sessions: All prescribed exercises MUST be set as custom movements (`existsInCatalog: false`, `catalogId: null`). You MUST provide explicit sets, reps, targetRpe, tempo, step-by-step customInstructions, and coachingCue.\n"
            "   - For PAIN-FREE CATALOG sessions: Exercises found in the candidate list can use `existsInCatalog: true` with their verified catalogId.\n"
            "   - Under no circumstances omit sets, reps, or volume parameters when prescribing a routine."
        )

    async def _post_vllm_chat(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.0,
        max_tokens: Optional[int] = 2048
    ) -> str:
        url = f"{self.vllm_base_url}/chat/completions"
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "stream": False
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code != 200:
                raise RuntimeError(
                    f"vLLM API rejected request [HTTP {resp.status_code}]: {resp.text}"
                )
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()

    def _sanitize_workout_items(self, proposal: WorkoutProposal, is_clinical: bool) -> WorkoutProposal:
        """Enforces schema integrity and custom protocol designations."""
        for item in proposal.items:
            if is_clinical:
                # All clinical rehab sessions are custom protocols by design
                item.existsInCatalog = False
                item.catalogId = None
            else:
                # Pain-free catalog route: verify ID existence
                if item.existsInCatalog:
                    if not item.catalogId or item.catalogId not in self.catalog_lookup:
                        item.existsInCatalog = False
                        item.catalogId = None

            # Guard against missing instructions or volume parameters
            if not item.customInstructions:
                item.customInstructions = [f"Perform {item.name} with controlled {item.tempo} tempo."]
            if not item.coachingCue:
                item.coachingCue = f"Focus on controlled execution and maintain proper form throughout."

        return proposal

    def _parse_synthesis_output(self, raw_output: str, is_clinical: bool) -> Tuple[str, Optional[WorkoutProposal]]:
        """Parses conversational coaching markdown and delimited structured JSON payload."""
        delimiter_start = "<!-- WORKOUT_PAYLOAD_START -->"
        delimiter_end = "<!-- WORKOUT_PAYLOAD_END -->"

        if delimiter_start not in raw_output:
            return raw_output.strip(), None

        parts = raw_output.split(delimiter_start)
        chat_text = parts[0].strip()
        remaining = parts[1]

        if delimiter_end in remaining:
            json_str = remaining.split(delimiter_end)[0].strip()
        else:
            json_str = remaining.strip()

        try:
            parsed_json = json.loads(json_str)
            proposal = WorkoutProposal(**parsed_json)
            proposal = self._sanitize_workout_items(proposal, is_clinical=is_clinical)
            return chat_text, proposal
        except Exception as e:
            print(f"Warning: Failed to parse workout JSON payload: {e}")
            return chat_text, None

    def _detect_injury_signals(self, query: str) -> bool:
        """Deterministic safety interceptor: catches physical pain/pathology keywords."""
        pattern = r"\b(pain|sharp|barking|hurt|hurts|tweak|tweaked|imping|tendon|tendonitis|tendinopathy|strain|sprain|pinch|pinching|pop|popped|soreness)\b"
        return bool(re.search(pattern, query, flags=re.IGNORECASE))

    async def execute(self, user_query: str) -> OrchestratorResponse:
        """
        Executes the 2-Stage Deterministic DAG:
        1. Pass 1: Intent Triage (LoRA Router) with deterministic Medical-First Interceptor.
        2. Stage 2: Tool Execution (Medical RAG or Pain-Free Catalog Search).
        3. Pass 2: Grounded Synthesis with full sets/reps and periodization.
        """
        # --- STAGE 1: Pass 1 Router ---
        pass1_messages = [
            {"role": "system", "content": ROUTER_SYSTEM_PROMPT},
            {"role": "user", "content": user_query}
        ]
        pass1_output = await self._post_vllm_chat(
            model=self.adapter_model,
            messages=pass1_messages,
            temperature=0.0,
            max_tokens=256
        )

        tool_call = None
        try:
            parsed = json.loads(pass1_output)
            if isinstance(parsed, dict) and "tool_call" in parsed:
                tool_call = parsed["tool_call"]
        except Exception:
            tool_call = None

        # Hard Guardrail: Any injury/symptom keyword mandates medical triage
        has_injury_symptoms = self._detect_injury_signals(user_query)
        if has_injury_symptoms:
            if not tool_call or tool_call.get("name") != "search_medical_db":
                print("[Safety Interceptor] Pathology detected in query. Enforcing route: 'search_medical_db'.")
                tool_call = {
                    "name": "search_medical_db",
                    "arguments": {"query": user_query}
                }

        # Direct Coaching (Class B periodization or Class D general advice)
        if not tool_call:
            return OrchestratorResponse(
                routing_class="DIRECT_COACHING",
                chat_text=pass1_output,
                has_workout=False,
                workout_proposal=None,
                telemetry={"tool_executed": None, "stage": "PASS_1_DIRECT"}
            )

        tool_name = tool_call.get("name")
        args = tool_call.get("arguments", {})
        is_clinical = (tool_name == "search_medical_db")

        # --- STAGE 2: Tool Execution ---
        if tool_name == "search_medical_db":
            query_arg = args.get("query", user_query)
            medical_result = self.tools.search_medical_db(query_arg)

            # Circuit Breaker: Tau > 0.38
            if medical_result.get("status") == "OUT_OF_SCOPE":
                return OrchestratorResponse(
                    routing_class="CLASS_A_OUT_OF_SCOPE",
                    chat_text=(
                        "Your query describes symptoms that fall outside our verified musculoskeletal sports "
                        "rehabilitation database (distance safety threshold exceeded). "
                        "For non-orthopedic symptoms or unverified pathology, please consult a qualified healthcare professional."
                    ),
                    has_workout=False,
                    workout_proposal=None,
                    telemetry={
                        "tool_executed": "search_medical_db",
                        "distance": medical_result.get("distance"),
                        "threshold": 0.38
                    }
                )

            clinical_card = medical_result.get("card", {})
            safe_alts = clinical_card.get("safe_alternatives", [])
            formatted_alts = []
            for alt in safe_alts:
                if isinstance(alt, dict):
                    formatted_alts.append(alt.get("name", alt.get("exercise_id", "")))
                elif isinstance(alt, str):
                    formatted_alts.append(alt)

            context_prompt = (
                f"Clinical Reference Data:\n"
                f"Condition: {clinical_card.get('condition_name', 'Musculoskeletal Condition')}\n"
                f"Contraindicated Movements: {clinical_card.get('contraindications', [])}\n"
                f"Contraindicated Mechanics: {clinical_card.get('biomechanical_rules', [])}\n"
                f"Acute Rehab Protocol: {clinical_card.get('rehab_protocol', [])}\n"
                f"Clinical Safe Alternatives:\n" + "\n".join(f"- {a}" for a in formatted_alts if a) + "\n\n"
                f"Athlete Query: '{user_query}'\n\n"
                f"PRESCRIPTION INSTRUCTION: The athlete wants to train around this condition. "
                f"Prescribe a complete custom workout routine adhering strictly to the contraindicated mechanics. "
                f"All workout items must have existsInCatalog: false, catalogId: null, and include explicit sets, reps, tempo, and cues."
            )
            routing_tag = "CLASS_A_INJURY"

        elif tool_name == "search_exercise_catalog":
            muscle = args.get("muscle", "")
            equipment = args.get("equipment", "")
            exclude = args.get("exclude_mechanics", "")

            catalog_results = self.tools.search_exercise_catalog(
                muscle=muscle,
                equipment=equipment,
                exclude_mechanics=exclude
            )

            candidate_list = []
            if isinstance(catalog_results, dict):
                matched_ids = catalog_results.get("matched_ids", [])
                candidate_list = [
                    {
                        "catalogId": cid,
                        "name": self.catalog_lookup.get(cid, {}).get("name", cid),
                        "equipment": self.catalog_lookup.get(cid, {}).get("equipment", "")
                    }
                    for cid in matched_ids[:10]
                ]
            elif isinstance(catalog_results, list):
                candidate_list = [
                    {
                        "catalogId": item.get("id", item.get("catalogId", "")),
                        "name": item.get("name", ""),
                        "equipment": item.get("equipment", "")
                    }
                    for item in catalog_results[:10]
                ]

            context_prompt = (
                f"Catalog Search Results:\n"
                f"Target Muscle: {muscle}\n"
                f"Equipment Available: {equipment}\n"
                f"Excluded Mechanics: {exclude}\n"
                f"Candidate Catalog Exercises:\n{json.dumps(candidate_list, indent=2)}\n\n"
                f"Athlete Query: '{user_query}'\n\n"
                f"PRESCRIPTION INSTRUCTION: Prescribe a complete workout routine utilizing the candidate catalog exercises. "
                f"All prescribed exercises must include explicit sets, reps, tempo, targetRpe, and coaching cues."
            )
            routing_tag = "CLASS_C_CATALOG"

        else:
            return OrchestratorResponse(
                routing_class="UNKNOWN_TOOL",
                chat_text=f"Unknown tool requested: {tool_name}",
                has_workout=False,
                workout_proposal=None
            )

        # --- STAGE 3: Pass 2 Grounded Synthesis ---
        pass2_messages = [
            {"role": "system", "content": self.synthesizer_system_prompt},
            *CONTRASTIVE_FEW_SHOTS,
            {"role": "user", "content": context_prompt}
        ]

        pass2_output = await self._post_vllm_chat(
            model=self.base_model,
            messages=pass2_messages,
            temperature=0.2,
            max_tokens=2048
        )

        chat_text, proposal = self._parse_synthesis_output(pass2_output, is_clinical=is_clinical)

        return OrchestratorResponse(
            routing_class=routing_tag,
            chat_text=chat_text,
            has_workout=(proposal is not None),
            workout_proposal=proposal,
            telemetry={
                "tool_executed": tool_name,
                "tool_args": args,
                "pass2_model": self.base_model,
                "safety_override": has_injury_symptoms
            }
        )