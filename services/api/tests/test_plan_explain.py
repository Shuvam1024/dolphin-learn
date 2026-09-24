"""S76: AI plan explainer validates names and numbers; falls back when off or bad."""

import uuid

import pytest
from app.config import settings
from app.db import SessionLocal
from app.main import app
from app.modules.ai_gateway.service import get_fake_provider, reset_provider
from app.modules.learning.plan_explain import (
    PlanExplainOut,
    clear_explain_cache,
    validate_plan_explain,
)
from app.modules.learning.planner import DeferredCompetency, PlannedCompetency, PlanProposal
from app.seed import seed
from fastapi.testclient import TestClient

client = TestClient(app)


@pytest.fixture(autouse=True)
def _clean_explain() -> None:
    clear_explain_cache()
    reset_provider()
    fake = get_fake_provider()
    fake.scripts.clear()
    fake.calls.clear()
    yield
    clear_explain_cache()
    reset_provider()


def _proposal() -> PlanProposal:
    included = (
        PlannedCompetency(
            key="python.names",
            name="Names and values",
            effort_low=5,
            effort_high=8,
            position=1,
            practice_depth="standard",
        ),
    )
    deferred = (
        DeferredCompetency(
            key="python.calls",
            name="Calling a function",
            effort_low=10,
            effort_high=15,
            reason_code="insufficient_minutes",
        ),
    )
    return PlanProposal(
        included=included,
        deferred=deferred,
        usable_minutes=15,
        estimated_required_low=5,
        estimated_required_high=8,
        scope_conflict=True,
        priority="understand",
        priority_label="Understand",
        priority_effect="Fits more topics using the low effort estimate.",
        review_reserve_minutes=0,
        learning_minutes=15,
    )


def test_validate_plan_explain_rejects_invented_lesson_and_number() -> None:
    proposal = _proposal()
    names = {item.name for item in proposal.included} | {item.name for item in proposal.deferred}
    numbers = {15, 5, 8, 10, 1}
    good = PlanExplainOut(
        summary="Names and values comes first in 15 minutes.",
        why_order="Calling a function waits until later.",
        what_is_left_out="Calling a function is deferred.",
    )
    assert validate_plan_explain(good, allowed_names=names, allowed_numbers=numbers) is True

    invented = PlanExplainOut(
        summary="Quantum Basket Weaving is next.",
        why_order="Names and values follows.",
        what_is_left_out="Calling a function waits.",
    )
    assert validate_plan_explain(invented, allowed_names=names, allowed_numbers=numbers) is False

    bad_number = PlanExplainOut(
        summary="Names and values in 99 minutes.",
        why_order="Order is fine.",
        what_is_left_out="Calling a function waits.",
    )
    assert validate_plan_explain(bad_number, allowed_names=names, allowed_numbers=numbers) is False


def test_plan_explain_falls_back_when_ai_off(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "ai_gateway_enabled", False)
    monkeypatch.setattr(settings, "ai_provider", "")
    with SessionLocal() as db:
        seed(db)
    issued = client.post(
        "/api/v1/dev/token",
        json={"email": f"s76-off-{uuid.uuid4().hex[:8]}@example.com"},
    )
    headers = {"Authorization": f"Bearer {issued.json()['access_token']}"}
    created = client.post(
        "/api/v1/goals",
        headers=headers,
        json={
            "title": "Learn Python",
            "domain_key": "python",
            "raw_request": "Names and calls.",
            "time_budget": {
                "mode": "one_off",
                "one_off_minutes": 15,
                "preferred_session_minutes": 15,
            },
        },
    )
    goal_id = created.json()["id"]
    proposed = client.post(f"/api/v1/goals/{goal_id}/plan-proposals", headers=headers)
    assert proposed.status_code == 200
    body = proposed.json()
    explain = body["plan_explanation"]
    assert explain["source"] == "deterministic"
    assert "Understand" in explain["summary"] or "minutes" in explain["summary"].lower()
    assert explain["why_order"]
    assert explain["what_is_left_out"]


def test_plan_explain_ai_rejects_bad_script_and_caches(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "ai_gateway_enabled", True)
    monkeypatch.setattr(settings, "ai_provider", "fake")
    monkeypatch.setattr(settings, "ai_daily_cap", 50)
    reset_provider()
    fake = get_fake_provider()
    fake.script(
        "plan_explain",
        {
            "summary": "Quantum Basket Weaving in 99 minutes.",
            "why_order": "Because.",
            "what_is_left_out": "Everything.",
        },
        {
            "summary": "Names and values fits in 15 minutes.",
            "why_order": "Prerequisites first for Calling a function later.",
            "what_is_left_out": "Calling a function waits for more minutes.",
        },
    )
    with SessionLocal() as db:
        seed(db)
    issued = client.post(
        "/api/v1/dev/token",
        json={"email": f"s76-ai-{uuid.uuid4().hex[:8]}@example.com"},
    )
    headers = {"Authorization": f"Bearer {issued.json()['access_token']}"}
    created = client.post(
        "/api/v1/goals",
        headers=headers,
        json={
            "title": "Learn Python",
            "domain_key": "python",
            "raw_request": "Names and calls.",
            "time_budget": {
                "mode": "one_off",
                "one_off_minutes": 15,
                "preferred_session_minutes": 15,
            },
        },
    )
    goal_id = created.json()["id"]
    first = client.post(f"/api/v1/goals/{goal_id}/plan-proposals", headers=headers)
    assert first.status_code == 200
    assert first.json()["plan_explanation"]["source"] == "deterministic"
    assert "plan_explain" in fake.calls

    # Same hash should hit cache without another provider call.
    calls_before = len(fake.calls)
    second = client.post(f"/api/v1/goals/{goal_id}/plan-proposals", headers=headers)
    assert second.status_code == 200
    assert second.json()["plan_explanation"] == first.json()["plan_explanation"]
    assert len(fake.calls) == calls_before


def test_replan_proposal_includes_explanation(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "ai_gateway_enabled", True)
    monkeypatch.setattr(settings, "ai_provider", "fake")
    reset_provider()
    fake = get_fake_provider()
    fake.script(
        "plan_explain",
        {
            "summary": "Names and values fits the remaining minutes.",
            "why_order": "Keep prerequisites ahead of Calling a function.",
            "what_is_left_out": "Calling a function stays deferred.",
        },
    )
    with SessionLocal() as db:
        seed(db)
    issued = client.post(
        "/api/v1/dev/token",
        json={"email": f"s76-re-{uuid.uuid4().hex[:8]}@example.com"},
    )
    headers = {"Authorization": f"Bearer {issued.json()['access_token']}"}
    created = client.post(
        "/api/v1/goals",
        headers=headers,
        json={
            "title": "Learn Python",
            "domain_key": "python",
            "raw_request": "Names and calls.",
            "time_budget": {
                "mode": "one_off",
                "one_off_minutes": 120,
                "preferred_session_minutes": 30,
            },
        },
    )
    goal_id = created.json()["id"]
    client.post(f"/api/v1/goals/{goal_id}/plans/accept", headers=headers)
    preview = client.post(f"/api/v1/goals/{goal_id}/replan-proposals", headers=headers)
    assert preview.status_code == 200
    explain = preview.json()["plan_explanation"]
    assert explain["source"] == "ai"
    assert explain["summary"]
