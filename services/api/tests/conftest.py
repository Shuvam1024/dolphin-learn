"""Shared pytest fixtures."""

from __future__ import annotations

import pytest
from app.rate_limit import clear_rate_limits


@pytest.fixture(autouse=True)
def _clear_rate_limits() -> None:
    clear_rate_limits()
    yield
    clear_rate_limits()
