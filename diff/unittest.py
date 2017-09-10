"""
Unittest integration.

"""

from __future__ import absolute_import
from unittest import TestCase

from diff import diff


class TestCase(TestCase):
    def assertEqual(self, one, two, *args, **kwargs):
        try:
            super(TestCase, self).assertEqual(
                one,
                two,
                *args,
                **kwargs
            )
        except self.failureException:
            if "msg" in kwargs:
                raise
            self.fail(diff(one, two).explain())
