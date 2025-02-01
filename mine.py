from qiskit import QuantumCircuit
import matplotlib.pyplot as plt
from dotenv import load_dotenv
import os
import networkx as nx
import pickle

from utils import apply_stabilizers, run_on_ibm, run_on_simulator, calculate_error_statistics, plot_error_stats
from utils import process_detection_events, build_mwpm_graph, apply_mwpm, inject_random_errors

load_dotenv()
API_KEY = os.getenv("IBM_API_KEY")
SIMULATION = False
NUM_TRIALS = 1
stats_history = []

if not SIMULATION: NUM_TRIALS = 1

for trial in range(NUM_TRIALS):
    grid = 7
    n_rounds = 4

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

    # qc = inject_random_errors(qc, grid, error_prob=0.1)  # After initialization, before stabilizers

    for _ in range(n_rounds - 1):
        classical_bits, stabilizer_map = apply_stabilizers(qc, grid, classical_bits, stabilizer_map)

    # iterate from (n_syndrome * n_rounds) till grid**2 to measure the grid qubits
    c = n_syndrome * n_rounds
    for i in range(grid**2):
        # print(f"Measuring qubit {i} onto classical bit {c}")
        qc.measure(i, c)
        c = c + 1

    # plot the circuit
    # qc.draw('mpl')
    # plt.savefig("circuit.png")
    # plt.close()

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

    logical_z_chain = [i * grid for i in range(grid) if i % 2 == 0]

    stats = calculate_error_statistics(G, counts, grid, matching, stabilizer_map, detection_events, logical_z_chain)
    stats['total_shots'] = sum(counts.values())
    stats_history.append(stats)

    # create a new object to combine all the stats and the counts
    stats['counts'] = counts

    # save stats under /stats folder with grid size as name. Save them as python objects.
    with open(f'stats/stats_grid_{grid}.pkl', 'wb') as f:
        pickle.dump(stats, f)

    # Draw the matching graph
    pos = nx.spring_layout(G)
    nx.draw(G, pos, with_labels=True, node_color='lightblue')
    labels = nx.get_edge_attributes(G, 'weight')
    nx.draw_networkx_edge_labels(G, pos, edge_labels=labels)
    plt.savefig(f"stats/{grid}_matching_graph.png")
    plt.close()

plot_error_stats(stats_history)