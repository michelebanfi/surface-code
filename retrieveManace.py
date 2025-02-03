# retrieve_results.py
import qiskit.providers
from qiskit_ibm_runtime import QiskitRuntimeService
import pickle
import os
from dotenv import load_dotenv


def build_surface_code_circuit(distance, rounds=4):
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
                classical_bit += 1

        # Measure X stabilizers (odd rows)
        for s in syndrome_qubits:
            r, c = divmod(s, n_cols)
            if r % 2 == 1:  # X stabilizers
                classical_bit += 1

    # Logical Z chain (vertical middle column data qubits)
    logical_z = [r * n_cols + 1 for r in range(1, n_rows, 2)]

    return stabilizer_map, logical_z


def calculate_distance_from_qubits(num_qubits):
    """Derive code distance from total qubit count"""
    return (num_qubits // 3 - 1) // 2


def main():
    load_dotenv()
    service = QiskitRuntimeService(channel="ibm_quantum", token=os.getenv("IBM_API_KEY"))

    # Retrieve your specific session
    session_id = "cygaq6wrta1g008v3k5g"
    jobs = service.jobs(session_id=session_id, limit=20)

    print(len(jobs))

    results = []

    for job in jobs:
        if job.status() != qiskit.providers.JobStatus.DONE:
            print(f"Skipping job {job.job_id()} - status: {job.status()}")
            continue

        try:
            # Get basic job info
            job_id = job.job_id()
            counts = job.result()[0].data.c.get_counts()

            keys = list((counts.keys()))[0]
            # print the length of one key
            # print(len(keys), len(keys)/4)


            # num_qubits = job.inputs["circuits"][0].num_qubits
            #
            # # Calculate code distance
            distance = calculate_distance_from_qubits(len(keys) / 4 + len(keys) / 4 + 1)
            print(distance)
            #
            # # Reconstruct stabilizer map and logical Z
            stabilizer_map, logical_z = build_surface_code_circuit(int(distance))
            print(logical_z)
            #
            # # Get measurement results
            # result = job.result()
            # counts = result[0].data.c.get_counts()
            #
            # Store for analysis
            results.append({
                "distance": distance,
                "job_id": job_id,
                "counts": counts,
                "stabilizer_map": stabilizer_map,
                "logical_z": logical_z,

            })

            # print(f"Processed distance {distance} from job {job_id}")

        except Exception as e:
            print(f"Failed processing job {job.job_id()}: {str(e)}")

    # Save recovered results
    with open("stats/optimized/recovered_results.pkl", "wb") as f:
        pickle.dump(results, f)

    print(f"\nSuccessfully recovered {len(results)} results")


if __name__ == "__main__":
    main()