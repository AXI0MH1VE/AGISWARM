from aggregator.coding import RatelessCoder
from aggregator.fixed_point import to_fixed
import numpy as np

def make_test_data():
    A = np.eye(4)
    return A.tolist(), [to_fixed(x) for x in [1, 2, 3, 4]]

def test_rateless_decode_identity():
    A, x_fixed = make_test_data()
    coder = RatelessCoder(A, 2)
    results = []
    for _ in range(2):
        coeffs, coded_block = coder.generate_task(x_fixed)
        y_nc = np.dot(np.array(coded_block), np.array(x_fixed))
        results.append((coeffs, y_nc.tolist()))
    out = coder.decode(results)
    assert out is not None
    assert len(out) == 4

