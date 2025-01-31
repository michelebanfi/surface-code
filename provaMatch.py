import networkx as nx
import matplotlib.pyplot as plt


def distance_between_stabilizers(stabA, stabB, stabilizer_map):
    """
    A naive 'distance' metric. In a real code, you'd compute the minimal
    path of data-qubit errors that flips both stabilizers. Here, we just
    do a quick measure: the size of the symmetric difference of their data qubits.
    """
    qubitsA = set(stabilizer_map.get(stabA, []))
    qubitsB = set(stabilizer_map.get(stabB, []))
    diff = qubitsA.symmetric_difference(qubitsB)
    return len(diff)


def find_flips(round_str_1, round_str_2):
    """
    Given two bit-strings for consecutive rounds (like '0000' and '1001'
    if there are 4 stabilizers), return the list of stabilizer indices
    that flipped (i.e. differ in bit).
    """
    flips = []
    for i in range(len(round_str_1)):
        if round_str_1[i] != round_str_2[i]:
            flips.append(i)
    return flips


def build_detection_graph(round_str_1, round_str_2, stabilizer_map, plot_graph=False):
    """
    1) Find which stabilizers flipped between round_str_1 and round_str_2.
    2) Build a Graph with one node per flipped stabilizer.
    3) Add weighted edges between all pairs of flipped stabilizers
       using 'distance_between_stabilizers'.
    4) Optionally plot the graph, then return it.
    """
    # 1) Identify flips
    flipped_stabs = find_flips(round_str_1, round_str_2)

    # 2) Build a NetworkX graph
    G = nx.Graph()
    for stab_idx in flipped_stabs:
        G.add_node(stab_idx)

    # 3) Add edges
    for i in range(len(flipped_stabs)):
        for j in range(i + 1, len(flipped_stabs)):
            stabA = flipped_stabs[i]
            stabB = flipped_stabs[j]
            dist = distance_between_stabilizers(stabA, stabB, stabilizer_map)
            G.add_edge(stabA, stabB, weight=dist)

    # 4) Plot if requested
    if plot_graph and G.number_of_nodes() > 0:
        pos = nx.spring_layout(G, seed=42)
        nx.draw(G, pos, with_labels=True)
        labels = nx.get_edge_attributes(G, 'weight')
        nx.draw_networkx_edge_labels(G, pos, edge_labels=labels)
        plt.show()
        plt.close()

    return G


def decode_round_pair(round_str_1, round_str_2, stabilizer_map, plot_graph=False):
    """
    Build the detection graph for flips between round_str_1 and round_str_2,
    then run MWPM via NetworkX, and return the matching set.
    """
    G = build_detection_graph(round_str_1, round_str_2, stabilizer_map, plot_graph=plot_graph)

    if G.number_of_nodes() == 0:
        # No flips at all
        return set()

    # MWPM with maximum cardinality
    matching = nx.min_weight_matching(G)
    return matching


def apply_corrections(match_result, stabilizer_map, data_qubit_states):
    """
    For each matched pair (stabA, stabB), flip the data qubits that
    differ between those stabilizers (naive approach).
    """
    for (stabA, stabB) in match_result:
        qubitsA = set(stabilizer_map.get(stabA, []))
        qubitsB = set(stabilizer_map.get(stabB, []))
        path_qubits = qubitsA.symmetric_difference(qubitsB)

        # Toggle those data qubits
        for dq in path_qubits:
            data_qubit_states[dq] ^= 1

        # trasform the dictionary data_qubit_states into a string

    data_qubit_states = ''.join([str(data_qubit_states[i]) for i in range(len(data_qubit_states))])

    return data_qubit_states


def decode_surface_code_shot(
        result_str,
        data_qubit_count,
        stabilizer_count,
        num_rounds,
        stabilizer_map,
        data_qubit_states=None,
        plot_graphs=False
    ):
    """
    High-level function:
      1. Parse `result_str` to extract data-qubit bits + stabilizer bits per round.
      2. For each pair of consecutive rounds, build detection graph & run MWPM.
      3. Apply naive corrections to data_qubit_states.

    Arguments:
      result_str        : e.g. '00000000000000000' for 3x3 code (9 data qubits + 8 ancillas).
      data_qubit_count  : e.g. 9 for a 3x3 code.
      stabilizer_count  : e.g. 4 if you have 4 stabilizers measured each round.
      num_rounds        : e.g. 2 (meaning we have 2 sets of stabilizer measurements).
      stabilizer_map    : dict: {stab_index -> [data_qubit_indices]}
      data_qubit_states : optional dict or list for the data qubit flips. If None, init all 0.
      plot_graphs       : whether to plot the detection graph for each round pair.

    Returns:
      updated data_qubit_states after naive MWPM corrections.
    """
    # 1) Initialize data_qubit_states if None
    if data_qubit_states is None:
        # Example: a dictionary from qubit index -> 0
        data_qubit_states = {i: 0 for i in range(data_qubit_count)}

    # 2) Parse the result_str
    #    According to your description: "the first N bits are data qubits (in reverse),
    #    then we have stabilizer_count * num_rounds bits for the stabilizers."
    #    We'll assume we read left->right in result_str:
    #    data_qubits_str = first data_qubit_count bits
    #    ancilla_str = next (stabilizer_count * num_rounds) bits.
    total_ancilla_bits = stabilizer_count * num_rounds

    if len(result_str) != data_qubit_count + total_ancilla_bits:
        raise ValueError(f"Result string length {len(result_str)} does not match "
                         f"data_qubit_count + stabilizer_count*num_rounds = "
                         f"{data_qubit_count + total_ancilla_bits}.")

    data_qubits_str = result_str[:data_qubit_count]
    ancilla_str = result_str[data_qubit_count:data_qubit_count + total_ancilla_bits]

    # Because Qiskit often reverses measurement order, you might want to reverse data_qubits_str
    # or do something similar. This depends on your exact measurement mapping. We'll just note it:
    # data_qubits_str = data_qubits_str[::-1]  # Reverse if needed

    # For each round i, we have a slice of ancilla_str of length = stabilizer_count.
    round_bits = []
    for r in range(num_rounds):
        start = r * stabilizer_count
        end = (r + 1) * stabilizer_count
        round_bits.append(ancilla_str[start:end])

    # 3) Now do pairwise decoding for consecutive rounds (r -> r+1).
    #    If num_rounds=2, we only do one difference (round0 -> round1).
    for r in range(num_rounds - 1):
        r_str_1 = round_bits[r]
        r_str_2 = round_bits[r + 1]

        # Use the decode_round_pair function
        match_result = decode_round_pair(r_str_1, r_str_2, stabilizer_map, plot_graph=plot_graphs)

        # Apply naive corrections to data qubits
        data_qubit_states = apply_corrections(match_result, stabilizer_map, data_qubit_states)

    # Return final data qubit states
    return data_qubit_states, data_qubits_str


# ---------------------- EXAMPLE USAGE ----------------------
if __name__ == "__main__":
    # For a 3x3 code:
    data_qubit_count = 9      # 3x3 = 9 data qubits
    stabilizer_count = 4      # e.g. we have 4 stabilizers
    num_rounds = 2            # measured them 2 times

    # Example stabilizer map (the indices might differ in your code):
    # Key = stabilizer index, Value = which data qubits it touches
    stabilizer_map_example = {1: [0, 2, 4], 3: [0, 4, 6], 5: [8, 2, 4], 7: [8, 4, 6]}

    # Let's say our measurement string is 17 bits:
    # (9 bits for data qubits, 8 bits for stabilizers in 2 rounds).
    # Example: "00000000000000000"
    # We'll flip a few bits to see interesting behavior:
    result_str = "10001110000100010"
    # Explanation (assuming left->right):
    # - first 9 = "000000001" for data qubits (in reverse)
    # - next 4 = "0000" for round 0 stabilizers
    # - next 4 = "0110" for round 1 stabilizers

    # Decode:
    final_data_states, data_qubit_string = decode_surface_code_shot(
        result_str=result_str,
        data_qubit_count=data_qubit_count,
        stabilizer_count=stabilizer_count,
        num_rounds=num_rounds,
        stabilizer_map=stabilizer_map_example,
        data_qubit_states=None,    # start all zero
        plot_graphs=True
    )

    print(f"Initial and final data qubit strings: \n {data_qubit_string} \n {final_data_states}")
