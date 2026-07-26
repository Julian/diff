"""
Pytest integration.
"""

from reprlib import Repr
from typing import Any

import pytest

from diff import Unequal, diff

#: pytest puts the first line we return next to the `assert`, where it
#: wants a summary of the comparison, not the start of an explanation.
_SUMMARY = Repr()
_SUMMARY.maxstring = _SUMMARY.maxother = 60


@pytest.hookimpl()
def pytest_assertrepr_compare(
    op: str,
    left: Any,
    right: Any,
) -> list[str] | None:
    """
    Explain why two objects which were expected to be equal differ.

    Returns:

        lines explaining the difference, or `None` to leave the
        assertion to pytest, which has perfectly good built-in output of
        its own whenever we have nothing specific to add

    """
    if op != "==":
        return None
    difference = diff(left, right)
    if difference is None or isinstance(difference, Unequal):
        return None
    summary = f"{_SUMMARY.repr(left)} == {_SUMMARY.repr(right)}"
    return [summary, *difference.explain().splitlines()]
