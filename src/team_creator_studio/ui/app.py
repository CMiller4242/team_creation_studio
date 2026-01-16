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
from team_creator_studio.ui.views.layers_panel import LayersPanel


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
        self.selected_layer_id = None

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
        # Create main container with three panes (browser | editor | layers)
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

        # Center pane: Editor
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

        # Right pane: Layers panel
        self.layers_panel = LayersPanel(
            main_container,
            on_layer_selected=self._on_layer_selected,
            on_add_layer=self._on_add_layer,
            on_delete_layer=self._on_delete_layer,
            on_move_up=self._on_move_layer_up,
            on_move_down=self._on_move_layer_down,
            on_rename=self._on_rename_layer,
            on_opacity_changed=self._on_opacity_changed,
            on_position_changed=self._on_position_changed,
            on_visibility_toggled=self._on_visibility_toggled,
        )
        main_container.add(self.layers_panel, weight=0)

        # Configure layers panel width
        self.layers_panel.configure(width=300)

        # Disable layers panel until project is opened
        self.layers_panel.set_enabled(False)

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

            # Enable and populate layers panel
            self.layers_panel.set_enabled(True)
            sorted_layers = project_state.get_sorted_layers()
            self.layers_panel.set_layers(sorted_layers)

            # Select default layer (top-most visible or highest order)
            if sorted_layers:
                visible_layers = [l for l in sorted_layers if l.visible]
                if visible_layers:
                    default_layer = visible_layers[-1]  # Top-most visible
                else:
                    default_layer = sorted_layers[-1]  # Highest order

                self.selected_layer_id = default_layer.id
                self.layers_panel.selected_layer_id = default_layer.id
                self.layers_panel._update_properties_panel()

                # Update editor target layer
                self.editor.set_target_layer(default_layer.name)
            else:
                self.selected_layer_id = None
                self.editor.set_target_layer(None)

            # Load and display composite image
            self._refresh_image()

        except Exception as e:
            self.editor.set_status("Error loading project", error=True)
            messagebox.showerror("Error", f"Failed to open project: {e}")

    def _on_import_image(self):
        """Handle import image button (legacy - use Add Layer instead)."""
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

            # Refresh display and layers
            self._refresh_ui()

            messagebox.showinfo("Success", f"Image imported successfully:\n{source_image.filename}")

        except Exception as e:
            self.editor.set_status("Error importing image", error=True)
            messagebox.showerror("Error", f"Failed to import image: {e}")

    def _on_apply_color_replace(self, target: str, new: str, tolerance: int, preserve_alpha: bool):
        """Handle apply color replace."""
        if not self.current_project_name or not self.current_team_name:
            messagebox.showwarning("No Project", "Please open a project first.")
            return

        if not self.selected_layer_id:
            messagebox.showwarning("No Layer Selected", "Please select a layer first.")
            return

        if not target or not new:
            messagebox.showwarning("Invalid Input", "Please enter both target and new colors.")
            return

        try:
            self.editor.set_status("Applying color replace...")

            # Apply operation to selected layer via service
            project_state = self.service.apply_color_replace_to_layer(
                self.current_team_name,
                self.current_project_name,
                target,
                new,
                tolerance,
                preserve_alpha,
                self.selected_layer_id
            )

            self.editor.set_status(f"Color replace applied to layer")

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

    # Layer operation callbacks

    def _on_layer_selected(self, layer_id: str):
        """Handle layer selection."""
        self.selected_layer_id = layer_id

        # Update editor target layer label
        try:
            result = self.service.load_project(self.current_team_name, self.current_project_name)
            if result:
                project_state, _ = result
                layer = project_state.get_layer_by_id(layer_id)
                if layer:
                    self.editor.set_target_layer(layer.name)
                else:
                    self.editor.set_target_layer(None)
        except Exception:
            pass

    def _on_add_layer(self):
        """Handle Add Layer button."""
        if not self.current_project_name or not self.current_team_name:
            messagebox.showwarning("No Project", "Please open a project first.")
            return

        # Open file dialog
        file_path = filedialog.askopenfilename(
            title="Select Image for New Layer",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.bmp *.gif"),
                ("PNG files", "*.png"),
                ("JPEG files", "*.jpg *.jpeg"),
                ("All files", "*.*")
            ]
        )

        if not file_path:
            return

        # Ask for layer name
        layer_name = simpledialog.askstring(
            "Layer Name",
            "Enter layer name (leave empty for default):",
            parent=self.root
        )

        if layer_name == "":
            layer_name = None

        try:
            self.editor.set_status("Adding layer...")

            # Add layer via service
            project_state = self.service.add_layer_from_image(
                self.current_team_name,
                self.current_project_name,
                Path(file_path),
                layer_name
            )

            self.editor.set_status("Layer added successfully")

            # Refresh UI
            self._refresh_ui()

            messagebox.showinfo("Success", "Layer added successfully.")

        except Exception as e:
            self.editor.set_status("Error adding layer", error=True)
            messagebox.showerror("Error", f"Failed to add layer: {e}")

    def _on_delete_layer(self, layer_id: str):
        """Handle Delete Layer button."""
        if not self.current_project_name or not self.current_team_name:
            return

        # Confirm deletion
        confirm = messagebox.askyesno(
            "Confirm Delete",
            "Are you sure you want to delete this layer?\nThis action cannot be undone."
        )

        if not confirm:
            return

        try:
            self.editor.set_status("Deleting layer...")

            # Delete layer via service
            project_state = self.service.delete_layer(
                self.current_team_name,
                self.current_project_name,
                layer_id
            )

            self.editor.set_status("Layer deleted successfully")

            # Refresh UI
            self._refresh_ui()

            messagebox.showinfo("Success", "Layer deleted successfully.")

        except ValueError as e:
            self.editor.set_status("Error deleting layer", error=True)
            messagebox.showerror("Error", str(e))
        except Exception as e:
            self.editor.set_status("Error deleting layer", error=True)
            messagebox.showerror("Error", f"Failed to delete layer: {e}")

    def _on_move_layer_up(self, layer_id: str):
        """Handle Move Up button."""
        if not self.current_project_name or not self.current_team_name:
            return

        try:
            self.editor.set_status("Moving layer up...")

            # Move layer via service
            project_state = self.service.move_layer(
                self.current_team_name,
                self.current_project_name,
                layer_id,
                "up"
            )

            self.editor.set_status("Layer moved up")

            # Refresh UI
            self._refresh_ui()

        except ValueError as e:
            self.editor.set_status("Cannot move layer", error=True)
            messagebox.showwarning("Info", str(e))
        except Exception as e:
            self.editor.set_status("Error moving layer", error=True)
            messagebox.showerror("Error", f"Failed to move layer: {e}")

    def _on_move_layer_down(self, layer_id: str):
        """Handle Move Down button."""
        if not self.current_project_name or not self.current_team_name:
            return

        try:
            self.editor.set_status("Moving layer down...")

            # Move layer via service
            project_state = self.service.move_layer(
                self.current_team_name,
                self.current_project_name,
                layer_id,
                "down"
            )

            self.editor.set_status("Layer moved down")

            # Refresh UI
            self._refresh_ui()

        except ValueError as e:
            self.editor.set_status("Cannot move layer", error=True)
            messagebox.showwarning("Info", str(e))
        except Exception as e:
            self.editor.set_status("Error moving layer", error=True)
            messagebox.showerror("Error", f"Failed to move layer: {e}")

    def _on_rename_layer(self, layer_id: str, new_name: str):
        """Handle Rename button."""
        if not self.current_project_name or not self.current_team_name:
            return

        try:
            self.editor.set_status("Renaming layer...")

            # Rename layer via service
            project_state = self.service.rename_layer(
                self.current_team_name,
                self.current_project_name,
                layer_id,
                new_name
            )

            self.editor.set_status("Layer renamed successfully")

            # Refresh layers panel (no re-render needed)
            result = self.service.load_project(self.current_team_name, self.current_project_name)
            if result:
                project_state, _ = result
                sorted_layers = project_state.get_sorted_layers()
                self.layers_panel.set_layers(sorted_layers)

                # Update editor target layer if this is the selected layer
                if layer_id == self.selected_layer_id:
                    self.editor.set_target_layer(new_name)

        except Exception as e:
            self.editor.set_status("Error renaming layer", error=True)
            messagebox.showerror("Error", f"Failed to rename layer: {e}")

    def _on_opacity_changed(self, layer_id: str, opacity: float):
        """Handle Apply Opacity button."""
        if not self.current_project_name or not self.current_team_name:
            return

        try:
            self.editor.set_status("Setting layer opacity...")

            # Set opacity via service
            project_state = self.service.set_layer_opacity(
                self.current_team_name,
                self.current_project_name,
                layer_id,
                opacity
            )

            self.editor.set_status("Layer opacity updated")

            # Refresh image only (no need to reload layers panel)
            self._refresh_image()

        except Exception as e:
            self.editor.set_status("Error setting opacity", error=True)
            messagebox.showerror("Error", f"Failed to set opacity: {e}")

    def _on_position_changed(self, layer_id: str, x: int, y: int):
        """Handle Apply Position button."""
        if not self.current_project_name or not self.current_team_name:
            return

        try:
            self.editor.set_status("Setting layer position...")

            # Set position via service
            project_state = self.service.set_layer_position(
                self.current_team_name,
                self.current_project_name,
                layer_id,
                x,
                y
            )

            self.editor.set_status("Layer position updated")

            # Refresh image only (no need to reload layers panel)
            self._refresh_image()

        except Exception as e:
            self.editor.set_status("Error setting position", error=True)
            messagebox.showerror("Error", f"Failed to set position: {e}")

    def _on_visibility_toggled(self, layer_id: str, visible: bool):
        """Handle visibility checkbox toggle."""
        if not self.current_project_name or not self.current_team_name:
            return

        try:
            # Set visibility via service
            project_state = self.service.set_layer_visibility(
                self.current_team_name,
                self.current_project_name,
                layer_id,
                visible
            )

            # Refresh image only (no need to reload layers panel)
            self._refresh_image()

        except Exception as e:
            self.editor.set_status("Error toggling visibility", error=True)
            messagebox.showerror("Error", f"Failed to toggle visibility: {e}")

    def _refresh_ui(self):
        """Refresh both image display and layers panel."""
        if not self.current_project_name or not self.current_team_name:
            return

        try:
            # Reload project state
            result = self.service.load_project(self.current_team_name, self.current_project_name)
            if not result:
                return

            project_state, _ = result

            # Refresh layers panel
            sorted_layers = project_state.get_sorted_layers()
            self.layers_panel.set_layers(sorted_layers)

            # Refresh image
            self._refresh_image()

            # Re-select layer if it still exists
            if self.selected_layer_id:
                layer = project_state.get_layer_by_id(self.selected_layer_id)
                if layer:
                    self.layers_panel.selected_layer_id = self.selected_layer_id
                    self.layers_panel._update_properties_panel()
                    self.editor.set_target_layer(layer.name)
                else:
                    # Layer was deleted, select default
                    if sorted_layers:
                        visible_layers = [l for l in sorted_layers if l.visible]
                        if visible_layers:
                            default_layer = visible_layers[-1]
                        else:
                            default_layer = sorted_layers[-1]

                        self.selected_layer_id = default_layer.id
                        self.layers_panel.selected_layer_id = default_layer.id
                        self.layers_panel._update_properties_panel()
                        self.editor.set_target_layer(default_layer.name)

        except Exception as e:
            self.editor.set_status("Error refreshing UI", error=True)

    def run(self):
        """Start the application main loop."""
        self.root.mainloop()


def launch_gui():
    """Launch the GUI application."""
    app = TeamCreationStudioApp()
    app.run()


if __name__ == "__main__":
    launch_gui()
