import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

# Create a figure and axis
fig, ax = plt.subplots(figsize=(8, 8))

# Define grid size (number of stabilizers in each dimension)
grid_size = 5

# Generate positions for a chessboard pattern
positions = [(i, j) for i in range(grid_size) for j in range(grid_size)]

# divide position by half
positions = [(i/2, j/2) for i, j in positions]

# Separate data qubits and stabilizers based on their positions
data_qubits = []
stabilizer_positions = []
# Define stabilizer types (Z for even rows, X for odd rows)
stabilizer_types = {}

for i in range(grid_size):
    for j in range(grid_size):
        if i % 2 == 0:
            if j % 2 == 0:
                data_qubits.append((i / 2, j / 2))
            else:
                stabilizer_positions.append((i / 2, j / 2))
                stabilizer_types[(i/2, j/2)] = 'Z'
        else:
            if j % 2 == 0:
                stabilizer_positions.append((i / 2, j / 2))
                stabilizer_types[(i / 2, j / 2)] = 'X'
            else:
                data_qubits.append((i / 2, j / 2))


# Plot colored "+"-shaped regions for stabilizers
for (i, j) in stabilizer_positions:
    stype = stabilizer_types[(i, j)]
    color = '#4BB96F' if stype == 'Z' else '#FEE02F'
    alpha = 0.9  # Transparency for overlapping regions

    # Horizontal arm of the "+" (covers left/right data qubits)
    ax.add_patch(Rectangle(
        (i - 0.5, j - 0.1), 1.0, 0.2,  # Position (x, y), width, height
        facecolor=color, alpha=alpha, edgecolor=None, zorder=1
    ))

    # Vertical arm of the "+" (covers top/bottom data qubits)
    ax.add_patch(Rectangle(
        (i - 0.1, j - 0.5), 0.2, 1.0,  # Position (x, y), width, height
        facecolor=color, alpha=alpha, edgecolor=None, zorder=1
    ))

# Plot data qubits (white circles)
for (x, y) in data_qubits:
    ax.add_patch(plt.Circle((x, y), radius=0.1, color='white', ec='black', lw=2, zorder=2))

# Plot stabilizers (black circles)
for (i, j) in stabilizer_positions:
    ax.add_patch(plt.Circle((i, j), radius=0.1, color='black', zorder=3))

# Adjust axis limits and appearance
ax.set_xlim(-0.5, grid_size / 2)
ax.set_ylim(-0.5, grid_size / 2)

ax.set_aspect('equal')
plt.axis('off')

plt.savefig("surface_code_plot.png", dpi=300) #bbox_inches="tight"