"""
Theme constants for Team Creation Studio GUI.

Defines colors, fonts, spacing, and other visual constants.
"""

# Colors
BG_PRIMARY = "#f0f0f0"
BG_SECONDARY = "#ffffff"
BG_DARK = "#2d2d2d"
BG_SIDEBAR = "#e8e8e8"

TEXT_PRIMARY = "#000000"
TEXT_SECONDARY = "#666666"
TEXT_LIGHT = "#999999"

ACCENT_PRIMARY = "#0066cc"
ACCENT_HOVER = "#0052a3"
ACCENT_ACTIVE = "#003d7a"

BORDER_COLOR = "#cccccc"
BORDER_DARK = "#999999"

ERROR_COLOR = "#cc0000"
SUCCESS_COLOR = "#00aa00"
WARNING_COLOR = "#ff8800"

# Fonts
# Try Windows fonts first, then fallback to cross-platform defaults
FONT_FAMILY = "Segoe UI"
FONT_FAMILY_FALLBACK = "TkDefaultFont"

FONT_SIZE_NORMAL = 9
FONT_SIZE_LARGE = 11
FONT_SIZE_HEADING = 12

# Spacing (all values must be integers)
PADDING_SMALL = 4
PADDING_MEDIUM = 8
PADDING_LARGE = 12
PADDING_XLARGE = 16

SPACING_SMALL = 4
SPACING_MEDIUM = 8
SPACING_LARGE = 12

# Widget sizes (all values must be integers)
BUTTON_HEIGHT = 30
BUTTON_WIDTH = 100

LIST_WIDTH = 250
LIST_MIN_HEIGHT = 200

INPUT_HEIGHT = 24
INPUT_WIDTH = 150

# Window defaults
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
WINDOW_MIN_WIDTH = 800
WINDOW_MIN_HEIGHT = 600


def get_font(size=FONT_SIZE_NORMAL, weight="normal"):
    """
    Get a font tuple for Tkinter widgets.
    Returns (family, size, weight).
    """
    return (FONT_FAMILY, size, weight)
