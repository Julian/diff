"""
A diff protocol for arbitrary Python objects.
"""

from diff._diff import Differ, diff, eq_from_diff
from diff._differences import (
    Constant,
    DifferentTypes,
    Nested,
    OnlyInOne,
    OnlyInTwo,
    Uncommon,
    Unequal,
)
from diff._protocols import Diffable, Difference, Implementation

__all__ = [
    "Constant",
    "Diffable",
    "Differ",
    "Difference",
    "DifferentTypes",
    "Implementation",
    "Nested",
    "OnlyInOne",
    "OnlyInTwo",
    "Uncommon",
    "Unequal",
    "diff",
    "eq_from_diff",
]
