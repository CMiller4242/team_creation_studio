"""
Non-destructive color replacement operation.

Replaces pixels matching a target color (within tolerance) with a new color.
"""

from typing import Tuple
from PIL import Image
import numpy as np

from team_creator_studio.imaging.color import color_distance


def apply_color_replace(
    image: Image.Image,
    target_rgb: Tuple[int, int, int],
    new_rgb: Tuple[int, int, int],
    tolerance: int = 0,
    preserve_alpha: bool = True,
) -> Image.Image:
    """
    Replace colors in an image matching target color (within tolerance) with new color.

    Uses Euclidean distance in RGB color space to determine color similarity.
    Preserves alpha channel by default.

    Args:
        image: PIL Image in RGBA mode
        target_rgb: Target color to replace (R, G, B) tuple
        new_rgb: New color to replace with (R, G, B) tuple
        tolerance: Tolerance for color matching (0-255, default 0 for exact match)
        preserve_alpha: If True, preserve original alpha values (default True)

    Returns:
        New PIL Image with colors replaced

    Algorithm:
        - For each pixel, calculate Euclidean distance from target color in RGB space
        - If distance <= tolerance, replace RGB with new_rgb
        - Alpha channel preserved if preserve_alpha=True
        - Fully transparent pixels (alpha=0) are never modified

    Examples:
        >>> img = Image.new("RGBA", (100, 100), (255, 255, 255, 255))
        >>> result = apply_color_replace(img, (255, 255, 255), (0, 255, 0), tolerance=10)
        >>> # White pixels replaced with green
    """
    # Ensure image is in RGBA mode
    if image.mode != "RGBA":
        image = image.convert("RGBA")

    # Convert image to numpy array for efficient processing
    img_array = np.array(image, dtype=np.uint8)

    # Extract RGB and alpha channels
    rgb = img_array[:, :, :3]  # Shape: (height, width, 3)
    alpha = img_array[:, :, 3]  # Shape: (height, width)

    # Calculate color distance for each pixel
    # Vectorized distance calculation for performance
    r_dist = rgb[:, :, 0].astype(np.float32) - target_rgb[0]
    g_dist = rgb[:, :, 1].astype(np.float32) - target_rgb[1]
    b_dist = rgb[:, :, 2].astype(np.float32) - target_rgb[2]

    distances = np.sqrt(r_dist**2 + g_dist**2 + b_dist**2)

    # Create mask for pixels to replace
    # Pixels match if: distance <= tolerance AND (not preserve_alpha OR alpha > 0)
    if preserve_alpha:
        # Don't replace fully transparent pixels
        mask = (distances <= tolerance) & (alpha > 0)
    else:
        mask = distances <= tolerance

    # Replace matching pixels with new color
    rgb[mask] = new_rgb

    # Reconstruct RGBA array
    result_array = np.dstack([rgb, alpha])

    # Convert back to PIL Image
    result_image = Image.fromarray(result_array, mode="RGBA")

    return result_image


def count_matching_pixels(
    image: Image.Image,
    target_rgb: Tuple[int, int, int],
    tolerance: int = 0,
) -> int:
    """
    Count pixels matching target color within tolerance.

    Useful for previewing how many pixels will be affected by color replacement.

    Args:
        image: PIL Image in RGBA mode
        target_rgb: Target color (R, G, B) tuple
        tolerance: Tolerance for color matching (0-255)

    Returns:
        Number of pixels matching the target color
    """
    if image.mode != "RGBA":
        image = image.convert("RGBA")

    img_array = np.array(image, dtype=np.uint8)
    rgb = img_array[:, :, :3]
    alpha = img_array[:, :, 3]

    # Calculate distances
    r_dist = rgb[:, :, 0].astype(np.float32) - target_rgb[0]
    g_dist = rgb[:, :, 1].astype(np.float32) - target_rgb[1]
    b_dist = rgb[:, :, 2].astype(np.float32) - target_rgb[2]

    distances = np.sqrt(r_dist**2 + g_dist**2 + b_dist**2)

    # Count matching pixels (excluding fully transparent)
    mask = (distances <= tolerance) & (alpha > 0)
    return int(np.sum(mask))


def get_unique_colors(image: Image.Image, include_alpha: bool = False) -> list:
    """
    Get list of unique colors in the image.

    Args:
        image: PIL Image
        include_alpha: If True, include alpha in unique colors

    Returns:
        List of unique color tuples
    """
    if image.mode != "RGBA":
        image = image.convert("RGBA")

    img_array = np.array(image)

    if include_alpha:
        pixels = img_array.reshape(-1, 4)
    else:
        pixels = img_array[:, :, :3].reshape(-1, 3)

    unique_colors = np.unique(pixels, axis=0)
    return [tuple(color) for color in unique_colors]
