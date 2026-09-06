# backend/agent_core/orchestrator.py

import json
import os
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import httpx
from pydantic import BaseModel, Field

from backend.rag_engine.tools import ClinicalRAGTools

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
    "ROUTING RULES:\n"
    "1. Orthopedic Injuries & Joint/Tendon Pathology: If the user reports physical joint pain, tendon irritation, or acute musculoskeletal symptoms, "
    "you MUST output a tool call to 'search_medical_db' in strict JSON format.\n"
    "2. Periodization, Plateaus & Fatigue: For lifting stalls (e.g., 5x5 plateaus), high fatigue, DOMS, deloads, or volume management, "
    "reason directly from your internal training principles. Respond with direct coaching text WITHOUT calling medical tools.\n"
    "3. Exercise Selection: If specific exercise movements matching equipment or negative constraints are required, call 'search_exercise_catalog'.\n"
    "4. Technique & General Coaching: Respond with direct coaching text without tools."
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
    # Positive Anchor: Injury + Wants to Train -> Emits Markdown + Delimited JSON
    {
        "role": "user",
        "content": (
            "Clinical Reference Data:\n"
            "Condition: Patellar Tendinopathy (Jumper's Knee)\n"
            "Contraindicated Mechanics: Deep knee flexion past 90 degrees under load, forward knee shear.\n"
            "Acute Rehab Protocol: Spanish Squat Isometric Hold: 5 sets x 45s.\n"
            "Candidate Catalog Exercises:\n"
            "- ID: Leg_Press | Name: Leg Press | Equipment: Machine\n"
            "- ID: Seated_Leg_Curl | Name: Seated Leg Curl | Equipment: Machine\n\n"
            "Athlete Query: 'Tendon below my kneecap is barking on deep squats. Can I still get a leg workout using machines today?'"
        )
    },
    {
        "role": "assistant",
        "content": (
            "Your patellar tendon is reacting to high compressive and shear forces at deep knee flexion angles. "
            "We are pulling out free-weight back squats today and switching to movements that maintain a vertical tibia.\n\n"
            "We will begin with isometric Spanish squats to desensitize the patellar tendon, followed by high-and-wide foot placement "
            "on the leg press to train knee extension without anterior translation.\n\n"
            "<!-- WORKOUT_PAYLOAD_START -->\n"
            "{\n"
            '  "title": "Patellar-Sparing Lower Body Session",\n'
            '  "targetFocus": "Quads & Hamstrings",\n'
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
            '        "Anchor a heavy resistance band around a rig behind both knees.",\n'
            '        "Squat to approximately 60-70 degrees of knee flexion, maintaining a vertical shin angle.",\n'
            '        "Hold statically against band tension."\n'
            "      ],\n"
            '      "coachingCue": "Maintain continuous quadriceps tension without letting the knees track forward."\n'
            "    },\n"
            "    {\n"
            '      "name": "Leg Press",\n'
            '      "existsInCatalog": true,\n'
            '      "catalogId": "Leg_Press",\n'
            '      "category": "compound",\n'
            '      "sets": 3,\n'
            '      "reps": "10-12",\n'
            '      "targetRpe": 7,\n'
            '      "tempo": "3-0-1-0",\n'
            '      "customInstructions": [],\n'
            '      "coachingCue": "Place feet high and wide on the platform to shift load into the posterior chain and minimize forward shear."\n'
            "    },\n"
            "    {\n"
            '      "name": "Seated Leg Curl",\n'
            '      "existsInCatalog": true,\n'
            '      "catalogId": "Seated_Leg_Curl",\n'
            '      "category": "accessory",\n'
            '      "sets": 3,\n'
            '      "reps": "12-15",\n'
            '      "targetRpe": 8,\n'
            '      "tempo": "3-0-1-0",\n'
            '      "customInstructions": [],\n'
            '      "coachingCue": "Strict 3-second eccentric on every repetition to strengthen the knee flexors."\n'
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
            "Candidate Catalog Exercises: []\n\n"
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

        # Detect Project Root (assumes orchestrator is at backend/agent_core/)
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
            "1. Conversational Coaching: Address the user naturally in Markdown. Explain pathology, why certain mechanics are avoided, and provide actionable cues.\n"
            "2. Workout Intent Gate:\n"
            "   - IF the user asks to train, lift, or substitute exercises: Append a structured workout payload wrapped in `<!-- WORKOUT_PAYLOAD_START -->` and `<!-- WORKOUT_PAYLOAD_END -->`.\n"
            "   - IF the user ONLY asks about an injury, diagnosis, or pain mechanism without asking to train: Provide clinical triage and rehab advice ONLY. DO NOT output the workout payload block or delimiters.\n"
            "3. Exercise Schema Rules:\n"
            "   - For catalog exercises, set existsInCatalog: true and provide the exact catalogId.\n"
            "   - For clinical rehab protocols not in the standard catalog, set existsInCatalog: false, catalogId: null, and supply step-by-step cues in customInstructions.\n\n"
            "JSON FORMAT (Only when workout is appropriate):\n"
            "<!-- WORKOUT_PAYLOAD_START -->\n"
            "{\n"
            '  "title": "Descriptive Title",\n'
            '  "targetFocus": "Target Area",\n'
            '  "estimatedMinutes": 45,\n'
            '  "items": [\n'
            "    {\n"
            '      "name": "Exercise Name",\n'
            '      "existsInCatalog": true,\n'
            '      "catalogId": "Exact_ID_or_null",\n'
            '      "category": "warmup_rehab | compound | accessory",\n'
            '      "sets": 3,\n'
            '      "reps": "8-12",\n'
            '      "targetRpe": 7,\n'
            '      "tempo": "3-0-1-0",\n'
            '      "customInstructions": [],\n'
            '      "coachingCue": "Specific execution cue"\n'
            "    }\n"
            "  ]\n"
            "}\n"
            "<!-- WORKOUT_PAYLOAD_END -->"
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

    def _sanitize_workout_items(self, proposal: WorkoutProposal) -> WorkoutProposal:
        """Enforces referential integrity: demotes unverified catalog IDs to custom items."""
        for item in proposal.items:
            if item.existsInCatalog:
                if not item.catalogId or item.catalogId not in self.catalog_lookup:
                    item.existsInCatalog = False
                    item.catalogId = None
                    if not item.customInstructions:
                        item.customInstructions = [f"Execute {item.name} with controlled tempo ({item.tempo})."]
        return proposal

    def _parse_synthesis_output(self, raw_output: str) -> Tuple[str, Optional[WorkoutProposal]]:
        """Parses the text and the delimited JSON block."""
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
            proposal = self._sanitize_workout_items(proposal)
            return chat_text, proposal
        except Exception as e:
            print(f"Warning: Failed to parse workout JSON payload: {e}")
            return chat_text, None

    async def execute(self, user_query: str) -> OrchestratorResponse:
        """
        Executes the 2-Stage Deterministic DAG:
        1. Pass 1: Intent Triage (LoRA Router)
        2. Tool Execution & Circuit-Breaker Check (tau = 0.38)
        3. Pass 2: Grounded Synthesis (Base Qwen 2.5 with Radix cached Periodization)
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

        # --- STAGE 2: Direct Execution (Class B or Class D) ---
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

        # --- STAGE 3: Tool Execution & Medical Safety Circuit Breaker ---
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
            candidate_list = []
            for alt in clinical_card.get("safe_alternatives", []):
                if isinstance(alt, dict) and "exercise_id" in alt:
                    candidate_list.append(alt)
                elif isinstance(alt, str):
                    candidate_list.append({"catalogId": None, "name": alt})

            context_prompt = (
                f"Clinical Reference Data:\n"
                f"Condition: {clinical_card.get('condition_name', 'Musculoskeletal Condition')}\n"
                f"Contraindicated Movements: {clinical_card.get('contraindications', [])}\n"
                f"Contraindicated Mechanics: {clinical_card.get('biomechanical_rules', [])}\n"
                f"Acute Rehab Protocol: {clinical_card.get('rehab_protocol', [])}\n"
                f"Candidate Exercises: {json.dumps(candidate_list)}\n\n"
                f"Athlete Query: '{user_query}'"
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

            # Safely handle both dict and list returns from search_exercise_catalog
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
            else:
                candidate_list = []

            context_prompt = (
                f"Catalog Search Results:\n"
                f"Target Muscle: {muscle}\n"
                f"Equipment Available: {equipment}\n"
                f"Excluded Mechanics: {exclude}\n"
                f"Candidate Catalog Exercises:\n{json.dumps(candidate_list, indent=2)}\n\n"
                f"Athlete Query: '{user_query}'"
            )
            routing_tag = "CLASS_C_CATALOG"

        else:
            return OrchestratorResponse(
                routing_class="UNKNOWN_TOOL",
                chat_text=f"Unknown tool requested: {tool_name}",
                has_workout=False,
                workout_proposal=None
            )

        # --- STAGE 4: Pass 2 Grounded Synthesis ---
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

        chat_text, proposal = self._parse_synthesis_output(pass2_output)

        return OrchestratorResponse(
            routing_class=routing_tag,
            chat_text=chat_text,
            has_workout=(proposal is not None),
            workout_proposal=proposal,
            telemetry={
                "tool_executed": tool_name,
                "tool_args": args,
                "pass2_model": self.base_model
            }
        )