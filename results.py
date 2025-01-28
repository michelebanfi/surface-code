from qiskit.visualization import plot_histogram
from qiskit_ibm_runtime import QiskitRuntimeService
import matplotlib.pyplot as plt

service = QiskitRuntimeService(
    channel='ibm_quantum',
    instance='ibm-q/open/main',
    token='039fcc48a1c2eae0fa22fe7857e5a02ed89cd782d5738fac3bbd97d8f6e0506b330bd51db32ed92ca4a07490141cc7c3dfade0618db865772491155d7b4f2192'
)
job = service.job('cybs2e101rbg008jv960')
job_result = job.result()
print(f"Ancillas outcome: {job_result[0].data.c.get_counts()}")
print(f"Qubit outcome: {job_result[0].data.meas.get_counts()}")

# print max result from the classical register
max_result = max(job_result[0].data.c.get_counts(), key=job_result[0].data.c.get_counts().get)
print(f"Max result from classical register: {max_result}")

# print max result from the measurement register
max_result = max(job_result[0].data.meas.get_counts(), key=job_result[0].data.meas.get_counts().get)
print(f"Max result from measurement register: {max_result}")

# Classical register histogram
plot_histogram(job_result[0].data.c.get_counts())
plt.show()
plt.close()

# Measurement register histogram
plot_histogram(job_result[0].data.meas.get_counts())
plt.show()
plt.close()

# To get counts for a particular pub result, use
#
# pub_result = job_result[<idx>].data.<classical register>.get_counts()
#
# where <idx> is the index of the pub and <classical register> is the name of the classical register.
# You can use circuit.cregs to find the name of the classical registers.