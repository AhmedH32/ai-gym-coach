# backend/analytics_engine/recovery.py
import math


class AnalyticsEngine:
    @staticmethod
    def calculate_e1rm(weight: float, reps: int) -> float:
        """Epley formula: e1RM = W * (1 + R / 30). Pure function."""
        if reps <= 0 or weight <= 0:
            return 0.0
        if reps == 1:
            return round(float(weight), 2)
        return round(float(weight) * (1.0 + (reps / 30.0)), 2)

    @staticmethod
    def calculate_recovery_percentage(hours_elapsed: float, k: float = 0.1, t0: float = 36.0) -> float:
        """Sigmoidal decay curve for biological recovery. Pure function."""
        if hours_elapsed < 0:
            return 0.0
        exponent = -k * (hours_elapsed - t0)
        exponent = max(min(exponent, 50.0), -50.0)
        recovery = 100.0 / (1.0 + math.exp(exponent))
        return round(max(0.0, min(100.0, recovery)), 1)

    @staticmethod
    def classify_volume_status(weekly_hard_sets: int) -> str:
        """Volume landmark tier: MEV_DEFICIT, OPTIMAL_MAV, or MRV_EXCEEDED."""
        if weekly_hard_sets < 6:
            return "MEV_DEFICIT"
        elif 6 <= weekly_hard_sets <= 20:
            return "OPTIMAL_MAV"
        else:
            return "MRV_EXCEEDED"

    @staticmethod
    def detect_plateau(e1rm_history: list[float], consecutive_threshold: int = 3) -> bool:
        """Evaluates whether a specific exercise has stalled over N sessions."""
        if len(e1rm_history) < consecutive_threshold:
            return False
        recent = e1rm_history[-consecutive_threshold:]
        for i in range(1, len(recent)):
            if recent[i] > recent[i - 1]:
                return False  # Progressive overload achieved
        return True

    @classmethod
    def evaluate_muscle_recovery(cls, target_muscle: str, hours_elapsed: float, weekly_sets: int) -> dict:
        """Evaluates systemic and local fatigue for a specific muscle group."""
        recovery_pct = cls.calculate_recovery_percentage(hours_elapsed)
        volume_status = cls.classify_volume_status(weekly_sets)
        return {
            "muscle": target_muscle,
            "recovery_pct": recovery_pct,
            "volume_status": volume_status,
            "weekly_sets": weekly_sets
        }

    @classmethod
    def evaluate_exercise_progression(cls, exercise_id: str, historical_e1rms: list[float]) -> dict:
        """Evaluates overload progression and plateau status for a specific movement pattern."""
        stalled = cls.detect_plateau(historical_e1rms)
        current_e1rm = historical_e1rms[-1] if historical_e1rms else 0.0
        return {
            "exercise_id": exercise_id,
            "current_e1rm": current_e1rm,
            "plateau_detected": stalled
        }

    @classmethod
    def build_system_context(
        cls, 
        muscle_states: list[dict], 
        stalled_exercises: list[str]
    ) -> str:
        """Formats the calculated states into a clean prompt injection block."""
        muscle_summaries = [
            f"{m['muscle']}: {m['recovery_pct']}% recovered ({m['volume_status']}, {m['weekly_sets']} sets)"
            for m in muscle_states
        ]
        muscles_str = " | ".join(muscle_summaries)
        plateau_str = f"Stalled Movements: {', '.join(stalled_exercises)}" if stalled_exercises else "No Stalled Movements"
        
        return f"[PHYSIOLOGICAL CONTEXT | {muscles_str} | {plateau_str}]"
