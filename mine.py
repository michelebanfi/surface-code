from qiskit_ibm_runtime import QiskitRuntimeService, Session, Sampler
from qiskit import QuantumCircuit, transpile
from qiskit.visualization import plot_histogram
import matplotlib.pyplot as plt
from collections import defaultdict
from qiskit_ibm_provider import IBMProvider
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager

API_KEY = "039fcc48a1c2eae0fa22fe7857e5a02ed89cd782d5738fac3bbd97d8f6e0506b330bd51db32ed92ca4a07490141cc7c3dfade0618db865772491155d7b4f2192"

grid = 3
n_rounds = 2
print(f"LOG - grid: {grid}, n_rounds: {n_rounds}")

n_data = (grid ** 2)//2 + 1

n_syndrome = (grid ** 2) - n_data

data_qubits = list(range(grid**2))
ancilla_qubits = list(range(9, 13))

qc = QuantumCircuit(n_data + n_syndrome, n_syndrome * n_rounds)
print(f"LOG - initialized circuit with: {n_data + n_syndrome} qubits and with {n_syndrome * n_rounds} ancillas")

stabilizer_map = {}

# appy not gate to recognize the data qubits which are in the even row
for i in range(grid**2):
    if i % 2 == 0:
        qc.initialize([1, 0], i)
    else:
        stabilizer_map[i] = []

classical_bits = 0
print(stabilizer_map)

def logical_x(qc):
    available_qubits = [0, 2]
    for q in available_qubits:
        qc.x(q)

# Create stabilizers
def apply_stabilizers(qc, grid, classical_bits=0):
    global stabilizer_map
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
    return classical_bits

print("LOG - applying stabilizers")

classical_bits = apply_stabilizers(qc, grid, classical_bits)

qc.barrier()
logical_x(qc)
qc.barrier()

classical_bits = apply_stabilizers(qc, grid, classical_bits)
qc.measure_all()

# iterate through the stabilizer map
for k, v in stabilizer_map.items():
    # the value is a list of connections, remove duplicates
    stabilizer_map[k] = list(set(v))

print(stabilizer_map)

# simulate
print("LOG - COMPILING CIRCUIT")

# Instead of AerSimulator, use IBM Quantum Provider
def run_on_ibm():
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

    return counts

print("LOG - RUNNING SIMULATION")

counts = run_on_ibm()

print(counts)

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

print("LOG - DECODING RESULTS")
# Apply decoder
corrected = mwpm_decoder(counts, stabilizer_map)

# Analyze results
print("LOG - Most common outcomes:")
for res, count in sorted(corrected.items(), key=lambda x: -x[1])[:5]:
    print(f"{res} : {count}")


plot_histogram([counts, corrected],
               legend=['Raw Results', 'Corrected'],
               title='Surface Code Results',
               figsize=(15, 6),
               sort='value_desc')
plt.show()
plt.close()