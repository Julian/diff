"""
Concrete kinds of difference.

The `Difference` protocol asks only for `explain` and `reversed`, which
is a deliberately low bar for anyone implementing `__diff__` on their
own type. The differences here are richer than that -- they keep hold of
the objects (or pieces of objects) involved, so that they can be
inspected, walked or re-rendered rather than only printed.
"""

from __future__ import annotations

from textwrap import indent
from typing import TYPE_CHECKING, Any

from attrs import field, frozen

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

    from diff._protocols import Difference


@frozen
class Constant:
    """
    A difference with a fixed explanation.

    Its explanation is assumed not to depend on which object came first,
    so reversing it does nothing. Say more than this if yours does.
    """

    _explanation: str = field(alias="explanation")

    def explain(self) -> str:
        """
        The explanation this difference was created with.
        """
        return self._explanation

    def reversed(self) -> Constant:
        """
        A constant explanation is the same in both directions.
        """
        return self


@frozen
class Unequal:
    """
    Two objects which are not equal, with nothing more to be said.

    This is what you get when nothing knows anything specific about the
    objects being compared, and is a signal to any caller that it likely
    can do better on its own.
    """

    _one: Any = field(alias="one")
    _two: Any = field(alias="two")

    def explain(self) -> str:
        """
        Simply show both objects.
        """
        return f"{self._one!r} != {self._two!r}"

    def reversed(self) -> Unequal:
        """
        Swap the two objects.
        """
        return Unequal(one=self._two, two=self._one)


@frozen
class DifferentTypes:
    """
    Two objects of differing type.

    They may even compare equal, as `1` and `True` do.
    """

    _one: Any = field(alias="one")
    _two: Any = field(alias="two")

    def explain(self) -> str:
        """
        Name both types alongside both objects.
        """
        one, two = type(self._one).__name__, type(self._two).__name__
        return f"{self._one!r} is a {one} but {self._two!r} is a {two}"

    def reversed(self) -> DifferentTypes:
        """
        Swap the two objects.
        """
        return DifferentTypes(one=self._two, two=self._one)


@frozen
class OnlyInOne:
    """
    Something present in the first object and missing from the second.
    """

    _value: Any = field(alias="value")

    def explain(self) -> str:
        """
        Show what is missing.
        """
        return f"{self._value!r} is only in the first object"

    def reversed(self) -> OnlyInTwo:
        """
        The same value, now only in the second object.
        """
        return OnlyInTwo(value=self._value)


@frozen
class OnlyInTwo:
    """
    Something present in the second object and missing from the first.
    """

    _value: Any = field(alias="value")

    def explain(self) -> str:
        """
        Show what is missing.
        """
        return f"{self._value!r} is only in the second object"

    def reversed(self) -> OnlyInOne:
        """
        The same value, now only in the first object.
        """
        return OnlyInOne(value=self._value)


@frozen
class Uncommon:
    """
    Two unordered collections, each containing what the other does not.
    """

    _one: frozenset[Any] = field(converter=frozenset, alias="one")
    _two: frozenset[Any] = field(converter=frozenset, alias="two")

    def explain(self) -> str:
        """
        Show what each collection has to itself.
        """
        lines: list[str] = []
        if self._one:
            lines.append(f"only in the first object: {_listed(self._one)}")
        if self._two:
            lines.append(f"only in the second object: {_listed(self._two)}")
        return "\n".join(lines)

    def reversed(self) -> Uncommon:
        """
        Swap the two collections.
        """
        return Uncommon(one=self._two, two=self._one)


@frozen
class Nested:
    """
    Differences found within the pieces of two larger objects.

    Each one is labelled with an accessor -- a snippet spelling out how
    to reach the differing piece, like ``['key']``, ``[0]`` or
    ``.attribute`` -- which is concatenated all the way down, so that
    explanations point directly at where to look.
    """

    _differences: tuple[tuple[str, Difference], ...] = field(
        converter=tuple,
        alias="differences",
    )

    def __iter__(self) -> Iterator[tuple[str, Difference]]:
        return iter(self._differences)

    def flattened(self) -> Iterable[tuple[str, Difference]]:
        """
        Each difference which isn't itself nested, and its full path.

        Returns:

            pairs of the path to reach a difference and the difference

        """
        for accessor, difference in self._differences:
            if isinstance(difference, Nested):
                for path, inner in difference.flattened():
                    yield f"{accessor}{path}", inner
            else:
                yield accessor, difference

    def explain(self) -> str:
        """
        Explain each difference, prefixed by where it was found.
        """
        lines: list[str] = []
        for path, difference in self.flattened():
            explanation = difference.explain()
            if "\n" in explanation:
                lines.append(f"{path}:\n{indent(explanation, '  ')}")
            else:
                lines.append(f"{path}: {explanation}")
        return "\n".join(lines)

    def reversed(self) -> Nested:
        """
        Reverse every difference, leaving the paths alone.
        """
        return Nested(
            differences=[
                (accessor, difference.reversed())
                for accessor, difference in self._differences
            ],
        )


def _listed(values: Iterable[Any]) -> str:
    """
    Show some values in an order which doesn't depend on hashing.
    """
    return ", ".join(sorted(repr(each) for each in values))
