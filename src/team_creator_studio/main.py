"""
Main CLI entry point for Team Creation Studio.

Provides commands for managing teams and projects within the workspace.
"""

import argparse
import sys
from pathlib import Path

from team_creator_studio.config.settings import Settings
from team_creator_studio.storage.workspace import WorkspaceManager


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
