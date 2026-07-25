from collections import OrderedDict
from dataclasses import dataclass, field as dataclass_field
from textwrap import dedent

from attrs import define, field, frozen
import pytest

from diff import (
    Constant,
    Diffable,
    Differ,
    Difference,
    DifferentTypes,
    Nested,
    OnlyInOne,
    OnlyInTwo,
    Uncommon,
    Unequal,
    diff,
    eq_from_diff,
)


class TestProtocol:
    def test_custom_diff(self):
        class Something:
            def __diff__(self, other):
                return Constant(explanation="nope")

        assert diff(Something(), 12).explain() == "nope"

    def test_diff_returning_none_means_equal(self):
        class AlwaysTheSame:
            def __diff__(self, other):
                return None

        assert diff(AlwaysTheSame(), 12) is None

    def test_not_implemented_falls_back(self):
        class NoIdea:
            def __diff__(self, other):
                return NotImplemented

        one, two = NoIdea(), NoIdea()
        assert diff(one, two) == Unequal(one=one, two=two)

    def test_not_implemented_lets_the_other_side_try(self):
        class NoIdea:
            def __diff__(self, other):
                return NotImplemented

        class SomeIdea:
            def __diff__(self, other):
                return Constant(explanation="I got this")

        assert diff(NoIdea(), SomeIdea()).explain() == "I got this"

    def test_the_second_object_gets_a_turn(self):
        class Rightmost:
            def __diff__(self, other):
                return Constant(explanation="the right one spoke")

        difference = diff(12, Rightmost())
        assert difference.explain() == "the right one spoke"

    def test_the_second_objects_difference_is_reversed(self):
        class Rightmost:
            def __diff__(self, other):
                return OnlyInOne(value=37)

        # 37 was only in `Rightmost`, which was the *second* object.
        assert diff(12, Rightmost()) == OnlyInTwo(value=37)

    def test_a_foreign_difference_is_reversed_too(self):
        """
        Reversal goes through the protocol, not through our own types.
        """

        @frozen
        class Sided:
            side: str

            def explain(self):
                return f"seen from the {self.side}"

            def reversed(self):
                other = "left" if self.side == "right" else "right"
                return Sided(side=other)

        class Rightmost:
            def __diff__(self, other):
                return Sided(side="left")

        difference = diff(12, Rightmost())
        assert difference == Sided(side="right")
        assert difference.explain() == "seen from the right"

    def test_the_first_object_wins(self):
        class Leftmost:
            def __diff__(self, other):
                return Constant(explanation="the left one spoke")

        class Rightmost:
            def __diff__(self, other):  # pragma: no cover
                return Constant(explanation="the right one spoke")

        difference = diff(Leftmost(), Rightmost())
        assert difference.explain() == "the left one spoke"

    def test_a_subclass_goes_first(self):
        class Parent:
            def __diff__(self, other):  # pragma: no cover
                return Constant(explanation="parent")

        class Child(Parent):
            def __diff__(self, other):
                return Constant(explanation="child")

        assert diff(Parent(), Child()).explain() == "child"

    def test_a_subclass_which_does_not_override_does_not_go_first(self):
        class Parent:
            def __diff__(self, other):
                return OnlyInOne(value=12)

        class Child(Parent):
            pass

        assert diff(Parent(), Child()) == OnlyInOne(value=12)

    def test_diff_is_looked_up_on_the_type(self):
        """
        Special methods live on types, not on instances.
        """

        class Sneaky:
            pass

        one = Sneaky()
        one.__diff__ = lambda other: Constant(explanation="from the instance")
        assert diff(one, Sneaky()) != Constant(explanation="from the instance")

    def test_classes_are_not_diffable_just_by_having_the_attribute(self):
        """
        A class has a `__diff__` attribute, but is not itself diffable.
        """

        class One:
            def __diff__(self, other):
                return Constant(explanation="nope")  # pragma: no cover

        class Two:
            def __diff__(self, other):
                return Constant(explanation="nope")  # pragma: no cover

        assert diff(One, Two) == Unequal(one=One, two=Two)


class TestDiff:
    def test_equal_returns_none(self):
        assert diff(12, 12) is None

    def test_identical_objects_never_differ(self):
        one = object()
        assert diff(one, one) is None

    def test_nan_does_not_differ_from_itself(self):
        nan = float("nan")
        assert diff(nan, nan) is None

    def test_distinct_nans_do_differ(self):
        assert diff(float("nan"), float("nan")) is not None

    def test_no_specific_diff_info(self):
        one, two = object(), object()
        assert diff(one, two) == Unequal(one=one, two=two)

    def test_nonequality_is_truthy(self):
        one, two = object(), object()
        assert diff(one, two)


class TestCycles:
    """
    Objects which contain themselves shouldn't blow the stack.

    Plain ``==`` does, so here we manage slightly better than Python.
    """

    def test_plain_equality_cannot_do_this(self):
        one, two = [], []
        one.append(one)
        two.append(two)
        with pytest.raises(RecursionError):
            one == two  # noqa: B015

    def test_two_equal_cycles(self):
        one, two = [], []
        one.append(one)
        two.append(two)
        assert diff(one, two) is None

    def test_two_differing_cycles(self):
        one, two = [1], [2]
        one.append(one)
        two.append(two)
        assert diff(one, two).explain() == "[0]: 1 != 2"

    def test_a_cycle_against_a_finite_object(self):
        one = [1]
        one.append(one)
        assert diff(one, [1, [1, [1]]]) is not None

    def test_mutually_recursive_mappings(self):
        one, two = {}, {}
        one["self"], two["self"] = one, two
        assert diff(one, two) is None

    def test_a_cycle_under_a_differing_key(self):
        cycle = {}
        cycle["self"] = cycle
        one = {"a": 1, "cycle": cycle}
        two = {"a": 2, "cycle": cycle}
        assert diff(one, two).explain() == "['a']: 1 != 2"

    def test_the_guard_is_unwound(self):
        """
        Diffing the same pair again still works the second time round.
        """
        one, two = {"a": 1}, {"a": 2}
        first = diff(one, two)
        assert first is not None
        assert diff(one, two) == first


class TestStrictTypes:
    def test_by_default_true_is_one(self):
        assert diff(1, True) is None

    def test_strictly_true_is_not_one(self):
        strict = Differ(strict_types=True)
        assert strict(1, True) == DifferentTypes(one=1, two=True)

    def test_strictly_equal_things_of_one_type_are_still_equal(self):
        strict = Differ(strict_types=True)
        assert strict(1, 1) is None

    def test_strict_types_skips_diff(self):
        class Anything:
            def __diff__(self, other):
                return Constant(explanation="nope")  # pragma: no cover

        strict = Differ(strict_types=True)
        assert isinstance(strict(Anything(), 12), DifferentTypes)


class TestRegistry:
    def test_with_implementation(self):
        class Widget:
            def __init__(self, size):
                self.size = size

        def widgets(differ, one, two):
            return Constant(explanation=f"{one.size} vs {two.size}")

        differ = diff.with_implementation(Widget, widgets)
        assert differ(Widget(1), Widget(2)).explain() == "1 vs 2"

    def test_implementations_are_inherited_along_the_mro(self):
        class Widget:
            pass

        class Gadget(Widget):
            pass

        def widgets(differ, one, two):
            return Constant(explanation="a widget of some sort")

        differ = diff.with_implementation(Widget, widgets)
        explanation = differ(Gadget(), Gadget()).explain()
        assert explanation == "a widget of some sort"

    def test_the_type_itself_still_wins(self):
        class Widget:
            def __diff__(self, other):
                return Constant(explanation="the widget spoke")

        def widgets(differ, one, two):
            return Constant(explanation="nope")  # pragma: no cover

        differ = diff.with_implementation(Widget, widgets)
        assert differ(Widget(), Widget()).explain() == "the widget spoke"

    def test_the_second_objects_type_is_looked_up_too(self):
        class Widget:
            pass

        def widgets(differ, one, two):
            # registered implementations are only handed their own type
            assert isinstance(one, Widget)
            return OnlyInOne(value="a widget")

        differ = diff.with_implementation(Widget, widgets)
        # the widget was the *second* argument, so this is turned around
        assert differ(12, Widget()) == OnlyInTwo(value="a widget")

    def test_a_more_derived_registration_wins(self):
        class Widget:
            pass

        class Gadget(Widget):
            pass

        def widgets(differ, one, two):
            return Constant(explanation="widget")  # pragma: no cover

        def gadgets(differ, one, two):
            return Constant(explanation="gadget")

        differ = diff.with_implementation(
            Widget,
            widgets,
        ).with_implementation(Gadget, gadgets)
        assert differ(Gadget(), Gadget()).explain() == "gadget"

    def test_the_registry_is_not_mutated_in_place(self):
        class Widget:
            pass

        def widgets(differ, one, two):
            return Constant(explanation="nope")  # pragma: no cover

        one = diff.with_implementation(Widget, widgets)
        with pytest.raises(TypeError):
            one._registry[int] = widgets

    def test_with_fallback(self):
        class Widget:
            pass

        def anything(differ, one, two):
            return Constant(explanation="caught by the fallback")

        differ = diff.with_fallback(anything)
        explanation = differ(Widget(), Widget()).explain()
        assert explanation == "caught by the fallback"

    def test_a_declining_fallback_is_skipped(self):
        def never(differ, one, two):
            return NotImplemented

        differ = diff.with_fallback(never)
        assert differ(1, 2) == Unequal(one=1, two=2)

    def test_an_implementation_can_recurse(self):
        class Widget:
            def __init__(self, size):
                self.size = size

        def widgets(differ, one, two):
            return differ(one.size, two.size)

        differ = diff.with_implementation(Widget, widgets)
        assert differ(Widget(1), Widget(1)) is None
        assert differ(Widget(1), Widget(2)) == Unequal(one=1, two=2)

    def test_with_implementation_leaves_the_original_alone(self):
        class Widget:
            pass

        def widgets(differ, one, two):
            return Constant(explanation="nope")  # pragma: no cover

        diff.with_implementation(Widget, widgets)
        assert isinstance(diff(Widget(), Widget()), Unequal)

    def test_with_fallback_leaves_the_original_alone(self):
        def anything(differ, one, two):
            return Constant(explanation="nope")  # pragma: no cover

        diff.with_fallback(anything)
        assert diff(object(), object()) is not None

    def test_configuration_is_preserved(self):
        def widgets(differ, one, two):
            return Constant(explanation="the implementation ran")

        def anything(differ, one, two):
            return Constant(explanation="the fallback ran")

        differ = (
            Differ(strict_types=True)
            .with_fallback(anything)
            .with_implementation(complex, widgets)
        )
        assert differ(1, True) == DifferentTypes(one=1, two=True)
        assert differ(1, 2).explain() == "the fallback ran"
        assert differ(1j, 2j).explain() == "the implementation ran"


class TestEqFromDiff:
    def test_equal(self):
        assert Version(1) == Version(1)

    def test_unequal(self):
        assert Version(1) != Version(2)

    def test_not_implemented_passes_through(self):
        assert Version(1) != "not a version"
        assert Version(1).__eq__("not a version") is NotImplemented

    def test_it_is_unhashable_like_any_class_defining_eq(self):
        with pytest.raises(TypeError):
            hash(Version(1))

    def test_an_explicit_hash_survives(self):
        sentinel = 37

        @eq_from_diff
        class Hashable:
            def __diff__(self, other):
                return None  # pragma: no cover

            def __hash__(self):
                return sentinel

        assert hash(Hashable()) == sentinel

    def test_it_needs_a_diff(self):
        with pytest.raises(TypeError):

            @eq_from_diff
            class Nope:
                pass

    def test_it_will_not_clobber_an_eq(self):
        with pytest.raises(TypeError):

            @eq_from_diff
            class Nope:  # noqa: PLW1641
                def __diff__(self, other):
                    return None  # pragma: no cover

                def __eq__(self, other):
                    return True  # pragma: no cover

    def test_an_inherited_diff_is_enough(self):
        class Parent:
            def __diff__(self, other):
                return None

        @eq_from_diff
        class Child(Parent):
            pass

        assert Child() == Child()

    def test_the_class_is_returned(self):
        assert Version(1).number == 1


@eq_from_diff
class Version:
    """
    A class which knows only how it differs, and gets `__eq__` for free.
    """

    def __init__(self, number):
        self.number = number

    def __diff__(self, other):
        if not isinstance(other, Version):
            return NotImplemented
        if self.number == other.number:
            return None
        return Constant(explanation=f"v{self.number} vs v{other.number}")


class TestStrings:
    def test_multiline(self):
        one = "foo\nbar\nbaz"
        two = "foo\nquux\nbaz"
        assert diff(one, two).explain() == dedent(
            """
              foo
            - bar
            + quux
              baz
            """,
        ).strip("\n")

    def test_one_line(self):
        assert diff("foo", "bar") == Unequal(one="foo", two="bar")

    def test_a_common_prefix_is_pointed_at(self):
        explanation = diff("foobar", "foobaz").explain()
        assert explanation == "'foobar' != 'foobaz' (differing at index 5)"

    def test_equal(self):
        # a distinct object, so we don't just short-circuit on identity
        assert diff("foo", "FOO".lower()) is None

    def test_a_string_is_not_a_sequence_of_characters(self):
        assert diff("ab", "xy") == Unequal(one="ab", two="xy")

    def test_against_a_non_string(self):
        assert diff("ab", 12) == Unequal(one="ab", two=12)

    def test_bytes_are_left_whole(self):
        assert diff(b"ab", b"ax") == Unequal(one=b"ab", two=b"ax")


class TestMappings:
    def test_a_differing_value(self):
        difference = diff({"a": 1, "b": 2}, {"a": 1, "b": 3})
        assert difference.explain() == "['b']: 2 != 3"

    def test_a_missing_key(self):
        difference = diff({"a": 1, "b": 2}, {"a": 1})
        assert difference.explain() == "['b']: 2 is only in the first object"

    def test_an_extra_key(self):
        difference = diff({"a": 1}, {"a": 1, "b": 2})
        assert difference.explain() == "['b']: 2 is only in the second object"

    def test_nesting_is_flattened_into_a_path(self):
        difference = diff({"a": {"b": {"c": 1}}}, {"a": {"b": {"c": 2}}})
        assert difference.explain() == "['a']['b']['c']: 1 != 2"

    def test_equal(self):
        assert diff({"a": 1}, {"a": 1}) is None

    def test_against_a_non_mapping(self):
        assert diff({"a": 1}, 12) == Unequal(one={"a": 1}, two=12)

    def test_differing_mapping_types(self):
        assert diff({"a": 1}, OrderedDict(a=1)) is None


class TestSequences:
    def test_a_differing_element(self):
        assert diff([1, 2, 3], [1, 9, 3]).explain() == "[1]: 2 != 9"

    def test_a_shorter_second(self):
        difference = diff([1, 2], [1])
        assert difference.explain() == "[1]: 2 is only in the first object"

    def test_a_longer_second(self):
        difference = diff([1], [1, 2])
        assert difference.explain() == "[1]: 2 is only in the second object"

    def test_equal(self):
        assert diff([1, 2], [1, 2]) is None

    def test_tuples(self):
        assert diff((1, 2), (1, 9)).explain() == "[1]: 2 != 9"

    def test_a_list_is_not_a_tuple(self):
        """
        Equal elements wouldn't make these equal, so say the real reason.
        """
        assert diff([1, 2], (1, 2)) == DifferentTypes(one=[1, 2], two=(1, 2))
        assert diff([1, 2], (1, 9)) == DifferentTypes(one=[1, 2], two=(1, 9))

    def test_a_range_is_not_a_list(self):
        assert diff(range(2), [0, 1]) == DifferentTypes(
            one=range(2),
            two=[0, 1],
        )

    def test_a_subclass_is_still_a_list(self):
        class MyList(list):
            pass

        assert diff(MyList([1, 2]), [1, 2]) is None
        assert diff(MyList([1, 2]), [1, 9]).explain() == "[1]: 2 != 9"

    def test_against_a_non_sequence(self):
        assert diff([1], 12) == Unequal(one=[1], two=12)

    def test_against_a_string(self):
        assert diff(["a", "b"], "ab") == Unequal(one=["a", "b"], two="ab")


class TestSets:
    def test_both_directions(self):
        difference = diff({1, 2, 3}, {2, 3, 4})
        assert difference.explain() == dedent(
            """
            only in the first object: 1
            only in the second object: 4
            """,
        ).strip("\n")

    def test_only_in_the_first(self):
        difference = diff({1, 2}, {1})
        assert difference.explain() == "only in the first object: 2"

    def test_only_in_the_second(self):
        difference = diff({1}, {1, 2})
        assert difference.explain() == "only in the second object: 2"

    def test_ordering_does_not_depend_on_hashing(self):
        difference = diff({"b", "a", "c"}, set())
        assert difference.explain() == (
            "only in the first object: 'a', 'b', 'c'"
        )

    def test_equal(self):
        assert diff({1}, {1}) is None

    def test_frozensets(self):
        assert diff(frozenset([1]), {1}) is None

    def test_against_a_non_set(self):
        assert diff({1}, 12) == Unequal(one={1}, two=12)


@define
class Config:
    timeout: int
    retries: int


@define
class Secretive:
    shown: int
    hidden: int = field(eq=False)


@dataclass
class Point:
    x: int
    y: int


@dataclass
class Tagged:
    value: int
    tag: str = dataclass_field(compare=False)


class TestFields:
    def test_attrs(self):
        difference = diff(Config(30, 3), Config(60, 3))
        assert difference.explain() == ".timeout: 30 != 60"

    def test_dataclasses(self):
        assert diff(Point(1, 2), Point(1, 3)).explain() == ".y: 2 != 3"

    def test_equal(self):
        assert diff(Point(1, 2), Point(1, 2)) is None

    def test_fields_excluded_from_equality_are_ignored(self):
        assert diff(Secretive(1, 2), Secretive(1, 3)) is None

    def test_dataclass_fields_excluded_from_comparison_are_ignored(self):
        assert diff(Tagged(1, "a"), Tagged(1, "b")) is None

    def test_differing_classes_are_left_alone(self):
        one, two = Config(30, 3), Point(1, 2)
        assert diff(one, two) == Unequal(one=one, two=two)

    def test_a_plain_object_is_left_alone(self):
        one, two = object(), object()
        assert diff(one, two) == Unequal(one=one, two=two)

    def test_recursing_into_containers(self):
        one = {"points": [Point(1, 2)]}
        two = {"points": [Point(1, 9)]}
        assert diff(one, two).explain() == "['points'][0].y: 2 != 9"


class TestConstant:
    def test_it_has_a_constant_explanation(self):
        difference = Constant(explanation="my explanation")
        assert difference.explain() == "my explanation"

    def test_it_is_a_difference(self):
        assert isinstance(Constant(explanation="foo"), Difference)

    def test_reversing_does_nothing(self):
        difference = Constant(explanation="my explanation")
        assert difference.reversed() is difference


class TestUnequal:
    def test_explain(self):
        assert Unequal(one=1, two=2).explain() == "1 != 2"

    def test_reversed(self):
        assert Unequal(one=1, two=2).reversed() == Unequal(one=2, two=1)


class TestDifferentTypes:
    def test_explain(self):
        difference = DifferentTypes(one=1, two="1")
        assert difference.explain() == "1 is a int but '1' is a str"

    def test_reversed(self):
        difference = DifferentTypes(one=1, two="1")
        assert difference.reversed() == DifferentTypes(one="1", two=1)


class TestOnlyIn:
    def test_one_explain(self):
        explanation = OnlyInOne(value=12).explain()
        assert explanation == "12 is only in the first object"

    def test_two_explain(self):
        explanation = OnlyInTwo(value=12).explain()
        assert explanation == "12 is only in the second object"

    def test_one_reversed(self):
        assert OnlyInOne(value=12).reversed() == OnlyInTwo(value=12)

    def test_two_reversed(self):
        assert OnlyInTwo(value=12).reversed() == OnlyInOne(value=12)


class TestUncommon:
    def test_reversed(self):
        difference = Uncommon(one={1}, two={2})
        assert difference.reversed() == Uncommon(one={2}, two={1})


class TestNested:
    def test_iteration(self):
        inner = Unequal(one=1, two=2)
        nested = Nested(differences=[("['a']", inner)])
        assert list(nested) == [("['a']", inner)]

    def test_flattened(self):
        inner = Unequal(one=1, two=2)
        nested = Nested(
            differences=[
                ("['a']", Nested(differences=[("['b']", inner)])),
            ],
        )
        assert list(nested.flattened()) == [("['a']['b']", inner)]

    def test_multiline_explanations_are_indented(self):
        inner = Constant(explanation="one\ntwo")
        nested = Nested(differences=[("['a']", inner)])
        assert nested.explain() == dedent(
            """
            ['a']:
              one
              two
            """,
        ).strip("\n")

    def test_reversed(self):
        nested = Nested(differences=[("['a']", Unequal(one=1, two=2))])
        assert nested.reversed() == Nested(
            differences=[("['a']", Unequal(one=2, two=1))],
        )


class TestDiffableProtocol:
    def test_a_diffable_object(self):
        class Something:
            def __diff__(self, other):
                return Constant(explanation="nope")  # pragma: no cover

        assert isinstance(Something(), Diffable)

    def test_a_non_diffable_object(self):
        assert not isinstance(object(), Diffable)
