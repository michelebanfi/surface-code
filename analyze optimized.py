# analyze_surface_code.py
import pickle
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from collections import defaultdict
from tqdm import tqdm

def apply_mwpm(G):
    # Invert weights for max weight matching
    inverted_G = nx.Graph()
    for u, v, data in G.edges(data=True):
        inverted_G.add_edge(u, v, weight=-data['weight'])

    matching = nx.max_weight_matching(inverted_G, maxcardinality=True)
    total_weight = sum(G[u][v]['weight'] for u, v in matching)

    return list(matching), total_weight

def process_detection_events(counts, distance, n_rounds=4):
    """Process measurement outcomes for 3-column surface code"""
    n_rows = 2 * distance + 1
    detection_events = []

    # Syndrome qubits follow checkerboard pattern in 3-column grid
    syndrome_indices = []
    for r in range(n_rows):
        for c in range(3):
            if (r + c) % 2 == 1:
                syndrome_indices.append(r * 3 + c)

    n_syndrome = len(syndrome_indices)

    for shot in counts.keys():
        syndrome_part = shot[-n_syndrome * n_rounds:]
        syndrome_rounds = [syndrome_part[i * n_syndrome: (i + 1) * n_syndrome]
                           for i in range(n_rounds)]

        for t in range(1, n_rounds):
            current = syndrome_rounds[t]
            previous = syndrome_rounds[t - 1]
            for s_idx in range(n_syndrome):
                if current[s_idx] != previous[s_idx]:
                    q = syndrome_indices[s_idx]
                    row, col = divmod(q, 3)
                    stab_type = 'Z' if (row % 2 == 0) else 'X'
                    detection_events.append((row, col, stab_type, t))

    return detection_events

def build_mwpm_graph(detection_events, distance):
    """Build matching graph for 3-column architecture"""
    G = nx.Graph()
    G.add_node('boundary')

    for event in tqdm(detection_events):
        row, col, stab_type, t = event
        node_id = f"{row},{col},{t}"
        G.add_node(node_id)

        # Calculate distance to boundary
        if stab_type == 'Z':
            # Vertical boundaries for Z stabilizers
            distance_to_boundary = min(row, (2 * distance) - row)
        else:
            # Horizontal boundaries for X stabilizers
            distance_to_boundary = min(col, 2 - col)  # Only 3 columns

        G.add_edge(node_id, 'boundary', weight=distance_to_boundary)

        # Connect to other events
        for other in detection_events:
            if other == event:
                continue
            orow, ocol, ostab_type, ot = other
            if ostab_type != stab_type:
                continue

            # Manhattan distance in 3-column grid
            vertical_dist = abs(row - orow)
            horizontal_dist = abs(col - ocol)
            manhattan = vertical_dist + horizontal_dist
            other_id = f"{orow},{ocol},{ot}"
            G.add_edge(node_id, other_id, weight=manhattan)

    return G

def calculate_logical_error(counts, logical_chain, corrections, initial_state=0):
    """
    Calculate logical error rate using parity of corrections along the logical chain.
    (Assumes you know the initial state or can infer it from stabilizers)
    """
    logical_errors = 0
    total_shots = sum(counts.values())

    for shot, freq in counts.items():
        # Infer net corrections along logical chain
        # This is where physical layout mapping matters!
        net_flips = sum(corrections.get(q, 0) for q in logical_chain) % 2

        # Compare to expected parity based on initial state
        logical_errors += freq * (net_flips != initial_state)

    return logical_errors / total_shots

def determine_corrections(matching, detection_events, distance):
    corrections = defaultdict(int)  # key: qubit index, value: number of corrections (mod 2)

    for pair in matching:
        node1, node2 = pair

        # Handle boundary connections
        if node1 == 'boundary' or node2 == 'boundary':
            # Determine which node is the event (not boundary)
            event_node = node1 if node2 == 'boundary' else node2
            row, col, t = map(int, event_node.split(','))
            stab_type = 'Z' if (row % 2 == 0) else 'X'

            # Find path from event to nearest boundary
            path = path_to_boundary((row, col), stab_type, distance)
            for qubit in path:
                corrections[qubit] += 1
        else:
            # Extract positions from node IDs
            row1, col1, t1 = map(int, node1.split(','))
            row2, col2, t2 = map(int, node2.split(','))
            stab_type = 'Z' if (row1 % 2 == 0) else 'X'

            # Find shortest path between the two events
            path = find_shortest_path((row1, col1), (row2, col2), stab_type)
            for qubit in path:
                corrections[qubit] += 1

    # Apply modulo 2 (each correction flips the qubit)
    return {q: c % 2 for q, c in corrections.items()}

def path_to_boundary(position, stab_type, distance):
    """Determine the path from a detection event to the nearest boundary."""
    row, col = position
    path = []

    if stab_type == 'Z':
        # Vertical boundary (top or bottom)
        if row < distance:
            # Move up to top boundary
            for r in range(row, -1, -1):
                path.append((r, col))
        else:
            # Move down to bottom boundary
            for r in range(row, 2 * distance + 1):
                path.append((r, col))
    else:
        # Horizontal boundary (left or right in 3-column)
        if col == 0:
            # Move left (but 3-column, so leftmost is col 0)
            pass  # Already at boundary
        elif col == 2:
            # Move right (but 3-column, rightmost is col 2)
            pass  # Already at boundary
    return path  # Simplified; adjust based on lattice structure

def find_shortest_path(pos1, pos2, stab_type):
    """Find path between two positions for a given stabilizer type."""
    path = []
    r1, c1 = pos1
    r2, c2 = pos2

    # Manhattan path (simplified)
    # Vertical movement first for Z, horizontal for X
    if stab_type == 'Z':
        step_r = 1 if r2 > r1 else -1
        for r in range(r1, r2, step_r):
            path.append((r, c1))
        step_c = 1 if c2 > c1 else -1
        for c in range(c1, c2 + step_c, step_c):
            path.append((r2, c))
    else:
        step_c = 1 if c2 > c1 else -1
        for c in range(c1, c2, step_c):
            path.append((r1, c))
        step_r = 1 if r2 > r1 else -1
        for r in range(r1, r2 + step_r, step_r):
            path.append((r, c2))
    return path

def analyze_results(results):
    error_rates = defaultdict(list)
    results = results[::-1]  # Reverse if necessary


    for result in results:
        d = int(result['distance'])
        counts = result['counts']

        # take only 30 elements counts from dictionary
        counts = {k: counts[k] for k in list(counts)[:30]}

        stabilizer_map = result['stabilizer_map']
        logical_z = result['logical_z']

        print("LOG - Processing detection events")
        detection_events = process_detection_events(counts, d)

        print("LOG - Creating graph")
        G = build_mwpm_graph(detection_events, d)

        print("LOG - Applying MWPM")
        matching, _ = apply_mwpm(G)

        print("LOG - Determining corrections")
        # Determine corrections from matching
        corrections = determine_corrections(matching, detection_events, d)

        print("LOG - Calculating logical error rate")
        # Calculate logical error rate with corrections
        error_rate = calculate_logical_error(counts, logical_z, corrections)
        error_rates[d].append(error_rate)

        print(f"Distance {d}: {error_rate}")

    avg_errors = {d: np.mean(rates) for d, rates in error_rates.items()}
    return avg_errors

def plot_logical_errors(avg_errors):
    """Plot logical error rate vs code distance"""
    distances = sorted(avg_errors.keys())
    rates = [avg_errors[d] for d in distances]

    plt.figure(figsize=(8, 5))
    plt.plot(distances, rates, 'o-')
    plt.xlabel('Code Distance')
    plt.ylabel('Logical Error Rate')
    plt.title('Surface Code Performance (3-column architecture)')
    plt.grid(True)
    plt.savefig('logical_error_rates.png')
    plt.close()

if __name__ == "__main__":
    # Load recovered results
    with open("stats/optimized/recovered_results.pkl", "rb") as f:
        results = pickle.load(f)

    # Analyze results
    avg_errors = analyze_results(results)

    # Plot results
    plot_logical_errors(avg_errors)
    print("Analysis complete. Plot saved as logical_error_rates.png")