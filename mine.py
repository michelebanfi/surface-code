from qiskit import QuantumCircuit
import matplotlib.pyplot as plt
import networkx as nx
from dotenv import load_dotenv
import os

from utils import apply_stabilizers, run_on_ibm, run_on_simulator
from utils import process_detection_events, build_mwpm_graph, apply_mwpm, calculate_logical_error

load_dotenv()
API_KEY = os.getenv("IBM_API_KEY")
SIMULATION = True
LOAD = False

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

classical_bits, stabilizer_map = apply_stabilizers(qc, grid, classical_bits, stabilizer_map)

qc.x(0)

for _ in range(n_rounds - 1):
    classical_bits, stabilizer_map = apply_stabilizers(qc, grid, classical_bits, stabilizer_map)

# iterate from (n_syndrome * n_rounds) till grid**2 to measure the grid qubits
c = n_syndrome * n_rounds
for i in range(grid**2):
    # print(f"Measuring qubit {i} onto classical bit {c}")
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

detection_events = process_detection_events(counts, grid, n_rounds)
G = build_mwpm_graph(detection_events, grid)
matching, total_weight = apply_mwpm(G)

# Vertical chain for logical Z (indices 0,4,8 in 3x3 grid)
# logical_z_chain = [i*2 for i in range(grid)]
logical_z_chain = [0, 6]

# After detection_events and matching are calculated
logical_error_rate = calculate_logical_error(
    counts,
    grid=3,
    matching=matching,
    stabilizer_map=stabilizer_map,
    detection_events=detection_events
)

# Draw the matching graph
pos = nx.spring_layout(G)
nx.draw(G, pos, with_labels=True, node_color='lightblue')
labels = nx.get_edge_attributes(G, 'weight')
nx.draw_networkx_edge_labels(G, pos, edge_labels=labels)
plt.savefig("matching_graph.png")
plt.close()

print(f"Logical Error Rate: {logical_error_rate:.4f}")