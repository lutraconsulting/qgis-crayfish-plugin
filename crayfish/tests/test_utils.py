import math
from ..utils import integrate


def test_integrate():
    x = list(range(1, 10))
    y = x
    value = (y[-1]*y[-1]-y[0]*y[0])/2
    assert integrate(x, y) == value


def test_integrate_with_nan():
    x = list(range(1, 10))
    y = x
    # introduce some NaN values
    for i in [0, 5, -1]:
        y[i] = math.nan
    x[6] = math.nan
    value = (y[4]*y[4]-y[1]*y[1])/2 + (y[-2]*y[-2]-y[7]*y[7])/2
    assert integrate(x, y) == value


def test_integrate_fail():
    x = list(range(1, 10))
    y = list(range(1, 9))
    assert integrate(x, y) is None
