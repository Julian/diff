"""
The protocols which make up the difference protocol.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

if TYPE_CHECKING:
    from types import NotImplementedType

    from diff._diff import Differ


@runtime_checkable
class Difference(Protocol):
    """
    Some difference between two objects.

    Differences are directional -- they describe how a second object
    differs from a first one -- so every difference must know how to be
    turned around, which is what allows the right-hand side of a
    comparison to be the one which explains it.
    """

    def explain(self) -> str:
        """
        Explain this difference.

        Returns:

            a representation of the difference

        """
        ...

    def reversed(self) -> Difference:
        """
        The same difference, seen from the other direction.

        Returns:

            a difference where the two objects have swapped places

        """
        ...


@runtime_checkable
class Diffable[D_co: Difference](Protocol):
    """
    An object which can explain how other objects differ from it.

    `__diff__` should return:

        * `None` if there is no difference whatsoever

        * `NotImplemented` if it has no idea how to compare itself to
          the given object, in which case the other object gets a turn

        * otherwise, a `Difference`

    """

    def __diff__(self, other: Any) -> D_co | NotImplementedType | None: ...


class Implementation(Protocol):
    """
    A way to diff objects which is defined outside of the objects.

    Implementations exist for types which will never grow a `__diff__`
    of their own -- builtins, types from libraries you do not control,
    or whole categories of type like `attrs` classes.

    They follow the same convention as `Diffable.__diff__`, returning
    `NotImplemented` whenever they do not apply, and they are handed the
    `Differ` doing the work so that they can recurse into any pieces.
    """

    def __call__(
        self,
        differ: Differ,
        one: Any,
        two: Any,
    ) -> Difference | NotImplementedType | None: ...
