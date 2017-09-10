from unittest import TestCase

import diff


class TestDiff(TestCase):
    def test_equal_is_falsy(self):
        one = object()
        self.assertFalse(diff.diff(one, one))

    def test_no_specific_diff_info(self):
        one, two = object(), object()
        self.assertEqual(diff.diff(one, two), diff.NotEqual(one, two))

    def test_nonequality_is_falsy(self):
        one, two = object(), object()
        self.assertTrue(diff.NotEqual(one, two))
