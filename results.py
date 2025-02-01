from qiskit.visualization import plot_histogram
from qiskit_ibm_runtime import QiskitRuntimeService
import matplotlib.pyplot as plt
from dotenv import load_dotenv
import os

from mine import stats_history
from utils import process_detection_events, build_mwpm_graph, apply_mwpm, calculate_error_statistics, plot_error_stats

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
# cyf04e101rbg008k8r0g 5x5 grid, 4 rounds, no not in the middle
job = service.job('cyf04e101rbg008k8r0g')
grid = 5
n_rounds = 4
stabilizer_map = {1: [0, 2, 6], 3: [8, 2, 4], 5: [0, 10, 6], 7: [8, 2, 12, 6], 9: [8, 4, 14], 11: [16, 10, 12, 6], 13: [8, 18, 12, 14], 15: [16, 10, 20], 17: [16, 18, 12, 22], 19: [24, 18, 14], 21: [16, 20, 22], 23: [24, 18, 22]}

print(job)
pub_result = job.result()
counts = pub_result[0].data.c.get_counts()

print(counts)

detection_events = process_detection_events(counts, grid, n_rounds)
G = build_mwpm_graph(detection_events, grid)
matching, total_weight = apply_mwpm(G)

logical_z_chain = [0, 10, 20]

stats = calculate_error_statistics(G, counts, grid, matching, stabilizer_map, detection_events, logical_z_chain)
stats['total_shots'] = sum(counts.values())
stats_history.append(stats)

# Draw the matching graph
# pos = nx.spring_layout(G)
# nx.draw(G, pos, with_labels=True, node_color='lightblue')
# labels = nx.get_edge_attributes(G, 'weight')
# nx.draw_networkx_edge_labels(G, pos, edge_labels=labels)
# plt.savefig("matching_graph.png")
# plt.close()

# print(f"Logical Error Rate: {logical_error_rate:.4f}")

plot_error_stats(stats_history)