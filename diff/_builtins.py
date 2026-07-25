"""
Ways to diff types which will never implement `__diff__` themselves.

Nothing here needs the cooperation of the type being diffed, which is
the point -- `int` is not going to grow a `__diff__` any time soon, and
neither is anyone else's library.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence, Set
from dataclasses import fields as dataclass_fields, is_dataclass
from difflib import ndiff
from os.path import commonprefix
from types import MappingProxyType, NotImplementedType
from typing import TYPE_CHECKING, Any

from attrs import fields as attrs_fields, has as is_attrs_class

from diff._differences import (
    Constant,
    DifferentTypes,
    Nested,
    OnlyInOne,
    OnlyInTwo,
    Uncommon,
    Unequal,
)

if TYPE_CHECKING:
    from diff._diff import Differ
    from diff._protocols import Difference, Implementation

#: Sequence types which are far better served by diffing them whole.
_NOT_REALLY_SEQUENCES = (str, bytes, bytearray)


def strings(
    differ: Differ,
    one: Any,
    two: Any,
) -> Difference | NotImplementedType | None:
    """
    Diff two strings, line by line if there is more than one of them.

    A one-line string gets shown whole rather than as a line diff, which
    would just be both strings again with markers in front of them, and
    which reads particularly badly nested inside a larger difference.
    """
    if not isinstance(one, str) or not isinstance(two, str):
        return NotImplemented
    if one == two:
        return None

    if "\n" in one or "\n" in two:
        lines = ndiff(one.splitlines(), two.splitlines())
        return Constant(explanation="\n".join(lines))

    common = len(commonprefix([one, two]))
    if not common:
        return Unequal(one=one, two=two)
    return Constant(
        explanation=f"{one!r} != {two!r} (differing at index {common})",
    )


def mappings(
    differ: Differ,
    one: Any,
    two: Any,
) -> Difference | NotImplementedType | None:
    """
    Diff two mappings key by key, recursing into their values.
    """
    if not isinstance(one, Mapping) or not isinstance(two, Mapping):
        return NotImplemented

    differences: list[tuple[str, Difference]] = []

    for key, value in one.items():
        accessor = f"[{key!r}]"
        if key not in two:
            differences.append((accessor, OnlyInOne(value=value)))
        else:
            difference = differ(value, two[key])
            if difference is not None:
                differences.append((accessor, difference))

    differences.extend(
        (f"[{key!r}]", OnlyInTwo(value=value))
        for key, value in two.items()
        if key not in one
    )

    if not differences:
        return None
    return Nested(differences=differences)


def sets(
    differ: Differ,
    one: Any,
    two: Any,
) -> Difference | NotImplementedType | None:
    """
    Diff two unordered collections by what each has to itself.
    """
    if not isinstance(one, Set) or not isinstance(two, Set):
        return NotImplemented
    only_one, only_two = one - two, two - one
    if not only_one and not only_two:
        return None
    return Uncommon(one=only_one, two=only_two)


def sequences(
    differ: Differ,
    one: Any,
    two: Any,
) -> Difference | NotImplementedType | None:
    """
    Diff two sequences index by index, recursing into their elements.

    Sequences of unrelated types simply differ by type, since no
    element-by-element story would explain why they aren't equal.
    """
    if not isinstance(one, Sequence) or not isinstance(two, Sequence):
        return NotImplemented
    if isinstance(one, _NOT_REALLY_SEQUENCES):
        return NotImplemented
    if isinstance(two, _NOT_REALLY_SEQUENCES):
        return NotImplemented

    # `Sequence`, unlike `Mapping` and `Set`, supplies no `__eq__`, so
    # sequences of unrelated types are unequal however their elements
    # compare -- and saying a list is not a tuple beats pointing at some
    # element as if changing it would help.
    if not isinstance(one, type(two)) and not isinstance(two, type(one)):
        return DifferentTypes(one=one, two=two)

    differences: list[tuple[str, Difference]] = []
    for index in range(min(len(one), len(two))):
        difference = differ(one[index], two[index])
        if difference is not None:
            differences.append((f"[{index}]", difference))

    differences.extend(
        (f"[{index}]", OnlyInOne(value=one[index]))
        for index in range(len(two), len(one))
    )
    differences.extend(
        (f"[{index}]", OnlyInTwo(value=two[index]))
        for index in range(len(one), len(two))
    )

    if not differences:
        return None
    return Nested(differences=differences)


def fields(
    differ: Differ,
    one: Any,
    two: Any,
) -> Difference | NotImplementedType | None:
    """
    Diff two `attrs` or `dataclasses` instances field by field.
    """
    names = _comparable_fields(type(one))
    if names is None or _comparable_fields(type(two)) != names:
        return NotImplemented

    differences: list[tuple[str, Difference]] = []
    for name in names:
        difference = differ(getattr(one, name), getattr(two, name))
        if difference is not None:
            differences.append((f".{name}", difference))

    if not differences:
        return None
    return Nested(differences=differences)


def _comparable_fields(klass: type) -> tuple[str, ...] | None:
    """
    The fields which take part in equality, for classes which have them.

    Returns:

        each field's name, or `None` for classes with no such notion

    """
    if is_attrs_class(klass):
        return tuple(each.name for each in attrs_fields(klass) if each.eq)
    if is_dataclass(klass):
        return tuple(
            each.name for each in dataclass_fields(klass) if each.compare
        )
    return None


#: Diffing for particular types, checked against the type's own MRO.
BUILTIN_REGISTRY: Mapping[type, Implementation] = MappingProxyType(
    {str: strings},
)

#: Diffing for whole categories of object, tried in order afterwards.
#: Each declines by returning `NotImplemented`, so order only matters
#: where a type could plausibly match more than one of them.
BUILTIN_FALLBACKS: tuple[Implementation, ...] = (
    mappings,
    sets,
    sequences,
    fields,
)
