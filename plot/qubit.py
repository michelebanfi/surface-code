import matplotlib.pyplot as plt

# Create figure with two subplots
fig, (ax_phys, ax_log) = plt.subplots(1, 2, figsize=(8, 6), dpi=300)

# Draw physical qubit (single black circle)
ax_phys.add_patch(plt.Circle((0.5, 0.5), 0.1, color='black'))
ax_phys.set_xlim(0, 1)
ax_phys.set_ylim(0, 1)
ax_phys.set_aspect('equal')
ax_phys.axis('off')
ax_phys.set_title('Physical Qubit')

# Draw logical qubit structure
# Positions for black circles (x's) and white circles (o's)
x_positions = [(1, 0), (0, 1), (2, 1), (1, 2), (0, 3), (2, 3), (1, 4), (0, 5), (2, 5), (1, 6)]
o_positions = [(1, 1), (1, 3), (1, 5)]

# Plot black circles
for x, y in x_positions:
    ax_log.add_patch(plt.Circle((x, y), 0.4, color='black'))

# Plot white circles with black borders
for x, y in o_positions:
    ax_log.add_patch(plt.Circle((x, y), 0.4, edgecolor='black', facecolor='white', linewidth=2))

# Configure logical qubit plot
ax_log.set_xlim(-1, 3)
ax_log.set_ylim(-1, 7)
ax_log.invert_yaxis()  # Put first row at the top
ax_log.set_aspect('equal')
ax_log.axis('off')
ax_log.set_title('Logical Qubit')

plt.tight_layout()
plt.savefig("physical_logical_qubit.png")