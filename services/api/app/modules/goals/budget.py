"""Validate a time budget before it is stored.

Calendar horizon and study minutes are different ideas. A budget is either one
block of minutes or a repeating weekly window — never both, and never negative.
"""

from typing import Literal

from pydantic import BaseModel, model_validator

BudgetMode = Literal["one_off", "weekly"]


class TimeBudgetSpec(BaseModel):
    mode: BudgetMode
    one_off_minutes: int | None = None
    weekly_minutes_per_day: int | None = None
    horizon_days: int | None = None
    preferred_session_minutes: int

    @model_validator(mode="after")
    def minutes_are_consistent(self) -> "TimeBudgetSpec":
        if self.preferred_session_minutes < 0:
            raise ValueError("preferred session minutes cannot be negative")
        if self.mode == "one_off":
            if self.one_off_minutes is None or self.one_off_minutes < 0:
                raise ValueError("one-off minutes must be zero or more")
            if self.weekly_minutes_per_day is not None or self.horizon_days is not None:
                raise ValueError("a one-off budget cannot also set a weekly window")
            return self
        if self.weekly_minutes_per_day is None or self.weekly_minutes_per_day < 0:
            raise ValueError("weekly minutes per day must be zero or more")
        if self.horizon_days is None or self.horizon_days <= 0:
            raise ValueError("a weekly budget needs a positive horizon in days")
        if self.one_off_minutes is not None:
            raise ValueError("a weekly budget cannot also set one-off minutes")
        return self
