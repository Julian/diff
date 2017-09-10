import attr


@attr.s
class NotEqual(object):
    one = attr.ib()
    two = attr.ib()


def diff(one, two):
    return NotEqual(one, two)
