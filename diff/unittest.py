"""
Unittest integration.

"""

from unittest import TestCase

from diff import diff


class TestCase(TestCase):
    """
    A `unittest.TestCase` which shows failure diff messages using this library.
    """

    def assertEqual(self, one, two, *args, **kwargs):
        """
        Compare the two objects showing a diff if they're unexpectedly unequal.
        """
        try:
            super().assertEqual(one, two, *args, **kwargs)
        except self.failureException:
            if "msg" in kwargs:
                raise
            self.fail(diff(one, two).explain())
