from __future__ import annotations

from diff import diff


class ConcreteDifference:
    def explain(self):
        return "foo"


class Something:
    def __diff__(self, other: object) -> ConcreteDifference:
        return ConcreteDifference()


difference: ConcreteDifference | None = diff(Something(), Something())
