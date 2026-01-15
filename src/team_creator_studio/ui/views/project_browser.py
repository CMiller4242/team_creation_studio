"""
Project browser view.

Shows teams and projects in a Canva-like browser interface.
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from typing import Optional, Callable, List, Dict, Any

from team_creator_studio.ui import theme


class ProjectBrowser(ttk.Frame):
    """
    Project browser panel showing teams and projects.

    Provides:
    - Teams list with scrolling
    - Projects list for selected team
    - New Team / New Project buttons
    - Click to open project callback
    """

    def __init__(
        self,
        parent,
        on_project_selected: Optional[Callable[[str, str], None]] = None,
        on_new_team: Optional[Callable[[str], None]] = None,
        on_new_project: Optional[Callable[[str, str], None]] = None,
    ):
        """
        Initialize project browser.

        Args:
            parent: Parent widget
            on_project_selected: Callback(team_name, project_name) when project is opened
            on_new_team: Callback(team_name) when new team is created
            on_new_project: Callback(team_name, project_name) when new project is created
        """
        super().__init__(parent)

        self.on_project_selected = on_project_selected
        self.on_new_team = on_new_team
        self.on_new_project = on_new_project

        self.teams_data = []
        self.projects_data = []
        self.selected_team = None

        self._create_widgets()

    def _create_widgets(self):
        """Create the browser UI."""
        # Configure style
        self.configure(style="Browser.TFrame")

        # Title
        title_frame = ttk.Frame(self)
        title_frame.pack(fill="x", padx=theme.PADDING_MEDIUM, pady=theme.PADDING_MEDIUM)

        title_label = ttk.Label(
            title_frame,
            text="Project Browser",
            font=theme.get_font(theme.FONT_SIZE_HEADING, "bold")
        )
        title_label.pack(side="left")

        # Teams section
        teams_frame = ttk.LabelFrame(self, text="Teams", padding=theme.PADDING_MEDIUM)
        teams_frame.pack(fill="both", expand=False, padx=theme.PADDING_MEDIUM, pady=theme.PADDING_SMALL)

        # Teams listbox with scrollbar
        teams_scroll_frame = ttk.Frame(teams_frame)
        teams_scroll_frame.pack(fill="both", expand=True)

        teams_scrollbar = ttk.Scrollbar(teams_scroll_frame)
        teams_scrollbar.pack(side="right", fill="y")

        self.teams_listbox = tk.Listbox(
            teams_scroll_frame,
            yscrollcommand=teams_scrollbar.set,
            height=8,
            font=theme.get_font(theme.FONT_SIZE_NORMAL)
        )
        self.teams_listbox.pack(side="left", fill="both", expand=True)
        teams_scrollbar.config(command=self.teams_listbox.yview)

        self.teams_listbox.bind("<<ListboxSelect>>", self._on_team_selected)

        # New team button
        new_team_btn = ttk.Button(
            teams_frame,
            text="New Team",
            command=self._on_new_team_clicked
        )
        new_team_btn.pack(fill="x", pady=(theme.PADDING_SMALL, 0))

        # Projects section
        projects_frame = ttk.LabelFrame(self, text="Projects", padding=theme.PADDING_MEDIUM)
        projects_frame.pack(fill="both", expand=True, padx=theme.PADDING_MEDIUM, pady=theme.PADDING_SMALL)

        # Projects listbox with scrollbar
        projects_scroll_frame = ttk.Frame(projects_frame)
        projects_scroll_frame.pack(fill="both", expand=True)

        projects_scrollbar = ttk.Scrollbar(projects_scroll_frame)
        projects_scrollbar.pack(side="right", fill="y")

        self.projects_listbox = tk.Listbox(
            projects_scroll_frame,
            yscrollcommand=projects_scrollbar.set,
            font=theme.get_font(theme.FONT_SIZE_NORMAL)
        )
        self.projects_listbox.pack(side="left", fill="both", expand=True)
        projects_scrollbar.config(command=self.projects_listbox.yview)

        self.projects_listbox.bind("<Double-Button-1>", self._on_project_double_clicked)

        # Project buttons frame
        project_buttons_frame = ttk.Frame(projects_frame)
        project_buttons_frame.pack(fill="x", pady=(theme.PADDING_SMALL, 0))

        new_project_btn = ttk.Button(
            project_buttons_frame,
            text="New Project",
            command=self._on_new_project_clicked
        )
        new_project_btn.pack(side="left", fill="x", expand=True, padx=(0, theme.PADDING_SMALL))

        open_project_btn = ttk.Button(
            project_buttons_frame,
            text="Open Project",
            command=self._on_open_project_clicked
        )
        open_project_btn.pack(side="left", fill="x", expand=True)

    def set_teams(self, teams: List[Dict[str, Any]]):
        """
        Set the teams list.

        Args:
            teams: List of team dicts with 'name' and 'slug' keys
        """
        self.teams_data = teams
        self.teams_listbox.delete(0, tk.END)

        for team in teams:
            self.teams_listbox.insert(tk.END, team["name"])

    def set_projects(self, projects: List[Dict[str, Any]]):
        """
        Set the projects list for the selected team.

        Args:
            projects: List of project dicts with 'name' and 'slug' keys
        """
        self.projects_data = projects
        self.projects_listbox.delete(0, tk.END)

        for project in projects:
            self.projects_listbox.insert(tk.END, project["name"])

    def _on_team_selected(self, event):
        """Handle team selection."""
        selection = self.teams_listbox.curselection()
        if not selection:
            return

        index = selection[0]
        if index < len(self.teams_data):
            team = self.teams_data[index]
            self.selected_team = team
            # Clear projects list - parent controller will populate it
            self.projects_listbox.delete(0, tk.END)
            # Notify parent via callback (if needed)

    def _on_project_double_clicked(self, event):
        """Handle project double-click to open."""
        self._on_open_project_clicked()

    def _on_open_project_clicked(self):
        """Handle open project button click."""
        if not self.selected_team:
            messagebox.showwarning("No Team Selected", "Please select a team first.")
            return

        selection = self.projects_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Project Selected", "Please select a project to open.")
            return

        index = selection[0]
        if index < len(self.projects_data):
            project = self.projects_data[index]
            if self.on_project_selected:
                self.on_project_selected(self.selected_team["name"], project["name"])

    def _on_new_team_clicked(self):
        """Handle new team button click."""
        team_name = simpledialog.askstring(
            "New Team",
            "Enter team name:",
            parent=self
        )

        if team_name:
            team_name = team_name.strip()
            if team_name:
                if self.on_new_team:
                    self.on_new_team(team_name)
            else:
                messagebox.showwarning("Invalid Name", "Team name cannot be empty.")

    def _on_new_project_clicked(self):
        """Handle new project button click."""
        if not self.selected_team:
            messagebox.showwarning("No Team Selected", "Please select a team first.")
            return

        project_name = simpledialog.askstring(
            "New Project",
            f"Enter project name for team '{self.selected_team['name']}':",
            parent=self
        )

        if project_name:
            project_name = project_name.strip()
            if project_name:
                if self.on_new_project:
                    self.on_new_project(self.selected_team["name"], project_name)
            else:
                messagebox.showwarning("Invalid Name", "Project name cannot be empty.")

    def get_selected_team(self) -> Optional[Dict[str, Any]]:
        """Get the currently selected team."""
        return self.selected_team
