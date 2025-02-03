from qiskit import QuantumCircuit
from qiskit_ibm_runtime import QiskitRuntimeService, Session, Sampler
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager

import pickle

from qiskit import QuantumCircuit
import numpy as np


def build_surface_code_circuit(distance, rounds=4):
    """
    Build a rotated surface code circuit with alternating data/syndrome qubits.

    Args:
        distance (int): Code distance (determines grid size)
        rounds (int): Number of measurement rounds

    Returns:
        QuantumCircuit: Surface code circuit
        dict: Stabilizer map {syndrome_qubit: [data_qubits]}
        list: Logical Z qubit chain (vertical data qubits)
    """
    n_rows = 2 * distance + 1
    n_cols = 3
    total_qubits = n_rows * n_cols

    # Identify data and syndrome qubits
    data_qubits = []
    syndrome_qubits = []
    for r in range(n_rows):
        for c in range(n_cols):
            idx = r * n_cols + c
            if (r + c) % 2 == 0:  # Checkerboard pattern
                data_qubits.append(idx)
            else:
                syndrome_qubits.append(idx)

    qc = QuantumCircuit(total_qubits, len(syndrome_qubits) * rounds)

    # Initialize data qubits
    for q in data_qubits:
        qc.initialize([1, 0], q)  # Initialize to |0>

    # Build stabilizer map
    stabilizer_map = {}
    for s in syndrome_qubits:
        r, c = divmod(s, n_cols)
        neighbors = []

        # Z stabilizers (even rows)
        if r % 2 == 0:
            # Connect to horizontal neighbors
            if c > 0: neighbors.append(s - 1)
            if c < n_cols - 1: neighbors.append(s + 1)
            # Connect to vertical neighbors
            if r > 0: neighbors.append(s - n_cols)
            if r < n_rows - 1: neighbors.append(s + n_cols)

        # X stabilizers (odd rows)
        else:
            # Connect to vertical neighbors
            if r > 0: neighbors.append(s - n_cols)
            if r < n_rows - 1: neighbors.append(s + n_cols)
            # Connect to horizontal neighbors
            if c > 0: neighbors.append(s - 1)
            if c < n_cols - 1: neighbors.append(s + 1)

        stabilizer_map[s] = [q for q in neighbors if q in data_qubits]

    classical_bit = 0

    # Measurement rounds
    for _ in range(rounds):
        # Measure Z stabilizers (even rows)
        for s in syndrome_qubits:
            r, c = divmod(s, n_cols)
            if r % 2 == 0:  # Z stabilizers
                qc.reset(s)
                for neighbor in stabilizer_map[s]:
                    qc.cx(neighbor, s)
                qc.measure(s, classical_bit)
                classical_bit += 1
                qc.barrier()

        # Measure X stabilizers (odd rows)
        for s in syndrome_qubits:
            r, c = divmod(s, n_cols)
            if r % 2 == 1:  # X stabilizers
                qc.reset(s)
                qc.h(s)
                for neighbor in stabilizer_map[s]:
                    qc.cx(s, neighbor)
                qc.h(s)
                qc.measure(s, classical_bit)
                classical_bit += 1
                qc.barrier()

    # Logical Z chain (vertical middle column data qubits)
    logical_z = [r * n_cols + 1 for r in range(1, n_rows, 2)]

    return qc, stabilizer_map, logical_z


# =============================================================================
# Main loop: create circuits for a range of distances, submit jobs within a Qiskit session,
# and save a results structure for later processing.
# =============================================================================

# Dictionary to map distance to jobID and a list to store full results.
job_dict = {}
results = []

# Instantiate IBM Quantum service (adjust channel/backed as needed)
service = QiskitRuntimeService(channel="ibm_quantum")
backend = service.least_busy(operational=True, simulator=False)
pm = generate_preset_pass_manager(target=backend.target, optimization_level=0)

# Open a session; all jobs will run in this session.
with Session(backend=backend) as session:
    sampler = Sampler(mode=session)

    # Loop over distances; here we use d from 3 to 20 such that the total qubits = 3*(2*d+1) stay under 128.
    # for d in range(3, 21):
    #     qc, stabilizer_map, logical_z = build_surface_code_circuit(distance=d, rounds=4)
    #     # (Optional) Process the circuit with a preset pass manager
    #     surface_code = pm.run(qc)
    #     # Submit the job (using 1024 shots, for example)
    #     job = sampler.run([surface_code], shots=1024)
    #     result = job.result()
    #     counts = result[0].data.c.get_counts()
    #     job_id = job.job_id()
    #     job_dict[d] = job_id
    #
    #     # Structure the results for this circuit.
    #     result_structure = {
    #         'distance': d,
    #         'job_id': job_id,
    #         'counts': counts,
    #         'stabilizer_map': stabilizer_map,
    #         'logical_z': logical_z
    #     }
    #     results.append(result_structure)

    jobs = []
    for d in range(3, 21):
        qc, stabilizer_map, logical_z = build_surface_code_circuit(distance=d, rounds=4)
        surface_code = pm.run(qc)
        job = sampler.run([surface_code], shots=1024)
        jobs.append((d, job))

    # After all jobs are submitted, collect results
    results = []
    for d, job in jobs:
        result = job.result()
        counts = result[0].data.c.get_counts()
        job_id = job.job_id()

        job_dict[d] = job_id

        # Structure the results for this circuit.
        result_structure = {
            'distance': d,
            'job_id': job_id,
            'counts': counts,
            'stabilizer_map': stabilizer_map,
            'logical_z': logical_z
        }
        results.append(result_structure)

# Save the dictionary {distance: job_id} to a pickle file.
with open('optimized/job_ids.pkl', 'wb') as f:
    pickle.dump(job_dict, f)

# Save the full results structure to another pickle file.
with open('optimized/results.pkl', 'wb') as f:
    pickle.dump(results, f)
