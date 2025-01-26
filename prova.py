import numpy as np
from qiskit import QuantumCircuit, ClassicalRegister, transpile
from qiskit.visualization import plot_histogram
import matplotlib.pyplot as plt
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error

##############################################################################
# 1) Define layout (indices of data vs ancilla qubits)
##############################################################################
grid = 3

data_qubits = list(range(grid**2))              # q0..q8 are data qubits
ancilla_qubits = list(range(9, 13))       # q9..q12 are ancillas

# For convenience, define which data qubits belong to which plaquette:
# We'll name them:
#  - ancilla 9  => top-left (X-type)
#  - ancilla 10 => top-right (Z-type)
#  - ancilla 11 => bottom-left (Z-type)
#  - ancilla 12 => bottom-right (X-type)
#
# Coordinates of data qubits in the 3x3 grid:
#   row = i, col = j => qubit index = 3*i + j
#
# top-left plaquette includes data qubits: q0, q1, q3, q4
# top-right plaquette includes data qubits: q1, q2, q4, q5
# bottom-left plaquette includes data qubits: q3, q4, q6, q7
# bottom-right plaquette includes data qubits: q4, q5, q7, q8

plaquette_map = {
    9:  [0, 1, 3, 4],  # X-stabilizer
    10: [1, 2, 4, 5],  # Z-stabilizer
    11: [3, 4, 6, 7],  # Z-stabilizer
    12: [4, 5, 7, 8]   # X-stabilizer
}

# We also specify which ancillas measure X-type vs Z-type
x_ancillas = [9, 12]
z_ancillas = [10, 11]

##############################################################################
# 2) One round of stabilizer measurement
##############################################################################
def measure_stabilizers_one_round(qc, round_index, cbit_offset=0):
    """
    Apply one round of stabilizer measurement for all 4 plaquettes.
    The result of each ancilla measurement is stored in classical bits
    [cbit_offset, cbit_offset+1, cbit_offset+2, cbit_offset+3].
    """

    for a in ancilla_qubits:
        # 2.1. Reset ancilla to |0> (often required in repeated measurement)
        #     (In a real device, you'd reset or re-initialize ancilla.)
        qc.reset(a)

        # 2.2. Based on X-type or Z-type, do the appropriate routine:
        if a in x_ancillas:
            # X-stabilizer
            qc.h(a)  # put ancilla in |+> basis
            for dq in plaquette_map[a]:
                qc.cx(dq, a)
            qc.h(a)
        else:
            # Z-stabilizer
            # no initial hadamard, measure in Z basis
            for dq in plaquette_map[a]:
                qc.cx(dq, a)

        # 2.3. Measure ancilla
        qc.measure(a, cbit_offset)
        cbit_offset += 1

    # Put a barrier between rounds for clarity
    qc.barrier()
    return cbit_offset


##############################################################################
# 3) Logical operators as strings of physical gates
##############################################################################
def logical_x(qc):
    """
    A path of physical X gates going from top to bottom across the middle column:
    data qubits [1, 4, 7].
    """
    for q in [1, 4, 7]:
        qc.x(q)

def logical_z(qc):
    """
    A path of physical Z gates going from left to right across the middle row:
    data qubits [3, 4, 5].
    """
    for q in [3, 4, 5]:
        qc.z(q)


##############################################################################
# 4) Build a full circuit
##############################################################################

# We'll do 2 rounds of stabilizer measurement.
num_rounds = 2
# Each round uses 4 ancillas -> 4 measurement outcomes.
# Total classical bits needed = 4 * num_rounds + final data-qubit measurement
num_stabilizer_cbits = 4 * num_rounds

# We'll also measure the 9 data qubits at the end => 9 more classical bits
final_data_cbits = 9

qc = QuantumCircuit(13, num_stabilizer_cbits + final_data_cbits)

# 4.1. Initialize data qubits in |0>
# (Qiskit automatically starts qubits in |0>, but we show this explicitly.)
for dq in data_qubits:
    qc.initialize([1, 0], dq)

qc.barrier()

# 4.2. Repeat stabilizer measurements
cbit_offset = 0
for r in range(1):
    cbit_offset = measure_stabilizers_one_round(qc, r, cbit_offset=cbit_offset)

# 4.3. Apply a logical X, then a logical Z (or vice versa)
qc.barrier()
logical_x(qc)  # chain from top to bottom across col=1
qc.barrier()
#logical_z(qc)  # chain from left to right across row=1
qc.barrier()

cbit_offset = measure_stabilizers_one_round(qc, 2, cbit_offset=cbit_offset)

# 4.4. Finally, measure all data qubits in Z basis to see the result
for i, dq in enumerate(data_qubits):
    qc.measure(dq, num_stabilizer_cbits + i)

qc.barrier()

# Draw the circuit
qc.draw('mpl')
plt.show()

noiseModel = NoiseModel()
# noiseModel.add_all_qubit_quantum_error(depolarizing_error(0.05, 1), ['x'])
# noiseModel.add_all_qubit_quantum_error(depolarizing_error(0.05, 1), ['h','x', 'z', 'reset'])
# noiseModel.add_all_qubit_quantum_error(depolarizing_error(0.05, 2), ['cx'])
# noiseModel.add_all_qubit_quantum_error(depolarizing_error(0.05, 1), ['measure'])

simulator = AerSimulator(noise_model=noiseModel)
compiled_circuit = transpile(qc, simulator)

result = simulator.run(compiled_circuit, shots=1024).result()
counts = result.get_counts()

print(counts)

# extract the logical measurement results
logical_results = {}
error_results = {}
for output in counts:
    logical_outcome = output[:num_stabilizer_cbits]
    error_outcome = output[num_stabilizer_cbits:]
    logical_results[logical_outcome] = counts[output]
    error_results[error_outcome] = counts[output]

print("Measurement outcomes:", logical_results)
print("Error outcomes:", error_results)

plot_histogram(counts)
plt.show()