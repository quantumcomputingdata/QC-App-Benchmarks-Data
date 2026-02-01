# Usage: python3 rcs.py <n_qubits> <depth> <repeats>
import time
import sys
import cudaq
import numpy as np

percent_2q = 0.25
shots = 1000

def get_random_circuit(n_qubits, n_gates):
    kernel = cudaq.make_kernel()
    qubits = kernel.qalloc(n_qubits)

    for _ in range(n_gates):
        gate_size = np.random.choice(["1Q", "2Q"], p=[1 - percent_2q, percent_2q])
        if gate_size == "2Q":
            qubit_pair = np.random.choice(range(n_qubits), size=2, replace=False)
            q0, q1 = (int(q) for q in qubit_pair)
            kernel.cz(qubits[q0], qubits[q1])

        else:  # "1Q"
            q0 = np.random.choice(range(n_qubits))
            q0 = int(q0)

            gate_type = np.random.choice(["h", "rx", "ry", "rz"])
            if gate_type == "h":
                kernel.h(qubits[q0])
            else:  # "rx", "ry", "rz"
                random_angle = float(np.random.uniform(0, np.pi))
                add_gate = getattr(kernel, gate_type)
                add_gate(random_angle, qubits[q0])
    return kernel

n_qubits = int(sys.argv[1])
depth = int(sys.argv[2])
repeats = int(sys.argv[3])

n_gates = n_qubits * depth
cudaq.set_target("nvidia", option="mgpu,fp32")
np.random.seed(3)

timings = []
for i in range(repeats):
    kernel = get_random_circuit(n_qubits, n_gates)
    result = cudaq.sample(kernel, shots_count=shots)
    start_time = time.time()
    result = cudaq.sample(kernel, shots_count=shots)
    end_time = time.time()
    timings.append(end_time - start_time)

avg_time = sum(timings) / len(timings)
print(f"[CPU] Average simulation time: {avg_time:.6f} s")

