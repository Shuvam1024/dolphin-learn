"""Turn a proposal into an immutable plan version when the learner accepts."""

from app.modules.curriculum.models import Competency
from app.modules.goals.models import Goal, TimeBudget
from app.modules.identity.models import User
from app.modules.learning.models import (
    ActivityVersion,
    LearningPath,
    Lesson,
    PlanActivity,
    PlanVersion,
)
from app.modules.learning.planner import PlanProposal
from app.modules.learning.proposals import propose_for_goal
from sqlalchemy import func, select
from sqlalchemy.orm import Session


def rationale_for(proposal: PlanProposal) -> str:
    lines = [
        f"Usable minutes: {proposal.usable_minutes}.",
        (
            "Estimated required minutes: "
            f"{proposal.estimated_required_low}–{proposal.estimated_required_high}."
        ),
    ]
    if proposal.scope_conflict:
        lines.append("Scope conflict: the low estimate is above the usable minutes.")
    if not proposal.deferred:
        lines.append("Deferred: none.")
    else:
        lines.append("Deferred:")
        for item in proposal.deferred:
            lines.append(f"- {item.key} ({item.reason_code})")
    return "\n".join(lines)


def _path(db: Session, user: User, goal: Goal) -> LearningPath:
    found = db.scalar(
        select(LearningPath).where(
            LearningPath.user_id == user.id,
            LearningPath.goal_id == goal.id,
        )
    )
    if found is not None:
        return found
    found = LearningPath(user_id=user.id, goal_id=goal.id)
    db.add(found)
    db.flush()
    return found


def accept_proposal(
    db: Session,
    user: User,
    goal: Goal,
    budget: TimeBudget,
) -> tuple[PlanVersion, PlanProposal]:
    proposal = propose_for_goal(db, goal, budget, None)
    path = _path(db, user, goal)
    latest = db.scalar(
        select(func.max(PlanVersion.version_number)).where(
            PlanVersion.learning_path_id == path.id
        )
    )
    version = PlanVersion(
        learning_path_id=path.id,
        version_number=(latest or 0) + 1,
        status="accepted",
        rationale=rationale_for(proposal),
        usable_minutes=proposal.usable_minutes,
    )
    db.add(version)
    db.flush()
    position = 1
    for item in proposal.included:
        activities = db.execute(
            select(ActivityVersion, Lesson.title)
            .join(Lesson, ActivityVersion.lesson_id == Lesson.id)
            .join(Competency, Lesson.competency_id == Competency.id)
            .where(Competency.key == item.key)
            .order_by(Lesson.key, ActivityVersion.version)
        ).all()
        for activity, lesson_title in activities:
            title = f"{lesson_title}: {activity.activity_type}"
            db.add(
                PlanActivity(
                    plan_version_id=version.id,
                    position=position,
                    title=title[:200],
                    estimated_minutes_low=activity.effort_minutes_low,
                    estimated_minutes_high=activity.effort_minutes_high,
                    activity_version_id=activity.id,
                )
            )
            position += 1
    db.commit()
    db.refresh(version)
    return version, proposal


def activities_for(db: Session, version: PlanVersion) -> list[PlanActivity]:
    rows = db.scalars(
        select(PlanActivity)
        .where(PlanActivity.plan_version_id == version.id)
        .order_by(PlanActivity.position)
    )
    return list(rows)


def latest_accepted(db: Session, user: User, goal: Goal) -> PlanVersion | None:
    return db.scalar(
        select(PlanVersion)
        .join(LearningPath, PlanVersion.learning_path_id == LearningPath.id)
        .where(
            LearningPath.user_id == user.id,
            LearningPath.goal_id == goal.id,
            PlanVersion.status == "accepted",
        )
        .order_by(PlanVersion.version_number.desc())
    )
