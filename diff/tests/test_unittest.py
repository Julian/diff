from unittest import TestCase

from diff import Constant
import diff.unittest


class TestTestCase(diff.unittest.TestCase, TestCase):
    def assertFails(self, *args, **kwargs):
        expected = kwargs.pop("expected")
        with TestCase.assertRaises(self, self.failureException) as e:
            self.addCleanup(setattr, self, "longMessage", self.longMessage)
            self.longMessage = False
            self.assertEqual(*args, **kwargs)
        TestCase.assertEqual(self, str(e.exception), expected)

    def test_assertEqual_ints(self):
        self.assertFails(1, 2, expected="1 != 2")

    def test_assertEqual_custom(self):
        class SillyObject(object):
            def __diff__(self, other):
                return Constant(explanation="Hahaha no.")

        self.assertFails(SillyObject(), 2, expected="Hahaha no.")

    def test_assertEqual_overridden_msg(self):
        self.assertFails(1, 2, msg="foo", expected="foo")
