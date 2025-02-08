import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

# Create a figure and axis
fig, ax = plt.subplots(figsize=(8, 8))

# Define grid size (number of stabilizers in each dimension)
grid_size = 9

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

# remove the stabilizer at coordinates (2.0, 2.5)
stabilizer_positions.remove((2.0, 2.5))

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

# plot a red circle in over the data qubits representing the logical operator which is a Z chain
# first of all identify the data qubits which are in the third column
logical_operator_z = [(i, j) for i, j in data_qubits if i == 1]
# then add a red circle over the data qubits, and a red line connecting them

for (x, y) in logical_operator_z:
    ax.add_patch(plt.Circle((x, y), radius=0.13, color='red', zorder=4))
    ax.plot([x, x], [y - 0.5, y + 0.5], color='red', lw=6, zorder=4)

# plot a red circle in over the data qubits representing the logical operator which is a Z chain
# first of all identify the data qubits which are in the third column
logical_operator_x = [(i, j) for i, j in data_qubits if j == 1]
# then add a red circle over the data qubits, and a red line connecting them

for (x, y) in logical_operator_x:
    ax.add_patch(plt.Circle((x, y), radius=0.13, color='blue', zorder=4))
    ax.plot([x - 0.5, x + 0.5], [y, y], color='blue', lw=6, zorder=4)

logical_hole = [(2.0, 2.0), (1.5, 2.5), (2.0, 3.0), (2.5, 2.5)]

for (x, y) in logical_hole:
    ax.add_patch(plt.Circle((x, y), radius=0.13, color='purple', zorder=4))
    if y == 2.5:
        ax.plot([x, x], [y - 0.5, y + 0.5], color='purple', lw=6, zorder=4)
    else:
        ax.plot([x - 0.5, x + 0.5], [y, y], color='purple', lw=6, zorder=4)

# Plot data qubits (white circles)
for (x, y) in data_qubits:
    ax.add_patch(plt.Circle((x, y), radius=0.1, color='white', ec='black', lw=2, zorder=5))

# Plot stabilizers (black circles)
for (i, j) in stabilizer_positions:
    ax.add_patch(plt.Circle((i, j), radius=0.1, color='black', zorder=3))

# Add double arrow with label
ax.annotate(
    '', xy=((grid_size / 2) + 0.2, grid_size / 2), xytext=((grid_size / 2) + 0.2, -0.5),
    arrowprops=dict(arrowstyle='<->', color='black', lw=4)
)
ax.text(grid_size / 2 , grid_size / 4 - 0.1, '$d = 5$', color='black', fontsize=17, ha='center', va='center', backgroundcolor='white')

# Adjust axis limits and appearance
ax.set_xlim(-0.5, (grid_size / 2) + 0.3)
ax.set_ylim(-0.5, (grid_size / 2) + 0.3)

ax.set_aspect('equal')
plt.axis('off')

# Add text annotations
ax.text(-0.7, 1.13, '$\\hat{X}_L$', color='blue', fontsize=30, ha='center', weight="bold")
ax.text(1.2, 4.7, '$\\hat{Z}_L$', color='red', fontsize=30, ha='center', weight="bold")

plt.savefig("surface_code_plot_logical_operator.png", dpi=300) #bbox_inches="tight"