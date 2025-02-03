import pickle

def calculate_logical_error(rounds_output, stabilizer_indices, stabilizer_map, stabilizer_type, central_qubits, d):
    """
    Calculate logical X or Z errors based on stabilizer measurements.

    Args:
        rounds_output (list of str): Stabilizer measurements ordered oldest to newest.
        stabilizer_map (dict): Maps stabilizer indices to connected data qubits.
        stabilizer_type (dict): Maps stabilizer indices to 'X' or 'Z'.
        central_qubits (list): Data qubits in the central column.
        d (int): Code distance.

    Returns:
        tuple: (logical_x_error, logical_z_error)
    """

    logical_x = False
    logical_z = False

    if len(rounds_output) < 2:
        return (False, False, False)

    for i in range(len(rounds_output) - 1):
        current = rounds_output[i]
        next_r = rounds_output[i + 1]

        x_counts = {q: 0 for q in central_qubits}
        z_counts = {q: 0 for q in central_qubits}

        per_round_bitflip = 0

        for bit_idx in range(len(current)):
            if current[bit_idx] != next_r[bit_idx]:
                per_round_bitflip += 1
                stabilizer = stabilizer_indices[bit_idx]
                if stabilizer in stabilizer_map:
                    stype = stabilizer_type.get(stabilizer, None)
                    for q in stabilizer_map[stabilizer]:
                        if q in central_qubits:
                            if stype == 'Z':
                                # Z stabilizer flips indicate X errors on data qubits
                                x_counts[q] += 1
                            elif stype == 'X':
                                # X stabilizer flips indicate Z errors on data qubits
                                z_counts[q] += 1
        print(per_round_bitflip)
        # Check parity (odd counts indicate potential errors)
        x_errors = sum(1 for q in central_qubits if x_counts[q] % 2 != 0)
        z_errors = sum(1 for q in central_qubits if z_counts[q] % 2 != 0)

        total_errors = x_errors + z_errors > d // 2

        # Update logical flags if any interval has an error
        if x_errors > d // 2:
            logical_x = True
        if z_errors > d // 2:
            logical_z = True

        x_errors = 0
        z_errors = 0

    total_logic = logical_x or logical_z
    return (logical_x, logical_z, total_logic)

with open('../stats/optimized/recovered_results.pkl', 'rb') as f:
    results = pickle.load(f)

def analyze_results(results):
    results = results[::-1]  # Reverse if necessary


    for result in results:
        d = int(result['distance'])
        counts = result['counts']

        # take only 30 elements counts from dictionary
        counts = {k: counts[k] for k in list(counts)[:100]}

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

            _, _, total_errors = calculate_logical_error(splitted_c, stabilizer_indices, stabilizer_map, stabilizer_type, logical_z, d)
            if total_errors:
                total_errors_count += 1

        print(f"Distance {d}: {total_errors_count / 100}")


analyze_results(results)