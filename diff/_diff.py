from difflib import ndiff
from typing import Any, Protocol, TypeVar, overload, runtime_checkable

from attrs import field, frozen


@runtime_checkable
class Difference(Protocol):
    def explain(self) -> str:
        """
        Explain this difference.

        Returns:

            a representation of the difference
        """
        ...


D_co = TypeVar("D_co", bound=Difference, covariant=True)


@runtime_checkable
class Diffable(Protocol[D_co]):
    def __diff__(self, other: Any) -> D_co: ...


@frozen
class Constant:
    _explanation: str = field(alias="explanation")

    def explain(self) -> str:
        return self._explanation


@overload
def diff(one: Diffable[D_co], two: Any) -> D_co | None: ...


@overload
def diff(one: str, two: str) -> Difference | None: ...


# I don't understand why repeating the annotation is needed here, but otherwise
# pyright says it doesn't know the return type. Overall the docs for overload
# also seem poor.
def diff(one: Diffable[D_co] | str, two: ...) -> ...:
    if one == two:
        return

    match (one, two):
        case Diffable(), _:
            return one.__diff__(two)
        case str(), str():
            result = "\n".join(ndiff(one.splitlines(), two.splitlines()))
        case _:
            result = f"{one!r} != {two!r}"

    return Constant(explanation=result)
