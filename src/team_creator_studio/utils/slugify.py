"""
Slug generation utilities for Team Creation Studio.

Provides functions to convert human-readable names into filesystem-safe slugs.
"""

import re
import unicodedata


def slugify(text: str) -> str:
    """
    Convert a string to a filesystem-safe slug.

    The slugify function:
    - Converts to lowercase
    - Removes accents and diacritics
    - Replaces spaces and underscores with hyphens
    - Removes invalid characters
    - Collapses multiple hyphens
    - Strips leading/trailing hyphens

    Args:
        text: Input string to slugify

    Returns:
        str: Slugified string (lowercase, hyphens, alphanumeric)

    Examples:
        >>> slugify("Pembroke Dominion")
        'pembroke-dominion'
        >>> slugify("Primary Logo v1")
        'primary-logo-v1'
        >>> slugify("Test___Project   Name!!")
        'test-project-name'
    """
    if not text:
        return ""

    # Normalize unicode characters (remove accents)
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")

    # Convert to lowercase
    text = text.lower()

    # Replace spaces and underscores with hyphens
    text = re.sub(r"[\s_]+", "-", text)

    # Remove invalid characters (keep alphanumeric and hyphens)
    text = re.sub(r"[^a-z0-9\-]", "", text)

    # Collapse multiple hyphens
    text = re.sub(r"-+", "-", text)

    # Strip leading/trailing hyphens
    text = text.strip("-")

    return text
