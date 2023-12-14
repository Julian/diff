"""
Unittest integration.

"""

from typing import Any
from unittest import TestCase as _UnittestTestCase

from diff import diff


class TestCase(_UnittestTestCase):
    """
    A `unittest.TestCase` which shows failure diff messages using this library.
    """

    def assertEqual(self, first: Any, second: Any, *args: Any, **kwargs: Any):
        """
        Compare the two objects showing a diff if they're unexpectedly unequal.
        """
        try:
            super().assertEqual(first, second, *args, **kwargs)
        except self.failureException:
            if "msg" in kwargs:
                raise
            difference = diff(first, second)
            assert (  # noqa: S101
                difference is not None
            ), "This shouldn't happen! assertEqual failed but these are equal"
            self.fail(difference.explain())
