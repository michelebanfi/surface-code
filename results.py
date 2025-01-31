from qiskit.visualization import plot_histogram
from qiskit_ibm_runtime import QiskitRuntimeService
import matplotlib.pyplot as plt
from dotenv import load_dotenv
import os


load_dotenv()
API_KEY = os.getenv("IBM_API_KEY")

service = QiskitRuntimeService(
    channel='ibm_quantum',
    instance='ibm-q/open/main',
    token=API_KEY
)
# cyca1sz7v8tg008g29ag    5qubits
# cybs2e101rbg008jv960
# cydqckt9b62g008jgdwg   7qubits with not in the middle
# cydqh6mrta1g0087zskg 7 qubits without not in the middle, last one
# cyeeyhjnrmz00086gxa0 LAST ONE, 4 rounds, no not in the middle, 5x5 grid
job = service.job('cydqh6mrta1g0087zskg')
print(job)
job_result = job.result()
print("items: ",job_result[0].data.items())
print("keys: ",job_result[0].data.keys())
print("values: ",job_result[0].data.values())
print(f"Ancillas outcome: {job_result[0].data.c.get_counts()}")


# print max result from the classical register
max_result = max(job_result[0].data.c.get_counts(), key=job_result[0].data.c.get_counts().get)
print(f"Max result from classical register: {max_result}")

# Classical register histogram
# plot_histogram(job_result[0].data.c.get_counts())
# plt.show()
# plt.close()


# To get counts for a particular pub result, use
#
# pub_result = job_result[<idx>].data.<classical register>.get_counts()
#
# where <idx> is the index of the pub and <classical register> is the name of the classical register.
# You can use circuit.cregs to find the name of the classical registers.