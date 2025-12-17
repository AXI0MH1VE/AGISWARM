import numpy as np
import json
import sys

def generate_sparse_matrix(n, density, scale_bits=31):
    A = np.random.rand(n, n)
    A[A > density] = 0.0
    B = np.random.randn(n, 1) * 0.1
    x0 = np.random.randn(n) * 0.1
    u = np.zeros(1).tolist()
    mat = {
        "A": A.tolist(),
        "B": B.tolist(),
        "x0": x0.tolist(),
        "u": u,
        "scale_bits": scale_bits
    }
    return mat

if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    density = float(sys.argv[2]) if len(sys.argv) > 2 else 0.2
    out = generate_sparse_matrix(n, density)
    with open(f"sparse_matrix_{n}_{density}.json", "w") as f:
        json.dump(out, f, indent=2)
    print(f"Saved sparse_matrix_{n}_{density}.json")

