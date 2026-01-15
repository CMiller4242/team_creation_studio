"""
Color parsing and conversion utilities.

Supports multiple color input formats: hex strings, RGB tuples, comma-separated strings.
"""

import re
from typing import Tuple, Union


def parse_color(color_input: str) -> Tuple[int, int, int]:
    """
    Parse color from various input formats to RGB tuple.

    Supported formats:
    - Hex: "#RRGGBB" or "#rrggbb" (with or without #)
    - RGB: "R,G,B" or "R, G, B" (0-255)

    Args:
        color_input: Color string in supported format

    Returns:
        Tuple of (R, G, B) with values 0-255

    Raises:
        ValueError: If color format is invalid or values out of range

    Examples:
        >>> parse_color("#FF0000")
        (255, 0, 0)
        >>> parse_color("ff0000")
        (255, 0, 0)
        >>> parse_color("255,0,0")
        (255, 0, 0)
        >>> parse_color("255, 0, 0")
        (255, 0, 0)
    """
    color_input = color_input.strip()

    # Try hex format
    if color_input.startswith("#") or re.match(r"^[0-9A-Fa-f]{6}$", color_input):
        return hex_to_rgb(color_input)

    # Try comma-separated RGB
    if "," in color_input:
        parts = color_input.split(",")
        if len(parts) == 3:
            try:
                r, g, b = [int(p.strip()) for p in parts]
                if all(0 <= v <= 255 for v in (r, g, b)):
                    return (r, g, b)
                else:
                    raise ValueError(
                        f"RGB values must be 0-255, got: {r}, {g}, {b}"
                    )
            except ValueError as e:
                raise ValueError(f"Invalid RGB format: {color_input}") from e

    raise ValueError(
        f"Unrecognized color format: '{color_input}'. "
        f"Expected hex (#RRGGBB) or RGB (R,G,B)"
    )


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """
    Convert hex color to RGB tuple.

    Args:
        hex_color: Hex color string (with or without #)

    Returns:
        Tuple of (R, G, B) with values 0-255

    Raises:
        ValueError: If hex format is invalid

    Examples:
        >>> hex_to_rgb("#FF0000")
        (255, 0, 0)
        >>> hex_to_rgb("00FF00")
        (0, 255, 0)
    """
    hex_color = hex_color.strip()

    # Remove # if present
    if hex_color.startswith("#"):
        hex_color = hex_color[1:]

    # Validate format
    if not re.match(r"^[0-9A-Fa-f]{6}$", hex_color):
        raise ValueError(f"Invalid hex color format: {hex_color}")

    # Convert to RGB
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)

    return (r, g, b)


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """
    Convert RGB tuple to hex color string.

    Args:
        r: Red value (0-255)
        g: Green value (0-255)
        b: Blue value (0-255)

    Returns:
        Hex color string with # prefix (uppercase)

    Raises:
        ValueError: If RGB values are out of range

    Examples:
        >>> rgb_to_hex(255, 0, 0)
        '#FF0000'
        >>> rgb_to_hex(0, 255, 0)
        '#00FF00'
    """
    if not all(0 <= v <= 255 for v in (r, g, b)):
        raise ValueError(f"RGB values must be 0-255, got: {r}, {g}, {b}")

    return f"#{r:02X}{g:02X}{b:02X}"


def color_distance(color1: Tuple[int, int, int], color2: Tuple[int, int, int]) -> float:
    """
    Calculate Euclidean distance between two colors in RGB space.

    Args:
        color1: First RGB color tuple
        color2: Second RGB color tuple

    Returns:
        Distance value (0 to ~441 for RGB colors)

    Examples:
        >>> color_distance((255, 0, 0), (255, 0, 0))
        0.0
        >>> color_distance((0, 0, 0), (255, 255, 255))
        441.67...
    """
    r1, g1, b1 = color1
    r2, g2, b2 = color2

    return ((r1 - r2) ** 2 + (g1 - g2) ** 2 + (b1 - b2) ** 2) ** 0.5


def validate_rgb(r: int, g: int, b: int) -> bool:
    """
    Validate RGB values are in valid range.

    Args:
        r: Red value
        g: Green value
        b: Blue value

    Returns:
        True if all values are 0-255, False otherwise
    """
    return all(isinstance(v, int) and 0 <= v <= 255 for v in (r, g, b))
