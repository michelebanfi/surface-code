import numpy as np
from qiskit import QuantumCircuit, ClassicalRegister, transpile
from qiskit.visualization import plot_histogram
import matplotlib.pyplot as plt
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error

grid = 3
n_rounds = 2

n_data = (grid ** 2)//2 + 1

n_syndrome = (grid ** 2) - n_data

data_qubits = list(range(grid**2))
ancilla_qubits = list(range(9, 13))

qc = QuantumCircuit(n_data + n_syndrome, n_syndrome * n_rounds)
print(f"initialized circuit with: {n_data + n_syndrome} qubits and with {n_syndrome * n_rounds} ancillas")

# appy not gate to recognize the data qubits which are in the even row
for i in range(grid**2):
     if i % 2 == 0:
         qc.initialize([1, 0], i)


classical_bits = 0

def logical_x(qc):
    available_qubits = [0, 2]
    for q in available_qubits:
        qc.x(q)

# Create stabilizers
def apply_stabilizers(qc, grid, classical_bits=0):
    for i in range(grid):
        for j in range(grid):
            current = i * grid + j
            # if even row, z-syndrome (without Hadamards)
            if i % 2 == 0:
                if j % 2 == 1:
                    print("Applying Z stabilizers for qubit", current)
                    qc.reset(current)
                    qc.cx(current - 1, current)  # previuos qubit
                    qc.cx(current + 1, current)  # next qubit
                    # if is the first row of the grid, then the qubit has connection with the qubit in the last row
                    if i != 0:
                        qc.cx(current - grid, current)  # qubit above
                    if i != grid - 1:
                        qc.cx(current + grid, current)  # qubit below
                    # measure the qubit onto the corresponding classical bit
                    qc.measure(current, classical_bits)
                    classical_bits += 1
                    qc.barrier()
            else:
                if j % 2 == 0:
                    print("Applying X stabilizers for qubit", current)
                    qc.reset(current)
                    qc.h(current)
                    qc.cx(current + grid, current)  # qubit below
                    qc.cx(current - grid, current)  # qubit above
                    # if is the last row of the grid, then the qubit has connection with the qubit in the first row
                    if j != 0:
                        qc.cx(current - 1, current)
                    if j != grid - 1:
                        qc.cx(current + 1, current)  # next qubit
                    qc.h(current)
                    qc.measure(current, classical_bits)
                    qc.barrier()
                    classical_bits += 1
    return classical_bits

classical_bits = apply_stabilizers(qc, grid, classical_bits)

qc.barrier()
logical_x(qc)
qc.barrier()

classical_bits = apply_stabilizers(qc, grid, classical_bits)
qc.measure_all()

# draw the circuit
qc.draw(output='mpl')
plt.show()
plt.close()

# simulate
simulator = AerSimulator()
compiled_circuit = transpile(qc, simulator)

result = simulator.run(compiled_circuit, shots=1024).result()
counts = result.get_counts()

print(counts)

##############################################################################
# 4) Build a full circuit
##############################################################################

# # We'll do 2 rounds of stabilizer measurement.
# num_rounds = 2
# # Each round uses 4 ancillas -> 4 measurement outcomes.
# # Total classical bits needed = 4 * num_rounds + final data-qubit measurement
# num_stabilizer_cbits = 4 * num_rounds
#
# # We'll also measure the 9 data qubits at the end => 9 more classical bits
# final_data_cbits = 9
#
# qc = QuantumCircuit(13, num_stabilizer_cbits + final_data_cbits)
#
# # 4.1. Initialize data qubits in |0>
# # (Qiskit automatically starts qubits in |0>, but we show this explicitly.)
# for dq in data_qubits:
#     qc.initialize([1, 0], dq)
#
# qc.barrier()
#
# # 4.2. Repeat stabilizer measurements
# cbit_offset = 0
# for r in range(1):
#     cbit_offset = measure_stabilizers_one_round(qc, r, cbit_offset=cbit_offset)
#
# # 4.3. Apply a logical X, then a logical Z (or vice versa)
# qc.barrier()
# logical_x(qc)  # chain from top to bottom across col=1
# qc.barrier()
# logical_z(qc)  # chain from left to right across row=1
# qc.barrier()
#
# cbit_offset = measure_stabilizers_one_round(qc, 2, cbit_offset=cbit_offset)
#
# # 4.4. Finally, measure all data qubits in Z basis to see the result
# for i, dq in enumerate(data_qubits):
#     qc.measure(dq, num_stabilizer_cbits + i)
#
# qc.barrier()
#
# # Draw the circuit
# qc.draw('mpl')
# plt.show()
#
# noiseModel = NoiseModel()
# noiseModel.add_all_qubit_quantum_error(depolarizing_error(0.05, 1), ['x'])
# # noiseModel.add_all_qubit_quantum_error(depolarizing_error(0.05, 1), ['h','x', 'z', 'reset'])
# # noiseModel.add_all_qubit_quantum_error(depolarizing_error(0.05, 2), ['cx'])
# # noiseModel.add_all_qubit_quantum_error(depolarizing_error(0.05, 1), ['measure'])
#
# simulator = AerSimulator(noise_model=noiseModel)
# compiled_circuit = transpile(qc, simulator)
#
# result = simulator.run(compiled_circuit, shots=1024).result()
# counts = result.get_counts()
#
# print(counts)
#
# # extract the logical measurement results
# logical_results = {}
# error_results = {}
# for output in counts:
#     logical_outcome = output[:num_stabilizer_cbits]
#     error_outcome = output[num_stabilizer_cbits:]
#     logical_results[logical_outcome] = counts[output]
#     error_results[error_outcome] = counts[output]
#
# print("Measurement outcomes:", logical_results)
# print("Error outcomes:", error_results)
#
# plot_histogram(counts)
# plt.show()