import numpy.testing

from tqec.compile.detectors.compute import _get_or_default


def test_get_or_default() -> None:
    array = numpy.array([i + numpy.arange(10) for i in range(10)])
    numpy.testing.assert_array_equal(
        _get_or_default(array, [(1, 3), (2, 3)], default=0), [[3], [4]]
    )
    numpy.testing.assert_array_equal(
        _get_or_default(array, [(-1, 3), (2, 3)], default=0), [[0], [2], [3], [4]]
    )
    numpy.testing.assert_array_equal(
        _get_or_default(array, [(-1, 3), (2, 3)], default=34), [[34], [2], [3], [4]]
    )
    numpy.testing.assert_array_equal(
        _get_or_default(array, [(1000, 1002), (345, 347)], default=34),
        numpy.full((2, 2), 34),
    )
