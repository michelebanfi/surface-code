import matplotlib.pyplot as plt
import numpy as np


def aggregate_stats(stats_list):
    """
    Given a list of stats dictionaries (one per trial for a fixed grid size),
    compute the average logical error rate, detected error rate, and physical error count.
    Returns a dictionary with these averages.
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


def plot_comparison(grid_sizes, aggregated_stats):
    """
    Given a list of grid sizes (e.g., [5,7,9]) and corresponding aggregated statistics (a list of dicts),
    generate plots comparing average logical error rate and detected error rate.
    """
    logical_error_rates = [s['avg_logical_error_rate'] for s in aggregated_stats]
    detected_error_rates = [s['avg_detected_error_rate'] for s in aggregated_stats]
    physical_errors = [s['avg_physical_errors'] for s in aggregated_stats]

    plt.figure(figsize=(12, 5))

    # Logical error rate vs. grid size
    plt.subplot(1, 2, 1)
    plt.plot(grid_sizes, logical_error_rates, 'o-', label='Logical error rate')
    plt.plot(grid_sizes, detected_error_rates, 's--', label='Detected error rate')
    plt.xlabel("Grid size (L x L)")
    plt.ylabel("Error rate (per shot)")
    plt.title("Error Rates vs. Grid Size")
    plt.legend()

    # Physical errors (normalized per shot) vs. grid size
    plt.subplot(1, 2, 2)
    plt.plot(grid_sizes, physical_errors, 'd-', color='purple', label='Physical errors/shot')
    plt.xlabel("Grid size (L x L)")
    plt.ylabel("Average Physical Errors per shot")
    plt.title("Physical Errors vs. Grid Size")
    plt.legend()

    plt.tight_layout()
    plt.savefig("grid_comparison.png")
    plt.show()


# Example usage:
# Suppose you ran your simulation for each grid size and obtained a list of stats for each:
stats_5x5 = [...]  # list of stats dictionaries for 5x5 grid
stats_7x7 = [...]  # similarly for 7x7 grid
stats_9x9 = [...]

aggregated_5 = aggregate_stats(stats_5x5)
aggregated_7 = aggregate_stats(stats_7x7)
aggregated_9 = aggregate_stats(stats_9x9)

grid_sizes = [5, 7, 9]
aggregated_stats = [aggregated_5, aggregated_7, aggregated_9]
plot_comparison(grid_sizes, aggregated_stats)
