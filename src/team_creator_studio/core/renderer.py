"""
Project rendering and compositing.

Handles rendering the current project state to a composite image.
"""

from pathlib import Path
from typing import Optional

from team_creator_studio.core.models import ProjectState
from team_creator_studio.imaging.io import load_image, save_png


def render_project(project_state: ProjectState, project_path: Path) -> Path:
    """
    Render the current project state to a composite image.

    Milestone 3: Respects active_op_index for undo/redo:
    - If active_op_index == -1: use base layer
    - If active_op_index >= 0: use operation at that index
    - Future: Support multiple layers with blending

    Args:
        project_state: Current project state
        project_path: Absolute path to project directory

    Returns:
        Path to the rendered composite image (relative to project root)

    Raises:
        ValueError: If project has no layers or images
        FileNotFoundError: If required image files don't exist
    """
    # Determine source image for composite based on active_op_index
    composite_source = None

    # Case 1: active_op_index points to an operation
    if project_state.active_op_index >= 0 and project_state.active_op_index < len(project_state.operations):
        active_op = project_state.operations[project_state.active_op_index]
        composite_source = project_path / active_op.output_path

        if not composite_source.exists():
            raise FileNotFoundError(
                f"Operation output missing: {active_op.output_path}. "
                f"Cannot render composite for operation at index {project_state.active_op_index}."
            )

    # Case 2: active_op_index == -1 or no operations: use base layer
    elif project_state.layers:
        base_layer = project_state.get_base_layer()
        if base_layer:
            composite_source = project_path / base_layer.layer_path

            if not composite_source.exists():
                raise FileNotFoundError(
                    f"Base layer missing: {base_layer.layer_path}. "
                    f"Cannot render composite."
                )

    # No source available
    if not composite_source:
        raise ValueError(
            "Cannot render project: no operations or layers with valid images"
        )

    # Load source image
    composite_image = load_image(composite_source)

    # Save composite to working directory
    composite_path = project_path / "working" / "composite.png"
    save_png(composite_image, composite_path)

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
    Render multiple layers with blending (future implementation).

    For Milestone 2, this is a placeholder that calls render_project.
    Future milestones will implement proper layer compositing with:
    - Layer visibility
    - Opacity
    - Blend modes
    - Layer ordering

    Args:
        project_state: Current project state
        project_path: Absolute path to project directory
        output_path: Optional output path (defaults to working/composite.png)

    Returns:
        Path to rendered composite (relative to project root)
    """
    # For now, delegate to simple render_project
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
