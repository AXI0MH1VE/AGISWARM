import numpy as np
from .fixed_point import to_fixed

PRIME = 65521

class RatelessCoder:
    def __init__(self, matrix_A, R):
        self.R = R
        self.matrix_A = np.array(matrix_A)
        self.rows, self.cols = self.matrix_A.shape
        chunk_size = int(np.ceil(self.rows / R))
        self.chunks = []
        for i in range(R):
            start = i * chunk_size
            end = min(start + chunk_size, self.rows)
            chunk = np.zeros((chunk_size, self.cols))
            if start < self.rows:
                real_data = self.matrix_A[start:end]
                chunk[0:real_data.shape[0], :] = real_data
            self.chunks.append(chunk)

    def generate_task(self, x_fixed_list):
        coeffs = np.random.randint(1, 255, size=self.R).tolist()
        coded_matrix_block = np.zeros_like(self.chunks[0])
        for i, c in enumerate(coeffs):
            coded_matrix_block += c * self.chunks[i]

        coded_fixed = []
        for r in range(coded_matrix_block.shape[0]):
            row_f = [to_fixed(val) for val in coded_matrix_block[r]]
            coded_fixed.append(row_f)
        return coeffs, coded_fixed

    def decode(self, received_results):
        if len(received_results) < self.R: return None
        subset = received_results[:self.R]
        C_matrix = np.array([item[0] for item in subset])
        Y_vector = np.array([item[1] for item in subset])
        try:
            decoded_chunks = np.linalg.solve(C_matrix, Y_vector)
            flat_result = []
            for chunk_row in decoded_chunks:
                for val in chunk_row:
                    flat_result.append(int(round(val)))
            return flat_result[:self.rows]
        except np.linalg.LinAlgError:
            return None

