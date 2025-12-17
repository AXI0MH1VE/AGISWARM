"""
Q1.31 Fixed Point Arithmetic Library.
Enforces deterministic behavior by avoiding standard floating point units.
"""
Q_BITS = 31
MAX_INT = (1 << 31) - 1
MIN_INT = -(1 << 31)

def to_fixed(float_val):
    raw = int(float_val * (1 << Q_BITS))
    return max(min(raw, MAX_INT), MIN_INT)

def from_fixed(fixed_val):
    return fixed_val / (1 << Q_BITS)

def mul_sat(a, b):
    res = (a * b) >> Q_BITS
    return max(min(res, MAX_INT), MIN_INT)

def add_sat(a, b):
    res = a + b
    return max(min(res, MAX_INT), MIN_INT)

def matvec_fixed(matrix_fixed, vec_fixed):
    rows = len(matrix_fixed)
    cols = len(matrix_fixed[0])
    result = []
    for r in range(rows):
        acc = 0
        for c in range(cols):
            prod = mul_sat(matrix_fixed[r][c], vec_fixed[c])
            acc = add_sat(acc, prod)
        result.append(acc)
    return result

