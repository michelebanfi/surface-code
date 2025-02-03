import pickle
import matplotlib.pyplot as plt
import networkx as nx

from utils import apply_stabilizers, run_on_ibm, run_on_simulator, calculate_error_statistics, plot_error_stats
from utils import process_detection_events, build_mwpm_graph, apply_mwpm, inject_random_errors

grids = [5, 7, 9, 11]

def load_stats(filename):
    with open(filename, 'rb') as f:
        data = pickle.load(f)
    # If the loaded object is a dictionary, wrap it in a list for uniform handling.
    if isinstance(data, dict):
        return [data]
    return data

def calculate_stabilizer_map(grid):
    """
    Calculate the stabilizer map for a grid of qubits.

    For each qubit in the grid, if it is a stabilizer qubit then its key is added to the dictionary with
    a list of neighboring qubits. The rules are as follows:

    - Z-stabilizers: For qubits in even-numbered rows (i % 2 == 0) and odd-numbered columns (j % 2 == 1),
      add:
         * Left neighbor: index current - 1
         * Right neighbor: index current + 1
         * Above neighbor: current - grid (if not in the first row)
         * Below neighbor: current + grid (if not in the last row)

    - X-stabilizers: For qubits in odd-numbered rows (i % 2 == 1) and even-numbered columns (j % 2 == 0),
      add:
         * Below neighbor: current + grid
         * Above neighbor: current - grid
         * Left neighbor: current - 1 (if not in the first column)
         * Right neighbor: current + 1 (if not in the last column)

    Parameters:
        grid (int): The grid dimension (assumes a grid of size grid x grid).

    Returns:
        dict: A dictionary where each key is the index of a stabilizer qubit and the value is a list of its neighbor indices.
    """
    stabilizer_map = {}

    for i in range(grid):
        for j in range(grid):
            current = i * grid + j
            # Z-stabilizers: even row and odd column
            if i % 2 == 0 and j % 2 == 1:
                stabilizer_map[current] = []
                # left neighbor (always valid since j is odd and j-1 exists)
                stabilizer_map[current].append(current - 1)
                # right neighbor
                stabilizer_map[current].append(current + 1)
                # add neighbor above if not in the first row
                if i != 0:
                    stabilizer_map[current].append(current - grid)
                # add neighbor below if not in the last row
                if i != grid - 1:
                    stabilizer_map[current].append(current + grid)

            # X-stabilizers: odd row and even column
            elif i % 2 == 1 and j % 2 == 0:
                stabilizer_map[current] = []
                # below neighbor
                stabilizer_map[current].append(current + grid)
                # above neighbor
                stabilizer_map[current].append(current - grid)
                # left neighbor (if not in the first column)
                if j != 0:
                    stabilizer_map[current].append(current - 1)
                # right neighbor (if not in the last column)
                if j != grid - 1:
                    stabilizer_map[current].append(current + 1)

    return stabilizer_map

for grid in grids:
    print("LOG - Loading stats")
    stats = load_stats(f'stats/boundary/stats_grid_{grid}.pkl')
    stats = stats[0]
    stabilizer_map = calculate_stabilizer_map(grid)

    logical_z_chain = [(i * grid) + 1 for i in range(grid) if i % 2 != 0]
    print(f"LOG - Logical chain with d: {len(logical_z_chain)}")

    n_rounds = 4
    counts = stats['counts']

    print("LOG - Processing detection events")
    detection_events = process_detection_events(counts, grid, n_rounds)
    G = build_mwpm_graph(detection_events, grid)
    matching, total_weight = apply_mwpm(G)

    new_stats = calculate_error_statistics(G, counts, grid, matching, stabilizer_map, detection_events, logical_z_chain)
    new_stats['total_shots'] = sum(counts.values())

    new_stats['counts'] = counts


    print("LOG - Dumping stats")
    with open(f'stats/internal/stats_grid_{grid}.pkl', 'wb') as f:
        pickle.dump(stats, f)

    pos = nx.spring_layout(G)
    nx.draw(G, pos, with_labels=True, node_color='lightblue')
    labels = nx.get_edge_attributes(G, 'weight')
    nx.draw_networkx_edge_labels(G, pos, edge_labels=labels)
    plt.savefig(f"stats/internal/{grid}_matching_graph.png")
    plt.close()
    # print(f"Grid size: {grid}")