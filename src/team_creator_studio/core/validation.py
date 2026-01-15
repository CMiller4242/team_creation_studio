"""
Project state validation and repair utilities.

Ensures project metadata is consistent and recovers from common errors.
"""

from pathlib import Path
from typing import List

from team_creator_studio.core.models import ProjectState


def validate_and_repair_project_state(
    project_state: ProjectState,
    project_path: Path,
    verbose: bool = False
) -> List[str]:
    """
    Validate and repair project state.

    Checks:
    - active_op_index is within valid range
    - Referenced files exist
    - Composite path is valid

    Repairs:
    - Clamps active_op_index to valid range
    - Updates composite path if missing/invalid
    - Normalizes paths to relative paths
    - Updates timestamp

    Args:
        project_state: Project state to validate
        project_path: Absolute path to project directory
        verbose: If True, print repair actions

    Returns:
        List of repair actions performed (empty if no repairs needed)
    """
    repairs = []

    # 1. Validate and repair active_op_index
    if project_state.operations:
        max_index = len(project_state.operations) - 1
        if project_state.active_op_index > max_index:
            old_index = project_state.active_op_index
            project_state.active_op_index = max_index
            repairs.append(f"Clamped active_op_index from {old_index} to {max_index}")

        if project_state.active_op_index < -1:
            old_index = project_state.active_op_index
            project_state.active_op_index = -1
            repairs.append(f"Clamped active_op_index from {old_index} to -1")
    else:
        # No operations: must be -1
        if project_state.active_op_index != -1:
            old_index = project_state.active_op_index
            project_state.active_op_index = -1
            repairs.append(f"Set active_op_index to -1 (no operations), was {old_index}")

    # 2. Validate operation output files exist
    # For operations before or at active index, check if output files exist
    for i in range(project_state.active_op_index + 1):
        if i < len(project_state.operations):
            op = project_state.operations[i]
            op_output_path = project_path / op.output_path
            if not op_output_path.exists():
                # Missing operation output: move active index back
                old_index = project_state.active_op_index
                project_state.active_op_index = i - 1
                repairs.append(
                    f"Operation {i} output missing ({op.output_path}), "
                    f"moved active_op_index from {old_index} to {project_state.active_op_index}"
                )
                break

    # 3. Infer canvas size from first layer if not set or invalid (Milestone 5)
    if project_state.canvas_width <= 0 or project_state.canvas_height <= 0:
        if project_state.layers:
            # Try to infer from first layer
            first_layer = project_state.layers[0]
            layer_bitmap_path = project_path / first_layer.layer_path
            if layer_bitmap_path.exists():
                try:
                    from team_creator_studio.imaging.io import get_image_info
                    info = get_image_info(layer_bitmap_path)
                    if info:
                        old_width = project_state.canvas_width
                        old_height = project_state.canvas_height
                        project_state.canvas_width = info["width"]
                        project_state.canvas_height = info["height"]
                        repairs.append(
                            f"Inferred canvas size from first layer: {old_width}x{old_height} -> "
                            f"{project_state.canvas_width}x{project_state.canvas_height}"
                        )
                except Exception as e:
                    repairs.append(f"Warning: Could not infer canvas size: {e}")

    # 4. Normalize layer order
    if project_state.layers:
        # Check if all orders are the same (likely old format)
        orders = [layer.order for layer in project_state.layers]
        if len(set(orders)) == 1 and len(orders) > 1:
            # All the same order, reassign
            project_state.normalize_layer_order()
            repairs.append(f"Normalized layer order for {len(project_state.layers)} layers")

    # 5. Validate composite path
    needs_composite_update = False
    if project_state.active_composite_path:
        composite_abs = project_path / project_state.active_composite_path
        if not composite_abs.exists():
            repairs.append(f"Composite file missing: {project_state.active_composite_path}")
            needs_composite_update = True
    else:
        # No composite path set
        if project_state.active_op_index >= 0 or project_state.layers:
            needs_composite_update = True
            repairs.append("Composite path not set")

    # Note: Actual composite re-rendering should be done by the caller
    # We just flag that it's needed
    if needs_composite_update:
        repairs.append("Composite needs re-rendering")

    # 6. Validate paths are relative
    # Check source images
    for img in project_state.source_images:
        if Path(img.original_path).is_absolute():
            # Try to make relative
            try:
                abs_path = Path(img.original_path)
                rel_path = abs_path.relative_to(project_path)
                img.original_path = str(rel_path)
                repairs.append(f"Converted image path to relative: {rel_path}")
            except ValueError:
                # Can't make relative (outside project)
                repairs.append(f"Warning: Image path outside project: {img.original_path}")

    # Check layers
    for layer in project_state.layers:
        if Path(layer.layer_path).is_absolute():
            try:
                abs_path = Path(layer.layer_path)
                rel_path = abs_path.relative_to(project_path)
                layer.layer_path = str(rel_path)
                repairs.append(f"Converted layer path to relative: {rel_path}")
            except ValueError:
                repairs.append(f"Warning: Layer path outside project: {layer.layer_path}")

    # Check operations
    for op in project_state.operations:
        if Path(op.output_path).is_absolute():
            try:
                abs_path = Path(op.output_path)
                rel_path = abs_path.relative_to(project_path)
                op.output_path = str(rel_path)
                repairs.append(f"Converted operation path to relative: {rel_path}")
            except ValueError:
                repairs.append(f"Warning: Operation path outside project: {op.output_path}")

    # 7. Update timestamp if repairs were made
    if repairs:
        project_state.update_timestamp()

    # Print repairs if verbose
    if verbose and repairs:
        print("Project state repairs:")
        for repair in repairs:
            print(f"  - {repair}")

    return repairs


def check_project_health(project_state: ProjectState, project_path: Path) -> dict:
    """
    Check project health and return diagnostics.

    Args:
        project_state: Project state to check
        project_path: Absolute path to project directory

    Returns:
        Dictionary with health information:
        - healthy: bool
        - issues: list of issue descriptions
        - warnings: list of warning descriptions
    """
    issues = []
    warnings = []

    # Check if operations are within range
    if project_state.operations:
        if project_state.active_op_index >= len(project_state.operations):
            issues.append(f"active_op_index ({project_state.active_op_index}) >= operation count ({len(project_state.operations)})")

    # Check if referenced files exist
    for img in project_state.source_images:
        img_path = project_path / img.original_path
        if not img_path.exists():
            warnings.append(f"Source image missing: {img.original_path}")

    for layer in project_state.layers:
        layer_path = project_path / layer.layer_path
        if not layer_path.exists():
            warnings.append(f"Layer file missing: {layer.layer_path}")

    for i, op in enumerate(project_state.operations):
        op_path = project_path / op.output_path
        if not op_path.exists():
            if i <= project_state.active_op_index:
                issues.append(f"Active operation {i} output missing: {op.output_path}")
            else:
                warnings.append(f"Future operation {i} output missing: {op.output_path}")

    if project_state.active_composite_path:
        composite_path = project_path / project_state.active_composite_path
        if not composite_path.exists():
            warnings.append(f"Composite missing: {project_state.active_composite_path}")

    return {
        "healthy": len(issues) == 0,
        "issues": issues,
        "warnings": warnings,
    }
