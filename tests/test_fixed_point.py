import pytest
from aggregator import fixed_point as fx

def test_to_from_fixed():
    vals = [0.0, 1.0, -1.0, 0.5, -0.5]
    for v in vals:
        f = fx.to_fixed(v)
        assert abs(fx.from_fixed(f) - v) < 1e-7

def test_add_saturation():
    max_v = fx.MAX_INT
    min_v = fx.MIN_INT
    assert fx.add_sat(max_v, 1) == max_v
    assert fx.add_sat(min_v, -1) == min_v

def test_mul_saturation():
    assert fx.mul_sat(fx.MAX_INT, fx.MAX_INT) == fx.MAX_INT
    assert fx.mul_sat(fx.MIN_INT, fx.MIN_INT) == fx.MAX_INT
    assert fx.mul_sat(fx.MAX_INT, fx.MIN_INT) == fx.MIN_INT

def test_matvec_fixed():
    mat = [
        [fx.to_fixed(0.5), fx.to_fixed(-0.5)],
        [fx.to_fixed(1.0), fx.to_fixed(1.0)]
    ]
    vec = [fx.to_fixed(1.0), fx.to_fixed(1.0)]
    res = fx.matvec_fixed(mat, vec)
    assert abs(fx.from_fixed(res[0])) < 1e-6
    assert abs(fx.from_fixed(res[1]) - 2.0) < 1e-6

