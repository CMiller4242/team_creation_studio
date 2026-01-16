"""
Main CLI entry point for Team Creation Studio.

Provides commands for managing teams and projects within the workspace.
"""

import argparse
import shutil
import sys
import uuid
from pathlib import Path

from team_creator_studio.config.settings import Settings
from team_creator_studio.storage.workspace import WorkspaceManager
from team_creator_studio.core.models import ProjectState, SourceImage, Layer, OperationRecord
from team_creator_studio.core.renderer import render_project
from team_creator_studio.core.validation import validate_and_repair_project_state
from team_creator_studio.core.services import ProjectService
from team_creator_studio.imaging.io import load_image, save_png
from team_creator_studio.imaging.color import parse_color, rgb_to_hex
from team_creator_studio.ops.color_replace import apply_color_replace
import json
import os


def cmd_where(args):
    """Print the workspace path and confirm it exists."""
    settings = Settings()
    workspace_path = settings.get_workspace_path()

    if workspace_path.exists():
        print(f"Workspace: {workspace_path}")
        print("Status: exists")
    else:
        print(f"Workspace: {workspace_path}")
        print("Status: does not exist (will be created on first use)")

    return 0


def cmd_create_team(args):
    """Create a new team."""
    settings = Settings()
    manager = WorkspaceManager(settings)

    team_name = args.team
    if not team_name:
        print("Error: --team is required", file=sys.stderr)
        return 1

    try:
        team_path = manager.create_team(team_name)
        print(f"Team created: {team_path}")
        return 0
    except Exception as e:
        print(f"Error creating team: {e}", file=sys.stderr)
        return 1


def cmd_create_project(args):
    """Create a new project."""
    settings = Settings()
    manager = WorkspaceManager(settings)

    team_name = args.team
    project_name = args.project

    if not team_name:
        print("Error: --team is required", file=sys.stderr)
        return 1

    if not project_name:
        print("Error: --project is required", file=sys.stderr)
        return 1

    try:
        project_path = manager.create_project(team_name, project_name)
        print(f"Project created: {project_path}")
        return 0
    except Exception as e:
        print(f"Error creating project: {e}", file=sys.stderr)
        return 1


def cmd_import_image(args):
    """Import an image into a project."""
    settings = Settings()
    manager = WorkspaceManager(settings)

    team_name = args.team
    project_name = args.project
    image_path = Path(args.path)

    if not team_name:
        print("Error: --team is required", file=sys.stderr)
        return 1

    if not project_name:
        print("Error: --project is required", file=sys.stderr)
        return 1

    if not image_path.exists():
        print(f"Error: Image file not found: {image_path}", file=sys.stderr)
        return 1

    try:
        # Ensure project exists
        project_path = manager.ensure_project_exists(team_name, project_name)

        # Load project state
        project_state = ProjectState.load(project_path)
        if not project_state:
            print("Error: Could not load project state", file=sys.stderr)
            return 1

        # Validate and repair project state
        repairs = validate_and_repair_project_state(project_state, project_path)
        if repairs:
            project_state.save(project_path)

        # Generate unique filename to avoid collisions
        original_filename = image_path.name
        base_name = image_path.stem
        extension = image_path.suffix
        unique_filename = original_filename

        dest_path = project_path / "source_uploads" / unique_filename
        counter = 1
        while dest_path.exists():
            unique_filename = f"{base_name}_{counter}{extension}"
            dest_path = project_path / "source_uploads" / unique_filename
            counter += 1

        # Copy image to source_uploads
        shutil.copy2(image_path, dest_path)

        # Create SourceImage record
        relative_path = f"source_uploads/{unique_filename}"
        source_image = SourceImage.create(unique_filename, relative_path)
        project_state.add_source_image(source_image)

        # Load image to create initial layer in working directory
        img = load_image(dest_path)
        layer_filename = f"{source_image.id}.png"
        layer_path = project_path / "working" / layer_filename
        save_png(img, layer_path)

        # Create base layer
        layer = Layer.create(
            name=f"Base: {unique_filename}",
            layer_type="raster",
            layer_path=f"working/{layer_filename}",
            source_image_id=source_image.id,
        )
        project_state.add_layer(layer)

        # Save updated project state
        project_state.save(project_path)

        print(f"Image imported: {dest_path}")
        print(f"Source image ID: {source_image.id}")
        print(f"Layer ID: {layer.id}")
        print(f"Project updated: {project_path / 'meta' / 'project.json'}")

        return 0
    except Exception as e:
        print(f"Error importing image: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


def cmd_color_replace(args):
    """Apply color replacement operation to a project."""
    settings = Settings()
    service = ProjectService(settings)

    team_name = args.team
    project_name = args.project
    layer_id = args.layer_id if hasattr(args, 'layer_id') and args.layer_id else None

    if not team_name or not project_name:
        print("Error: --team and --project are required", file=sys.stderr)
        return 1

    try:
        # Parse colors
        tolerance = args.tolerance
        preserve_alpha = args.preserve_alpha.lower() in ("true", "1", "yes")

        # Use service layer for color replace (with layer support)
        project_state = service.apply_color_replace_to_layer(
            team_name,
            project_name,
            args.target,
            args.new,
            tolerance,
            preserve_alpha,
            layer_id
        )

        # Parse for output display
        target_rgb = parse_color(args.target)
        new_rgb = parse_color(args.new)

        print(f"Color replacement applied:")
        print(f"  Target: {rgb_to_hex(*target_rgb)} {target_rgb}")
        print(f"  New: {rgb_to_hex(*new_rgb)} {new_rgb}")
        print(f"  Tolerance: {tolerance}")
        print(f"  Preserve alpha: {preserve_alpha}")
        if layer_id:
            print(f"  Applied to layer: {layer_id}")
        else:
            print(f"  Applied to active layer")
        print(f"Project state saved")

        return 0
    except Exception as e:
        print(f"Error applying color replace: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


def cmd_export(args):
    """Export project composite to exports directory."""
    settings = Settings()
    manager = WorkspaceManager(settings)

    team_name = args.team
    project_name = args.project
    export_name = args.name
    export_format = args.format

    if not team_name or not project_name:
        print("Error: --team and --project are required", file=sys.stderr)
        return 1

    if export_format != "png":
        print(f"Error: Only PNG format is supported in this milestone (got: {export_format})", file=sys.stderr)
        return 1

    try:
        # Get project path
        project_path = manager.get_project_path(team_name, project_name)
        if not project_path:
            print(f"Error: Project not found: {team_name} / {project_name}", file=sys.stderr)
            return 1

        # Load project state
        project_state = ProjectState.load(project_path)
        if not project_state:
            print("Error: Could not load project state", file=sys.stderr)
            return 1

        # Validate and repair project state
        repairs = validate_and_repair_project_state(project_state, project_path)
        if repairs:
            project_state.save(project_path)

        # Determine composite path
        if project_state.active_composite_path:
            composite_path = project_path / project_state.active_composite_path
        elif project_state.layers:
            # No composite yet, use base layer
            base_layer = project_state.get_base_layer()
            composite_path = project_path / base_layer.layer_path
        else:
            print("Error: Project has no images to export", file=sys.stderr)
            return 1

        if not composite_path.exists():
            print(f"Error: Composite image not found: {composite_path}", file=sys.stderr)
            return 1

        # Generate export filename
        if export_name:
            export_filename = f"{export_name}.{export_format}"
        else:
            from datetime import datetime
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            export_filename = f"{project_state.project_slug}_{timestamp}.{export_format}"

        # Copy composite to exports
        export_path = project_path / "exports" / export_filename
        export_path.parent.mkdir(exist_ok=True)

        # Load and save to ensure proper format
        img = load_image(composite_path)
        save_png(img, export_path)

        print(f"Export successful:")
        print(f"  Source: {composite_path.relative_to(project_path)}")
        print(f"  Output: {export_path}")
        print(f"  Format: PNG")
        print(f"  Size: {img.width}x{img.height}")

        return 0
    except Exception as e:
        print(f"Error exporting: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


def cmd_project_info(args):
    """Display project information."""
    settings = Settings()
    manager = WorkspaceManager(settings)

    team_name = args.team
    project_name = args.project

    if not team_name or not project_name:
        print("Error: --team and --project are required", file=sys.stderr)
        return 1

    try:
        # Get project path
        project_path = manager.get_project_path(team_name, project_name)
        if not project_path:
            print(f"Error: Project not found: {team_name} / {project_name}", file=sys.stderr)
            return 1

        # Load project state
        project_state = ProjectState.load(project_path)
        if not project_state:
            print("Error: Could not load project state", file=sys.stderr)
            return 1

        # Validate and repair project state
        repairs = validate_and_repair_project_state(project_state, project_path)
        if repairs:
            project_state.save(project_path)

        # Display project information
        print("=" * 60)
        print(f"Project: {project_state.project_name}")
        print(f"Team: {project_state.team_name}")
        print(f"Path: {project_path}")
        print("=" * 60)
        print(f"Created: {project_state.created_at}")
        print(f"Updated: {project_state.updated_at}")
        print()

        # Source images
        print(f"Source Images: {len(project_state.source_images)}")
        for img in project_state.source_images:
            print(f"  - {img.filename} (ID: {img.id[:8]}...)")
            print(f"    Path: {img.original_path}")
            print(f"    Imported: {img.imported_at}")
        print()

        # Layers
        print(f"Layers: {len(project_state.layers)}")
        for layer in project_state.layers:
            print(f"  - {layer.name} (ID: {layer.id[:8]}...)")
            print(f"    Type: {layer.type}")
            print(f"    Path: {layer.layer_path}")
            print(f"    Visible: {layer.visible}, Opacity: {layer.opacity}")
        print()

        # Operations
        print(f"Operations: {len(project_state.operations)}")
        for op in project_state.operations:
            print(f"  - {op.op_type} (ID: {op.id[:8]}...)")
            print(f"    Created: {op.created_at}")
            if op.note:
                print(f"    Note: {op.note}")
            print(f"    Output: {op.output_path}")
        print()

        # Composite
        if project_state.active_composite_path:
            composite_abs = project_path / project_state.active_composite_path
            if composite_abs.exists():
                from team_creator_studio.imaging.io import get_image_info
                info = get_image_info(composite_abs)
                print(f"Active Composite: {project_state.active_composite_path}")
                print(f"  Size: {info['width']}x{info['height']}")
                print(f"  Format: {info['format']}")
                print(f"  Mode: {info['mode']}")
            else:
                print(f"Active Composite: {project_state.active_composite_path} (missing)")
        else:
            print("Active Composite: None")

        print("=" * 60)

        return 0
    except Exception as e:
        print(f"Error displaying project info: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


def cmd_list_teams(args):
    """List all teams in the workspace."""
    settings = Settings()
    manager = WorkspaceManager(settings)

    try:
        teams_path = settings.get_teams_path()

        if not teams_path.exists():
            print("No teams found (workspace/teams/ does not exist)")
            return 0

        # List team directories
        team_dirs = [d for d in teams_path.iterdir() if d.is_dir()]

        if not team_dirs:
            print("No teams found")
            return 0

        print(f"Teams ({len(team_dirs)}):")
        print("-" * 60)

        for team_dir in sorted(team_dirs):
            team_slug = team_dir.name
            team_json = team_dir / "team.json"

            if team_json.exists():
                try:
                    with open(team_json, "r", encoding="utf-8") as f:
                        team_data = json.load(f)
                    team_name = team_data.get("name", team_slug)
                    created_at = team_data.get("created_at", "unknown")
                    print(f"  {team_slug}")
                    print(f"    Name: {team_name}")
                    print(f"    Created: {created_at}")
                except Exception as e:
                    print(f"  {team_slug} (error reading metadata: {e})")
            else:
                print(f"  {team_slug} (no metadata)")

        return 0
    except Exception as e:
        print(f"Error listing teams: {e}", file=sys.stderr)
        return 1


def cmd_list_projects(args):
    """List projects for a team."""
    settings = Settings()
    manager = WorkspaceManager(settings)

    team_name = args.team
    if not team_name:
        print("Error: --team is required", file=sys.stderr)
        return 1

    try:
        team_path = manager.get_team_path(team_name)
        if not team_path:
            print(f"Team not found: {team_name}", file=sys.stderr)
            return 1

        projects_path = team_path / "projects"
        if not projects_path.exists():
            print(f"No projects found for team: {team_name}")
            return 0

        # List project directories
        project_dirs = [d for d in projects_path.iterdir() if d.is_dir()]

        if not project_dirs:
            print(f"No projects found for team: {team_name}")
            return 0

        print(f"Projects for {team_name} ({len(project_dirs)}):")
        print("-" * 60)

        for project_dir in sorted(project_dirs):
            project_slug = project_dir.name
            project_json = project_dir / "meta" / "project.json"

            if project_json.exists():
                try:
                    project_state = ProjectState.load(project_dir)
                    if project_state:
                        print(f"  {project_slug}")
                        print(f"    Name: {project_state.project_name}")
                        print(f"    Created: {project_state.created_at}")
                        print(f"    Updated: {project_state.updated_at}")
                        print(f"    Operations: {len(project_state.operations)}")
                except Exception as e:
                    print(f"  {project_slug} (error reading metadata: {e})")
            else:
                print(f"  {project_slug} (no metadata)")

        return 0
    except Exception as e:
        print(f"Error listing projects: {e}", file=sys.stderr)
        return 1


def cmd_list_ops(args):
    """List operations for a project."""
    settings = Settings()
    manager = WorkspaceManager(settings)

    team_name = args.team
    project_name = args.project

    if not team_name or not project_name:
        print("Error: --team and --project are required", file=sys.stderr)
        return 1

    try:
        project_path = manager.get_project_path(team_name, project_name)
        if not project_path:
            print(f"Project not found: {team_name} / {project_name}", file=sys.stderr)
            return 1

        project_state = ProjectState.load(project_path)
        if not project_state:
            print("Error: Could not load project state", file=sys.stderr)
            return 1

        # Validate and repair
        repairs = validate_and_repair_project_state(project_state, project_path)
        if repairs:
            project_state.save(project_path)

        if not project_state.operations:
            print("No operations in project history")
            return 0

        print(f"Operations for {project_name} ({len(project_state.operations)}):")
        print("=" * 80)
        print(f"{'Idx':<4} {'Active':<7} {'ID':<10} {'Type':<15} {'Created':<25} {'Details'}")
        print("-" * 80)

        for i, op in enumerate(project_state.operations):
            active_marker = "*" if i == project_state.active_op_index else ""
            op_id_short = op.id[:8]
            created = op.created_at[:19] if len(op.created_at) > 19 else op.created_at

            # Extract details based on op type
            details = ""
            if op.op_type == "color_replace":
                params = op.params
                target = params.get("target_hex", "?")
                new = params.get("new_hex", "?")
                tol = params.get("tolerance", 0)
                details = f"{target}→{new} (tol:{tol})"

            print(f"{i:<4} {active_marker:<7} {op_id_short:<10} {op.op_type:<15} {created:<25} {details}")

        print("=" * 80)
        print(f"Active operation index: {project_state.active_op_index}")

        return 0
    except Exception as e:
        print(f"Error listing operations: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


def cmd_undo(args):
    """Undo the last operation."""
    settings = Settings()
    manager = WorkspaceManager(settings)

    team_name = args.team
    project_name = args.project

    if not team_name or not project_name:
        print("Error: --team and --project are required", file=sys.stderr)
        return 1

    try:
        project_path = manager.get_project_path(team_name, project_name)
        if not project_path:
            print(f"Project not found: {team_name} / {project_name}", file=sys.stderr)
            return 1

        project_state = ProjectState.load(project_path)
        if not project_state:
            print("Error: Could not load project state", file=sys.stderr)
            return 1

        # Validate and repair
        validate_and_repair_project_state(project_state, project_path)

        # Try to undo
        if not project_state.can_undo():
            print("Nothing to undo (already at base state)")
            return 0

        old_index = project_state.active_op_index
        project_state.undo()

        # Re-render composite
        try:
            render_project(project_state, project_path)
        except Exception as e:
            print(f"Warning: Could not render composite: {e}", file=sys.stderr)

        # Save state
        project_state.save(project_path)

        if project_state.active_op_index == -1:
            print(f"Undo successful: Moved from operation {old_index} to base layer")
        else:
            active_op = project_state.operations[project_state.active_op_index]
            print(f"Undo successful: Moved from operation {old_index} to operation {project_state.active_op_index}")
            print(f"Active operation: {active_op.op_type} (ID: {active_op.id[:8]}...)")

        return 0
    except Exception as e:
        print(f"Error during undo: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


def cmd_redo(args):
    """Redo the next operation."""
    settings = Settings()
    manager = WorkspaceManager(settings)

    team_name = args.team
    project_name = args.project

    if not team_name or not project_name:
        print("Error: --team and --project are required", file=sys.stderr)
        return 1

    try:
        project_path = manager.get_project_path(team_name, project_name)
        if not project_path:
            print(f"Project not found: {team_name} / {project_name}", file=sys.stderr)
            return 1

        project_state = ProjectState.load(project_path)
        if not project_state:
            print("Error: Could not load project state", file=sys.stderr)
            return 1

        # Validate and repair
        validate_and_repair_project_state(project_state, project_path)

        # Try to redo
        if not project_state.can_redo():
            print("Nothing to redo (already at latest state)")
            return 0

        old_index = project_state.active_op_index
        project_state.redo()

        # Re-render composite
        try:
            render_project(project_state, project_path)
        except Exception as e:
            print(f"Warning: Could not render composite: {e}", file=sys.stderr)

        # Save state
        project_state.save(project_path)

        active_op = project_state.operations[project_state.active_op_index]
        print(f"Redo successful: Moved from operation {old_index} to operation {project_state.active_op_index}")
        print(f"Active operation: {active_op.op_type} (ID: {active_op.id[:8]}...)")

        return 0
    except Exception as e:
        print(f"Error during redo: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


def cmd_delete_op(args):
    """Delete a specific operation."""
    settings = Settings()
    manager = WorkspaceManager(settings)

    team_name = args.team
    project_name = args.project
    op_id = args.id

    if not team_name or not project_name or not op_id:
        print("Error: --team, --project, and --id are required", file=sys.stderr)
        return 1

    if len(op_id) < 6:
        print("Error: Operation ID must be at least 6 characters", file=sys.stderr)
        return 1

    try:
        project_path = manager.get_project_path(team_name, project_name)
        if not project_path:
            print(f"Project not found: {team_name} / {project_name}", file=sys.stderr)
            return 1

        project_state = ProjectState.load(project_path)
        if not project_state:
            print("Error: Could not load project state", file=sys.stderr)
            return 1

        # Validate and repair
        validate_and_repair_project_state(project_state, project_path)

        # Find operation
        result = project_state.get_operation_by_id(op_id)
        if not result:
            print(f"Operation not found: {op_id}", file=sys.stderr)
            return 1

        op_index, op = result

        # Confirm deletion
        print(f"Deleting operation {op_index}:")
        print(f"  ID: {op.id}")
        print(f"  Type: {op.op_type}")
        print(f"  Created: {op.created_at}")
        print(f"  Output: {op.output_path}")

        # Delete output file
        output_file = project_path / op.output_path
        if output_file.exists():
            try:
                # Safety check: ensure file is within project directory
                output_file.resolve().relative_to(project_path.resolve())
                output_file.unlink()
                print(f"  Deleted output file: {op.output_path}")
            except (ValueError, OSError) as e:
                print(f"  Warning: Could not delete output file: {e}")

        # Delete operation from state
        old_active_index = project_state.active_op_index
        project_state.delete_operation(op_index)

        # Re-render composite
        try:
            render_project(project_state, project_path)
            print(f"  Re-rendered composite")
        except Exception as e:
            print(f"  Warning: Could not render composite: {e}", file=sys.stderr)

        # Save state
        project_state.save(project_path)

        print(f"\nOperation deleted successfully")
        print(f"Active operation index changed: {old_active_index} → {project_state.active_op_index}")

        return 0
    except ValueError as e:
        # Ambiguous ID
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error deleting operation: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


def cmd_add_layer(args):
    """Add a new layer from an image file."""
    settings = Settings()
    service = ProjectService(settings)

    team_name = args.team
    project_name = args.project
    image_path = Path(args.path)
    layer_name = args.name if hasattr(args, 'name') and args.name else None

    if not team_name or not project_name:
        print("Error: --team and --project are required", file=sys.stderr)
        return 1

    if not image_path.exists():
        print(f"Error: Image file not found: {image_path}", file=sys.stderr)
        return 1

    try:
        # Add layer via service
        project_state = service.add_layer_from_image(
            team_name,
            project_name,
            image_path,
            layer_name
        )

        # Find the newly added layer (highest order)
        sorted_layers = project_state.get_sorted_layers()
        new_layer = sorted_layers[-1] if sorted_layers else None

        if new_layer:
            print(f"Layer added successfully:")
            print(f"  Name: {new_layer.name}")
            print(f"  ID: {new_layer.id}")
            print(f"  Order: {new_layer.order}")
            print(f"  Visible: {new_layer.visible}")
            print(f"  Opacity: {new_layer.opacity}")
            print(f"  Position: ({new_layer.x}, {new_layer.y})")

        return 0
    except Exception as e:
        print(f"Error adding layer: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


def cmd_layers(args):
    """List all layers in a project."""
    settings = Settings()
    manager = WorkspaceManager(settings)

    team_name = args.team
    project_name = args.project

    if not team_name or not project_name:
        print("Error: --team and --project are required", file=sys.stderr)
        return 1

    try:
        project_path = manager.get_project_path(team_name, project_name)
        if not project_path:
            print(f"Project not found: {team_name} / {project_name}", file=sys.stderr)
            return 1

        project_state = ProjectState.load(project_path)
        if not project_state:
            print("Error: Could not load project state", file=sys.stderr)
            return 1

        # Validate and repair
        repairs = validate_and_repair_project_state(project_state, project_path)
        if repairs:
            project_state.save(project_path)

        if not project_state.layers:
            print("No layers in project")
            return 0

        # Display layers (sorted by order, top to bottom)
        sorted_layers = project_state.get_sorted_layers()

        print(f"Layers for {project_name} ({len(sorted_layers)}):")
        print("=" * 100)
        print(f"{'Order':<6} {'ID':<10} {'Name':<30} {'Visible':<8} {'Opacity':<8} {'X':<6} {'Y':<6}")
        print("-" * 100)

        for layer in reversed(sorted_layers):  # Top to bottom
            id_short = layer.id[:8]
            visible_str = "Yes" if layer.visible else "No"
            opacity_str = f"{int(layer.opacity * 100)}%"

            print(f"{layer.order:<6} {id_short:<10} {layer.name:<30} {visible_str:<8} {opacity_str:<8} {layer.x:<6} {layer.y:<6}")

        print("=" * 100)

        return 0
    except Exception as e:
        print(f"Error listing layers: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


def cmd_set_layer(args):
    """Set layer properties."""
    settings = Settings()
    service = ProjectService(settings)

    team_name = args.team
    project_name = args.project
    layer_id = args.layer_id

    if not team_name or not project_name or not layer_id:
        print("Error: --team, --project, and --layer-id are required", file=sys.stderr)
        return 1

    try:
        # Check what properties to set
        has_changes = False

        # Set visibility
        if hasattr(args, 'visible') and args.visible is not None:
            visible = args.visible.lower() in ("true", "1", "yes")
            service.set_layer_visibility(team_name, project_name, layer_id, visible)
            print(f"Layer visibility set to: {visible}")
            has_changes = True

        # Set opacity
        if hasattr(args, 'opacity') and args.opacity is not None:
            opacity = float(args.opacity) / 100.0  # Convert from 0-100 to 0.0-1.0
            service.set_layer_opacity(team_name, project_name, layer_id, opacity)
            print(f"Layer opacity set to: {int(opacity * 100)}%")
            has_changes = True

        # Set position
        if (hasattr(args, 'x') and args.x is not None) and (hasattr(args, 'y') and args.y is not None):
            service.set_layer_position(team_name, project_name, layer_id, int(args.x), int(args.y))
            print(f"Layer position set to: ({args.x}, {args.y})")
            has_changes = True

        # Rename layer
        if hasattr(args, 'name') and args.name:
            service.rename_layer(team_name, project_name, layer_id, args.name)
            print(f"Layer renamed to: {args.name}")
            has_changes = True

        if not has_changes:
            print("No changes specified. Use --visible, --opacity, --x/--y, or --name", file=sys.stderr)
            return 1

        print("Layer properties updated successfully")
        return 0

    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error setting layer properties: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


def cmd_move_layer(args):
    """Move layer up or down in the layer stack."""
    settings = Settings()
    service = ProjectService(settings)

    team_name = args.team
    project_name = args.project
    layer_id = args.layer_id
    direction = args.direction

    if not team_name or not project_name or not layer_id or not direction:
        print("Error: --team, --project, --layer-id, and --direction are required", file=sys.stderr)
        return 1

    if direction not in ("up", "down"):
        print("Error: --direction must be 'up' or 'down'", file=sys.stderr)
        return 1

    try:
        project_state = service.move_layer(team_name, project_name, layer_id, direction)
        print(f"Layer moved {direction} successfully")
        return 0

    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error moving layer: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


def cmd_delete_layer(args):
    """Delete a layer from the project."""
    settings = Settings()
    service = ProjectService(settings)

    team_name = args.team
    project_name = args.project
    layer_id = args.layer_id

    if not team_name or not project_name or not layer_id:
        print("Error: --team, --project, and --layer-id are required", file=sys.stderr)
        return 1

    try:
        project_state = service.delete_layer(team_name, project_name, layer_id)
        print(f"Layer deleted successfully")
        print(f"Remaining layers: {len(project_state.layers)}")
        return 0

    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error deleting layer: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


def cmd_gui(args):
    """Launch the GUI application."""
    try:
        from team_creator_studio.ui.app import launch_gui
        launch_gui()
        return 0
    except ImportError as e:
        print(f"Error: Could not load GUI module: {e}", file=sys.stderr)
        print("Make sure all dependencies are installed (Pillow, numpy)", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error launching GUI: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


def cmd_reset_project(args):
    """Reset project to initial state, keeping only source uploads."""
    settings = Settings()
    manager = WorkspaceManager(settings)

    team_name = args.team
    project_name = args.project

    if not team_name or not project_name:
        print("Error: --team and --project are required", file=sys.stderr)
        return 1

    try:
        project_path = manager.get_project_path(team_name, project_name)
        if not project_path:
            print(f"Project not found: {team_name} / {project_name}", file=sys.stderr)
            return 1

        project_state = ProjectState.load(project_path)
        if not project_state:
            print("Error: Could not load project state", file=sys.stderr)
            return 1

        print(f"Resetting project: {project_name}")
        print("=" * 60)
        print("This will delete:")
        print("  - All operation outputs (working/ops/)")
        print("  - Composite image (working/composite.png)")
        print("  - Working layers (working/*.png)")
        print("  - Layer files (layers/)")
        print("  - Mask files (masks/)")
        print("  - History files (history/)")
        print()
        print("This will preserve:")
        print("  - Source uploads (source_uploads/)")
        print("  - Project metadata structure")
        print()

        # Count files to delete
        files_to_delete = []
        dirs_to_clear = ["working", "layers", "masks", "history"]

        for dir_name in dirs_to_clear:
            dir_path = project_path / dir_name
            if dir_path.exists():
                for item in dir_path.rglob("*"):
                    if item.is_file():
                        files_to_delete.append(item)

        print(f"Files to delete: {len(files_to_delete)}")

        # Confirmation
        response = input("Proceed with reset? (yes/no): ").strip().lower()
        if response not in ("yes", "y"):
            print("Reset cancelled")
            return 0

        # Delete files
        deleted_count = 0
        for file_path in files_to_delete:
            try:
                file_path.unlink()
                deleted_count += 1
            except Exception as e:
                print(f"Warning: Could not delete {file_path}: {e}")

        # Recreate empty directories
        for dir_name in dirs_to_clear:
            dir_path = project_path / dir_name
            dir_path.mkdir(parents=True, exist_ok=True)

        # Reset project state
        project_state.operations = []
        project_state.active_op_index = -1
        project_state.active_composite_path = None
        project_state.update_timestamp()

        # Save state
        project_state.save(project_path)

        print()
        print("Reset complete:")
        print(f"  Files deleted: {deleted_count}")
        print(f"  Operations cleared: all")
        print(f"  Active index reset: -1")
        print(f"  Source uploads preserved: {len(project_state.source_images)}")

        return 0
    except Exception as e:
        print(f"Error resetting project: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="team_creator_studio",
        description="Team Creation Studio - Manage teams and projects for game asset creation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # where command
    parser_where = subparsers.add_parser(
        "where",
        help="Print the workspace path and confirm it exists"
    )
    parser_where.set_defaults(func=cmd_where)

    # create-team command
    parser_create_team = subparsers.add_parser(
        "create-team",
        help="Create a new team"
    )
    parser_create_team.add_argument(
        "--team",
        required=True,
        help="Team name (will be slugified)"
    )
    parser_create_team.set_defaults(func=cmd_create_team)

    # create-project command
    parser_create_project = subparsers.add_parser(
        "create-project",
        help="Create a new project within a team"
    )
    parser_create_project.add_argument(
        "--team",
        required=True,
        help="Team name (will be slugified, auto-creates if needed)"
    )
    parser_create_project.add_argument(
        "--project",
        required=True,
        help="Project name (will be slugified)"
    )
    parser_create_project.set_defaults(func=cmd_create_project)

    # import-image command
    parser_import = subparsers.add_parser(
        "import-image",
        help="Import an image into a project"
    )
    parser_import.add_argument(
        "--team",
        required=True,
        help="Team name"
    )
    parser_import.add_argument(
        "--project",
        required=True,
        help="Project name"
    )
    parser_import.add_argument(
        "--path",
        required=True,
        help="Path to image file"
    )
    parser_import.set_defaults(func=cmd_import_image)

    # color-replace command
    parser_color_replace = subparsers.add_parser(
        "color-replace",
        help="Apply color replacement to project"
    )
    parser_color_replace.add_argument(
        "--team",
        required=True,
        help="Team name"
    )
    parser_color_replace.add_argument(
        "--project",
        required=True,
        help="Project name"
    )
    parser_color_replace.add_argument(
        "--target",
        required=True,
        help="Target color to replace (hex or R,G,B)"
    )
    parser_color_replace.add_argument(
        "--new",
        required=True,
        help="New replacement color (hex or R,G,B)"
    )
    parser_color_replace.add_argument(
        "--tolerance",
        type=int,
        default=0,
        help="Color matching tolerance (0-255, default: 0)"
    )
    parser_color_replace.add_argument(
        "--preserve-alpha",
        default="true",
        help="Preserve alpha channel (true/false, default: true)"
    )
    parser_color_replace.add_argument(
        "--layer-id",
        help="Layer ID or prefix to apply operation to (optional, defaults to active layer)"
    )
    parser_color_replace.set_defaults(func=cmd_color_replace)

    # export command
    parser_export = subparsers.add_parser(
        "export",
        help="Export project to exports directory"
    )
    parser_export.add_argument(
        "--team",
        required=True,
        help="Team name"
    )
    parser_export.add_argument(
        "--project",
        required=True,
        help="Project name"
    )
    parser_export.add_argument(
        "--name",
        help="Export filename (without extension, optional)"
    )
    parser_export.add_argument(
        "--format",
        default="png",
        help="Export format (only png supported for now)"
    )
    parser_export.set_defaults(func=cmd_export)

    # project-info command
    parser_info = subparsers.add_parser(
        "project-info",
        help="Display project information"
    )
    parser_info.add_argument(
        "--team",
        required=True,
        help="Team name"
    )
    parser_info.add_argument(
        "--project",
        required=True,
        help="Project name"
    )
    parser_info.set_defaults(func=cmd_project_info)

    # list-teams command
    parser_list_teams = subparsers.add_parser(
        "list-teams",
        help="List all teams in workspace"
    )
    parser_list_teams.set_defaults(func=cmd_list_teams)

    # list-projects command
    parser_list_projects = subparsers.add_parser(
        "list-projects",
        help="List projects for a team"
    )
    parser_list_projects.add_argument(
        "--team",
        required=True,
        help="Team name"
    )
    parser_list_projects.set_defaults(func=cmd_list_projects)

    # list-ops command
    parser_list_ops = subparsers.add_parser(
        "list-ops",
        help="List operations for a project"
    )
    parser_list_ops.add_argument(
        "--team",
        required=True,
        help="Team name"
    )
    parser_list_ops.add_argument(
        "--project",
        required=True,
        help="Project name"
    )
    parser_list_ops.set_defaults(func=cmd_list_ops)

    # undo command
    parser_undo = subparsers.add_parser(
        "undo",
        help="Undo the last operation"
    )
    parser_undo.add_argument(
        "--team",
        required=True,
        help="Team name"
    )
    parser_undo.add_argument(
        "--project",
        required=True,
        help="Project name"
    )
    parser_undo.set_defaults(func=cmd_undo)

    # redo command
    parser_redo = subparsers.add_parser(
        "redo",
        help="Redo the next operation"
    )
    parser_redo.add_argument(
        "--team",
        required=True,
        help="Team name"
    )
    parser_redo.add_argument(
        "--project",
        required=True,
        help="Project name"
    )
    parser_redo.set_defaults(func=cmd_redo)

    # delete-op command
    parser_delete_op = subparsers.add_parser(
        "delete-op",
        help="Delete a specific operation"
    )
    parser_delete_op.add_argument(
        "--team",
        required=True,
        help="Team name"
    )
    parser_delete_op.add_argument(
        "--project",
        required=True,
        help="Project name"
    )
    parser_delete_op.add_argument(
        "--id",
        required=True,
        help="Operation ID or unique prefix (>=6 chars)"
    )
    parser_delete_op.set_defaults(func=cmd_delete_op)

    # reset-project command
    parser_reset = subparsers.add_parser(
        "reset-project",
        help="Reset project to initial state (preserves source uploads)"
    )
    parser_reset.add_argument(
        "--team",
        required=True,
        help="Team name"
    )
    parser_reset.add_argument(
        "--project",
        required=True,
        help="Project name"
    )
    parser_reset.set_defaults(func=cmd_reset_project)

    # add-layer command
    parser_add_layer = subparsers.add_parser(
        "add-layer",
        help="Add a new layer from an image file"
    )
    parser_add_layer.add_argument(
        "--team",
        required=True,
        help="Team name"
    )
    parser_add_layer.add_argument(
        "--project",
        required=True,
        help="Project name"
    )
    parser_add_layer.add_argument(
        "--path",
        required=True,
        help="Path to image file"
    )
    parser_add_layer.add_argument(
        "--name",
        help="Layer name (optional)"
    )
    parser_add_layer.set_defaults(func=cmd_add_layer)

    # layers command
    parser_layers = subparsers.add_parser(
        "layers",
        help="List all layers in a project"
    )
    parser_layers.add_argument(
        "--team",
        required=True,
        help="Team name"
    )
    parser_layers.add_argument(
        "--project",
        required=True,
        help="Project name"
    )
    parser_layers.set_defaults(func=cmd_layers)

    # set-layer command
    parser_set_layer = subparsers.add_parser(
        "set-layer",
        help="Set layer properties"
    )
    parser_set_layer.add_argument(
        "--team",
        required=True,
        help="Team name"
    )
    parser_set_layer.add_argument(
        "--project",
        required=True,
        help="Project name"
    )
    parser_set_layer.add_argument(
        "--layer-id",
        required=True,
        help="Layer ID or unique prefix (>=6 chars)"
    )
    parser_set_layer.add_argument(
        "--visible",
        help="Set visibility (true/false)"
    )
    parser_set_layer.add_argument(
        "--opacity",
        type=int,
        help="Set opacity (0-100)"
    )
    parser_set_layer.add_argument(
        "--x",
        type=int,
        help="Set X position"
    )
    parser_set_layer.add_argument(
        "--y",
        type=int,
        help="Set Y position"
    )
    parser_set_layer.add_argument(
        "--name",
        help="Rename layer"
    )
    parser_set_layer.set_defaults(func=cmd_set_layer)

    # move-layer command
    parser_move_layer = subparsers.add_parser(
        "move-layer",
        help="Move layer up or down in the layer stack"
    )
    parser_move_layer.add_argument(
        "--team",
        required=True,
        help="Team name"
    )
    parser_move_layer.add_argument(
        "--project",
        required=True,
        help="Project name"
    )
    parser_move_layer.add_argument(
        "--layer-id",
        required=True,
        help="Layer ID or unique prefix (>=6 chars)"
    )
    parser_move_layer.add_argument(
        "--direction",
        required=True,
        choices=["up", "down"],
        help="Direction to move (up or down)"
    )
    parser_move_layer.set_defaults(func=cmd_move_layer)

    # delete-layer command
    parser_delete_layer = subparsers.add_parser(
        "delete-layer",
        help="Delete a layer from the project"
    )
    parser_delete_layer.add_argument(
        "--team",
        required=True,
        help="Team name"
    )
    parser_delete_layer.add_argument(
        "--project",
        required=True,
        help="Project name"
    )
    parser_delete_layer.add_argument(
        "--layer-id",
        required=True,
        help="Layer ID or unique prefix (>=6 chars)"
    )
    parser_delete_layer.set_defaults(func=cmd_delete_layer)

    # gui command
    parser_gui = subparsers.add_parser(
        "gui",
        help="Launch the GUI application"
    )
    parser_gui.set_defaults(func=cmd_gui)

    # Parse arguments
    args = parser.parse_args()

    # If no command specified, show help
    if not args.command:
        parser.print_help()
        return 0

    # Execute command
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
