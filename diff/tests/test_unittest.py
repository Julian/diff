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
        class SillyObject:
            def __diff__(self, other):
                return Constant(explanation="Hahaha no.")

        self.assertFails(SillyObject(), 2, expected="Hahaha no.")

    def test_assertEqual_overridden_msg(self):
        self.assertFails(1, 2, msg="foo", expected="foo")

    def test_assertEqual_disagreeing_eq_and_diff(self):
        """
        A type whose ``__eq__`` and ``__diff__`` do not agree.

        There's nothing sensible to say, so the original failure stands.
        """

        class Contrarian:  # noqa: PLW1641
            def __eq__(self, other):
                return False

            def __diff__(self, other):
                return None

            def __repr__(self):
                return "<Contrarian>"

        self.assertFails(
            Contrarian(),
            Contrarian(),
            expected="<Contrarian> != <Contrarian>",
        )
