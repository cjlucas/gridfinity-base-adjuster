"""Tunable parameters for stacking-lip auto-detection.

There is no user-facing --lip-height override (deliberate scope
decision -- see lip_detect.py's module docstring for why): a stacking
lip's exact height and shape are generator-dependent, so a hardcoded
default would silently cut the wrong amount on an unfamiliar
generator's output.
"""

# Gridfinity bin heights are built from a fixed vertical unit (a bin's
# base + walls sum to a whole multiple of this) -- already documented
# in this project's own CLAUDE.md re: the reference implementation's
# "profile + bridge = one Z-unit" convention. A stacking lip is purely
# additive height on top of that, so (total mesh height) mod this unit
# is the primary detection signal -- see lip_detect.py.
UNIT_HEIGHT_MM = 7.0

# Bounds on how tall a detected lip is allowed to be to count as a real
# lip rather than noise/coincidence. Covers both the gridfinity.xyz
# nominal spec height (4.4mm, sharp tip) and gridfinity-rebuilt-openscad's
# actual filleted mesh height (3.55147mm), with margin either side.
LIP_HEIGHT_MIN_MM = 2.5
LIP_HEIGHT_MAX_MM = 5.0

# Z offsets (below the very top, and below the candidate cut plane) used
# to sample the outer wall footprint for the confirmation check.
CONFIRM_SAMPLE_NEAR_TOP_MM = 0.05
CONFIRM_SAMPLE_BELOW_CUT_MM = 0.5

# The outer footprint width near the top must differ from the width
# just below the candidate cut by at least this much to confirm a real
# geometric transition exists there (e.g. a tip fillet), rather than the
# height-modulo match being coincidental.
CONFIRM_MIN_WIDTH_DELTA_MM = 0.05
