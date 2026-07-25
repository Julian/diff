"""
Diffing arbitrary Python objects.
"""

from __future__ import annotations

from contextvars import ContextVar
from types import MappingProxyType, NotImplementedType
from typing import TYPE_CHECKING, Any, overload

from attrs import field, frozen

from diff._builtins import BUILTIN_FALLBACKS, BUILTIN_REGISTRY
from diff._differences import DifferentTypes, Unequal

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator, Mapping

    from diff._protocols import Diffable, Difference, Implementation

#: Which pairs of objects we are part-way through diffing, so that
#: objects which contain themselves terminate instead of blowing the
#: stack -- a pair already in progress has no *new* difference to
#: report. Plain `==` simply raises `RecursionError` here, so this is
#: one of the few places we manage better than Python itself.
_IN_PROGRESS: ContextVar[frozenset[tuple[int, int]]] = ContextVar(
    "in progress",
    default=frozenset(),
)


@frozen
class Differ:
    """
    Something which knows how to explain why objects differ.

    Diffing an object asks, in order:

        * the type of either object, via `__diff__`

        * any `Implementation` registered here for either type

        * any fallback implementation registered here, which is how
          entire categories of object (mappings, `attrs` classes) are
          handled

    and if nothing has an opinion, falls back to plain old ``==``.

    Each of the above may decline by returning `NotImplemented`, in
    which case the next one gets a turn -- including the second object,
    whose difference is turned around before being returned.
    """

    _strict_types: bool = field(default=False, alias="strict_types")
    _registry: Mapping[type, Implementation] = field(
        default=BUILTIN_REGISTRY,
        alias="registry",
    )
    _fallbacks: tuple[Implementation, ...] = field(
        default=BUILTIN_FALLBACKS,
        converter=tuple,
        alias="fallbacks",
    )

    @overload
    def __call__[D: Difference](
        self,
        one: Diffable[D],
        two: Any,
    ) -> D | None: ...

    @overload
    def __call__(self, one: Any, two: Any) -> Difference | None: ...

    def __call__(self, one: Any, two: Any) -> Difference | None:
        """
        Diff two objects.

        Returns:

            why the two differ, or `None` if they do not

        """
        if one is two:
            return None

        if self._strict_types and type(one) is not type(two):
            return DifferentTypes(one=one, two=two)

        in_progress = _IN_PROGRESS.get()
        pair = id(one), id(two)
        if pair in in_progress:
            return None

        token = _IN_PROGRESS.set(in_progress | {pair})
        try:
            return self._difference(one, two)
        finally:
            _IN_PROGRESS.reset(token)

    def _difference(self, one: Any, two: Any) -> Difference | None:
        """
        Ask everything which might know, then simply fall back to `==`.
        """
        for implementation, first, second, reverse in self._attempts(one, two):
            difference = implementation(self, first, second)
            if isinstance(difference, NotImplementedType):
                continue
            if difference is None:
                return None
            return difference.reversed() if reverse else difference

        return None if one == two else Unequal(one=one, two=two)

    def with_implementation(
        self,
        klass: type,
        implementation: Implementation,
    ) -> Differ:
        """
        A differ which also knows how to diff one particular type.

        Returns:

            a new differ, leaving this one alone

        """
        registry = {**self._registry, klass: implementation}
        return Differ(
            strict_types=self._strict_types,
            registry=MappingProxyType(registry),
            fallbacks=self._fallbacks,
        )

    def with_fallback(self, implementation: Implementation) -> Differ:
        """
        A differ which tries one more implementation for any object.

        The implementation is tried last, and should return
        `NotImplemented` for objects it does not apply to.

        Returns:

            a new differ, leaving this one alone

        """
        return Differ(
            strict_types=self._strict_types,
            registry=self._registry,
            fallbacks=(*self._fallbacks, implementation),
        )

    def _attempts(
        self,
        one: Any,
        two: Any,
    ) -> Iterator[tuple[Implementation, Any, Any, bool]]:
        """
        Every way we might diff the two objects, in the order to try.

        Returns:

            an implementation, what to pass it, and whether the result
            will need turning around

        """
        sides = [(one, two, False), (two, one, True)]
        if _reflected_first(one, two):
            sides.reverse()

        lookups = (_protocol, self._registered, self._fallback)
        for lookup in lookups:
            for first, second, reverse in sides:
                for implementation in lookup(first):
                    yield implementation, first, second, reverse

    def _registered(self, obj: Any) -> Iterator[Implementation]:
        """
        Whatever is registered for the object's type, if anything is.
        """
        for klass in type(obj).__mro__:
            implementation = self._registry.get(klass)
            if implementation is not None:
                yield implementation
                return

    def _fallback(self, obj: Any) -> Iterable[Implementation]:
        """
        Every fallback, which are tried for objects of any type.
        """
        return self._fallbacks


#: Diff two objects using sane defaults.
diff = Differ()


def _protocol(obj: Any) -> Iterator[Implementation]:
    """
    The object's own `__diff__`, looked up on its type as is proper.
    """
    method = getattr(type(obj), "__diff__", None)
    if method is not None:
        yield lambda differ, one, two: method(one, two)


def _reflected_first(one: Any, two: Any) -> bool:
    """
    Should the second object be given the first say?

    Mirroring what Python itself does for binary operators, a subclass
    which overrides `__diff__` gets to go before its parent does.
    """
    one_type, two_type = type(one), type(two)
    return (
        two_type is not one_type
        and issubclass(two_type, one_type)
        and getattr(two_type, "__diff__", None)
        is not getattr(one_type, "__diff__", None)
    )


def eq_from_diff[C: type[Any]](cls: C) -> C:
    """
    Derive a class's `__eq__` from the `__diff__` it already defines.

    Two instances are equal exactly when diffing them finds no
    difference, and `NotImplemented` passes straight through, which is
    the same thing it means to both protocols.

    As Python does for any class defining `__eq__`, the class becomes
    unhashable unless it also defines its own `__hash__`.

    Returns:

        the same class, now with an `__eq__`

    Raises:

        TypeError:

            if the class has no `__diff__` to derive from, or defines an
            `__eq__` which would silently be thrown away

    """
    if getattr(cls, "__diff__", None) is None:
        message = f"{cls.__name__} defines no __diff__ to derive from."
        raise TypeError(message)
    if "__eq__" in cls.__dict__:
        message = f"{cls.__name__} already defines its own __eq__."
        raise TypeError(message)

    def __eq__(self: Any, other: Any) -> Any:
        difference = self.__diff__(other)
        if difference is NotImplemented:
            return NotImplemented
        return difference is None

    cls.__eq__ = __eq__
    if "__hash__" not in cls.__dict__:
        cls.__hash__ = None
    return cls
