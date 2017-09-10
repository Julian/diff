from unittest import TestCase

from zope.interface import verify

import diff


class TestDiff(TestCase):
    def test_custom_diff(self):
        class Something(object):
            def __diff__(self, other):
                return diff.Constant(explanation="nope")
        self.assertEqual(diff.diff(Something(), 12).explain(), "nope")

    def test_coerced_diff(self):
        class Something(object):
            def __diff__(self, other):
                return "something is not " + repr(other)
        self.assertEqual(
            diff.diff(Something(), 12).explain(), "something is not 12",
        )

    def test_equal_is_falsy(self):
        one = object()
        self.assertFalse(diff.diff(one, one))

    def test_no_specific_diff_info(self):
        one, two = object(), object()
        self.assertEqual(diff.diff(one, two), diff.NotEqual(one, two))

    def test_nonequality_is_falsy(self):
        one, two = object(), object()
        self.assertTrue(diff.NotEqual(one, two))


class TestConstant(TestCase):
    def test_it_has_a_constant_explanation(self):
        difference = diff.Constant(explanation="my explanation")
        self.assertEqual(difference.explain(), "my explanation")

    def test_it_is_a_difference(self):
        verify.verifyClass(diff.Difference, diff.Constant)
