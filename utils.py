from qiskit_ibm_runtime import QiskitRuntimeService, Session, Sampler
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from collections import defaultdict
from qiskit_aer import AerSimulator
from qiskit import transpile

def logical_x(qc):
    available_qubits = [0, 2]
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

                    qc.cx(current + grid, current)  # qubit below
                    stabilizer_map[current].append(current + grid)
                    qc.cx(current - grid, current)  # qubit above
                    stabilizer_map[current].append(current - grid)
                    # if is the last row of the grid, then the qubit has connection with the qubit in the first row
                    if j != 0:
                        qc.cx(current - 1, current)
                        stabilizer_map[current].append(current - 1)
                    if j != grid - 1:
                        qc.cx(current + 1, current)  # next qubit
                        stabilizer_map[current].append(current + 1)
                    qc.h(current)
                    qc.measure(current, classical_bits)
                    qc.barrier()
                    classical_bits += 1
    return classical_bits, stabilizer_map

# Decoder implementation
def mwpm_decoder(counts, stabilizer_map):
    corrected_counts = defaultdict(int)

    for bitstring, count in counts.items():
        # Split into syndrome (8 bits) and final measurement (9 bits)
        bitstring = bitstring.split(' ')
        # final_meas = bitstring[:grid**2]
        # syndrome = bitstring[grid**2:]
        final_meas = bitstring[0]
        syndrome = bitstring[1]

        # Compare syndrome rounds
        round1 = [int(s) for s in syndrome[:4]]
        round2 = [int(s) for s in syndrome[4:]]
        defects = [i for i in range(4) if round1[i] != round2[i]]

        # Simple MWPM heuristic for 3x3 grid
        corrections = set()
        if len(defects) == 2:
            # Match adjacent defects
            d1, d2 = defects
            common_qubits = set(stabilizer_map[d1 * 2]) & set(stabilizer_map[d2 * 2])
            if common_qubits:
                corrections.add(min(common_qubits))

        # Apply corrections to final measurement
        corrected = list(final_meas[::-1])  # Qiskit uses little-endian
        for q in corrections:
            if q < len(corrected):
                corrected[q] = '1' if corrected[q] == '0' else '0'

        corrected_counts[''.join(corrected[::-1]) + ' ' + syndrome] += count

    return corrected_counts

# Instead of AerSimulator, use IBM Quantum Provider
def run_on_ibm(qc):
    service = QiskitRuntimeService()

    backend = service.least_busy(operational=True, simulator=False)
    pm = generate_preset_pass_manager(target=backend.target, optimization_level=1)
    # Authenticate with your IBM Quantum token
    # IBMProvider.save_account(API_KEY)  # Only need to do this once
    # provider = IBMProvider()

    # Get available backends (quantum computers)
    # print("Available backends:")
    # for backend in provider.backends():
    #     print(f"- {backend.name} ({backend.num_qubits} qubits)")
    #
    # # Choose a backend - example using ibmq_qasm_simulator for testing
    # backend = provider.get_backend('ibm_brisbane')  # Replace with actual device name
    #
    # # Transpile for the target backend
    # print(f"Transpiling for {backend.name}...")
    # transpiled_qc = transpile(qc, backend=backend, optimization_level=3)
    #
    # # Submit job
    # print(f"Submitting job to {backend.name}...")
    # job = backend.run(transpiled_qc, shots=1024)
    #
    # # Monitor job status
    # print(f"Job ID: {job.job_id()}")
    # print("Job status:", job.status())

    # Retrieve results when complete
    # result = job.result()
    # counts = result.get_counts()

    surface_code = pm.run(qc)

    with Session(backend=backend) as session:
        sampler = Sampler(mode=session)
        job = sampler.run([surface_code], shots=1024)
        pub_result = job.result()[0]
        print(f"Sampler job ID: {job.job_id()}")
        print(f"Counts: {pub_result.data.cr.get_counts()}")

    return pub_result.data.cr.get_counts()

def run_on_simulator(qc):
    # Use AerSimulator for simulation
    simulator = AerSimulator()
    compiled_circuit = transpile(qc, simulator)
    result = simulator.run(compiled_circuit, shots=1024).result()
    counts = result.get_counts()
    return counts