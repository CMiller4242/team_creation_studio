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
from team_creator_studio.imaging.io import load_image, save_png
from team_creator_studio.imaging.color import parse_color, rgb_to_hex
from team_creator_studio.ops.color_replace import apply_color_replace


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
    manager = WorkspaceManager(settings)

    team_name = args.team
    project_name = args.project

    if not team_name or not project_name:
        print("Error: --team and --project are required", file=sys.stderr)
        return 1

    try:
        # Parse colors
        target_rgb = parse_color(args.target)
        new_rgb = parse_color(args.new)
        tolerance = args.tolerance
        preserve_alpha = args.preserve_alpha.lower() in ("true", "1", "yes")

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

        # Check if project has any layers
        if not project_state.layers:
            print("Error: Project has no layers. Import an image first.", file=sys.stderr)
            print("Use: python -m team_creator_studio import-image --team \"...\" --project \"...\" --path \"...\"")
            return 1

        # Determine input image
        base_layer = project_state.get_base_layer()
        if project_state.operations:
            # Use last operation output
            last_op = project_state.operations[-1]
            input_path = project_path / last_op.output_path
            input_layer_id = last_op.input_layer_id
        else:
            # Use base layer
            input_path = project_path / base_layer.layer_path
            input_layer_id = base_layer.id

        if not input_path.exists():
            print(f"Error: Input image not found: {input_path}", file=sys.stderr)
            return 1

        # Load input image
        input_image = load_image(input_path)

        # Apply color replace operation
        result_image = apply_color_replace(
            input_image,
            target_rgb,
            new_rgb,
            tolerance,
            preserve_alpha,
        )

        # Save operation output
        op_id = str(uuid.uuid4())
        output_filename = f"{op_id}_color_replace.png"
        output_path = project_path / "working" / "ops"
        output_path.mkdir(exist_ok=True)
        output_file = output_path / output_filename
        save_png(result_image, output_file)

        # Create operation record
        operation = OperationRecord.create(
            op_type="color_replace",
            params={
                "target_rgb": list(target_rgb),
                "target_hex": rgb_to_hex(*target_rgb),
                "new_rgb": list(new_rgb),
                "new_hex": rgb_to_hex(*new_rgb),
                "tolerance": tolerance,
                "preserve_alpha": preserve_alpha,
            },
            input_layer_id=input_layer_id,
            output_path=f"working/ops/{output_filename}",
            note=f"Replace {rgb_to_hex(*target_rgb)} with {rgb_to_hex(*new_rgb)} (tolerance: {tolerance})",
        )
        project_state.add_operation(operation)

        # Render composite
        composite_rel_path = render_project(project_state, project_path)

        # Save updated project state
        project_state.save(project_path)

        print(f"Color replacement applied:")
        print(f"  Target: {rgb_to_hex(*target_rgb)} {target_rgb}")
        print(f"  New: {rgb_to_hex(*new_rgb)} {new_rgb}")
        print(f"  Tolerance: {tolerance}")
        print(f"  Preserve alpha: {preserve_alpha}")
        print(f"Operation output: {output_file}")
        print(f"Composite updated: {project_path / composite_rel_path}")
        print(f"Project state saved: {project_path / 'meta' / 'project.json'}")

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
