"""Session Studio projection: position, estimate, activity state, and actions."""

from __future__ import annotations

import uuid
from typing import Any

from app.modules.ai_gateway.service import is_enabled
from app.modules.curriculum.models import Competency
from app.modules.goals.models import Goal
from app.modules.identity.models import User
from app.modules.learning.models import (
    ActivityVersion,
    LearningPath,
    LearningSession,
    Lesson,
    PlanActivity,
    PlanVersion,
    SessionEvent,
)
from app.modules.learning.sessions import activity_snapshot
from app.modules.learning.study_time import session_active_minutes
from sqlalchemy import select
from sqlalchemy.orm import Session

INPUT_KIND = {
    "reading": "none",
    "worked_example": "none",
    "objective": "choice",
    "short_answer": "text",
    "numeric": "number",
    "free_recall": "recall",
    "reflection": "text",
}


def _repeat_for_activity(
    db: Session,
    session: LearningSession,
    activity_id: uuid.UUID,
) -> bool:
    event = db.scalar(
        select(SessionEvent)
        .where(
            SessionEvent.session_id == session.id,
            SessionEvent.event_type == "fresh_check",
            SessionEvent.payload["activity_version_id"].astext == str(activity_id),
        )
        .order_by(SessionEvent.created_at.desc(), SessionEvent.id.desc())
    )
    if event is None:
        return False
    return str(event.payload.get("repeat", "")).lower() == "true"

INPUT_KIND = {
    "reading": "none",
    "worked_example": "none",
    "objective": "choice",
    "short_answer": "text",
    "numeric": "number",
    "free_recall": "recall",
    "reflection": "text",
}


def _plan_activities(db: Session, session: LearningSession) -> list[PlanActivity]:
    if session.plan_activity_id is None:
        return []
    current = db.get(PlanActivity, session.plan_activity_id)
    if current is None:
        return []
    return list(
        db.scalars(
            select(PlanActivity)
            .where(PlanActivity.plan_version_id == current.plan_version_id)
            .order_by(PlanActivity.position)
        )
    )


def _goal_for(db: Session, session: LearningSession) -> Goal | None:
    if session.plan_activity_id is None:
        return None
    plan = db.get(PlanActivity, session.plan_activity_id)
    if plan is None:
        return None
    version = db.get(PlanVersion, plan.plan_version_id)
    if version is None:
        return None
    path = db.get(LearningPath, version.learning_path_id)
    if path is None:
        return None
    return db.get(Goal, path.goal_id)


def compute_actions(
    *,
    activity_type: str,
    recorded: bool,
    outcome: str,
    assistance: str,
    help_kind: str,
    tutor_enabled: bool,
    challenge: bool,
    is_last: bool,
    awaiting_self_report: bool = False,
    stop_point: bool = False,
) -> dict[str, Any]:
    can_hint = activity_type in {"objective", "short_answer", "numeric"} and not recorded
    can_reveal = can_hint and help_kind == "none"
    can_fresh = recorded and assistance == "assisted" and not awaiting_self_report
    can_explain = tutor_enabled
    if activity_type in {"reading", "worked_example", "reflection"}:
        primary = "finish" if is_last else "continue"
    elif activity_type == "free_recall" and awaiting_self_report:
        primary = "submit"
    elif not recorded:
        primary = "submit"
    elif can_fresh:
        primary = "fresh_check"
    elif is_last:
        primary = "finish"
    else:
        primary = "continue"
    if stop_point and not awaiting_self_report and primary != "submit":
        primary = "finish"
    return {
        "primary": primary,
        "can_hint": can_hint,
        "can_reveal": can_reveal and not challenge,
        "can_fresh_check": can_fresh,
        "can_pause": True,
        "can_explain_differently": can_explain,
        "stop_point": stop_point and not awaiting_self_report,
        "awaiting_self_report": awaiting_self_report,
        "can_keep_going": stop_point and not is_last and not awaiting_self_report,
    }


def _sized_remaining(
    remaining: list[PlanActivity],
    target: int,
) -> tuple[int, int]:
    if not remaining:
        return 0, 0
    if target <= 0:
        return (
            sum(item.estimated_minutes_low for item in remaining),
            sum(item.estimated_minutes_high for item in remaining),
        )
    low = 0
    high = 0
    count = 0
    for item in remaining:
        next_low = low + item.estimated_minutes_low
        if count >= 1 and next_low > target:
            break
        low = next_low
        high += item.estimated_minutes_high
        count += 1
    return low, high


def build_studio(
    db: Session,
    user: User,
    session: LearningSession,
    *,
    mode: str = "guided",
) -> dict[str, Any]:
    activities = _plan_activities(db, session)
    total = len(activities)
    position = 1
    for index, item in enumerate(activities, start=1):
        if item.id == session.plan_activity_id:
            position = index
            break
    remaining = activities[position - 1 :] if activities else []
    goal = _goal_for(db, session)
    snap = activity_snapshot(db, session)
    challenge = mode == "challenge"
    tutor_on = is_enabled(db, user)
    active = session_active_minutes(db, session)
    target = int(getattr(session, "target_minutes", 0) or 0)
    if target <= 0 and goal is not None:
        from app.modules.goals.service import budget_for

        budget = budget_for(db, goal)
        if budget is not None and budget.preferred_session_minutes:
            target = budget.preferred_session_minutes
    low, high = _sized_remaining(remaining, target)
    lesson_title = ""
    competency_name = ""
    activity_payload: dict[str, Any] | None = None
    current_complete = True
    awaiting_self_report = False
    actions = compute_actions(
        activity_type="reading",
        recorded=False,
        outcome="",
        assistance="",
        help_kind="none",
        tutor_enabled=tutor_on,
        challenge=challenge,
        is_last=True,
        stop_point=False,
    )

    if session.plan_activity_id is not None:
        plan = db.get(PlanActivity, session.plan_activity_id)
        activity = (
            db.get(ActivityVersion, plan.activity_version_id)
            if plan and plan.activity_version_id
            else None
        )
        if activity is not None:
            lesson = db.get(Lesson, activity.lesson_id)
            if lesson is not None:
                lesson_title = lesson.title
                competency = db.get(Competency, lesson.competency_id)
                competency_name = competency.name if competency else ""
            choices: list[dict[str, str]] = []
            payload = activity.payload or {}
            raw_choices = payload.get("choices") if isinstance(payload, dict) else None
            if isinstance(raw_choices, list):
                for choice in raw_choices:
                    if isinstance(choice, dict):
                        choices.append(
                            {
                                "id": str(choice.get("id", "")),
                                "label": str(choice.get("label", "")),
                            }
                        )
            recorded = bool(snap and snap.get("recorded_choice"))
            outcome = str(snap.get("outcome") if snap else "")
            assistance = str(snap.get("attempt_assistance") if snap else "")
            help_kind = str(snap.get("help") if snap else "none")
            revealed = ""
            if not challenge and snap:
                revealed = str(snap.get("revealed_choice") or "")
            from app.modules.learning.tutor import tutor_state

            help_state = tutor_state(db, session, activity.id)
            explanation = ""
            misconception = ""
            misconception_source = "seed"
            show_feedback = recorded or bool(revealed)
            if show_feedback and activity.explanation:
                explanation = activity.explanation
            if (
                recorded
                and snap
                and snap.get("recorded_choice")
                and activity.misconceptions
                and activity.activity_type == "objective"
            ):
                key = str(snap["recorded_choice"])
                notes = activity.misconceptions
                if isinstance(notes, dict):
                    misconception = str(notes.get(key, ""))
            if recorded and activity.activity_type in {"short_answer", "numeric"}:
                from app.modules.learning.models import Attempt, Evaluation

                latest_attempt = db.scalar(
                    select(Attempt)
                    .where(
                        Attempt.session_id == session.id,
                        Attempt.activity_version_id == activity.id,
                    )
                    .order_by(Attempt.submitted_at.desc())
                )
                if latest_attempt is not None:
                    evaluation = db.scalar(
                        select(Evaluation).where(Evaluation.attempt_id == latest_attempt.id)
                    )
                    if evaluation is not None and evaluation.feedback_json:
                        note = evaluation.feedback_json.get("misconception_note")
                        source = evaluation.feedback_json.get("misconception_source")
                        if note:
                            misconception = str(note)
                            misconception_source = str(source or "ai")
            awaiting_self_report = outcome == "awaiting_self_report"
            self_rating = ""
            recall_covered: list[str] = []
            recall_missing: list[str] = []
            recall_feedback = ""
            if recorded and activity.activity_type == "free_recall":
                from app.modules.learning.models import Attempt, Evaluation

                latest_attempt = db.scalar(
                    select(Attempt)
                    .where(
                        Attempt.session_id == session.id,
                        Attempt.activity_version_id == activity.id,
                    )
                    .order_by(Attempt.submitted_at.desc())
                )
                if latest_attempt is not None:
                    self_rating = str(latest_attempt.response.get("self_rating", ""))
                    evaluation = db.scalar(
                        select(Evaluation).where(Evaluation.attempt_id == latest_attempt.id)
                    )
                    if evaluation is not None and evaluation.feedback_json:
                        covered = evaluation.feedback_json.get("covered") or []
                        missing = evaluation.feedback_json.get("missing") or []
                        if isinstance(covered, list):
                            recall_covered = [str(item) for item in covered]
                        if isinstance(missing, list):
                            recall_missing = [str(item) for item in missing]
                        recall_feedback = str(
                            evaluation.feedback_json.get("one_sentence_feedback", "") or ""
                        )
            body_markdown = lesson.body_markdown if lesson is not None else ""
            if activity.activity_type == "worked_example":
                payload_body = payload.get("body_markdown") if isinstance(payload, dict) else None
                if isinstance(payload_body, str) and payload_body.strip():
                    body_markdown = payload_body
            if activity.activity_type == "free_recall" and not recorded:
                body_markdown = ""
            activity_payload = {
                "activity_type": activity.activity_type,
                "item_id": activity.item_id,
                "title": lesson_title or (plan.title if plan else ""),
                "prompt_markdown": activity.prompt,
                "body_markdown": body_markdown,
                "input_kind": INPUT_KIND.get(activity.activity_type, "none"),
                "choices": choices,
                "provisional": activity.provisional,
                "state": {
                    "recorded": recorded,
                    "response": str(snap.get("recorded_choice") if snap else ""),
                    "outcome": outcome,
                    "assistance": assistance,
                    "hint_text": help_state["hint_text"],
                    "hint_source": help_state["hint_source"],
                    "revealed_answer": revealed,
                    "explanation": explanation,
                    "misconception_note": misconception,
                    "misconception_source": misconception_source,
                    "alt_explanation": help_state["alt_explanation"],
                    "repeat": _repeat_for_activity(db, session, activity.id),
                    "self_rating": self_rating,
                    "awaiting_self_report": awaiting_self_report,
                    "recall_covered": recall_covered,
                    "recall_missing": recall_missing,
                    "recall_feedback": recall_feedback,
                },
            }
            if activity.activity_type in {"reading", "worked_example", "reflection"}:
                current_complete = True
            elif awaiting_self_report:
                current_complete = False
            else:
                current_complete = recorded
            actions = compute_actions(
                activity_type=activity.activity_type,
                recorded=recorded,
                outcome=outcome,
                assistance=assistance,
                help_kind=help_kind,
                tutor_enabled=tutor_on,
                challenge=challenge,
                is_last=position >= total,
                awaiting_self_report=awaiting_self_report,
                stop_point=bool(target > 0 and active >= target and current_complete),
            )

    return {
        "id": str(session.id),
        "status": session.status,
        "active_minutes": active,
        "target_minutes": target,
        "goal": (
            {"id": str(goal.id), "title": goal.title}
            if goal is not None
            else {"id": "", "title": ""}
        ),
        "lesson": {"title": lesson_title, "competency_name": competency_name},
        "position": position,
        "total": total,
        "remaining_estimate": {"low": low, "high": high},
        "activity": activity_payload,
        "actions": actions,
        "tutor": {
            "enabled": tutor_on,
            "pending_request_id": "",
        },
        "summary": None,
    }
