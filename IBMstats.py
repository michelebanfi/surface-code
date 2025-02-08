# Initialize your account
from qiskit_ibm_runtime import QiskitRuntimeService
import numpy as np

service = QiskitRuntimeService(instance="ibm-q/open/main")

backend = service.backend("ibm_kyiv")

measure_errors = [backend.target['measure'][(q,)].error for q in range(backend.num_qubits)]

# sum all measure errors
# print(sum(measure_errors))

# Get average measurement error rate
p_meas = sum(measure_errors) / backend.num_qubits

# Get average single-qubit gate error rate (proxy for p_data)
gate_error = [backend.target['x'][(q,)].error for q in range(backend.num_qubits)]
p_data = sum(gate_error) / backend.num_qubits
#
time_weight = -np.log(p_meas)
#
space_weight = -np.log(p_data)
#
# print(f"Average measurement error rate: {p_meas}")
# print(f"Average single-qubit gate error rate: {p_data}")
print(f"Time weight: {time_weight}")
print(f"Space weight: {space_weight}")


# Time weight: 3.514132443661577
# Space weight: 6.758792810989775