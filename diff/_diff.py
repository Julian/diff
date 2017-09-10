from zope.interface import Interface, implementer
import attr


class Difference(Interface):
    def explain():
        """
        Explain this difference.

        Returns:

            str: a representation of the difference

        """


@implementer(Difference)
@attr.s
class Constant(object):

    _explanation = attr.ib()

    def explain(self):
        return self._explanation


@attr.s
class NotEqual(object):

    one = attr.ib()
    two = attr.ib()

    def __bool__(self):
        return True

    __nonzero__ = __bool__

    def explain(self):
        return "{0.one} != {0.two}".format(self)


def diff(one, two):
    if one != two:
        differ = getattr(one, "__diff__", None)
        if differ is None:
            return NotEqual(one, two)
        difference = differ(two)
        return Difference(difference, Constant(explanation=difference))
    return False
