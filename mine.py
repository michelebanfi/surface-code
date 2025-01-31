from qiskit import QuantumCircuit, transpile
from qiskit.visualization import plot_histogram
import matplotlib.pyplot as plt

from utils import apply_stabilizers, logical_x, mwpm_decoder, run_on_ibm, run_on_simulator

API_KEY = "039fcc48a1c2eae0fa22fe7857e5a02ed89cd782d5738fac3bbd97d8f6e0506b330bd51db32ed92ca4a07490141cc7c3dfade0618db865772491155d7b4f2192"
SIMULATION = True

grid = 3
n_rounds = 2

if grid % 2 != 1:
    raise ValueError("Grid size must be an odd number")

n_data = (grid ** 2)//2 + 1
n_syndrome = (grid ** 2) - n_data

data_qubits = list(range(grid**2))

qc = QuantumCircuit(n_data + n_syndrome, (n_syndrome * n_rounds) + grid**2)

stabilizer_map = {}

# Initialize the qubits
for i in range(grid**2):
    if i % 2 == 0:
        qc.initialize([1, 0], i)
    else:
        stabilizer_map[i] = []

classical_bits = 0
# for i in range(n_rounds):
#     classical_bits, stabilizer_map = apply_stabilizers(qc, grid, classical_bits, stabilizer_map)
classical_bits, stabilizer_map = apply_stabilizers(qc, grid, classical_bits, stabilizer_map)
qc.x(0)
classical_bits, stabilizer_map = apply_stabilizers(qc, grid, classical_bits, stabilizer_map)

# iterate from (n_syndrome * n_rounds) till grid**2 to measure the grid qubits
c = n_syndrome * n_rounds
for i in range(grid**2):
    print(f"Measuring qubit {i} onto classical bit {c}")
    qc.measure(i, c)
    c = c + 1

# plot the circuit
qc.draw('mpl')
plt.savefig("circuit.png")
plt.close()

# iterate through the stabilizer map
for k, v in stabilizer_map.items():
    # the value is a list of connections, remove duplicates
    stabilizer_map[k] = list(set(v))

print(stabilizer_map)

if SIMULATION:
    counts = run_on_simulator(qc)
else:
    counts = run_on_ibm(qc)

print(counts)

# Apply decoder
corrected = mwpm_decoder(counts, stabilizer_map, n_rounds)

# Analyze results
print("LOG - Most common outcomes:")
for res, count in sorted(corrected.items(), key=lambda x: -x[1])[:5]:
    print(f"{res} : {count}")


plot_histogram([counts, corrected],
               legend=['Raw Results', 'Corrected'],
               title='Surface Code Results',
               figsize=(15, 6),
               sort='value_desc')
plt.show()
plt.close()