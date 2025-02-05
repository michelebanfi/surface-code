import pickle
from itertools import combinations
import networkx as nx
import matplotlib.pyplot as plt

def _process_mwpm(syndromes, stabilizer_adj, stabilizer_map, central_qubits, d, time_weight, space_weight):
    """
    Helper function to perform MWPM for a specific error type.
    """
    if len(syndromes) == 0:
        return False

    # Create graph and add all syndrome nodes
    G = nx.Graph()
    for s in syndromes:
        G.add_node(s)

    # Add time-like and space-like edges
    for i, (s1, t1) in enumerate(syndromes):
        for j, (s2, t2) in enumerate(syndromes[i + 1:], i + 1):
            # Time-like edges (same stabilizer, consecutive rounds)
            if s1 == s2 and abs(t1 - t2) == 1:
                G.add_edge((s1, t1), (s2, t2), weight=time_weight)
            # Space-like edges (adjacent stabilizers, same round)
            elif t1 == t2 and s2 in stabilizer_adj.get(s1, []):
                G.add_edge((s1, t1), (s2, t2), weight=space_weight)

    # Virtual node for odd number of syndromes
    if G.number_of_nodes() % 2 != 0:
        virtual_node = (-1, -1)
        G.add_node(virtual_node)
        for node in G.nodes():
            if node != virtual_node:
                G.add_edge(node, virtual_node, weight=1e9)  # High weight to avoid if possible

    # plot the graph
    # plt.figure(figsize=(12, 5), dpi=300)
    # pos = nx.spring_layout(G, k=0.5)
    # nx.draw(G, pos, with_labels=True)
    # labels = nx.get_edge_attributes(G, 'weight')
    # nx.draw_networkx_edge_labels(G, pos, edge_labels=labels)
    # plt.savefig(f"graph_{d}.png")

    # Find minimum weight perfect matching
    matching = nx.algorithms.matching.min_weight_matching(G)

    # Extract affected data qubits
    error_qubits = set()
    for edge in matching:
        (s1, t1), (s2, t2) = edge
        if s1 == -1 or s2 == -1:
            continue  # Ignore virtual node

        # Get shared data qubits for spatial edges
        if t1 == t2:
            shared = set(stabilizer_map[s1]) & set(stabilizer_map[s2])
            error_qubits.update(shared)
        # Time-like edges affect stabilizer's data qubits
        else:
            error_qubits.update(stabilizer_map[s1])

    # Count central column qubits with odd parity
    central_errors = len(error_qubits & set(central_qubits))
    return central_errors > d // 2

def build_stabilizer_adjacency(stabilizer_map):
    """
    Build adjacency list for stabilizers based on shared data qubits.
    """
    adjacency = {}
    stabilizers = list(stabilizer_map.keys())
    for s1, s2 in combinations(stabilizers, 2):
        shared_qubits = set(stabilizer_map[s1]) & set(stabilizer_map[s2])
        if len(shared_qubits) > 0:
            adjacency.setdefault(s1, []).append(s2)
            adjacency.setdefault(s2, []).append(s1)
    return adjacency

def calculate_logical_error_mwpm(rounds_output, stabilizer_indices, stabilizer_map, stabilizer_type, central_qubits, d, time_weight=1.0, space_weight=1.0):
    """
    Detect logical errors using MWPM (surface code decoding).

    Args:
        rounds_output (list of str): Stabilizer measurements ordered oldest to newest.
        stabilizer_indices (list): Order of stabilizers in the measurement string.
        stabilizer_map (dict): Maps stabilizer indices to connected data qubits.
        stabilizer_type (dict): Maps stabilizer indices to 'X' or 'Z'.
        central_qubits (list): Data qubits in the central column.
        d (int): Code distance.
        time_weight (float): Weight for time-like edges.
        space_weight (float): Weight for space-like edges.

    Returns:
        tuple: (logical_x_error, logical_z_error)
    """
    if len(rounds_output) < 2:
        return (False, False)

    # Build stabilizer adjacency for spatial edges
    stabilizer_adj = build_stabilizer_adjacency(stabilizer_map)

    # Extract syndromes (stabilizer, round) for each error type
    syndromes_x = []
    syndromes_z = []

    logical_error = 0

    for round_idx in range(len(rounds_output) - 1):
        current = rounds_output[round_idx]
        next_r = rounds_output[round_idx + 1]

        for bit_idx in range(len(current)):
            if current[bit_idx] != next_r[bit_idx]:
                stabilizer = stabilizer_indices[bit_idx]
                stype = stabilizer_type.get(stabilizer, None)
                if stype == 'Z':
                    syndromes_x.append((stabilizer, round_idx))
                elif stype == 'X':
                    syndromes_z.append((stabilizer, round_idx))

        # Process X and Z errors separately
        logical_x = _process_mwpm(syndromes_x, stabilizer_adj, stabilizer_map, central_qubits, d, time_weight, space_weight)
        logical_z = _process_mwpm(syndromes_z, stabilizer_adj, stabilizer_map, central_qubits, d, time_weight, space_weight)
        if logical_x or logical_z:
            logical_error += 1

        # reset syndromes
        syndromes_x = []
        syndromes_z = []

    return (logical_error / 3)

def analyze_results(results):
    results = results[::-1]  # Reverse if necessary

    for result in results:
        d = int(result['distance'])
        if d%2 == 0:
            continue
        counts = result['counts']

        # take only 30 elements counts from dictionary
        counts = {k: counts[k] for k in list(counts)}

        stabilizer_map = result['stabilizer_map']
        logical_z = result['logical_z']

        # calculate stabilizer type
        maximun = (d * 2 + 1) * 3
        stabilizer_type = {}
        for i in range(1, maximun, 2):
            if i % 6 == 1:
                stabilizer_type[i] = 'Z'
            else:
                stabilizer_type[i] = 'X'

        # stabilizer_indices is a list of numbers from maximum - 2 to 1
        stabilizer_indices = list(range(maximun - 2, 0, -2))

        counts = list(counts.keys())

        total_errors_count = 0

        for c in counts:
            lent = int(len(c)/ 4)
            splitted_c = [c[i:i+lent] for i in range(0, len(c), lent)]

            splitted_c = splitted_c[::-1]

            for i in splitted_c:
                print(i)

            logical = calculate_logical_error_mwpm(splitted_c, stabilizer_indices, stabilizer_map, stabilizer_type, logical_z, d)

            if logical:
                total_errors_count += 1

        print(f"Distance {d}: {total_errors_count / len(counts)}")
        distances.append(d)
        logical_errors.append(total_errors_count / len(counts))

with open('../stats/optimized/recovered_results.pkl', 'rb') as f:
    results = pickle.load(f)

distances = []
logical_errors = []

analyze_results(results)

# plot distances and logical errors
plt.figure(figsize=(12, 5), dpi=300)
plt.plot(distances, logical_errors, 'o-', label='Logical Error Rate')
plt.grid()
plt.xlabel("Code Distance")
plt.ylabel("Error Rate (per shot)")
plt.title("Logical Error Rate vs. Code Distance")
plt.legend()
plt.savefig("final_result.png")

