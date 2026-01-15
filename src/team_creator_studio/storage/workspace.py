"""
Workspace management for Team Creation Studio.

Handles creation and organization of teams and projects within the workspace.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from team_creator_studio.config.settings import Settings
from team_creator_studio.utils.slugify import slugify


class WorkspaceManager:
    """Manages workspace structure and operations."""

    def __init__(self, settings: Settings):
        """
        Initialize workspace manager.

        Args:
            settings: Settings instance with workspace configuration
        """
        self.settings = settings
        self.workspace_path = settings.get_workspace_path()
        self.teams_path = settings.get_teams_path()

    def create_team(self, team_name: str) -> Path:
        """
        Create a new team directory with metadata.

        Args:
            team_name: Human-readable team name

        Returns:
            Path: Path to created team directory

        Creates:
            - workspace/teams/<team-slug>/
            - workspace/teams/<team-slug>/team.json
            - workspace/teams/<team-slug>/projects/
        """
        team_slug = slugify(team_name)
        if not team_slug:
            raise ValueError(f"Invalid team name: '{team_name}'")

        team_path = self.teams_path / team_slug

        # Create team directory
        team_path.mkdir(parents=True, exist_ok=True)

        # Create projects subdirectory
        projects_path = team_path / "projects"
        projects_path.mkdir(exist_ok=True)

        # Write team metadata
        team_json_path = team_path / "team.json"
        team_metadata = {
            "name": team_name,
            "slug": team_slug,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "description": "",
            "members": []
        }

        with open(team_json_path, "w", encoding="utf-8") as f:
            json.dump(team_metadata, f, indent=2, ensure_ascii=False)

        return team_path

    def create_project(self, team_name: str, project_name: str) -> Path:
        """
        Create a new project with full directory structure.

        Args:
            team_name: Human-readable team name (auto-creates if needed)
            project_name: Human-readable project name

        Returns:
            Path: Path to created project directory

        Creates:
            - Full project directory structure
            - meta/project.json with metadata
            - palettes/palette.json with initial palette
        """
        team_slug = slugify(team_name)
        project_slug = slugify(project_name)

        if not team_slug:
            raise ValueError(f"Invalid team name: '{team_name}'")
        if not project_slug:
            raise ValueError(f"Invalid project name: '{project_name}'")

        team_path = self.teams_path / team_slug

        # Create team if it doesn't exist
        if not team_path.exists():
            self.create_team(team_name)

        # Create project directory structure
        project_path = team_path / "projects" / project_slug
        project_path.mkdir(parents=True, exist_ok=True)

        # Create project subdirectories
        subdirs = [
            "source_uploads",
            "working",
            "layers",
            "masks",
            "exports",
            "meta",
            "palettes",
            "history"
        ]

        for subdir in subdirs:
            (project_path / subdir).mkdir(exist_ok=True)

        # Write project metadata
        self._write_project_metadata(project_path, team_name, project_name, team_slug, project_slug)

        # Write initial palette
        self._write_initial_palette(project_path)

        return project_path

    def _write_project_metadata(
        self,
        project_path: Path,
        team_name: str,
        project_name: str,
        team_slug: str,
        project_slug: str
    ) -> None:
        """
        Write project.json metadata file using ProjectState model.

        Args:
            project_path: Path to project directory
            team_name: Human-readable team name
            project_name: Human-readable project name
            team_slug: Team slug
            project_slug: Project slug
        """
        from team_creator_studio.core.models import ProjectState

        # Create new project state
        project_state = ProjectState.create_new(
            team_name, team_slug, project_name, project_slug
        )

        # Save to meta/project.json
        project_state.save(project_path)

    def _write_initial_palette(self, project_path: Path) -> None:
        """
        Write initial palette.json file.

        Args:
            project_path: Path to project directory
        """
        palette_path = project_path / "palettes" / "palette.json"

        initial_palette = {
            "id": "default",
            "name": "Default Palette",
            "created_at": datetime.utcnow().isoformat() + "Z",
            "colors": [
                {"name": "Black", "hex": "#000000", "rgb": [0, 0, 0]},
                {"name": "White", "hex": "#FFFFFF", "rgb": [255, 255, 255]},
                {"name": "Red", "hex": "#FF0000", "rgb": [255, 0, 0]},
                {"name": "Green", "hex": "#00FF00", "rgb": [0, 255, 0]},
                {"name": "Blue", "hex": "#0000FF", "rgb": [0, 0, 255]},
                {"name": "Yellow", "hex": "#FFFF00", "rgb": [255, 255, 0]},
                {"name": "Cyan", "hex": "#00FFFF", "rgb": [0, 255, 255]},
                {"name": "Magenta", "hex": "#FF00FF", "rgb": [255, 0, 255]}
            ]
        }

        with open(palette_path, "w", encoding="utf-8") as f:
            json.dump(initial_palette, f, indent=2, ensure_ascii=False)

    def get_team_path(self, team_name: str) -> Optional[Path]:
        """
        Get the path to a team directory.

        Args:
            team_name: Human-readable team name

        Returns:
            Optional[Path]: Path to team directory if it exists, None otherwise
        """
        team_slug = slugify(team_name)
        team_path = self.teams_path / team_slug

        if team_path.exists():
            return team_path
        return None

    def get_project_path(self, team_name: str, project_name: str) -> Optional[Path]:
        """
        Get the path to a project directory.

        Args:
            team_name: Human-readable team name
            project_name: Human-readable project name

        Returns:
            Optional[Path]: Path to project directory if it exists, None otherwise
        """
        team_slug = slugify(team_name)
        project_slug = slugify(project_name)

        project_path = self.teams_path / team_slug / "projects" / project_slug

        if project_path.exists():
            return project_path
        return None

    def ensure_project_exists(self, team_name: str, project_name: str) -> Path:
        """
        Ensure project exists, creating it if necessary.

        Args:
            team_name: Human-readable team name
            project_name: Human-readable project name

        Returns:
            Path: Path to project directory
        """
        project_path = self.get_project_path(team_name, project_name)

        if project_path is None:
            project_path = self.create_project(team_name, project_name)

        return project_path
