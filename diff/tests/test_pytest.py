"""
https://docs.pytest.org/en/stable/how-to/writing_plugins.html#testing-plugins
"""

from diff._pytest_plugin import pytest_assertrepr_compare

pytest_plugins = ["pytester"]


def test_it_explains_a_nested_difference(pytester):
    pytester.makepyfile(
        """
        def test_dicts():
            assert {"a": {"b": 1}} == {"a": {"b": 2}}
        """,
    )
    result = pytester.runpytest_subprocess()
    result.assert_outcomes(failed=1)
    assert "['a']['b']: 1 != 2" in result.stdout.str()


def test_it_explains_a_custom_difference(pytester):
    pytester.makepyfile(
        """
        from diff import Constant

        class Silly:
            def __diff__(self, other):
                return Constant(explanation="Hahaha no.")

        def test_silly():
            assert Silly() == 12
        """,
    )
    result = pytester.runpytest_subprocess()
    result.assert_outcomes(failed=1)
    assert "Hahaha no." in result.stdout.str()


def test_it_leaves_other_operators_alone(pytester):
    """
    Only ``==`` gets explained -- ``in``, ``<`` and friends are not ours.
    """
    pytester.makepyfile(
        """
        def test_containment():
            assert 3 in [1, 2]

        def test_inequality():
            x = [1, 2, 3]
            assert x != [1, 2, 3]

        def test_ordering():
            assert [1, 3] < [1, 2]
        """,
    )
    result = pytester.runpytest_subprocess()
    result.assert_outcomes(failed=3)
    assert "INTERNALERROR" not in result.stdout.str()
    assert "assert 3 in [1, 2]" in result.stdout.str()
    # we would have explained this one had the operator been ``==``
    assert "[1]: 3 != 2" not in result.stdout.str()


def test_it_defers_when_it_has_nothing_to_add(pytester):
    """
    pytest's own output is good, so don't replace it with something worse.
    """
    pytester.makepyfile(
        """
        def test_ints():
            assert 1 == 2
        """,
    )
    result = pytester.runpytest_subprocess()
    result.assert_outcomes(failed=1)
    assert "1 != 2" not in result.stdout.str()


class TestHook:
    """
    The hook itself, which the tests above run in a subprocess.
    """

    def test_it_explains_a_difference(self):
        lines = pytest_assertrepr_compare("==", {"a": 1}, {"a": 2})
        assert lines == ["{'a': 1} == {'a': 2}", "['a']: 1 != 2"]

    def test_long_summaries_are_shortened(self):
        one, two = {"a": "x" * 500}, {"a": "y" * 500}
        summary, *_ = pytest_assertrepr_compare("==", one, two)
        assert "..." in summary
        assert len(summary) < len(repr(one))

    def test_it_ignores_other_operators(self):
        assert pytest_assertrepr_compare("!=", 1, 1) is None
        assert pytest_assertrepr_compare("in", 3, [1, 2]) is None
        # one where we would otherwise have had plenty to say
        assert pytest_assertrepr_compare("<", [1, 3], [1, 2]) is None

    def test_it_ignores_equal_objects(self):
        assert pytest_assertrepr_compare("==", 1, 1) is None

    def test_it_defers_when_it_knows_nothing(self):
        assert pytest_assertrepr_compare("==", 1, 2) is None
