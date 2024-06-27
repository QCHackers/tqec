import random
import sys

import pytest

from tqec.exceptions import TQECException
from tqec.templates.interval import Interval, Intervals


def test_interval_creation():
    Interval(0, 1)
    Interval(0, 0)
    Interval(float("-inf"), float("inf"))
    Interval(0, float("inf"))
    Interval(0, 10**100)

    error_message = r"^Cannot create an interval with [^ ]+ <= [^\.]+.$"
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


def test_interval_is_empty():
    assert Interval(0, 0).is_empty()
    assert Interval(float("-inf"), float("-inf")).is_empty()
    assert not Interval(float("-inf"), float("inf")).is_empty()


def test_random_interval_is_empty():
    for f in (_float() for _ in range(100)):
        assert Interval(f, f).is_empty()


def test_interval_emty_contains():
    interval = Interval(0, 0)
    assert not interval.contains(0)
    assert not interval.contains(-0)


def test_random_interval_contains():
    interval = Interval(_float(b=-10), _float(a=10))
    for f in (_float(-10, 10) for _ in range(100)):
        assert interval.contains(f)


def test_internal_overlaps_with_itself():
    a = Interval(0, 2)
    assert a.overlaps_with(a)
    assert not a.is_disjoint(a)

    a = Interval(float("-inf"), float("inf"))
    assert a.overlaps_with(a)
    assert not a.is_disjoint(a)


def test_interval_overlaps():
    a, b = Interval(0, 2), Interval(1, 3)
    assert a.overlaps_with(b)
    assert b.overlaps_with(a)
    assert not a.is_disjoint(b)
    assert not b.is_disjoint(a)
    assert a.intersection(b) == b.intersection(a) == Interval(1, 2)
    assert a.union(b) == b.union(a) == Intervals([Interval(0, 3)])


def test_interval_not_overlapping():
    a, b = Interval(0, 2), Interval(2, 3)
    assert not a.overlaps_with(b)
    assert not b.overlaps_with(a)
    assert a.is_disjoint(b)
    assert b.is_disjoint(a)
    assert a.intersection(b).is_empty()
    assert b.intersection(a).is_empty()
    assert a.union(b) == b.union(a) == Intervals([Interval(0, 3)])


def test_interval_included():
    a, b = Interval(float("-inf"), float("inf")), Interval(2, 3)
    assert a.overlaps_with(b)
    assert b.overlaps_with(a)
    assert not a.is_disjoint(b)
    assert not b.is_disjoint(a)
    assert a.intersection(b) == b
    assert a.union(b) == Intervals([a])
