from __future__ import annotations

from typing import TYPE_CHECKING, assert_type

from diff import Constant, Difference, diff

if TYPE_CHECKING:
    from types import NotImplementedType


class ConcreteDifference:
    def explain(self) -> str:
        return "foo"

    def reversed(self) -> ConcreteDifference:
        return self


class Something:
    def __diff__(self, other: object) -> ConcreteDifference:
        return ConcreteDifference()


assert_type(diff(Something(), Something()), ConcreteDifference | None)


class PartiallyDiffable:
    def __diff__(self, other: PartiallyDiffable) -> ConcreteDifference:
        return ConcreteDifference()


partially = PartiallyDiffable()
assert_type(diff(partially, partially), ConcreteDifference | None)


class MayDecline:
    """
    A `__diff__` which is allowed to say it has no idea, or no news.
    """

    def __diff__(
        self,
        other: object,
    ) -> Constant | None | NotImplementedType:
        return None


assert_type(diff(MayDecline(), 12), Constant | None)


class NotDiffableAtAll:
    pass


assert_type(diff(NotDiffableAtAll(), 12), Difference | None)
assert_type(diff("foo", "bar"), Difference | None)
assert_type(diff(1, 2), Difference | None)
