# backend/agent_core/vela_router.py
import os
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


# Batched System-1 Decision Schema for vllm-sr/vela3-fast
ROUTER_QUESTIONS: Dict[str, Dict[str, Any]] = {
    "intent": {
        "type": "choice",
        "instructions": "Classify the athlete's primary request intent.",
        "criteria": {
            "CLASS_0_RED_FLAG": (
                "Acute medical emergency or severe clinical red flag: crushing chest pain, shortness of breath, "
                "loss of bladder/bowel control, saddle numbness, loud audible pop with muscle balling up/bruising, "
                "joint dislocation, bone fracture, or syncope/vertigo."
            ),
            "CLASS_1_CLINICAL_RAG": (
                "Musculoskeletal joint pain, tendonitis, tendinopathy, pinching, aching, strain, sprain, "
                "finger tingling at the elbow, or localized gym injury symptoms where the athlete asks what happened "
                "or how to train around the pain."
            ),
            "CLASS_2_CATALOG_WORKOUT": (
                "Pain-free workout routine, hypertrophy/strength session, or exercise selection request "
                "specifying target muscles, body parts, or gym equipment with no injury or pain reported."
            ),
            "CLASS_3_DIRECT_COACHING": (
                "General strength coaching question about periodization, 1RM plateaus/stalls, deload weeks, "
                "recovery, systemic fatigue, muscle soreness (DOMS), or lifting technique without pain."
            ),
        },
    },
    "wants_workout_program": {
        "type": "noul",
        "instructions": (
            "Is the athlete asking for a workout routine, training session, exercise prescription, "
            "or exercise substitutions to perform today (rather than only asking a diagnostic question "
            "like 'what happened?' or general deload advice)?"
        ),
    },
    "target_muscle": {
        "type": "choice",
        "instructions": "Which primary muscle group or body part does the athlete want to train?",
        "criteria": {
            "chest": "Chest, pectorals, pecs, bench press, push day.",
            "back": "Back, lats, middle back, V-taper, pull-ups, rows, pull day.",
            "shoulders": "Shoulders, delts, deltoids, overhead press, lateral raises.",
            "biceps": "Biceps, bis, arm curls, preacher curls, hammer curls.",
            "triceps": "Triceps, tris, pushdowns, skullcrushers, dips.",
            "arms": "Both biceps and triceps together, full arm workout, bis and tris.",
            "quadriceps": "Quads, quadriceps, front of thighs, squats, leg extensions.",
            "hamstrings": "Hamstrings, hams, leg curls, Romanian deadlifts, hip hinges.",
            "glutes": "Glutes, butt, hip thrusts, glute bridges.",
            "calves": "Calves, gastrocnemius, soleus, calf raises.",
            "legs": "Full lower body, legs, leg workout, leg day (quads, hamstrings, glutes, calves).",
            "lower back": "Lower back, lumbar spinal erectors.",
            "traps": "Traps, trapezius, upper back shrugs.",
            "abdominals": "Abs, abdominals, core, six-pack, planks.",
            "unspecified": "No specific target muscle group or body part is requested.",
        },
    },
    "available_equipment": {
        "type": "choice",
        "instructions": "Which gym equipment does the athlete state they HAVE available to use?",
        "criteria": {
            "dumbbell": "Athlete has dumbbells, DBs, pairs of weights, rusty 20s, or home dumbbell set.",
            "barbell": "Athlete has a barbell, Olympic bar, squat rack, power rack, or plates.",
            "cable": "Athlete has a cable machine, pulley tower, functional trainer, or cable stack.",
            "machine": "Athlete has selectorized gym machines, leg press, or chest press machine.",
            "body only": "Athlete wants bodyweight only, calisthenics, pull-up bar, dip bars, or no equipment.",
            "kettlebells": "Athlete has kettlebells.",
            "bands": "Athlete has resistance bands or elastic loop bands.",
            "e-z curl bar": "Athlete has an EZ-curl bar.",
            "commercial_gym_all": "Full commercial gym access or no specific equipment limitation stated.",
        },
    },
    "has_explicit_exclusion": {
        "type": "noul",
        "instructions": (
            "Does the athlete explicitly mention equipment, machines, or movement mechanics they DO NOT have, "
            "refuse to use, or want to avoid (e.g., 'no barbell', 'without cables', 'don't bend me over')?"
        ),
    },
    "excluded_constraint": {
        "type": "choice",
        "instructions": "Which equipment or movement mechanic does the athlete explicitly lack, refuse, or want to avoid?",
        "criteria": {
            "barbell": "Athlete states NO barbell, lacks a barbell/rack, or wants to avoid barbell exercises.",
            "dumbbell": "Athlete states NO dumbbells or lacks dumbbells.",
            "cable": "Athlete states NO cables, no pulley machine, or wants to avoid cables.",
            "machine": "Athlete states NO machines, free weights only, or lacks gym machines.",
            "compound": "Athlete wants isolation movements only and wants to avoid multi-joint compound lifts.",
            "lower back": "Athlete wants to avoid bending over, axial spinal loading, deadlifts, or unsupported bent-over rows ('don't bend me over').",
            "none": "The athlete does not exclude any equipment or movement mechanic.",
        },
    },
}


class VelaSystemOneRouter:
    """
    System-1 Bidirectional Decision Encoder (`vllm-sr/vela3-fast`, 380M UltraBERT backbone).
    Executes the 6-question routing & slot-extraction schema in a single non-autoregressive
    forward pass (~25-35ms on Tesla T4).
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

        # Download ONLY the 1.52GB DecisionEncoder core (skipping 5.1GB of unused LoRA task adapters)
        local_dir = Path(
            snapshot_download(
                repo_id=repo_id,
                allow_patterns=["*.py", "*.json", "*.txt", "model.safetensors", "tokenizer*"],
            )
        )
        if str(local_dir) not in sys.path:
            sys.path.insert(0, str(local_dir))

        from vela3_encoder import DecisionEncoder

        self.encoder = DecisionEncoder.load(local_dir, device=self.device)

        # Warmup pass to initialize CUDA kernels / memory allocators
        _ = self.route("Warmup query for chest workout with dumbbells.")

    @staticmethod
    def _extract_noul_prob(block: Dict[str, Any]) -> float:
        """Handles both DecisionEncoder.predict ('noul': float) and /v1/systemone formats."""
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
        raw_out = self.encoder.predict(query, ROUTER_QUESTIONS)
        latency_ms = round((time.perf_counter() - t0) * 1000.0, 2)

        # Normalize output container across DecisionEncoder.predict vs Vela3Encoder.system_one
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

        # 3. Multi-Label Target Muscle Extraction from Calibrated Distribution
        muscle_block = ans.get("target_muscle", {})
        primary_muscle = muscle_block.get("choice", "unspecified")
        muscle_probs: Dict[str, float] = muscle_block.get("probabilities", {})

        target_muscles: List[str] = []
        if primary_muscle != "unspecified":
            target_muscles.append(primary_muscle)
            for m_key, m_prob in sorted(muscle_probs.items(), key=lambda x: x[1], reverse=True):
                if (
                    m_key not in ("unspecified", primary_muscle)
                    and float(m_prob) >= self.secondary_slot_threshold
                    and len(target_muscles) < 2
                ):
                    target_muscles.append(m_key)

        # 4. Explicit Negative Constraint Gate & Exclusion Extraction
        excl_gate_block = ans.get("has_explicit_exclusion", {})
        excl_prob = self._extract_noul_prob(excl_gate_block)
        has_exclusion = excl_prob >= 0.45

        excluded_constraints: List[str] = []
        if has_exclusion:
            excl_choice_block = ans.get("excluded_constraint", {})
            top_excl = excl_choice_block.get("choice", "none")
            excl_probs: Dict[str, float] = excl_choice_block.get("probabilities", {})
            if top_excl != "none":
                excluded_constraints.append(top_excl)
            for e_key, e_prob in sorted(excl_probs.items(), key=lambda x: x[1], reverse=True):
                if (
                    e_key not in ("none", top_excl)
                    and float(e_prob) >= 0.25
                    and len(excluded_constraints) < 2
                ):
                    excluded_constraints.append(e_key)

        # 5. Positive Available Equipment + Deterministic Set-Difference Subtraction
        equip_block = ans.get("available_equipment", {})
        primary_equip = equip_block.get("choice", "commercial_gym_all")
        equip_probs: Dict[str, float] = equip_block.get("probabilities", {})

        available_equipment: List[str] = []
        if primary_equip != "commercial_gym_all":
            available_equipment.append(primary_equip)
            for eq_key, eq_prob in sorted(equip_probs.items(), key=lambda x: x[1], reverse=True):
                if (
                    eq_key not in ("commercial_gym_all", primary_equip)
                    and float(eq_prob) >= self.secondary_slot_threshold
                    and len(available_equipment) < 3
                ):
                    available_equipment.append(eq_key)

        # Subtract negatively excluded equipment (eliminates positive attention bleeding)
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