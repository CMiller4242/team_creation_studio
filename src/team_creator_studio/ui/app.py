"""
Main GUI application for Team Creation Studio.

Provides a Tkinter-based desktop interface for managing teams, projects,
and performing image editing operations.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from pathlib import Path
from typing import Optional

from team_creator_studio.config.settings import Settings
from team_creator_studio.core.services import ProjectService
from team_creator_studio.ui import theme
from team_creator_studio.ui.views.project_browser import ProjectBrowser
from team_creator_studio.ui.views.editor_view import EditorView


class TeamCreationStudioApp:
    """
    Main application controller.

    Manages the application window, coordinates between views, and
    handles all business logic by calling the service layer.
    """

    def __init__(self):
        """Initialize the application."""
        self.root = tk.Tk()
        self.root.title("Team Creation Studio")
        self.root.geometry(f"{theme.WINDOW_WIDTH}x{theme.WINDOW_HEIGHT}")
        self.root.minsize(theme.WINDOW_MIN_WIDTH, theme.WINDOW_MIN_HEIGHT)

        # Initialize services
        self.settings = Settings()
        self.service = ProjectService(self.settings)

        # Current state
        self.current_team_name = None
        self.current_project_name = None

        # Configure styles
        self._configure_styles()

        # Create UI
        self._create_ui()

        # Load initial data
        self._load_teams()

    def _configure_styles(self):
        """Configure ttk styles."""
        style = ttk.Style()

        # Try to use a modern theme if available
        available_themes = style.theme_names()
        if "clam" in available_themes:
            style.theme_use("clam")
        elif "alt" in available_themes:
            style.theme_use("alt")

    def _create_ui(self):
        """Create the main UI layout."""
        # Create main container with two panes
        main_container = ttk.PanedWindow(self.root, orient="horizontal")
        main_container.pack(fill="both", expand=True)

        # Left pane: Project browser
        self.browser = ProjectBrowser(
            main_container,
            on_project_selected=self._on_project_opened,
            on_new_team=self._on_new_team,
            on_new_project=self._on_new_project
        )
        main_container.add(self.browser, weight=0)

        # Configure browser width
        self.browser.configure(width=theme.LIST_WIDTH)

        # Right pane: Editor
        self.editor = EditorView(
            main_container,
            on_import=self._on_import_image,
            on_undo=self._on_undo,
            on_redo=self._on_redo,
            on_refresh=self._on_refresh,
            on_export=self._on_export,
            on_apply_color_replace=self._on_apply_color_replace
        )
        main_container.add(self.editor, weight=1)

        # Bind browser team selection to load projects
        self.browser.teams_listbox.bind("<<ListboxSelect>>", self._on_team_selected)

    def _load_teams(self):
        """Load and display all teams."""
        try:
            teams = self.service.get_all_teams()
            self.browser.set_teams(teams)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load teams: {e}")

    def _on_team_selected(self, event):
        """Handle team selection in browser."""
        team = self.browser.get_selected_team()
        if team:
            self._load_projects(team["name"])

    def _load_projects(self, team_name: str):
        """Load and display projects for a team."""
        try:
            projects = self.service.get_projects_for_team(team_name)
            self.browser.set_projects(projects)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load projects: {e}")

    def _on_new_team(self, team_name: str):
        """Handle new team creation."""
        try:
            self.editor.set_status("Creating team...")
            team_path = self.service.create_team(team_name)
            self.editor.set_status(f"Team created: {team_name}")

            # Reload teams list
            self._load_teams()

            messagebox.showinfo("Success", f"Team created successfully:\n{team_path}")
        except Exception as e:
            self.editor.set_status("", error=False)
            messagebox.showerror("Error", f"Failed to create team: {e}")

    def _on_new_project(self, team_name: str, project_name: str):
        """Handle new project creation."""
        try:
            self.editor.set_status("Creating project...")
            project_path = self.service.create_project(team_name, project_name)
            self.editor.set_status(f"Project created: {project_name}")

            # Reload projects list for current team
            team = self.browser.get_selected_team()
            if team:
                self._load_projects(team["name"])

            messagebox.showinfo("Success", f"Project created successfully:\n{project_path}")
        except Exception as e:
            self.editor.set_status("", error=False)
            messagebox.showerror("Error", f"Failed to create project: {e}")

    def _on_project_opened(self, team_name: str, project_name: str):
        """Handle project opened from browser."""
        try:
            self.editor.set_status("Loading project...")

            # Load project state
            result = self.service.load_project(team_name, project_name)
            if not result:
                messagebox.showerror("Error", f"Failed to load project: {team_name} / {project_name}")
                self.editor.set_status("", error=False)
                return

            project_state, project_path = result

            # Store current project
            self.current_team_name = team_name
            self.current_project_name = project_name

            # Update status
            self.editor.set_status(f"Project: {project_name} | Team: {team_name}")

            # Load and display composite image
            self._refresh_image()

        except Exception as e:
            self.editor.set_status("Error loading project", error=True)
            messagebox.showerror("Error", f"Failed to open project: {e}")

    def _on_import_image(self):
        """Handle import image button."""
        if not self.current_project_name or not self.current_team_name:
            messagebox.showwarning("No Project", "Please open a project first.")
            return

        # Open file dialog
        file_path = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.bmp *.gif"),
                ("PNG files", "*.png"),
                ("JPEG files", "*.jpg *.jpeg"),
                ("All files", "*.*")
            ]
        )

        if not file_path:
            return

        try:
            self.editor.set_status("Importing image...")

            # Import image via service
            source_image, layer = self.service.import_image(
                self.current_team_name,
                self.current_project_name,
                Path(file_path)
            )

            self.editor.set_status(f"Image imported: {source_image.filename}")

            # Refresh display
            self._refresh_image()

            messagebox.showinfo("Success", f"Image imported successfully:\n{source_image.filename}")

        except Exception as e:
            self.editor.set_status("Error importing image", error=True)
            messagebox.showerror("Error", f"Failed to import image: {e}")

    def _on_apply_color_replace(self, target: str, new: str, tolerance: int, preserve_alpha: bool):
        """Handle apply color replace."""
        if not self.current_project_name or not self.current_team_name:
            messagebox.showwarning("No Project", "Please open a project first.")
            return

        if not target or not new:
            messagebox.showwarning("Invalid Input", "Please enter both target and new colors.")
            return

        try:
            self.editor.set_status("Applying color replace...")

            # Apply operation via service
            operation = self.service.apply_color_replace_operation(
                self.current_team_name,
                self.current_project_name,
                target,
                new,
                tolerance,
                preserve_alpha
            )

            self.editor.set_status(f"Color replace applied (ID: {operation.id[:8]})")

            # Refresh display
            self._refresh_image()

            messagebox.showinfo("Success", "Color replacement applied successfully.")

        except ValueError as e:
            self.editor.set_status("Error applying color replace", error=True)
            messagebox.showerror("Error", str(e))
        except Exception as e:
            self.editor.set_status("Error applying color replace", error=True)
            messagebox.showerror("Error", f"Failed to apply color replace: {e}")

    def _on_undo(self):
        """Handle undo button."""
        if not self.current_project_name or not self.current_team_name:
            messagebox.showwarning("No Project", "Please open a project first.")
            return

        try:
            self.editor.set_status("Undoing...")

            # Undo via service
            result = self.service.undo_operation(
                self.current_team_name,
                self.current_project_name
            )

            if result:
                self.editor.set_status("Undo successful")
                self._refresh_image()
            else:
                self.editor.set_status("Nothing to undo")
                messagebox.showinfo("Info", "Nothing to undo (already at base state).")

        except Exception as e:
            self.editor.set_status("Error during undo", error=True)
            messagebox.showerror("Error", f"Failed to undo: {e}")

    def _on_redo(self):
        """Handle redo button."""
        if not self.current_project_name or not self.current_team_name:
            messagebox.showwarning("No Project", "Please open a project first.")
            return

        try:
            self.editor.set_status("Redoing...")

            # Redo via service
            result = self.service.redo_operation(
                self.current_team_name,
                self.current_project_name
            )

            if result:
                self.editor.set_status("Redo successful")
                self._refresh_image()
            else:
                self.editor.set_status("Nothing to redo")
                messagebox.showinfo("Info", "Nothing to redo (already at latest state).")

        except Exception as e:
            self.editor.set_status("Error during redo", error=True)
            messagebox.showerror("Error", f"Failed to redo: {e}")

    def _on_refresh(self):
        """Handle refresh button."""
        if not self.current_project_name or not self.current_team_name:
            messagebox.showwarning("No Project", "Please open a project first.")
            return

        self._refresh_image()

    def _refresh_image(self):
        """Refresh the displayed image."""
        if not self.current_project_name or not self.current_team_name:
            return

        try:
            # Get composite image path
            image_path = self.service.get_composite_image_path(
                self.current_team_name,
                self.current_project_name
            )

            if image_path:
                self.editor.set_image(str(image_path))
            else:
                self.editor.clear_image()
                self.editor.set_status("No image to display")

        except Exception as e:
            self.editor.set_status("Error refreshing image", error=True)
            messagebox.showerror("Error", f"Failed to refresh image: {e}")

    def _on_export(self):
        """Handle export button."""
        if not self.current_project_name or not self.current_team_name:
            messagebox.showwarning("No Project", "Please open a project first.")
            return

        # Ask for export name
        export_name = simpledialog.askstring(
            "Export",
            "Enter export filename (without extension):",
            parent=self.root
        )

        # Allow default name (None)
        if export_name == "":
            export_name = None

        try:
            self.editor.set_status("Exporting...")

            # Export via service
            export_path = self.service.export_project(
                self.current_team_name,
                self.current_project_name,
                export_name,
                "png"
            )

            self.editor.set_status(f"Exported to: {export_path.name}")

            messagebox.showinfo(
                "Export Successful",
                f"Image exported successfully:\n{export_path}"
            )

        except Exception as e:
            self.editor.set_status("Error exporting", error=True)
            messagebox.showerror("Error", f"Failed to export: {e}")

    def run(self):
        """Start the application main loop."""
        self.root.mainloop()


def launch_gui():
    """Launch the GUI application."""
    app = TeamCreationStudioApp()
    app.run()


if __name__ == "__main__":
    launch_gui()
