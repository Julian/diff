try:
    from importlib import metadata
except ImportError:
    import importlib_metadata as metadata

from diff._diff import Constant, Difference, diff
__version__ = metadata.version("diff")
