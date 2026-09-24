"""Owned goal routes: create, list, get, and update, including time budgets."""

import uuid
from datetime import datetime
from typing import Literal

from app.db import get_db
from app.errors import ApiError
from app.modules.goals.budget import TimeBudgetSpec
from app.modules.goals.diagnostic import NOTE, skip_diagnostic, start_diagnostic, submit_diagnostic
from app.modules.goals.models import Goal, TimeBudget
from app.modules.goals.service import (
    budget_for,
    create_goal,
    get_owned_goal,
    list_goals,
    update_goal,
)
from app.modules.identity.deps import current_user
from app.modules.identity.models import User
from app.modules.learning.accept import accept_proposal, activities_for, latest_accepted
from app.modules.learning.copy import reason_text
from app.modules.learning.models import PlanVersion
from app.modules.learning.overview import build_overview
from app.modules.learning.plan_explain import explain_plan
from app.modules.learning.planner import PRIORITIES, normalize_priority
from app.modules.learning.proposals import propose_for_goal
from app.modules.learning.replan import (
    accept_replan,
    build_replan_proposal,
    proposal_hash,
    replan_goal,
)
from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, field_validator, model_validator
from sqlalchemy.orm import Session

router = APIRouter(prefix="/goals", tags=["goals"])

PriorityLiteral = Literal["understand", "apply", "make_it_stick"]
StatusLiteral = Literal["active", "paused", "archived"]
STATUSES = frozenset({"active", "paused", "archived"})


class NormalizeIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str

    @field_validator("text")
    @classmethod
    def _text(cls, value: str) -> str:
        return _clean_required(value)


class NormalizeOut(BaseModel):
    title: str
    domain_key: str
    outcomes: list[str]
    minutes_hint_per_outcome: int
    confidence: float
    source: str


@router.post("/normalize", response_model=NormalizeOut)
def post_normalize(
    body: NormalizeIn,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> NormalizeOut:
    from app.modules.goals.normalize import normalize_goal

    return NormalizeOut.model_validate(normalize_goal(db, user, body.text))


def _clean_required(value: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError("must not be empty")
    return cleaned


class GeneralOutcomeIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    statement: str
    minutes: int | None = None

    @field_validator("statement")
    @classmethod
    def _statement(cls, value: str) -> str:
        return _clean_required(value)


class GeneralIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    topic: str
    outcomes: list[GeneralOutcomeIn]
    notes_markdown: str | None = None

    @field_validator("topic")
    @classmethod
    def _topic(cls, value: str) -> str:
        return _clean_required(value)


class GoalIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    raw_request: str
    domain_key: str
    normalized_objective: str | None = None
    priority: PriorityLiteral = "understand"
    time_budget: TimeBudgetSpec | None = None
    general: GeneralIn | None = None

    @field_validator("title", "raw_request", "domain_key")
    @classmethod
    def _required_text(cls, value: str) -> str:
        return _clean_required(value)

    @field_validator("title")
    @classmethod
    def _title_length(cls, value: str) -> str:
        if len(value) > 200:
            raise ValueError("title must be 200 characters or fewer")
        return value

    @field_validator("normalized_objective")
    @classmethod
    def _objective(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    @field_validator("priority")
    @classmethod
    def _priority(cls, value: str) -> str:
        return normalize_priority(value)


class GoalUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = None
    raw_request: str | None = None
    domain_key: str | None = None
    normalized_objective: str | None = None
    priority: PriorityLiteral | None = None
    status: StatusLiteral | None = None
    time_budget: TimeBudgetSpec | None = None

    @field_validator("title", "raw_request", "domain_key")
    @classmethod
    def _optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _clean_required(value)

    @field_validator("title")
    @classmethod
    def _title_length(cls, value: str | None) -> str | None:
        if value is not None and len(value) > 200:
            raise ValueError("title must be 200 characters or fewer")
        return value

    @field_validator("normalized_objective")
    @classmethod
    def _objective(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    @field_validator("priority")
    @classmethod
    def _priority(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return normalize_priority(value)

    @field_validator("status")
    @classmethod
    def _status(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        if cleaned not in STATUSES:
            raise ValueError("status must be active, paused, or archived")
        return cleaned


class TimeBudgetOut(BaseModel):
    mode: Literal["one_off", "weekly"]
    one_off_minutes: int | None
    weekly_minutes_per_day: int | None
    horizon_days: int | None
    preferred_session_minutes: int


class GoalOut(BaseModel):
    id: uuid.UUID
    title: str
    raw_request: str
    domain_key: str
    normalized_objective: str | None
    priority: PriorityLiteral
    status: StatusLiteral
    created_at: datetime
    time_budget: TimeBudgetOut | None
    subject_name: str = ""
    next_lesson_title: str = ""
    remaining_minutes: int = 0
    usable_minutes: int = 0
    studied_minutes: int = 0


def _budget_out(row: TimeBudget | None) -> TimeBudgetOut | None:
    if row is None:
        return None
    mode: Literal["one_off", "weekly"] = "one_off" if row.mode == "one_off" else "weekly"
    return TimeBudgetOut(
        mode=mode,
        one_off_minutes=row.one_off_minutes,
        weekly_minutes_per_day=row.weekly_minutes_per_day,
        horizon_days=row.horizon_days,
        preferred_session_minutes=row.preferred_session_minutes,
    )


def _out(goal: Goal, budget: TimeBudget | None, *, card: dict[str, object] | None = None) -> GoalOut:
    priority = goal.priority if goal.priority in PRIORITIES else "understand"
    status = goal.status if goal.status in STATUSES else "active"
    extra = card or {}
    return GoalOut(
        id=goal.id,
        title=goal.title,
        raw_request=goal.raw_request,
        domain_key=goal.domain_key,
        normalized_objective=goal.normalized_objective,
        priority=priority,  # type: ignore[arg-type]
        status=status,  # type: ignore[arg-type]
        created_at=goal.created_at,
        time_budget=_budget_out(budget),
        subject_name=str(extra.get("subject_name", "")),
        next_lesson_title=str(extra.get("next_lesson_title", "")),
        remaining_minutes=int(extra.get("remaining_minutes", 0) or 0),
        usable_minutes=int(extra.get("usable_minutes", 0) or 0),
        studied_minutes=int(extra.get("studied_minutes", 0) or 0),
    )


@router.post("", response_model=GoalOut, status_code=201)
def post_goal(
    body: GoalIn,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> GoalOut:
    goal = create_goal(
        db,
        user,
        title=body.title,
        raw_request=body.raw_request,
        domain_key=body.domain_key,
        normalized_objective=body.normalized_objective,
        time_budget=body.time_budget,
        priority=body.priority,
        general=(
            None
            if body.general is None
            else body.general.model_dump()
        ),
    )
    return _out(goal, budget_for(db, goal))


@router.get("", response_model=list[GoalOut])
def get_goals(
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> list[GoalOut]:
    from app.modules.learning.home import _domain_name, _next_lesson_title
    from app.modules.learning.accept import latest_accepted
    from app.modules.learning.study_time import remaining_minutes, studied_minutes_for_goal

    rows: list[GoalOut] = []
    for goal in list_goals(db, user):
        version = latest_accepted(db, user, goal)
        usable = int(version.usable_minutes or 0) if version is not None else 0
        studied = studied_minutes_for_goal(db, user, goal)
        card = {
            "subject_name": _domain_name(db, goal.domain_key),
            "next_lesson_title": _next_lesson_title(db, user, goal) if version else "",
            "usable_minutes": usable,
            "studied_minutes": studied,
            "remaining_minutes": remaining_minutes(usable, studied),
        }
        rows.append(_out(goal, budget_for(db, goal), card=card))
    return rows


@router.patch("/{goal_id}", response_model=GoalOut)
def patch_goal(
    goal_id: uuid.UUID,
    body: GoalUpdate,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> GoalOut:
    sent = body.model_fields_set
    if not sent:
        raise ApiError("validation_error", "Update needs at least one field", status_code=422)
    goal = update_goal(
        db,
        user,
        goal_id,
        title=body.title,
        raw_request=body.raw_request,
        domain_key=body.domain_key,
        set_domain="domain_key" in sent,
        normalized_objective=body.normalized_objective,
        set_objective="normalized_objective" in sent,
        time_budget=body.time_budget,
        priority=body.priority,
        set_priority="priority" in sent,
        status=body.status,
        set_status="status" in sent,
    )
    return _out(goal, budget_for(db, goal))


class DiagnosticAnswerIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    activity_version_id: uuid.UUID
    choice: str

    @field_validator("choice")
    @classmethod
    def _choice(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("choice must not be empty")
        return cleaned


class DiagnosticIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: Literal["start", "skip", "submit"]
    answers: list[DiagnosticAnswerIn] | None = None

    @model_validator(mode="after")
    def answers_match_action(self) -> "DiagnosticIn":
        if self.action == "submit" and not self.answers:
            raise ValueError("submit needs at least one answer")
        return self


class DiagnosticItemOut(BaseModel):
    activity_version_id: uuid.UUID
    prompt: str


class DiagnosticAttemptOut(BaseModel):
    id: uuid.UUID
    activity_version_id: uuid.UUID


class DiagnosticOut(BaseModel):
    status: Literal["items", "skipped", "recorded"]
    mastery_claimed: bool
    note: str
    items: list[DiagnosticItemOut]
    attempts: list[DiagnosticAttemptOut]
    suggested_skip_keys: list[str] = []


@router.post("/{goal_id}/diagnostic", response_model=DiagnosticOut)
def post_diagnostic(
    goal_id: uuid.UUID,
    body: DiagnosticIn,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> DiagnosticOut:
    goal = get_owned_goal(db, user, goal_id)
    if body.action == "start":
        items = start_diagnostic(db, user, goal)
        return DiagnosticOut(
            status="items",
            mastery_claimed=False,
            note=NOTE,
            items=[
                DiagnosticItemOut(activity_version_id=item.id, prompt=item.prompt) for item in items
            ],
            attempts=[],
            suggested_skip_keys=[],
        )
    if body.action == "skip":
        skip_diagnostic(db, user, goal)
        return DiagnosticOut(
            status="skipped",
            mastery_claimed=False,
            note=NOTE,
            items=[],
            attempts=[],
            suggested_skip_keys=[],
        )
    assert body.answers is not None
    _run, attempts, suggestions = submit_diagnostic(
        db,
        user,
        goal,
        [(answer.activity_version_id, answer.choice) for answer in body.answers],
    )
    return DiagnosticOut(
        status="recorded",
        mastery_claimed=False,
        note=NOTE,
        items=[],
        attempts=[
            DiagnosticAttemptOut(id=attempt.id, activity_version_id=attempt.activity_version_id)
            for attempt in attempts
        ],
        suggested_skip_keys=suggestions,
    )


class ProposalIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    domain_key: str | None = None
    priority: PriorityLiteral | None = None
    skip_competency_keys: list[str] = []

    @field_validator("priority")
    @classmethod
    def _priority(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return normalize_priority(value)

    @field_validator("skip_competency_keys")
    @classmethod
    def _skips(cls, value: list[str]) -> list[str]:
        cleaned: list[str] = []
        for item in value:
            key = item.strip()
            if key and key not in cleaned:
                cleaned.append(key)
        return cleaned


class ProposalItemOut(BaseModel):
    competency_key: str
    name: str
    competency_name: str | None = None
    effort_low: int
    effort_high: int
    position: int | None = None
    reason_code: str | None = None
    reason_text: str | None = None
    practice_depth: str | None = None


class PlanExplanationOut(BaseModel):
    summary: str
    why_order: str
    what_is_left_out: str
    source: str


class ProposalOut(BaseModel):
    usable_minutes: int
    estimated_required_low: int
    estimated_required_high: int
    scope_conflict: bool
    included: list[ProposalItemOut]
    deferred: list[ProposalItemOut]
    priority: PriorityLiteral
    priority_label: str
    priority_effect: str
    review_reserve_minutes: int = 0
    learning_minutes: int = 0
    proposal_hash: str = ""
    plan_explanation: PlanExplanationOut | None = None


@router.post("/{goal_id}/plan-proposals", response_model=ProposalOut)
def post_plan_proposal(
    goal_id: uuid.UUID,
    body: ProposalIn | None = None,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> ProposalOut:
    """A proposal is a preview. It does not create a plan version."""
    goal = get_owned_goal(db, user, goal_id)
    budget = budget_for(db, goal)
    if budget is None:
        raise ApiError(
            "validation_error",
            "Add a time budget before asking for a plan",
            status_code=422,
        )
    override = None if body is None else body.priority
    skip_keys = None if body is None else body.skip_competency_keys
    proposal = propose_for_goal(
        db,
        goal,
        budget,
        None if body is None else body.domain_key,
        priority=override,
        skip_competency_keys=skip_keys,
    )
    digest = proposal_hash(proposal, studied=0, left=proposal.usable_minutes)
    explanation = explain_plan(
        db,
        user,
        proposal,
        proposal_hash=digest,
        goal_text=goal.raw_request or goal.title,
        remaining_minutes=proposal.usable_minutes,
    )
    return ProposalOut(
        usable_minutes=proposal.usable_minutes,
        estimated_required_low=proposal.estimated_required_low,
        estimated_required_high=proposal.estimated_required_high,
        scope_conflict=proposal.scope_conflict,
        included=[
            ProposalItemOut(
                competency_key=item.key,
                name=item.name,
                competency_name=item.name,
                effort_low=item.effort_low,
                effort_high=item.effort_high,
                position=item.position,
                practice_depth=item.practice_depth,
            )
            for item in proposal.included
        ],
        deferred=[
            ProposalItemOut(
                competency_key=item.key,
                name=item.name,
                competency_name=item.name,
                effort_low=item.effort_low,
                effort_high=item.effort_high,
                reason_code=item.reason_code,
                reason_text=reason_text(item.reason_code),
            )
            for item in proposal.deferred
        ],
        priority=proposal.priority,
        priority_label=proposal.priority_label,
        priority_effect=proposal.priority_effect,
        review_reserve_minutes=proposal.review_reserve_minutes,
        learning_minutes=proposal.learning_minutes,
        proposal_hash=digest,
        plan_explanation=PlanExplanationOut.model_validate(explanation),
    )


class PlanActivityOut(BaseModel):
    id: uuid.UUID
    position: int
    title: str
    estimated_minutes_low: int
    estimated_minutes_high: int


class AcceptedPlanOut(BaseModel):
    id: uuid.UUID
    version_number: int
    status: str
    rationale: str
    usable_minutes: int | None
    activities: list[PlanActivityOut]


def _plan_out(db: Session, version: PlanVersion) -> AcceptedPlanOut:
    return AcceptedPlanOut(
        id=version.id,
        version_number=version.version_number,
        status=version.status,
        rationale=version.rationale,
        usable_minutes=version.usable_minutes,
        activities=[
            PlanActivityOut(
                id=row.id,
                position=row.position,
                title=row.title,
                estimated_minutes_low=row.estimated_minutes_low,
                estimated_minutes_high=row.estimated_minutes_high,
            )
            for row in activities_for(db, version)
        ],
    )


@router.post("/{goal_id}/plans/accept", response_model=AcceptedPlanOut, status_code=201)
def post_accept_plan(
    goal_id: uuid.UUID,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> AcceptedPlanOut:
    goal = get_owned_goal(db, user, goal_id)
    budget = budget_for(db, goal)
    if budget is None:
        raise ApiError(
            "validation_error",
            "Add a time budget before accepting a plan",
            status_code=422,
        )
    version, _proposal = accept_proposal(db, user, goal, budget)
    return _plan_out(db, version)


@router.get("/{goal_id}/plan", response_model=AcceptedPlanOut)
def get_accepted_plan(
    goal_id: uuid.UUID,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> AcceptedPlanOut:
    goal = get_owned_goal(db, user, goal_id)
    version = latest_accepted(db, user, goal)
    if version is None:
        raise ApiError("not_found", "No accepted plan", status_code=404)
    return _plan_out(db, version)


class OverviewActivityOut(BaseModel):
    id: str
    position: int
    title: str
    label: str
    competency_key: str
    competency_name: str = ""
    lesson_title: str = ""
    facet: str = ""
    facet_label: str = ""
    effort: dict[str, int] = {}


class DeferredOut(BaseModel):
    competency_key: str
    competency_name: str = ""
    reason_code: str
    reason_text: str = ""


class ContinueOut(BaseModel):
    kind: str
    href: str
    goal_id: str


class PlanHistoryOut(BaseModel):
    version_number: int
    usable_minutes: int
    rationale: str


class OverviewOut(BaseModel):
    goal_id: str
    title: str
    version_number: int
    usable_minutes: int
    studied_minutes: int
    remaining_minutes: int = 0
    feasibility_note: str
    why_next: str
    continue_action: ContinueOut
    activities: list[OverviewActivityOut]
    deferred: list[DeferredOut]
    plan_history: list[PlanHistoryOut] = []


class ReplanProposalOut(BaseModel):
    proposal_hash: str
    usable_minutes: int
    remaining_minutes: int
    studied_minutes: int
    scope_conflict: bool
    included: list[ProposalItemOut]
    deferred: list[ProposalItemOut]
    priority_label: str = ""
    priority_effect: str = ""
    plan_explanation: PlanExplanationOut | None = None


class ReplanAcceptIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    proposal_hash: str


@router.post("/{goal_id}/replan-proposals", response_model=ReplanProposalOut)
def post_replan_proposal(
    goal_id: uuid.UUID,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> ReplanProposalOut:
    """Preview a replan. Writes nothing."""
    goal = get_owned_goal(db, user, goal_id)
    budget = budget_for(db, goal)
    if budget is None:
        raise ApiError(
            "validation_error",
            "Add a time budget before replanning",
            status_code=422,
        )
    proposal, studied, left, _ = build_replan_proposal(db, user, goal, budget)
    digest = proposal_hash(proposal, studied=studied, left=left)
    explanation = explain_plan(
        db,
        user,
        proposal,
        proposal_hash=digest,
        goal_text=goal.raw_request or goal.title,
        remaining_minutes=left,
    )
    return ReplanProposalOut(
        proposal_hash=digest,
        usable_minutes=proposal.usable_minutes,
        remaining_minutes=left,
        studied_minutes=studied,
        scope_conflict=proposal.scope_conflict,
        included=[
            ProposalItemOut(
                competency_key=item.key,
                name=item.name,
                competency_name=item.name,
                effort_low=item.effort_low,
                effort_high=item.effort_high,
                position=item.position,
                practice_depth=item.practice_depth,
            )
            for item in proposal.included
        ],
        deferred=[
            ProposalItemOut(
                competency_key=item.key,
                name=item.name,
                competency_name=item.name,
                effort_low=item.effort_low,
                effort_high=item.effort_high,
                reason_code=item.reason_code,
                reason_text=reason_text(item.reason_code),
            )
            for item in proposal.deferred
        ],
        priority_label=proposal.priority_label,
        priority_effect=proposal.priority_effect,
        plan_explanation=PlanExplanationOut.model_validate(explanation),
    )


@router.post("/{goal_id}/replan/accept", response_model=AcceptedPlanOut)
def post_replan_accept(
    goal_id: uuid.UUID,
    body: ReplanAcceptIn,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> AcceptedPlanOut:
    goal = get_owned_goal(db, user, goal_id)
    budget = budget_for(db, goal)
    if budget is None:
        raise ApiError(
            "validation_error",
            "Add a time budget before replanning",
            status_code=422,
        )
    version, _proposal = accept_replan(
        db, user, goal, budget, expected_hash=body.proposal_hash
    )
    return _plan_out(db, version)


@router.post("/{goal_id}/replan", response_model=AcceptedPlanOut, deprecated=True)
def post_replan(
    goal_id: uuid.UUID,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> AcceptedPlanOut:
    """Legacy one-shot replan. Prefer replan-proposals → replan/accept."""
    goal = get_owned_goal(db, user, goal_id)
    budget = budget_for(db, goal)
    if budget is None:
        raise ApiError(
            "validation_error",
            "Add a time budget before replanning",
            status_code=422,
        )
    version, _proposal = replan_goal(db, user, goal, budget)
    return _plan_out(db, version)


@router.get("/{goal_id}/overview", response_model=OverviewOut)
def get_overview(
    goal_id: uuid.UUID,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> OverviewOut:
    goal = get_owned_goal(db, user, goal_id)
    return OverviewOut.model_validate(build_overview(db, user, goal))


class OutlineOutcomeOut(BaseModel):
    statement: str
    reading_markdown: str
    recall_prompt: str
    reflection_prompt: str


class OutlineProposalOut(BaseModel):
    outcomes: list[OutlineOutcomeOut]
    source: str
    provisional: bool
    note: str


class OutlineAcceptIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    outcomes: list[OutlineOutcomeOut]


@router.post("/{goal_id}/outline-proposals", response_model=OutlineProposalOut)
def post_outline_proposal(
    goal_id: uuid.UUID,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> OutlineProposalOut:
    from app.modules.goals.outline import build_outline_proposal

    goal = get_owned_goal(db, user, goal_id)
    return OutlineProposalOut.model_validate(build_outline_proposal(db, user, goal))


@router.post("/{goal_id}/outline/accept")
def post_outline_accept(
    goal_id: uuid.UUID,
    body: OutlineAcceptIn,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    from app.modules.goals.outline import accept_outline

    goal = get_owned_goal(db, user, goal_id)
    applied = accept_outline(
        db,
        user,
        goal,
        [item.model_dump() for item in body.outcomes],
    )
    return {"applied": applied, "note": "Draft by the tutor — edit or remove"}


@router.delete("/{goal_id}/outline/items/{activity_id}")
def delete_outline_item(
    goal_id: uuid.UUID,
    activity_id: uuid.UUID,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    from app.modules.goals.outline import delete_provisional_item

    goal = get_owned_goal(db, user, goal_id)
    delete_provisional_item(db, user, goal, str(activity_id))
    return {"status": "deleted"}


@router.get("/{goal_id}", response_model=GoalOut)
def get_goal(
    goal_id: uuid.UUID,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> GoalOut:
    goal = get_owned_goal(db, user, goal_id)
    return _out(goal, budget_for(db, goal))
