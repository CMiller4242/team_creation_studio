"""
Configuration settings for Team Creation Studio.

Manages workspace paths and application settings.
"""

import os
from pathlib import Path


class Settings:
    """Application settings manager."""

    def __init__(self):
        """Initialize settings with default values."""
        self._workspace_path = None

    def get_workspace_path(self) -> Path:
        """
        Get the workspace directory path.

        Returns:
            Path: Absolute path to the workspace directory

        The workspace path is determined in the following order:
        1. TEAM_CREATOR_WORKSPACE environment variable
        2. workspace/ subdirectory in the project root
        """
        if self._workspace_path is not None:
            return self._workspace_path

        # Check environment variable
        env_workspace = os.environ.get("TEAM_CREATOR_WORKSPACE")
        if env_workspace:
            self._workspace_path = Path(env_workspace).resolve()
            return self._workspace_path

        # Default to workspace/ in project root
        # Find the project root by looking for pyproject.toml or src/ directory
        current = Path(__file__).resolve()
        project_root = self._find_project_root(current)

        self._workspace_path = project_root / "workspace"
        return self._workspace_path

    def _find_project_root(self, start_path: Path) -> Path:
        """
        Find the project root directory.

        Args:
            start_path: Starting path to search from

        Returns:
            Path: Project root directory
        """
        current = start_path
        for _ in range(10):  # Limit search depth
            # Check for project markers
            if (current / "pyproject.toml").exists():
                return current
            if (current / "src").exists() and (current / "workspace").exists():
                return current

            parent = current.parent
            if parent == current:  # Reached filesystem root
                break
            current = parent

        # Fallback: assume current working directory
        return Path.cwd()

    def get_teams_path(self) -> Path:
        """Get the teams directory path."""
        return self.get_workspace_path() / "teams"

    def get_templates_path(self) -> Path:
        """Get the templates directory path."""
        return self.get_workspace_path() / "templates"
