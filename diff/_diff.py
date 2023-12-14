from __future__ import annotations

from difflib import ndiff
from typing import Protocol, TypeVar, runtime_checkable

from attrs import field, frozen

T, U = TypeVar("T"), TypeVar("U")
T_co, U_co = TypeVar("T_co", covariant=True), TypeVar("U_co", covariant=True)


@runtime_checkable
class Diffable(Protocol):
    def __diff__(self: T, other: U) -> Difference[T, U]:
        ...


@runtime_checkable
class Difference(Protocol[T_co, U_co]):
    def explain(self) -> str:
        """
        Explain this difference.

        Returns:

            a representation of the difference
        """
        ...


@frozen
class Constant:
    _explanation: str = field(alias="explanation")

    def explain(self) -> str:
        return self._explanation


def diff(one: T, two: U) -> Difference[T, U] | None:
    if one == two:
        return

    match (one, two):
        case Diffable(), _:
            diff = one.__diff__(two)
        case str(), str():
            diff = "\n".join(ndiff(one.splitlines(), two.splitlines()))
        case _:
            return Constant(f"{one!r} != {two!r}")

    if isinstance(diff, Difference):
        return diff
    return Constant(explanation=diff)
