"""
Image I/O primitives for Team Creation Studio.

Handles loading and saving images with proper format conversion.
"""

from pathlib import Path
from typing import Union
from PIL import Image


def load_image(path: Union[str, Path]) -> Image.Image:
    """
    Load an image from disk and convert to RGBA mode.

    Args:
        path: Path to the image file

    Returns:
        PIL Image in RGBA mode

    Raises:
        FileNotFoundError: If image file doesn't exist
        PIL.UnidentifiedImageError: If file is not a valid image
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Image not found: {path}")

    img = Image.open(path)

    # Convert to RGBA for consistent handling
    if img.mode != "RGBA":
        img = img.convert("RGBA")

    return img


def save_png(image: Image.Image, path: Union[str, Path], optimize: bool = True):
    """
    Save an image as PNG format.

    Args:
        image: PIL Image to save
        path: Destination path
        optimize: Enable PNG optimization (default True)

    Raises:
        ValueError: If image is None
    """
    if image is None:
        raise ValueError("Cannot save None image")

    path = Path(path)

    # Ensure parent directory exists
    path.parent.mkdir(parents=True, exist_ok=True)

    # Ensure image is in RGBA mode before saving
    if image.mode != "RGBA":
        image = image.convert("RGBA")

    # Save as PNG
    image.save(path, "PNG", optimize=optimize)


def get_image_info(path: Union[str, Path]) -> dict:
    """
    Get basic information about an image without fully loading it.

    Args:
        path: Path to the image file

    Returns:
        Dictionary with image metadata (format, mode, size)

    Raises:
        FileNotFoundError: If image file doesn't exist
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Image not found: {path}")

    with Image.open(path) as img:
        return {
            "format": img.format,
            "mode": img.mode,
            "size": img.size,
            "width": img.width,
            "height": img.height,
        }
