from __future__ import annotations

from diff import diff


class ConcreteDifference:
    def explain(self):
        return "foo"


class Something:
    def __diff__(self, other: object) -> ConcreteDifference:
        return ConcreteDifference()


difference: ConcreteDifference | None = diff(Something(), Something())


class PartiallyDiffable:
    def __diff__(self, other: PartiallyDiffable) -> ConcreteDifference:
        return ConcreteDifference()


partially = PartiallyDiffable()
difference: ConcreteDifference | None = diff(partially, partially)
