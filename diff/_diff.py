import attr


@attr.s
class NotEqual(object):

    one = attr.ib()
    two = attr.ib()

    def __bool__(self):
        return True

    __nonzero__ = __bool__


def diff(one, two):
    if one != two:
        return NotEqual(one, two)
    return False
