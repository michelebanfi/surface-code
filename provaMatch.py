import networkx as nx
import matplotlib.pyplot as plt

def distance_between_stabilizers(stabA, stabB, stabilizer_map):
    """
    A naive 'distance' metric. In a real code, you'd compute the minimal
    path of data-qubit errors that flips both stabilizers. Here, we just
    do a quick measure: the size of the symmetric difference of their data qubits.
    """
    # Convert to sets
    qubitsA = set(stabilizer_map.get(stabA, []))
    qubitsB = set(stabilizer_map.get(stabB, []))
    # Symmetric difference
    diff = qubitsA.symmetric_difference(qubitsB)
    return len(diff)


def find_flips(t1, t2):
    """
    Given two 12-bit strings t1 and t2 (e.g. '000001000010'),
    return the list of stabilizer indices that flipped (i.e. differ).
    """
    flips = []
    for i in range(len(t1)):
        if t1[i] != t2[i]:
            flips.append(i)
    return flips


def build_detection_graph(t1, t2, stabilizer_map):
    """
    1) Find which stabilizers flipped between t1 and t2.
    2) Build a Graph with one node per flipped stabilizer.
    3) Add weighted edges between all pairs of flipped stabilizers.
    4) Return the resulting NetworkX graph.
    """
    G = nx.Graph()

    # 1) Find flips
    flipped_stabs = find_flips(t1, t2)  # list of stabilizer indices

    # 2) Add one node per flipped stabilizer
    #    Let's label each node simply by the stabilizer index (0..11)
    for stab_idx in flipped_stabs:
        G.add_node(stab_idx)

    # 3) Add edges between all pairs
    for i in range(len(flipped_stabs)):
        for j in range(i + 1, len(flipped_stabs)):
            stabA = flipped_stabs[i]
            stabB = flipped_stabs[j]
            dist = distance_between_stabilizers(stabA, stabB, stabilizer_map)
            # If you'd like, skip adding edges if dist is "too large," etc.
            G.add_edge(stabA, stabB, weight=dist)

    return G


def decode_once(t1, t2, stabilizer_map):
    """
    Build the detection graph for flips between t1 and t2,
    then run MWPM via NetworkX, and return the matching.
    """
    G = build_detection_graph(t1, t2, stabilizer_map)

    # plot the graph
    nx.draw(G, with_labels=True)
    plt.show()
    plt.close()

    if G.number_of_nodes() == 0:
        # No flips at all, no matching needed
        return set()

    # Run min_weight_matching, with maxcardinality=True to ensure
    # we match as many nodes as possible (helpful for perfect matching).
    matching = nx.min_weight_matching(G)
    return matching

def apply_corrections(match_result, stabilizer_map, data_qubit_states):
    """
    For each matched pair (stabA, stabB), flip the data qubits that
    differ between those stabilizers.
    """
    for (stabA, stabB) in match_result:
        qubitsA = set(stabilizer_map.get(stabA, []))
        qubitsB = set(stabilizer_map.get(stabB, []))
        path_qubits = qubitsA.symmetric_difference(qubitsB)
        for dq in path_qubits:
            data_qubit_states[dq] ^= 1  # Flip 0->1 or 1->0
    return data_qubit_states

# Example usage:

# Just a partial example map. You'd have a full dict for all 12 stabs:
stabilizer_map_example = {
    1: [0, 2, 6],
    3: [8, 2, 4],
    5: [0, 10, 6],
    7: [8, 2, 12, 6],
    9: [8, 4, 14],
    11: [16, 10, 12, 6],
    13: [8, 18, 12, 14],
    15: [16, 10, 20],
    17: [16, 18, 12, 22],
    19: [24, 18, 14],
    21: [16, 20, 22],
    23: [24, 18, 22]}

# Suppose we have 2 measurement rounds:
t1 = "000000000000"
t2 = "100001000010"
# t2 differs in the 5th bit and 10th bit, for instance.

# Build a naive data_qubit_states dict of size 25 (for a 5x5)
data_qubit_states = {i: 0 for i in range(25)}

match_result = decode_once(t1, t2, stabilizer_map_example)

print("Flips from t1 to t2 -> MWPM matching result:")
print(match_result)
# Example output might look like: {(5, 10)} meaning stabilizer #5 matched with #10

# 2) Apply corrections
updated_states = apply_corrections(match_result, stabilizer_map_example, data_qubit_states)

print("Data qubit states after naive correction:")
print(updated_states)