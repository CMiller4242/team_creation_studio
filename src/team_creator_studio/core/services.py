"""
Service layer for core operations.

This module provides reusable service functions that can be called by both
CLI and GUI interfaces. All business logic should be centralized here to
avoid duplication.
"""

import shutil
import uuid
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any

from team_creator_studio.config.settings import Settings
from team_creator_studio.storage.workspace import WorkspaceManager
from team_creator_studio.core.models import ProjectState, SourceImage, Layer, OperationRecord
from team_creator_studio.core.renderer import render_project
from team_creator_studio.core.validation import validate_and_repair_project_state
from team_creator_studio.imaging.io import load_image, save_png
from team_creator_studio.imaging.color import parse_color, rgb_to_hex
from team_creator_studio.ops.color_replace import apply_color_replace


class ProjectService:
    """Service for project operations."""

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or Settings()
        self.manager = WorkspaceManager(self.settings)

    def get_all_teams(self) -> List[Dict[str, Any]]:
        """Get all teams in the workspace."""
        import json

        teams_path = self.settings.get_teams_path()

        if not teams_path.exists():
            return []

        team_dirs = [d for d in teams_path.iterdir() if d.is_dir()]
        teams = []

        for team_dir in sorted(team_dirs):
            team_slug = team_dir.name
            team_json = team_dir / "team.json"

            if team_json.exists():
                try:
                    with open(team_json, "r", encoding="utf-8") as f:
                        team_data = json.load(f)
                    teams.append({
                        "slug": team_slug,
                        "name": team_data.get("name", team_slug),
                        "created_at": team_data.get("created_at", "unknown"),
                        "path": team_dir,
                    })
                except Exception:
                    teams.append({
                        "slug": team_slug,
                        "name": team_slug,
                        "created_at": "unknown",
                        "path": team_dir,
                    })
            else:
                teams.append({
                    "slug": team_slug,
                    "name": team_slug,
                    "created_at": "unknown",
                    "path": team_dir,
                })

        return teams

    def get_projects_for_team(self, team_name: str) -> List[Dict[str, Any]]:
        """Get all projects for a team."""
        team_path = self.manager.get_team_path(team_name)
        if not team_path:
            return []

        projects_path = team_path / "projects"
        if not projects_path.exists():
            return []

        project_dirs = [d for d in projects_path.iterdir() if d.is_dir()]
        projects = []

        for project_dir in sorted(project_dirs):
            project_slug = project_dir.name
            project_json = project_dir / "meta" / "project.json"

            if project_json.exists():
                try:
                    project_state = ProjectState.load(project_dir)
                    if project_state:
                        projects.append({
                            "slug": project_slug,
                            "name": project_state.project_name,
                            "created_at": project_state.created_at,
                            "updated_at": project_state.updated_at,
                            "operations_count": len(project_state.operations),
                            "path": project_dir,
                        })
                except Exception:
                    projects.append({
                        "slug": project_slug,
                        "name": project_slug,
                        "created_at": "unknown",
                        "updated_at": "unknown",
                        "operations_count": 0,
                        "path": project_dir,
                    })
            else:
                projects.append({
                    "slug": project_slug,
                    "name": project_slug,
                    "created_at": "unknown",
                    "updated_at": "unknown",
                    "operations_count": 0,
                    "path": project_dir,
                })

        return projects

    def create_team(self, team_name: str) -> Path:
        """Create a new team."""
        return self.manager.create_team(team_name)

    def create_project(self, team_name: str, project_name: str) -> Path:
        """Create a new project."""
        return self.manager.create_project(team_name, project_name)

    def load_project(self, team_name: str, project_name: str) -> Optional[Tuple[ProjectState, Path]]:
        """
        Load a project and return (project_state, project_path).
        Also runs validation and repairs if needed.
        Returns None if project not found or cannot be loaded.
        """
        project_path = self.manager.get_project_path(team_name, project_name)
        if not project_path:
            return None

        project_state = ProjectState.load(project_path)
        if not project_state:
            return None

        # Validate and repair
        repairs = validate_and_repair_project_state(project_state, project_path)
        if repairs:
            project_state.save(project_path)

        return project_state, project_path

    def import_image(
        self,
        team_name: str,
        project_name: str,
        image_path: Path
    ) -> Tuple[SourceImage, Layer]:
        """
        Import an image into a project.
        Returns (source_image, layer).
        Raises ValueError if validation fails.
        """
        if not image_path.exists():
            raise ValueError(f"Image file not found: {image_path}")

        # Ensure project exists
        project_path = self.manager.ensure_project_exists(team_name, project_name)

        # Load project state
        project_state = ProjectState.load(project_path)
        if not project_state:
            raise ValueError("Could not load project state")

        # Validate and repair
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

        return source_image, layer

    def apply_color_replace_operation(
        self,
        team_name: str,
        project_name: str,
        target_color: str,
        new_color: str,
        tolerance: int = 0,
        preserve_alpha: bool = True
    ) -> OperationRecord:
        """
        Apply color replacement operation.
        Returns the created operation record.
        Raises ValueError if validation fails.
        """
        # Parse colors
        target_rgb = parse_color(target_color)
        new_rgb = parse_color(new_color)

        # Get project
        project_path = self.manager.get_project_path(team_name, project_name)
        if not project_path:
            raise ValueError(f"Project not found: {team_name} / {project_name}")

        # Load project state
        project_state = ProjectState.load(project_path)
        if not project_state:
            raise ValueError("Could not load project state")

        # Validate and repair
        repairs = validate_and_repair_project_state(project_state, project_path)
        if repairs:
            project_state.save(project_path)

        # Check if project has any layers
        if not project_state.layers:
            raise ValueError("Project has no layers. Import an image first.")

        # Determine input image based on active_op_index
        base_layer = project_state.get_base_layer()
        if project_state.active_op_index >= 0:
            # Use active operation output
            active_op = project_state.operations[project_state.active_op_index]
            input_path = project_path / active_op.output_path
            input_layer_id = active_op.input_layer_id
        else:
            # Use base layer
            input_path = project_path / base_layer.layer_path
            input_layer_id = base_layer.id

        if not input_path.exists():
            raise ValueError(f"Input image not found: {input_path}")

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
        render_project(project_state, project_path)

        # Save updated project state
        project_state.save(project_path)

        return operation

    def undo_operation(self, team_name: str, project_name: str) -> bool:
        """
        Undo the last operation.
        Returns True if undo was performed, False if nothing to undo.
        Raises ValueError if project not found or cannot be loaded.
        """
        project_path = self.manager.get_project_path(team_name, project_name)
        if not project_path:
            raise ValueError(f"Project not found: {team_name} / {project_name}")

        project_state = ProjectState.load(project_path)
        if not project_state:
            raise ValueError("Could not load project state")

        # Validate and repair
        validate_and_repair_project_state(project_state, project_path)

        # Try to undo
        if not project_state.can_undo():
            return False

        project_state.undo()

        # Re-render composite
        render_project(project_state, project_path)

        # Save state
        project_state.save(project_path)

        return True

    def redo_operation(self, team_name: str, project_name: str) -> bool:
        """
        Redo the next operation.
        Returns True if redo was performed, False if nothing to redo.
        Raises ValueError if project not found or cannot be loaded.
        """
        project_path = self.manager.get_project_path(team_name, project_name)
        if not project_path:
            raise ValueError(f"Project not found: {team_name} / {project_name}")

        project_state = ProjectState.load(project_path)
        if not project_state:
            raise ValueError("Could not load project state")

        # Validate and repair
        validate_and_repair_project_state(project_state, project_path)

        # Try to redo
        if not project_state.can_redo():
            return False

        project_state.redo()

        # Re-render composite
        render_project(project_state, project_path)

        # Save state
        project_state.save(project_path)

        return True

    def export_project(
        self,
        team_name: str,
        project_name: str,
        export_name: Optional[str] = None,
        export_format: str = "png"
    ) -> Path:
        """
        Export project composite to exports directory.
        Returns the path to the exported file.
        Raises ValueError if validation fails.
        """
        if export_format != "png":
            raise ValueError(f"Only PNG format is supported (got: {export_format})")

        # Get project path
        project_path = self.manager.get_project_path(team_name, project_name)
        if not project_path:
            raise ValueError(f"Project not found: {team_name} / {project_name}")

        # Load project state
        project_state = ProjectState.load(project_path)
        if not project_state:
            raise ValueError("Could not load project state")

        # Validate and repair
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
            raise ValueError("Project has no images to export")

        if not composite_path.exists():
            raise ValueError(f"Composite image not found: {composite_path}")

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

        return export_path

    def get_composite_image_path(self, team_name: str, project_name: str) -> Optional[Path]:
        """
        Get the path to the current composite image for display.
        Returns None if no composite exists.
        """
        project_path = self.manager.get_project_path(team_name, project_name)
        if not project_path:
            return None

        project_state = ProjectState.load(project_path)
        if not project_state:
            return None

        # Validate and repair
        validate_and_repair_project_state(project_state, project_path)

        # Determine composite path
        if project_state.active_composite_path:
            composite_path = project_path / project_state.active_composite_path
            if composite_path.exists():
                return composite_path

        # Fall back to base layer if no composite
        if project_state.layers:
            base_layer = project_state.get_base_layer()
            layer_path = project_path / base_layer.layer_path
            if layer_path.exists():
                return layer_path

        return None
