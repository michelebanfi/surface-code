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
stats_11x11 = load_stats('stats/stats_grid_11.pkl')
# Add more grid sizes as needed (e.g., stats_9x9)

# Aggregate the stats (if you have only one run, aggregation simply returns that run's values)
agg_5 = aggregate_stats(stats_5x5)
agg_7 = aggregate_stats(stats_7x7)
agg_9 = aggregate_stats(stats_9x9)
agg_11 = aggregate_stats(stats_11x11)

# For plotting, we create lists of grid sizes and corresponding average metrics.
grid_sizes = [5, 7, 9, 11]
logical_error_rates = [agg_5['avg_logical_error_rate'], agg_7['avg_logical_error_rate'], agg_9['avg_logical_error_rate'], agg_11['avg_logical_error_rate']]
detected_error_rates = [agg_5['avg_detected_error_rate'], agg_7['avg_detected_error_rate'], agg_9['avg_detected_error_rate'], agg_11['avg_detected_error_rate']]
physical_errors = [agg_5['avg_physical_errors'], agg_7['avg_physical_errors'], agg_9['avg_physical_errors'], agg_11['avg_physical_errors']]

# Now plot the comparisons:
plt.figure(figsize=(12, 5))

# Plot logical and detected error rates versus grid size.
plt.subplot(1, 3, 1)
# plt.plot(grid_sizes, logical_error_rates, 'o-', label='Logical Error Rate')
plt.plot(grid_sizes, detected_error_rates, 'o-', label='Detected Error Rate', color='orange')
plt.xlabel("Grid Size (L x L)")
plt.ylabel("Error Rate (per shot)")
plt.title("Error Rates vs. Grid Size")
plt.legend()

# Plot average physical errors (normalized per shot) versus grid size.
plt.subplot(1, 3, 2)
plt.plot(grid_sizes, physical_errors, 'd-', color='purple', label='Physical Errors per Shot')
plt.xlabel("Grid Size (L x L)")
plt.ylabel("Average Physical Errors per Shot")
plt.title("Physical Errors vs. Grid Size")
plt.legend()

print("Logical Error Rates:", logical_error_rates)

# fit a linear model to the logical error rates
# y = mx + c
x = np.array(grid_sizes)
y = np.array(logical_error_rates)
m, c = np.polyfit(x, y, 1)
print(f"m: {m}, c: {c}")

# fit a log model to the logical error rates
# y = a * np.log(x) + b
a, b = np.polyfit(np.log(x), y, 1)
print(f"a: {a}, b: {b}")

plt.subplot(1, 3, 3)
plt.plot(grid_sizes, logical_error_rates, 'o-', label='Logical Error Rate')
# plt.plot(x, a*np.log(x) + b, 'g--', label=f'Fit: y = {a:.2f}log(x) + {b:.2f}')
# plt.plot(x, m*x + c, 'r--', label=f'Fit: y = {m:.2f}x + {c:.2f}')
plt.xlabel("Grid Size (L x L)")
plt.ylabel("Logical Error Rate (per shot)")
plt.title("Logical Error Rate vs. Grid Size")
plt.legend()

plt.tight_layout()
plt.savefig("grid_comparison.png")
plt.show()
