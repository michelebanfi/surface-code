from qiskit import QuantumCircuit, transpile
from qiskit.visualization import plot_histogram
import matplotlib.pyplot as plt
import networkx as nx
from dotenv import load_dotenv
import os

from utils import apply_stabilizers, logical_x, run_on_ibm, run_on_simulator

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

def process_detection_events(counts, grid, n_rounds):
    stabilizer_qubits = [i for i in range(grid ** 2) if i % 2 == 1]
    n_syndrome = len(stabilizer_qubits)
    detection_events = []

    for shot in counts.keys():
        syndrome_part = shot[-(n_syndrome * n_rounds):]
        syndrome_rounds = [syndrome_part[i * n_syndrome:(i + 1) * n_syndrome] for i in range(n_rounds)]

        for t in range(1, n_rounds):
            current = syndrome_rounds[t]
            previous = syndrome_rounds[t - 1]
            for s in range(n_syndrome):
                if current[s] != previous[s]:
                    qubit = stabilizer_qubits[s]
                    row = qubit // grid
                    col = qubit % grid
                    stab_type = 'Z' if (row % 2 == 0) else 'X'
                    detection_events.append((row, col, stab_type, t))
    return detection_events

def build_mwpm_graph(detection_events, grid):
    G = nx.Graph()
    G.add_node('boundary')

    for event in detection_events:
        row, col, stab_type, t = event
        node_id = f"{row},{col},{t}"
        G.add_node(node_id)

        # Distance to relevant boundary
        if stab_type == 'Z':
            distance = min(row, (grid - 1) - row)
        else:
            distance = min(col, (grid - 1) - col)
        G.add_edge(node_id, 'boundary', weight=distance)

        # Edges to other events
        for other in detection_events:
            if other == event:
                continue
            orow, ocol, ostab_type, ot = other
            if ostab_type != stab_type:
                continue
            manhattan = abs(row - orow) + abs(col - ocol)
            other_id = f"{orow},{ocol},{ot}"
            G.add_edge(node_id, other_id, weight=manhattan)

    return G

def apply_mwpm(G):
    # Invert weights for max weight matching
    inverted_G = nx.Graph()
    for u, v, data in G.edges(data=True):
        inverted_G.add_edge(u, v, weight=-data['weight'])

    matching = nx.max_weight_matching(inverted_G, maxcardinality=True)
    total_weight = sum(G[u][v]['weight'] for u, v in matching)

    return list(matching), total_weight

def calculate_logical_error(counts, grid, matching):
    logical_errors = 0
    total_shots = sum(counts.values())

    for shot, freq in counts.items():
        data_bits = shot[-(grid ** 2):]
        # Apply corrections based on matching
        # (Implement correction application here)
        # Compute logical Z by parity of a row
        logical_z = sum(int(data_bits[i]) for i in [0, 2, 4, 6, 8]) % 2
        if logical_z != 0:
            logical_errors += freq

    return logical_errors / total_shots

detection_events = process_detection_events(counts, grid, n_rounds)
G = build_mwpm_graph(detection_events, grid)
matching, total_weight = apply_mwpm(G)

# Vertical chain for logical Z (indices 0,4,8 in 3x3 grid)
# logical_z_chain = [i*2 for i in range(grid)]
logical_z_chain = [0, 6]

def calculate_logical_error(counts, grid, matching, stabilizer_map, detection_events):
    logical_errors = 0
    total_shots = sum(counts.values())

    # Map detection events to stabilizer indices
    event_to_stabilizer = {}
    for event in detection_events:
        row, col, stab_type, t = event
        qubit_idx = row * grid + col
        event_id = f"{row},{col},{t}"
        event_to_stabilizer[event_id] = qubit_idx

    for shot, freq in counts.items():
        data_bits = list(shot[:(grid ** 2)])

        # Apply corrections from matching
        for pair in matching:
            node1, node2 = pair

            # Get involved stabilizers
            stab1 = event_to_stabilizer.get(node1, None)
            stab2 = event_to_stabilizer.get(node2, None)

            # Boundary case
            if node1 == 'boundary' or node2 == 'boundary':
                # Find which stabilizer is real
                real_stab = stab1 if stab2 == 'boundary' else stab2

                # Flip all data qubits connected to this stabilizer
                for q in stabilizer_map.get(real_stab, []):
                    data_bits[q] = '1' if data_bits[q] == '0' else '0'
            else:
                # Find common data qubits between stabilizer pair
                common = set(stabilizer_map[stab1]) & set(stabilizer_map[stab2])
                for q in common:
                    data_bits[q] = '1' if data_bits[q] == '0' else '0'

        # Check logical Z parity
        parity = sum(int(data_bits[q]) for q in logical_z_chain) % 2
        if parity != 0:
            logical_errors += freq

    return logical_errors / total_shots

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