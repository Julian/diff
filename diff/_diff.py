import attr


@attr.s
class NotEqual(object):

    one = attr.ib()
    two = attr.ib()

    def __bool__(self):
        return False

    __nonzero__ = __bool__


def diff(one, two):
    return NotEqual(one, two)
