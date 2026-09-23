"""Pydantic shapes for on-disk curricula."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

ActivityType = Literal[
    "reading",
    "worked_example",
    "objective",
    "short_answer",
    "numeric",
    "free_recall",
    "reflection",
]


class EffortMinutes(BaseModel):
    model_config = ConfigDict(extra="forbid")

    low: int = Field(ge=0)
    high: int = Field(ge=0)


class DomainFile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    key: str
    name: str


class CompetencyFrontmatter(BaseModel):
    model_config = ConfigDict(extra="forbid")

    key: str
    name: str
    domain: str
    lesson_title: str
    requires: list[str] = Field(default_factory=list)
    effort_minutes: EffortMinutes
    reviewed_by: str
    reviewed_on: str


class ContentItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    type: ActivityType
    prompt: str
    choices: list[str] | None = None
    answer: str | None = None
    alternates: list[str] | None = None
    tolerance: float | None = None
    explanation: str | None = None
    misconceptions: dict[str, str] | list[Any] | None = None
    difficulty: int | None = Field(default=None, ge=1, le=3)
    effort_minutes: EffortMinutes


class CompetencyContent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path: str
    frontmatter: CompetencyFrontmatter
    reading_markdown: str
    worked_example_markdown: str | None = None
    items: list[ContentItem]
    line_map: dict[str, int] = Field(default_factory=dict)


class DomainContent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    domain: DomainFile
    competencies: list[CompetencyContent]
