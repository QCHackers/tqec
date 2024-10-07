import itertools
import random
import sys

import pytest

from tqec.exceptions import TQECException
from tqec.interval import EMPTY_INTERVAL, Interval, Intervals


def test_interval_creation() -> None:
    Interval(0, 1)
    Interval(0, 0)
    Interval(float("-inf"), float("inf"))
    Interval(0, float("inf"))
    Interval(0, 10**100)

    error_message = r"^Cannot create an interval with start=[^ ]+ > end=[^\.]+.$"
    with pytest.raises(TQECException, match=error_message):
        Interval(1, 0)
    with pytest.raises(TQECException, match=error_message):
        Interval(0, float("-inf"))
    with pytest.raises(
        TQECException, match=r"Cannot create an Interval with a NaN bound\."
    ):
        Interval(0, float("nan"))


def _float(a: float = -sys.float_info.max, b: float = sys.float_info.max) -> float:
    return random.uniform(a, b)


def get_random_intervals(n: int) -> list[Interval]:
    return [
        Interval(min(a, b), max(a, b))
        for a, b in ((_float(), _float()) for _ in range(n))
    ]


def test_interval_is_empty() -> None:
    assert Interval(0, 0).is_empty()
    assert Interval(float("-inf"), float("-inf")).is_empty()
    assert not Interval(float("-inf"), float("inf")).is_empty()
    assert EMPTY_INTERVAL.is_empty()
    assert not Interval(0, 0, start_excluded=False, end_excluded=False).is_empty()


def test_random_interval_is_empty() -> None:
    for f in (_float() for _ in range(100)):
        assert Interval(f, f, start_excluded=True, end_excluded=True).is_empty()
        assert Interval(f, f, start_excluded=False, end_excluded=True).is_empty()
        assert Interval(f, f, start_excluded=True, end_excluded=False).is_empty()
        assert not Interval(f, f, start_excluded=False, end_excluded=False).is_empty()


def test_interval_empty_contains() -> None:
    interval = Interval(0, 0)
    assert not interval.contains(0)
    assert not interval.contains(-0)


def test_random_interval_contains() -> None:
    interval = Interval(_float(b=-10), _float(a=10))
    for f in (_float(-10, 10) for _ in range(100)):
        assert interval.contains(f)


def test_internal_overlaps_with_itself() -> None:
    a = Interval(0, 2)
    assert a.overlaps_with(a)
    assert not a.is_disjoint(a)

    a = Interval(float("-inf"), float("inf"))
    assert a.overlaps_with(a)
    assert not a.is_disjoint(a)


def test_interval_overlaps() -> None:
    a, b = Interval(0, 2), Interval(1, 3)
    assert a.overlaps_with(b)
    assert b.overlaps_with(a)
    assert not a.is_disjoint(b)
    assert not b.is_disjoint(a)
    assert a.intersection(b) == b.intersection(a) == Interval(1, 2)
    assert a.union(b) == b.union(a) == Intervals([Interval(0, 3)])

    for start_excluded, end_excluded in itertools.product((True, False), (True, False)):
        a = Interval(0, 1, start_excluded=False, end_excluded=end_excluded)
        b = Interval(1, 2, start_excluded=start_excluded, end_excluded=True)
        are_disjoint = end_excluded or start_excluded

        assert a.is_disjoint(b) == are_disjoint
        assert b.is_disjoint(a) == are_disjoint
        assert a.overlaps_with(b) == (not are_disjoint)
        assert b.overlaps_with(a) == (not are_disjoint)


def test_interval_not_overlapping() -> None:
    a, b = Interval(0, 2), Interval(2, 3)
    assert not a.overlaps_with(b)
    assert not b.overlaps_with(a)
    assert a.is_disjoint(b)
    assert b.is_disjoint(a)
    assert a.intersection(b).is_empty()
    assert b.intersection(a).is_empty()
    assert a.union(b) == b.union(a) == Intervals([Interval(0, 3)])


def test_interval_included() -> None:
    a, b = Interval(float("-inf"), float("inf")), Interval(2, 3)
    assert a.overlaps_with(b)
    assert b.overlaps_with(a)
    assert not a.is_disjoint(b)
    assert not b.is_disjoint(a)
    assert a.intersection(b) == b
    assert a.union(b) == Intervals([a])


def test_intervals_creation() -> None:
    Intervals([])
    Intervals([Interval(float("-inf"), float("inf"))])
    Intervals([Interval(0, float("inf"))])
    Intervals([Interval(0, 1)])
    Intervals([Interval(i, i + 1) for i in range(10)])

    with pytest.raises(
        TQECException,
        match=r"Cannot build an Intervals instance with overlapping intervals\.",
    ):
        Intervals([Interval(0, 3), Interval(2, 4)])
    with pytest.raises(
        TQECException,
        match=r"Cannot build an Intervals instance with overlapping intervals\.",
    ):
        Intervals([Interval(0, 3), Interval(-2, 4)])

    # (False, False) results in overlapping intervals, which does not satisfy the
    # Intervals pre-conditions.
    for start_excluded, end_excluded in [(True, True), (True, False), (False, True)]:
        intervals = Intervals(
            [
                Interval(
                    i, i + 1, start_excluded=start_excluded, end_excluded=end_excluded
                )
                for i in range(10)
            ]
        )
        can_be_merged = not (start_excluded and end_excluded)
        expected_intervals = 1 if can_be_merged else 10
        assert len(intervals.intervals) == expected_intervals


def test_intervals_contains() -> None:
    intervals = Intervals([Interval(3, 5), Interval(0, 2)])
    for value, should_contain in [
        (0, True),
        (1, True),
        (2, False),
        (2.5, False),
        (3, True),
        (4, True),
        (5, False),
        (38924, False),
        (float("inf"), False),
        (float("nan"), False),
    ]:
        assert intervals.contains(value) == should_contain


def test_intervals_is_empty() -> None:
    assert Intervals([]).is_empty()
    assert Intervals([Interval(0, 0)]).is_empty()
    assert Intervals([Interval(i, i) for i in [-1, 0, float("inf"), float("-inf")]])


def test_intervals_intersection() -> None:
    a = Intervals([Interval(0, 1), Interval(2, 3), Interval(4, 5)])
    b = Intervals([Interval(0, 1), Interval(2.5, 3.5)])
    ab = Intervals([Interval(0, 1), Interval(2.5, 3)])

    assert a.intersection(a) == a
    assert a.intersection(b) == ab
    assert b.intersection(a) == ab


def test_interval_iter_integers() -> None:
    assert list(Interval(0.5, 10.5).iter_integers()) == list(range(1, 11))
    assert list(Interval(0, 10, end_excluded=True).iter_integers()) == list(
        range(0, 10)
    )
    assert list(Interval(-10, 10, end_excluded=False).iter_integers()) == list(
        range(-10, 11)
    )
    assert list(
        Interval(-10, 0, start_excluded=True, end_excluded=True).iter_integers()
    ) == list(range(-9, 0))
