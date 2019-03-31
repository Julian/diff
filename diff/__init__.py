from pkg_resources import get_distribution, DistributionNotFound
try:
    __version__ = get_distribution(__name__).version
except DistributionNotFound:  # pragma: no cover
    pass

from diff._diff import Constant, Difference, diff
