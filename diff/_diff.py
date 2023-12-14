from __future__ import annotations

from difflib import ndiff
from typing import Any, Protocol, runtime_checkable

from attrs import field, frozen


@runtime_checkable
class Diffable(Protocol):
    def __diff__(self, other: Any) -> Difference:
        ...


@runtime_checkable
class Difference(Protocol):
    def explain() -> str:
        """
        Explain this difference.

        Returns:

            a representation of the difference
        """


@frozen
class Constant:
    _explanation: str = field(alias="explanation")

    def explain(self):
        return self._explanation


def _no_specific_diff(one):
    return lambda two: Constant(f"{one!r} != {two!r}")


def diff(one, two) -> Difference:
    if one == two:
        return

    match one:
        case Diffable():
            diff = one.__diff__(two)
        case str():
            diff = "\n".join(ndiff(one.splitlines(), two.splitlines()))
        case _:
            return Constant(f"{one!r} != {two!r}")

    if isinstance(diff, Difference):
        return diff
    return Constant(explanation=diff)
