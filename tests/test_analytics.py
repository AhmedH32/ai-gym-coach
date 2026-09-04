import pytest
from backend.analytics_engine.recovery import AnalyticsEngine


def test_calculate_e1rm_edge_cases():
    assert AnalyticsEngine.calculate_e1rm(0, 10) == 0.0
    assert AnalyticsEngine.calculate_e1rm(100, 0) == 0.0
    assert AnalyticsEngine.calculate_e1rm(-100, 5) == 0.0
    # 1 rep max must return the exact load without formula distortion
    assert AnalyticsEngine.calculate_e1rm(140.0, 1) == 140.0


def test_calculate_e1rm_epley_precision():
    # 100kg x 10 reps: 100 * (1 + 10/30) = 133.33kg
    assert AnalyticsEngine.calculate_e1rm(100.0, 10) == 133.33
    # 80kg x 6 reps: 80 * (1 + 6/30) = 96.00kg
    assert AnalyticsEngine.calculate_e1rm(80.0, 6) == 96.0


def test_sigmoidal_recovery_decay():
    # Negative time clamped to 0
    assert AnalyticsEngine.calculate_recovery_percentage(-10.0) == 0.0
    # Immediately post-workout (t = 0h)
    assert AnalyticsEngine.calculate_recovery_percentage(0.0) < 5.0
    # Midpoint inflection at t0 = 36h must be exactly 50.0%
    assert AnalyticsEngine.calculate_recovery_percentage(36.0) == 50.0
    # Fully recovered window (> 72h)
    assert AnalyticsEngine.calculate_recovery_percentage(72.0) > 95.0


def test_volume_status_landmarks():
    assert AnalyticsEngine.classify_volume_status(0) == "MEV_DEFICIT"
    assert AnalyticsEngine.classify_volume_status(5) == "MEV_DEFICIT"
    assert AnalyticsEngine.classify_volume_status(6) == "OPTIMAL_MAV"
    assert AnalyticsEngine.classify_volume_status(14) == "OPTIMAL_MAV"
    assert AnalyticsEngine.classify_volume_status(20) == "OPTIMAL_MAV"
    assert AnalyticsEngine.classify_volume_status(21) == "MRV_EXCEEDED"


def test_detect_plateau_logic():
    # Insufficient microcycle history (< 3 sessions)
    assert not AnalyticsEngine.detect_plateau([])
    assert not AnalyticsEngine.detect_plateau([100.0, 100.0])
    
    # Progressing lifter
    assert not AnalyticsEngine.detect_plateau([95.0, 97.5, 100.0])
    
    # Stalled lifter (identical e1RMs over 3 sessions)
    assert AnalyticsEngine.detect_plateau([100.0, 100.0, 100.0])
    
    # Regressing lifter (fatigue accumulation over 3 sessions)
    assert AnalyticsEngine.detect_plateau([102.5, 100.0, 97.5])


def test_decoupled_state_evaluation_and_context_injection():
    # 1. Muscle-level fatigue
    chest_state = AnalyticsEngine.evaluate_muscle_recovery("chest", hours_elapsed=48.0, weekly_sets=14)
    assert chest_state["recovery_pct"] == 76.9
    assert chest_state["volume_status"] == "OPTIMAL_MAV"

    # 2. Exercise-level progression
    bench_progression = AnalyticsEngine.evaluate_exercise_progression(
        exercise_id="barbell_bench_press",
        historical_e1rms=[100.0, 100.0, 100.0]
    )
    assert bench_progression["plateau_detected"] is True
    assert bench_progression["current_e1rm"] == 100.0

    # 3. Prompt string compilation
    prompt_str = AnalyticsEngine.build_system_context(
        muscle_states=[chest_state],
        stalled_exercises=[bench_progression["exercise_id"]]
    )
    
    assert "[PHYSIOLOGICAL CONTEXT" in prompt_str
    assert "chest: 76.9% recovered" in prompt_str
    assert "Stalled Movements: barbell_bench_press" in prompt_str