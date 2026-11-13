# backend/agent_core/vela_router.py
import importlib
import os
import shutil
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import torch
from huggingface_hub import snapshot_download
from pydantic import BaseModel, Field


class RouterDecision(BaseModel):
    """Structured output of the single-pass batched Vela 3.0 Fast System-1 Router."""
    intent: str
    intent_confidence: float
    wants_workout_program: bool
    wants_workout_prob: float
    target_muscles: List[str] = Field(default_factory=list)
    available_equipment: List[str] = Field(default_factory=list)
    has_explicit_exclusion: bool = False
    exclusion_prob: float = 0.0
    excluded_constraints: List[str] = Field(default_factory=list)
    catalog_muscle_arg: Optional[str] = None
    catalog_equipment_arg: Optional[str] = None
    catalog_exclude_arg: Optional[str] = None
    latency_ms: float = 0.0
    raw_answers: Dict[str, Any] = Field(default_factory=dict)

    @property
    def confidence(self) -> float:
        return self.intent_confidence


ROUTER_QUESTIONS: Dict[str, Dict[str, Any]] = {
    "intent": {
        "type": "choice",
        "instructions": (
            "Classify the athlete's primary intent into one of the four categories below. "
            "If the athlete reports any pain, burning, pinching, aching, or barking tendon—even while "
            "requesting a workout—classify as CLASS_1_CLINICAL_RAG."
        ),
        "criteria": {
            "CLASS_0_RED_FLAG": (
                "Life-threatening emergency or severe acute trauma: crushing chest tightness radiating to jaw or arm, "
                "shortness of breath, loss of bladder or bowel control, saddle numbness, loud audible pop with muscle "
                "retraction or bruising, joint dislocation, or bone fracture."
            ),
            "CLASS_1_CLINICAL_RAG": (
                "Musculoskeletal injury, joint pain, tendon burning, pinching, aching, barking kneecap, elbow burning "
                "on grip, heel stabbing, or lift-provoked discomfort—including requests to give or prescribe a modified "
                "workout session or rehab routine around the symptom."
            ),
            "CLASS_2_CATALOG_WORKOUT": (
                "Standard hypertrophy, strength, or conditioning workout routine generation for target muscle groups "
                "and gym equipment by a healthy athlete."
            ),
            "CLASS_3_DIRECT_COACHING": (
                "General strength training theory, periodization, optimal rest periods between compound and isolation "
                "sets, training to muscular failure, deload week structure, weekly set volume (MEV/MAV/MRV), RPE "
                "autoregulation, or exercise execution technique without requesting a workout."
            ),
        },
    },
    "wants_workout_program": {
        "type": "noul",
        "instructions": (
            "Is the athlete asking for a workout routine, training session, or asking if they can get a workout in today "
            "(as opposed to asking 'what happened?', 'how should I deload?', or a form question)?"
        ),
    },
    "target_muscle": {
        "type": "choice",
        "instructions": "Which primary muscle group or body part does the athlete want to train?",
        "criteria": {
            "chest": "Chest, pectorals, pecs, bench press.",
            "back": "Back, lats, upper/middle back, pull-ups, rows.",
            "shoulders": "Shoulders, delts, deltoids, overhead press.",
            "biceps": "Biceps, bis, arm curls.",
            "triceps": "Triceps, tris, pushdowns, skullcrushers.",
            "arms": "Full arms, both biceps and triceps together, arm session.",
            "quadriceps": "Quads, quadriceps, front of thighs, squats.",
            "hamstrings": "Hamstrings, hams, leg curls, Romanian deadlifts.",
            "glutes": "Glutes, butt, hip thrusts, bridges.",
            "calves": "Calves, calf raises.",
            "legs": "Full lower body, legs, leg workout, leg day.",
            "lower back": "Lower back, lumbar erectors.",
            "traps": "Traps, trapezius, shrugs.",
            "abdominals": "Abs, abdominals, core.",
            "unspecified": "No specific muscle group or body part is being requested for training.",
        },
    },
    "has_equipment_constraint": {
        "type": "noul",
        "instructions": (
            "Does the athlete explicitly mention having specific workout equipment to use "
            "(such as dumbbells, rusty 20s, cables, machines, barbell, or bodyweight only)?"
        ),
    },
    "available_equipment": {
        "type": "choice",
        "instructions": "Which gym equipment does the athlete state they HAVE available to use?",
        "criteria": {
            "dumbbell": "Dumbbells, DBs, rusty 20s, pairs of weights.",
            "barbell": "Barbell, Olympic bar, squat rack, plates.",
            "cable": "Cables, cable machine, pulley tower.",
            "machine": "Gym machines, leg press, selectorized machines.",
            "body only": "Bodyweight only, calisthenics, no equipment.",
            "kettlebells": "Kettlebells.",
            "bands": "Resistance bands.",
            "commercial_gym_all": "Full commercial gym access or no specific equipment constraint.",
        },
    },
    "has_explicit_exclusion": {
        "type": "noul",
        "instructions": (
            "Does the athlete explicitly mention equipment, machines, or movement mechanics they DO NOT have, "
            "refuse to use, or want to avoid (e.g., 'no barbell', 'no machines', 'don't bend me over')?"
        ),
    },
    "excluded_constraint": {
        "type": "choice",
        "instructions": "Which equipment or movement mechanic does the athlete explicitly refuse or want to avoid?",
        "criteria": {
            "barbell": "Athlete states NO barbell or lacks a barbell.",
            "dumbbell": "Athlete states NO dumbbells.",
            "cable": "Athlete states NO cables.",
            "machine": "Athlete states NO machines.",
            "lower back": "Athlete wants to avoid bending over, lower back hinges, or axial spinal loading ('don't bend me over').",
            "none": "No equipment or movement mechanics are excluded or avoided.",
        },
    },
}


class VelaSystemOneRouter:
    """
    System-1 Bidirectional Decision Encoder (`vllm-sr/vela3-fast`, 380M UltraBERT backbone).
    Keeps native float32 master weights for full numerical stability while executing
    with hardware-adaptive Tensor Core autocast:
      - Ampere (sm_86, A10G) / Ada Lovelace (sm_89, L4, L40S): Native bfloat16 autocast.
      - Turing (sm_75, T4): High-throughput float16 autocast fallback.
    """

    def __init__(
        self,
        repo_id: str = "vllm-sr/vela3-fast",
        device: Optional[str] = None,
        secondary_slot_threshold: float = 0.22,
    ) -> None:
        env_device = os.environ.get("COPROCESSOR_DEVICE")
        if device is not None:
            self.device = device
        elif env_device:
            self.device = env_device
        elif torch.cuda.is_available():
            self.device = "cuda:1" if torch.cuda.device_count() > 1 else "cuda:0"
        else:
            self.device = "cpu"

        self.secondary_slot_threshold = secondary_slot_threshold
        self.autocast_dtype = (
            torch.bfloat16
            if (torch.cuda.is_available() and torch.cuda.is_bf16_supported())
            else torch.float16
        )

        local_dir = Path(
            snapshot_download(
                repo_id=repo_id,
                allow_patterns=["*.py", "*.json", "*.txt", "model.safetensors", "tokenizer*"],
            )
        )

        self._sanitize_vela3_artifacts(local_dir)

        if str(local_dir) not in sys.path:
            sys.path.insert(0, str(local_dir))

        import vela3_encoder
        importlib.reload(vela3_encoder)
        from vela3_encoder import DecisionEncoder

        self.encoder = DecisionEncoder.load(local_dir, device=self.device)
        _ = self.route("Warmup query for chest workout with dumbbells.")

    @staticmethod
    def _sanitize_vela3_artifacts(local_dir: Path) -> None:
        """
        Ensures vela3_encoder.py retains native float32 master weights while
        dispatching hardware-adaptive bfloat16 (sm_80+) / float16 (sm_75) autocast.
        """
        enc_file = local_dir / "vela3_encoder.py"
        if enc_file.exists():
            enc_code = enc_file.read_text(encoding="utf-8")
            modified = False

            # Defensively restore native float32 master weights if ever modified
            custom_dtype_str = "dtype=(torch.bfloat16 if (torch.cuda.is_available() and torch.cuda.is_bf16_supported()) else torch.float16)"
            if custom_dtype_str in enc_code:
                enc_code = enc_code.replace(custom_dtype_str, "dtype=torch.float32")
                modified = True

            if ".last_hidden_state.float()" in enc_code:
                enc_code = enc_code.replace(".last_hidden_state.float()", ".last_hidden_state")
                modified = True

            # Configure hardware-adaptive BF16/FP16 autocast
            if "_dtype = torch.bfloat16" not in enc_code:
                raw_lines = enc_code.splitlines()
                clean_lines = []
                for line in raw_lines:
                    if "amp = torch.autocast(" in line:
                        clean_lines.append(
                            '        _dtype = torch.bfloat16 if (torch.cuda.is_available() and torch.cuda.is_bf16_supported()) else torch.float16\n'
                            '        amp = torch.autocast("cuda", dtype=_dtype, enabled=str(self.device).startswith("cuda"))'
                        )
                    else:
                        clean_lines.append(line)
                enc_code = "\n".join(clean_lines)
                modified = True

            if modified:
                enc_file.write_text(enc_code, encoding="utf-8")
                hf_home = Path(os.environ.get("HF_HOME", Path.home() / ".cache" / "huggingface"))
                modules_cache = hf_home / "modules" / "transformers_modules"
                if modules_cache.exists():
                    shutil.rmtree(modules_cache, ignore_errors=True)
                print("✓ Configured vela3_encoder.py (native FP32 master weights + adaptive BF16/FP16 autocast).")

    @staticmethod
    def _extract_noul_prob(block: Dict[str, Any]) -> float:
        if "noul" in block and isinstance(block["noul"], (int, float)):
            return float(block["noul"])
        if "p_yes" in block and isinstance(block["p_yes"], (int, float)):
            return float(block["p_yes"])
        probs = block.get("probabilities", {})
        if isinstance(probs, dict) and "yes" in probs:
            return float(probs["yes"])
        return 1.0 if block.get("answer") == "yes" else 0.0

    def route(self, query: str) -> RouterDecision:
        t0 = time.perf_counter()
        with torch.inference_mode():
            raw_out = self.encoder.predict(query, ROUTER_QUESTIONS)
        latency_ms = round((time.perf_counter() - t0) * 1000.0, 2)

        if isinstance(raw_out, tuple):
            ans = raw_out[0]
        elif isinstance(raw_out, dict) and "answers" in raw_out and isinstance(raw_out["answers"], dict):
            ans = raw_out["answers"]
        else:
            ans = raw_out

        # 1. Intent Classification
        intent_block = ans.get("intent", {})
        intent = intent_block.get("choice", "CLASS_3_DIRECT_COACHING")
        intent_probs: Dict[str, float] = intent_block.get("probabilities", {})
        intent_conf = float(intent_block.get("confidence", intent_probs.get(intent, 0.0)))

        # 2. Workout Generation Gate
        wants_wo_block = ans.get("wants_workout_program", {})
        wants_wo_prob = self._extract_noul_prob(wants_wo_block)
        wants_workout = wants_wo_prob >= 0.50

        # 3. Multi-Label Target Muscle Extraction
        muscle_block = ans.get("target_muscle", {})
        primary_muscle = muscle_block.get("choice", "unspecified")
        muscle_probs: Dict[str, float] = muscle_block.get("probabilities", {})

        target_muscles: List[str] = []
        if primary_muscle and primary_muscle != "unspecified":
            target_muscles.append(primary_muscle)
            for m_key, m_prob in sorted(muscle_probs.items(), key=lambda x: x[1], reverse=True):
                if (
                    m_key not in (primary_muscle, "unspecified")
                    and float(m_prob) >= self.secondary_slot_threshold
                    and len(target_muscles) < 2
                ):
                    target_muscles.append(m_key)

        # 4. Explicit Negative Constraint Gate & Exclusion Extraction
        excl_gate_block = ans.get("has_explicit_exclusion", {})
        excl_prob = self._extract_noul_prob(excl_gate_block)
        has_exclusion = excl_prob >= 0.50

        excluded_constraints: List[str] = []
        if has_exclusion:
            excl_choice_block = ans.get("excluded_constraint", {})
            top_excl = excl_choice_block.get("choice", "none")
            if top_excl and top_excl != "none":
                excluded_constraints.append(top_excl)

        # 5. Positive Available Equipment (Gated by `has_equipment_constraint`)
        has_equip_block = ans.get("has_equipment_constraint", {})
        has_equip_prob = self._extract_noul_prob(has_equip_block)
        available_equipment: List[str] = []

        if has_equip_prob >= 0.50:
            equip_block = ans.get("available_equipment", {})
            primary_equip = equip_block.get("choice", "commercial_gym_all")
            equip_probs: Dict[str, float] = equip_block.get("probabilities", {})
            if primary_equip and primary_equip != "commercial_gym_all":
                available_equipment.append(primary_equip)
                for eq_key, eq_prob in sorted(equip_probs.items(), key=lambda x: x[1], reverse=True):
                    if (
                        eq_key not in (primary_equip, "commercial_gym_all")
                        and float(eq_prob) >= self.secondary_slot_threshold
                        and len(available_equipment) < 2
                    ):
                        available_equipment.append(eq_key)

        excluded_set = set(excluded_constraints)
        available_equipment = [eq for eq in available_equipment if eq not in excluded_set]

        catalog_muscle_arg = ", ".join(target_muscles) if target_muscles else None
        catalog_equipment_arg = ", ".join(available_equipment) if available_equipment else None
        catalog_exclude_arg = ", ".join(excluded_constraints) if excluded_constraints else None

        return RouterDecision(
            intent=intent,
            intent_confidence=round(intent_conf, 4),
            wants_workout_program=wants_workout,
            wants_workout_prob=round(wants_wo_prob, 4),
            target_muscles=target_muscles,
            available_equipment=available_equipment,
            has_explicit_exclusion=has_exclusion,
            exclusion_prob=round(excl_prob, 4),
            excluded_constraints=excluded_constraints,
            catalog_muscle_arg=catalog_muscle_arg,
            catalog_equipment_arg=catalog_equipment_arg,
            catalog_exclude_arg=catalog_exclude_arg,
            latency_ms=latency_ms,
            raw_answers=ans,
        )