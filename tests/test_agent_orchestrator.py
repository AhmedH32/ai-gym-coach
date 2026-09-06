# tests/test_agent_orchestrator.py

import json
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from backend.agent_core.orchestrator import (
    GymCoachOrchestrator,
    WorkoutProposal,
    WorkoutItem
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent

@pytest.fixture
def mock_tools():
    """Mock instance of ClinicalRAGTools."""
    tools = MagicMock()
    
    # Mock Medical DB response for Patellar Tendinopathy
    tools.search_medical_db.return_value = {
        "status": "MATCH",
        "distance": 0.18,
        "card": {
            "condition_name": "Patellar Tendinopathy",
            "contraindications": ["Deep barbell squats"],
            "biomechanical_rules": ["Avoid knee shear"],
            "rehab_protocol": ["Spanish squat isometric"],
            "safe_alternatives": [
                {"exercise_id": "Leg_Press", "name": "Leg Press"}
            ]
        }
    }
    
    # Mock Catalog response
    tools.search_exercise_catalog.return_value = [
        {"id": "Dumbbell_Bench_Press", "name": "Dumbbell Bench Press", "equipment": "dumbbell"}
    ]
    return tools


@pytest.fixture
def orchestrator(mock_tools):
    """Initializes orchestrator with mock tools and point to real exercises.json."""
    orch = GymCoachOrchestrator(
        vllm_base_url="http://mock-vllm:8001/v1",
        project_root=PROJECT_ROOT,
        rag_tools=mock_tools
    )
    # Ensure our catalog lookup has at least the test dummy
    orch.catalog_lookup["Leg_Press"] = {"id": "Leg_Press", "name": "Leg Press"}
    return orch


@pytest.mark.asyncio
async def test_class_b_direct_coaching(orchestrator):
    """Test Class B (Periodization / Plateau) -> Direct text, no tools called."""
    # Pass 1 returns pure coaching text (no JSON tool call)
    direct_advice = "To break through your 5x5 plateau, introduce a 10% deload week followed by wave loading."
    orchestrator._post_vllm_chat = AsyncMock(return_value=direct_advice)

    response = await orchestrator.execute("I've been stuck on 100kg bench 5x5 for 3 weeks. What should I do?")

    assert response.routing_class == "DIRECT_COACHING"
    assert response.has_workout is False
    assert response.workout_proposal is None
    assert "plateau" in response.chat_text.lower()
    orchestrator.tools.search_medical_db.assert_not_called()


@pytest.mark.asyncio
async def test_class_a_medical_safety_circuit_breaker(orchestrator):
    """Test Medical Tool with tau > 0.38 triggers immediate safe exit."""
    # Pass 1 returns tool call
    tool_call_json = json.dumps({
        "tool_call": {
            "name": "search_medical_db",
            "arguments": {"query": "chest pain and shortness of breath"}
        }
    })
    orchestrator._post_vllm_chat = AsyncMock(return_value=tool_call_json)
    
    # Simulate ChromaDB reporting OUT_OF_SCOPE (distance 0.45 > 0.38)
    orchestrator.tools.search_medical_db.return_value = {
        "status": "OUT_OF_SCOPE",
        "distance": 0.45
    }

    response = await orchestrator.execute("I have sharp chest pain and can't breathe after my set.")

    assert response.routing_class == "CLASS_A_OUT_OF_SCOPE"
    assert response.has_workout is False
    assert "safety threshold exceeded" in response.chat_text
    assert response.telemetry["distance"] == 0.45
    # Verify Pass 2 was NEVER called (preserving safety)
    assert orchestrator._post_vllm_chat.call_count == 1


@pytest.mark.asyncio
async def test_class_a_injury_with_workout_synthesis(orchestrator):
    """Test full 2-stage flow: Injury -> ChromaDB MATCH -> Pass 2 Delimited JSON."""
    # Setup mock returns:
    # 1st call (Pass 1 Router): returns medical tool call
    pass1_output = json.dumps({
        "tool_call": {
            "name": "search_medical_db",
            "arguments": {"query": "knee tendon pain squats"}
        }
    })
    
    # 2nd call (Pass 2 Synthesizer): returns chat text + delimited workout JSON
    pass2_output = (
        "Your patellar tendon is inflamed. Here is an adapted leg session.\n\n"
        "<!-- WORKOUT_PAYLOAD_START -->\n"
        "{\n"
        '  "title": "Patellar-Sparing Leg Session",\n'
        '  "targetFocus": "Quads",\n'
        '  "estimatedMinutes": 30,\n'
        '  "items": [\n'
        "    {\n"
        '      "name": "Spanish Squat Hold",\n'
        '      "existsInCatalog": false,\n'
        '      "catalogId": null,\n'
        '      "category": "warmup_rehab",\n'
        '      "sets": 3,\n'
        '      "reps": "45s",\n'
        '      "customInstructions": ["Band behind knees", "Hold at 60 deg"]\n'
        "    },\n"
        "    {\n"
        '      "name": "Leg Press",\n'
        '      "existsInCatalog": true,\n'
        '      "catalogId": "Leg_Press",\n'
        '      "category": "compound",\n'
        '      "sets": 3,\n'
        '      "reps": "10-12"\n'
        "    }\n"
        "  ]\n"
        "}\n"
        "<!-- WORKOUT_PAYLOAD_END -->"
    )

    orchestrator._post_vllm_chat = AsyncMock(side_effect=[pass1_output, pass2_output])

    response = await orchestrator.execute("Knee tendon hurts on deep squats, what can I do on machines?")

    assert response.routing_class == "CLASS_A_INJURY"
    assert response.has_workout is True
    assert response.workout_proposal is not None
    assert response.workout_proposal.title == "Patellar-Sparing Leg Session"
    assert len(response.workout_proposal.items) == 2

    # Check Custom Rehab Item
    rehab_item = response.workout_proposal.items[0]
    assert rehab_item.existsInCatalog is False
    assert rehab_item.catalogId is None
    assert len(rehab_item.customInstructions) > 0

    # Check Catalog Item
    catalog_item = response.workout_proposal.items[1]
    assert catalog_item.existsInCatalog is True
    assert catalog_item.catalogId == "Leg_Press"


@pytest.mark.asyncio
async def test_sanitizer_demotes_hallucinated_ids(orchestrator):
    """Verifies that if Pass 2 hallucinates a non-existent catalog ID, it is demoted to custom."""
    proposal = WorkoutProposal(
        title="Test Session",
        targetFocus="Chest",
        items=[
            WorkoutItem(
                name="Invented Press",
                existsInCatalog=True,
                catalogId="Fake_Nonexistent_Exercise_123",  # NOT in catalog_lookup
                sets=3,
                reps="10"
            )
        ]
    )

    sanitized = orchestrator._sanitize_workout_items(proposal)
    item = sanitized.items[0]
    
    # Must be demoted to prevent frontend broken image errors
    assert item.existsInCatalog is False
    assert item.catalogId is None
    assert len(item.customInstructions) > 0