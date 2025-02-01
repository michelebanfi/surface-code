import pickle
import numpy as np
import matplotlib.pyplot as plt

def load_stats(filename):
    with open(filename, 'rb') as f:
        data = pickle.load(f)
    # If the loaded object is a dictionary, wrap it in a list for uniform handling.
    if isinstance(data, dict):
        return [data]
    return data


def aggregate_stats(stats_list):
    """
    Given a list of stats dictionaries (one or more runs), compute the average values.
    Returns a dictionary with average logical error rate, detected error rate,
    and physical error count (total_errors per shot).
    """
    total_shots = np.mean([s['total_shots'] for s in stats_list])
    avg_logical_error_rate = np.mean([s['logical_errors'] / s['total_shots'] for s in stats_list])
    avg_detected_error_rate = np.mean([s['detected_errors'] / s['total_shots'] for s in stats_list])
    avg_physical_errors = np.mean([s['total_errors'] / s['total_shots'] for s in stats_list])

    return {
        'total_shots': total_shots,
        'avg_logical_error_rate': avg_logical_error_rate,
        'avg_detected_error_rate': avg_detected_error_rate,
        'avg_physical_errors': avg_physical_errors
    }


# Load your stats for each grid size:
stats_5x5 = load_stats('stats/stats_grid_5.pkl')
stats_7x7 = load_stats('stats/stats_grid_7.pkl')
stats_9x9 = load_stats('stats/stats_grid_9.pkl')
# Add more grid sizes as needed (e.g., stats_9x9)

# Aggregate the stats (if you have only one run, aggregation simply returns that run's values)
agg_5 = aggregate_stats(stats_5x5)
agg_7 = aggregate_stats(stats_7x7)
agg_9 = aggregate_stats(stats_9x9)

# For plotting, we create lists of grid sizes and corresponding average metrics.
grid_sizes = [5, 7, 9]
logical_error_rates = [agg_5['avg_logical_error_rate'], agg_7['avg_logical_error_rate'], agg_9['avg_logical_error_rate']]
detected_error_rates = [agg_5['avg_detected_error_rate'], agg_7['avg_detected_error_rate'], agg_9['avg_detected_error_rate']]
physical_errors = [agg_5['avg_physical_errors'], agg_7['avg_physical_errors'], agg_9['avg_physical_errors']]

# Now plot the comparisons:
plt.figure(figsize=(12, 5))

# Plot logical and detected error rates versus grid size.
plt.subplot(1, 2, 1)
plt.plot(grid_sizes, logical_error_rates, 'o-', label='Logical Error Rate')
plt.plot(grid_sizes, detected_error_rates, 's--', label='Detected Error Rate')
plt.xlabel("Grid Size (L x L)")
plt.ylabel("Error Rate (per shot)")
plt.title("Error Rates vs. Grid Size")
plt.legend()

# Plot average physical errors (normalized per shot) versus grid size.
plt.subplot(1, 2, 2)
plt.plot(grid_sizes, physical_errors, 'd-', color='purple', label='Physical Errors per Shot')
plt.xlabel("Grid Size (L x L)")
plt.ylabel("Average Physical Errors per Shot")
plt.title("Physical Errors vs. Grid Size")
plt.legend()

plt.tight_layout()
plt.savefig("grid_comparison.png")
plt.show()
