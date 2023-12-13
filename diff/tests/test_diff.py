from textwrap import dedent

from zope.interface import verify

import diff


class TestDiff:
    def test_custom_diff(self):
        class Something:
            def __diff__(self, other):
                return diff.Constant(explanation="nope")

        assert diff.diff(Something(), 12).explain() == "nope"

    def test_coerced_diff(self):
        class Something:
            def __diff__(self, other):
                return "something is not " + repr(other)

        assert diff.diff(Something(), 12).explain() == "something is not 12"

    def test_str(self):
        assert (
            diff.diff("foo", "foobar").explain()
            == dedent(
                """
            - foo
            + foobar
            """,
            ).strip("\n")
        )

    def test_equal_returns_none(self):
        one = object()
        assert diff.diff(one, one) is None

    def test_no_specific_diff_info(self):
        one, two = object(), object()
        assert diff.diff(one, two).explain() == f"{one!r} != {two!r}"

    def test_nonequality_is_truthy(self):
        one, two = object(), object()
        assert diff.diff(one, two)


class TestConstant:
    def test_it_has_a_constant_explanation(self):
        difference = diff.Constant(explanation="my explanation")
        assert difference.explain() == "my explanation"

    def test_it_is_a_difference(self):
        verify.verifyClass(diff.Difference, diff.Constant)
