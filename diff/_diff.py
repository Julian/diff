from difflib import ndiff

import attr
import zope.interface.registry


class Difference(zope.interface.Interface):
    def explain():
        """
        Explain this difference.

        Returns:

            str: a representation of the difference

        """


@zope.interface.implementer(Difference)
@attr.s
class Constant(object):

    _explanation = attr.ib()

    def explain(self):
        return self._explanation


def _no_specific_diff(one):
    return lambda two: Constant("{!r} != {!r}".format(one, two))


def diff(one, two):
    if one == two:
        return

    differ = getattr(one, "__diff__", None)
    if differ is None:
        differ = _registry.queryAdapter(one, Difference)
    difference = differ(two)
    return Difference(difference, Constant(explanation=difference))


_registry = zope.interface.registry.Components()
_registry.registerAdapter(
    lambda value: lambda other: "\n".join(
        ndiff(value.splitlines(), other.splitlines()),
    ),
    [str],
    Difference,
)
_registry.registerAdapter(
    _no_specific_diff,
    [None],
    Difference,
)
