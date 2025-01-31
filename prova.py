from pymatching import Matching

grid_size = 3
n_rounds = 2
syndrome_data = "01100110"
matching = Matching.from_grid(grid_size, grid_size, repetitions=n_rounds)
# Decode syndromes to get correction
correction = matching.decode(syndrome_data)