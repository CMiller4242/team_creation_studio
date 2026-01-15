"""
Project rendering and compositing.

Handles rendering the current project state to a composite image.
Milestone 5: Multi-layer compositing with visibility, opacity, and positioning.
"""

from pathlib import Path
from typing import Optional
from PIL import Image

from team_creator_studio.core.models import ProjectState, Layer
from team_creator_studio.imaging.io import load_image, save_png


def get_layer_bitmap_path(
    project_state: ProjectState,
    layer: Layer,
    project_path: Path
) -> Optional[Path]:
    """
    Get the current bitmap path for a layer considering active_op_index.

    Logic:
    - Find the latest operation for this layer up to active_op_index
    - If found, use output_layer_path (or output_path for legacy)
    - Otherwise, use the layer's original layer_path

    Args:
        project_state: Project state
        layer: Layer to get bitmap for
        project_path: Project directory path

    Returns:
        Absolute path to layer bitmap, or None if not found
    """
    # Find latest operation for this layer up to active_op_index
    latest_op_path = None

    for i in range(project_state.active_op_index + 1):
        if i < 0 or i >= len(project_state.operations):
            continue

        op = project_state.operations[i]
        if op.input_layer_id == layer.id:
            # This operation modifies this layer
            # Use output_layer_path if available, otherwise output_path
            if op.output_layer_path:
                latest_op_path = op.output_layer_path
            else:
                latest_op_path = op.output_path

    # Use operation output if found, otherwise use layer's original path
    if latest_op_path:
        bitmap_path = project_path / latest_op_path
    else:
        bitmap_path = project_path / layer.layer_path

    if bitmap_path.exists():
        return bitmap_path

    return None


def render_project(project_state: ProjectState, project_path: Path) -> Path:
    """
    Render the current project state to a composite image.

    Milestone 5: Multi-layer compositing with proper layer blending:
    - Creates transparent RGBA canvas at project's canvas size
    - Sorts layers by order (ascending: bottom to top)
    - For each visible layer:
      - Loads layer bitmap (respecting active_op_index)
      - Applies opacity
      - Pastes onto canvas at (x, y) position
    - Saves to working/composite.png

    Args:
        project_state: Current project state
        project_path: Absolute path to project directory

    Returns:
        Path to the rendered composite image (relative to project root)

    Raises:
        ValueError: If project has no visible layers
        FileNotFoundError: If required layer images don't exist
    """
    # Check if we have any layers
    if not project_state.layers:
        raise ValueError("Cannot render project: no layers")

    # Check if we have any visible layers
    if project_state.get_visible_layer_count() == 0:
        raise ValueError("Cannot render project: no visible layers")

    # Create transparent canvas
    canvas = Image.new(
        "RGBA",
        (project_state.canvas_width, project_state.canvas_height),
        (0, 0, 0, 0)  # Transparent
    )

    # Get sorted layers (bottom to top)
    sorted_layers = project_state.get_sorted_layers()

    # Composite each visible layer
    for layer in sorted_layers:
        if not layer.visible:
            continue

        # Get layer bitmap path
        layer_bitmap_path = get_layer_bitmap_path(project_state, layer, project_path)

        if not layer_bitmap_path:
            # Layer bitmap missing - log warning but continue
            print(f"Warning: Layer bitmap not found for layer '{layer.name}' (ID: {layer.id})")
            continue

        try:
            # Load layer image
            layer_image = load_image(layer_bitmap_path)

            # Convert to RGBA if needed
            if layer_image.mode != "RGBA":
                layer_image = layer_image.convert("RGBA")

            # Apply opacity if not 1.0
            if layer.opacity < 1.0:
                # Split into channels
                r, g, b, a = layer_image.split()

                # Multiply alpha by opacity
                import numpy as np
                alpha_array = np.array(a, dtype=np.float32)
                alpha_array = alpha_array * layer.opacity
                a = Image.fromarray(alpha_array.astype(np.uint8), mode='L')

                # Merge back
                layer_image = Image.merge("RGBA", (r, g, b, a))

            # Paste layer onto canvas at (x, y) position
            # Use the alpha channel as mask for proper compositing
            canvas.paste(layer_image, (layer.x, layer.y), layer_image)

        except Exception as e:
            print(f"Warning: Failed to composite layer '{layer.name}': {e}")
            continue

    # Save composite to working directory
    composite_path = project_path / "working" / "composite.png"
    composite_path.parent.mkdir(parents=True, exist_ok=True)
    save_png(canvas, composite_path)

    # Update project state with relative path
    relative_path = "working/composite.png"
    project_state.active_composite_path = relative_path

    return Path(relative_path)


def render_layers(
    project_state: ProjectState,
    project_path: Path,
    output_path: Optional[Path] = None,
) -> Path:
    """
    Render multiple layers with blending.

    Alias for render_project for backward compatibility.

    Args:
        project_state: Current project state
        project_path: Absolute path to project directory
        output_path: Optional output path (ignored, uses working/composite.png)

    Returns:
        Path to rendered composite (relative to project root)
    """
    return render_project(project_state, project_path)


def get_composite_path(project_state: ProjectState, project_path: Path) -> Optional[Path]:
    """
    Get the absolute path to the current composite image.

    Args:
        project_state: Current project state
        project_path: Absolute path to project directory

    Returns:
        Absolute path to composite image, or None if not available
    """
    if not project_state.active_composite_path:
        return None

    composite_path = project_path / project_state.active_composite_path

    if composite_path.exists():
        return composite_path

    return None
