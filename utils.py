from qiskit_ibm_runtime import QiskitRuntimeService, Session, Sampler
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit_aer import AerSimulator
from qiskit import transpile
from qiskit_aer.noise import NoiseModel, depolarizing_error
import networkx as nx
from random import random
import matplotlib.pyplot as plt

def logical_x(grid, qc):
    # the available qubits will be those in an even number between 0 and grid**2
    available_qubits = [i for i in range(grid) if i % 2 == 0]
    for q in available_qubits:
        qc.x(q)

def apply_stabilizers(qc, grid, classical_bits=0, stabilizer_map=None):
    for i in range(grid):
        for j in range(grid):
            current = i * grid + j
            # if even row, z-syndrome (without Hadamards)
            if i % 2 == 0:
                if j % 2 == 1:
                    # print("Applying Z stabilizers for qubit", current)
                    qc.reset(current)
                    qc.cx(current - 1, current)  # previuos qubit
                    stabilizer_map[current].append(current - 1)

                    qc.cx(current + 1, current)  # next qubit
                    stabilizer_map[current].append(current + 1)

                    # if is the first row of the grid, then the qubit has connection with the qubit in the last row
                    if i != 0:
                        qc.cx(current - grid, current)  # qubit above
                        stabilizer_map[current].append(current - grid)
                    if i != grid - 1:
                        qc.cx(current + grid, current)  # qubit below
                        stabilizer_map[current].append(current + grid)

                    # measure the qubit onto the corresponding classical bit
                    qc.measure(current, classical_bits)
                    classical_bits += 1
                    qc.barrier()
            else:
                if j % 2 == 0:
                    # print("Applying X stabilizers for qubit", current)
                    qc.reset(current)
                    qc.h(current)

                    qc.cx(current, current + grid)  # qubit below
                    stabilizer_map[current].append(current + grid)

                    qc.cx(current, current - grid)  # qubit above
                    stabilizer_map[current].append(current - grid)

                    # if is the last row of the grid, then the qubit has connection with the qubit in the first row
                    if j != 0:
                        qc.cx(current, current - 1)
                        stabilizer_map[current].append(current - 1)
                    if j != grid - 1:
                        qc.cx(current, current + 1)  # next qubit
                        stabilizer_map[current].append(current + 1)

                    qc.h(current)
                    qc.measure(current, classical_bits)
                    qc.barrier()
                    classical_bits += 1
    return classical_bits, stabilizer_map

# Instead of AerSimulator, use IBM Quantum Provider
def run_on_ibm(qc):
    service = QiskitRuntimeService()

    backend = service.least_busy(operational=True, simulator=False)
    pm = generate_preset_pass_manager(target=backend.target, optimization_level=0)
    surface_code = pm.run(qc)

    with Session(backend=backend) as session:
        sampler = Sampler(mode=session)
        job = sampler.run([surface_code], shots=1024)
        pub_result = job.result()
        print(f"Sampler job ID: {job.job_id()}")
        print(f"Counts: {pub_result[0].data.c.get_counts()}")

    return pub_result[0].data.c.get_counts()

def run_on_simulator(qc):
    # Use AerSimulator for simulation
    noiseModel = NoiseModel()
    #noiseModel.add_all_qubit_quantum_error(depolarizing_error(0.05, 1), 'x')
    #simulator = AerSimulator(noise_model=noiseModel)
    simulator = AerSimulator()
    compiled_circuit = transpile(qc, simulator)
    result = simulator.run(compiled_circuit, shots=1024).result()
    counts = result.get_counts()
    return counts

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

def calculate_logical_error_subrutine(counts, grid, matching, stabilizer_map, detection_events, logical_z_chain):
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

def calculate_error_statistics(G, counts, grid, matching, stabilizer_map, detection_events, logical_z_chain):
    stats = {
        'total_errors': 0,
        'detected_errors': len(detection_events),
        'corrected_pairs': len(matching),
        'logical_errors': 0,
        'weight_histogram': []
    }

    # Map detection events to stabilizers
    event_to_stabilizer = {}
    for event in detection_events:
        row, col, stab_type, t = event
        qubit_idx = row * grid + col
        event_id = f"{row},{col},{t}"
        event_to_stabilizer[event_id] = qubit_idx

    for shot, freq in counts.items():
        # Count physical errors (assuming ideal simulation)
        data_bits = list(shot[-(grid ** 2):])
        stats['total_errors'] += sum(int(bit) for bit in data_bits) * freq

        # Track matching weights
        for pair in matching:
            node1, node2 = pair
            if node1 != 'boundary' and node2 != 'boundary':
                weight = G[node1][node2]['weight']
                stats['weight_histogram'].extend([weight] * freq)

    # Add logical error calculation
    stats['logical_errors'] = calculate_logical_error_subrutine(counts, grid, matching, stabilizer_map, detection_events, logical_z_chain) * sum(
        counts.values())

    return stats

def plot_error_stats(stats_history):

    # print the stats history
    for stats in stats_history:
        print(stats)

    plt.figure(figsize=(12, 6))

    # Plot error rates
    plt.subplot(121)
    plt.plot([s['logical_errors'] / s['total_shots'] for s in stats_history], label='Logical')
    plt.plot([s['detected_errors'] / s['total_shots'] for s in stats_history], label='Detected')
    plt.xlabel('Trial')
    plt.ylabel('Error Rate')
    plt.legend()

    # Plot matching weights
    plt.subplot(122)
    all_weights = [w for s in stats_history for w in s['weight_histogram']]
    if all_weights:
        plt.hist(all_weights, bins=range(0, max(all_weights) + 1))
    else:
        plt.hist([], bins=range(0, 1))
    plt.xlabel('Matching Weight')
    plt.ylabel('Frequency')

    plt.tight_layout()
    plt.savefig("error_stats.png")
    plt.close()


def inject_random_errors(qc, grid, error_prob=0.1):
    """Inject random X errors with given probability"""
    for q in range(grid**2):
        if q % 2 == 0 and random() < error_prob:  # Only data qubits (even indices)
            qc.x(q)
    return qc