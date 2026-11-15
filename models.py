"""The shared task contract: validate input before it reaches SQLite or HTTP."""

import re
from datetime import date
from typing import Annotated

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    StrictBool,
    StringConstraints,
    field_validator,
)


def validate_date(value: str) -> str:
    """Accept only real calendar dates written exactly as YYYY-MM-DD."""
    if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value):
        raise ValueError("Use a date in YYYY-MM-DD format.")
    date.fromisoformat(value)  # Reject impossible dates, including invalid leap days.
    return value


# String limits keep accidental large input out of this small local application.
Title = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
Course = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)]
DateText = Annotated[str, AfterValidator(validate_date)]


class InputModel(BaseModel):
    """Reject misspelled fields rather than silently discarding user changes."""

    model_config = ConfigDict(extra="forbid")


class TaskCreate(InputModel):
    """Creation always starts with an incomplete task; the ID belongs to SQLite."""

    title: Title
    course: Course | None = None
    due_date: DateText | None = None


class TaskChanges(InputModel):
    """A sparse update: omitted values stay unchanged; null clears optional fields."""

    title: Title | None = None
    course: Course | None = None
    due_date: DateText | None = None
    completed: StrictBool | None = None

    @field_validator("title", "completed")
    @classmethod
    def reject_required_null(cls, value: object) -> object:
        """Defaults represent omission, but explicitly clearing required fields is invalid."""
        if value is None:
            raise ValueError("This field cannot be null.")
        return value


class TaskFilters(InputModel):
    """All filters combine with AND; due_before includes the specified date."""

    completed: bool | None = None
    course: Course | None = None
    due_before: DateText | None = None


class Task(TaskCreate):
    """The complete saved record returned by every successful write."""

    id: int
    completed: bool
