"""Reference Gridfinity base dimensions.

Reverse-engineered directly from real reference bins (gf-rebuilt
"Standard" bins) since they're the ground truth. The chamfer profile
below is the SAME absolute geometry regardless of foot size -- a 21mm
foot uses an identical profile to a 42mm foot, just applied around a
smaller top island (cell_size - BASE_GAP_MM instead of 42 - BASE_GAP_MM).
"""

# Cell pitch the *input* footprint is assumed to be built from (whole
# 42mm cells only -- see the scope decision in the project plan). Used
# for grid-origin detection.
GRID_DIMENSIONS_MM = (42.0, 42.0)

# Cell pitch the *newly generated* base is placed on: every occupied
# 42mm cell is split into this many independent smaller feet.
PLACEMENT_CELL_SIZE_MM = 21.0

BASE_GAP_MM = 0.5

# (inset, height) pairs, with height measured DOWNWARD from the top of
# the profile (where it meets the body, inset=0) to the bottom tip
# (inset=2.95, the narrowest point that noses into the baseplate).
BASE_PROFILE = [(0.0, 0.0), (2.15, 2.15), (2.15, 3.95), (2.95, 4.75)]

BASE_PROFILE_HEIGHT = 4.75
BASE_HEIGHT = 4.75

BASE_TOP_RADIUS = 3.75

# Default assumed height of an *existing input's* base, used only to pick
# the --base-height CLI default (where to cut). Confirmed against two
# independent real-world Gridfinity STLs to be 4.75mm -- same as
# BASE_HEIGHT above, though the two are conceptually distinct (one is a
# CLI default guess about input files, the other governs the newly
# generated foot's own geometry) and could diverge for nonstandard input.
DEFAULT_INPUT_BASE_HEIGHT = BASE_HEIGHT
