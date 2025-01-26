import numpy as np
from qiskit import QuantumCircuit, ClassicalRegister, transpile
from qiskit.visualization import plot_histogram
import matplotlib.pyplot as plt
from qiskit_aer import AerSimulator

grid = 3
n_rounds = 2

# Calculate data and ancilla qubits (example for 3x3 grid)
n_data = 5  # Example allocation, adjust based on your code's needs
n_ancilla = 4  # Number of stabilizers (adjust as needed)
total_qubits = n_data + n_ancilla

qc = QuantumCircuit(total_qubits, n_ancilla * n_rounds)

# Initialize data qubits (optional)
# for q in range(n_data):
#     qc.initialize([1, 0], q)  # Initialize to |0⟩

def apply_z_stabilizer(qc, data_qubits, ancilla, cl_bit):
    qc.reset(ancilla)
    qc.h(ancilla)
    for dq in data_qubits:
        qc.cx(ancilla, dq)
    qc.h(ancilla)
    qc.measure(ancilla, cl_bit)

def apply_x_stabilizer(qc, data_qubits, ancilla, cl_bit):
    qc.reset(ancilla)
    for dq in data_qubits:
        qc.h(dq)
        qc.cx(dq, ancilla)
        qc.h(dq)
    qc.measure(ancilla, cl_bit)

# Example stabilizer applications (adjust qubit indices as needed)
classical_bit = 0
# First round of stabilizers
apply_z_stabilizer(qc, [0, 1, 2, 3], n_data, classical_bit)
classical_bit +=1
apply_x_stabilizer(qc, [1, 2, 3, 4], n_data+1, classical_bit)
classical_bit +=1

qc.barrier()

# Second round of stabilizers
apply_z_stabilizer(qc, [0, 1, 2, 3], n_data, classical_bit)
classical_bit +=1
apply_x_stabilizer(qc, [1, 2, 3, 4], n_data+1, classical_bit)
classical_bit +=1

qc.draw('mpl')
plt.show()

# Simulate
simulator = AerSimulator()
compiled = transpile(qc, simulator)
result = simulator.run(compiled, shots=1024).result()
counts = result.get_counts()
print(counts)