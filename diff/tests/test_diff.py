from textwrap import dedent

from diff import Constant, Difference, diff


class TestDiff:
    def test_custom_diff(self):
        class Something:
            def __diff__(self, other):
                return Constant(explanation="nope")

        assert diff(Something(), 12).explain() == "nope"

    def test_coerced_diff(self):
        class Something:
            def __diff__(self, other):
                return "something is not " + repr(other)

        assert diff(Something(), 12).explain() == "something is not 12"

    def test_str(self):
        assert (
            diff("foo", "foobar").explain()
            == dedent(
                """
            - foo
            + foobar
            """,
            ).strip("\n")
        )

    def test_equal_returns_none(self):
        one = object()
        assert diff(one, one) is None

    def test_no_specific_diff_info(self):
        one, two = object(), object()
        assert diff(one, two).explain() == f"{one!r} != {two!r}"

    def test_nonequality_is_truthy(self):
        one, two = object(), object()
        assert diff(one, two)


class TestConstant:
    def test_it_has_a_constant_explanation(self):
        difference = Constant(explanation="my explanation")
        assert difference.explain() == "my explanation"

    def test_it_is_a_difference(self):
        assert isinstance(Constant, Difference)
