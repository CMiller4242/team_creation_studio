"""
Editor view.

Shows image preview, toolbar, and color replace controls.
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable
from PIL import Image, ImageTk

from team_creator_studio.ui import theme


class EditorView(ttk.Frame):
    """
    Editor view with image preview and controls.

    Provides:
    - Toolbar (Import, Undo, Redo, Refresh, Export)
    - Image viewer with scaling
    - Color replace panel
    """

    def __init__(
        self,
        parent,
        on_import: Optional[Callable[[], None]] = None,
        on_undo: Optional[Callable[[], None]] = None,
        on_redo: Optional[Callable[[], None]] = None,
        on_refresh: Optional[Callable[[], None]] = None,
        on_export: Optional[Callable[[], None]] = None,
        on_apply_color_replace: Optional[Callable[[str, str, int, bool], None]] = None,
    ):
        """
        Initialize editor view.

        Args:
            parent: Parent widget
            on_import: Callback for import button
            on_undo: Callback for undo button
            on_redo: Callback for redo button
            on_refresh: Callback for refresh button
            on_export: Callback for export button
            on_apply_color_replace: Callback(target, new, tolerance, preserve_alpha)
        """
        super().__init__(parent)

        self.on_import = on_import
        self.on_undo = on_undo
        self.on_redo = on_redo
        self.on_refresh = on_refresh
        self.on_export = on_export
        self.on_apply_color_replace = on_apply_color_replace

        # Keep references to prevent garbage collection
        self.current_image = None
        self.photo_image = None

        self._create_widgets()

    def _create_widgets(self):
        """Create the editor UI."""
        # Toolbar
        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", padx=theme.PADDING_MEDIUM, pady=theme.PADDING_MEDIUM)

        ttk.Button(toolbar, text="Import Image", command=self._on_import_clicked).pack(
            side="left", padx=(0, theme.PADDING_SMALL)
        )
        ttk.Button(toolbar, text="Undo", command=self._on_undo_clicked).pack(
            side="left", padx=(0, theme.PADDING_SMALL)
        )
        ttk.Button(toolbar, text="Redo", command=self._on_redo_clicked).pack(
            side="left", padx=(0, theme.PADDING_SMALL)
        )
        ttk.Button(toolbar, text="Refresh", command=self._on_refresh_clicked).pack(
            side="left", padx=(0, theme.PADDING_SMALL)
        )
        ttk.Button(toolbar, text="Export", command=self._on_export_clicked).pack(
            side="left", padx=(0, theme.PADDING_SMALL)
        )

        # Status label
        self.status_label = ttk.Label(toolbar, text="No project loaded", foreground=theme.TEXT_SECONDARY)
        self.status_label.pack(side="right")

        # Image viewer frame
        viewer_frame = ttk.LabelFrame(self, text="Image Viewer", padding=theme.PADDING_MEDIUM)
        viewer_frame.pack(fill="both", expand=True, padx=theme.PADDING_MEDIUM, pady=theme.PADDING_SMALL)

        # Canvas for image display with scrollbars
        canvas_frame = ttk.Frame(viewer_frame)
        canvas_frame.pack(fill="both", expand=True)

        self.image_canvas = tk.Canvas(
            canvas_frame,
            bg=theme.BG_SECONDARY,
            highlightthickness=1,
            highlightbackground=theme.BORDER_COLOR
        )
        self.image_canvas.pack(fill="both", expand=True)

        # Bind resize event
        self.image_canvas.bind("<Configure>", self._on_canvas_resize)

        # Placeholder text
        self.placeholder_text = self.image_canvas.create_text(
            0, 0,
            text="No image loaded\n\nOpen a project and import an image to get started",
            font=theme.get_font(theme.FONT_SIZE_LARGE),
            fill=theme.TEXT_LIGHT,
            anchor="center"
        )

        # Color Replace Panel
        color_panel = ttk.LabelFrame(self, text="Color Replace", padding=theme.PADDING_MEDIUM)
        color_panel.pack(fill="x", padx=theme.PADDING_MEDIUM, pady=theme.PADDING_SMALL)

        # Target layer indicator
        target_layer_frame = ttk.Frame(color_panel)
        target_layer_frame.pack(fill="x", pady=theme.PADDING_SMALL)

        ttk.Label(target_layer_frame, text="Target Layer:", width=12).pack(side="left")
        self.target_layer_label = ttk.Label(target_layer_frame, text="(No layer selected)", foreground=theme.TEXT_SECONDARY)
        self.target_layer_label.pack(side="left", padx=theme.PADDING_SMALL)

        # Target color row
        target_frame = ttk.Frame(color_panel)
        target_frame.pack(fill="x", pady=theme.PADDING_SMALL)

        ttk.Label(target_frame, text="Target Color:", width=12).pack(side="left")

        ttk.Label(target_frame, text="HEX:").pack(side="left", padx=(theme.PADDING_MEDIUM, theme.PADDING_SMALL))
        self.target_hex_entry = ttk.Entry(target_frame, width=10)
        self.target_hex_entry.pack(side="left", padx=(0, theme.PADDING_MEDIUM))
        self.target_hex_entry.insert(0, "#000000")

        ttk.Label(target_frame, text="RGB:").pack(side="left", padx=(0, theme.PADDING_SMALL))
        self.target_rgb_entry = ttk.Entry(target_frame, width=12)
        self.target_rgb_entry.pack(side="left")
        self.target_rgb_entry.insert(0, "0,0,0")

        # New color row
        new_frame = ttk.Frame(color_panel)
        new_frame.pack(fill="x", pady=theme.PADDING_SMALL)

        ttk.Label(new_frame, text="New Color:", width=12).pack(side="left")

        ttk.Label(new_frame, text="HEX:").pack(side="left", padx=(theme.PADDING_MEDIUM, theme.PADDING_SMALL))
        self.new_hex_entry = ttk.Entry(new_frame, width=10)
        self.new_hex_entry.pack(side="left", padx=(0, theme.PADDING_MEDIUM))
        self.new_hex_entry.insert(0, "#FFFFFF")

        ttk.Label(new_frame, text="RGB:").pack(side="left", padx=(0, theme.PADDING_SMALL))
        self.new_rgb_entry = ttk.Entry(new_frame, width=12)
        self.new_rgb_entry.pack(side="left")
        self.new_rgb_entry.insert(0, "255,255,255")

        # Tolerance row
        tolerance_frame = ttk.Frame(color_panel)
        tolerance_frame.pack(fill="x", pady=theme.PADDING_SMALL)

        ttk.Label(tolerance_frame, text="Tolerance:", width=12).pack(side="left")

        self.tolerance_var = tk.IntVar(value=0)
        self.tolerance_scale = ttk.Scale(
            tolerance_frame,
            from_=0,
            to=100,
            orient="horizontal",
            variable=self.tolerance_var,
            command=self._on_tolerance_changed
        )
        self.tolerance_scale.pack(side="left", fill="x", expand=True, padx=(theme.PADDING_MEDIUM, theme.PADDING_SMALL))

        self.tolerance_entry = ttk.Entry(tolerance_frame, width=5, textvariable=self.tolerance_var)
        self.tolerance_entry.pack(side="left")

        # Preserve alpha row
        alpha_frame = ttk.Frame(color_panel)
        alpha_frame.pack(fill="x", pady=theme.PADDING_SMALL)

        self.preserve_alpha_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            alpha_frame,
            text="Preserve alpha channel",
            variable=self.preserve_alpha_var
        ).pack(side="left")

        # Apply button
        self.apply_button = ttk.Button(
            color_panel,
            text="Apply Color Replace",
            command=self._on_apply_color_replace_clicked,
            state=tk.DISABLED  # Disabled until a layer is selected
        )
        self.apply_button.pack(fill="x", pady=(theme.PADDING_MEDIUM, 0))

    def _on_import_clicked(self):
        """Handle import button click."""
        if self.on_import:
            self.on_import()

    def _on_undo_clicked(self):
        """Handle undo button click."""
        if self.on_undo:
            self.on_undo()

    def _on_redo_clicked(self):
        """Handle redo button click."""
        if self.on_redo:
            self.on_redo()

    def _on_refresh_clicked(self):
        """Handle refresh button click."""
        if self.on_refresh:
            self.on_refresh()

    def _on_export_clicked(self):
        """Handle export button click."""
        if self.on_export:
            self.on_export()

    def _on_apply_color_replace_clicked(self):
        """Handle apply color replace button click."""
        if self.on_apply_color_replace:
            # Get target color (HEX takes precedence)
            target = self.target_hex_entry.get().strip()
            if not target or target == "#":
                target = self.target_rgb_entry.get().strip()

            # Get new color (HEX takes precedence)
            new = self.new_hex_entry.get().strip()
            if not new or new == "#":
                new = self.new_rgb_entry.get().strip()

            tolerance = self.tolerance_var.get()
            preserve_alpha = self.preserve_alpha_var.get()

            self.on_apply_color_replace(target, new, tolerance, preserve_alpha)

    def _on_tolerance_changed(self, value):
        """Handle tolerance slider change."""
        # Update entry to match slider
        # Value is a string from Scale widget
        pass

    def _on_canvas_resize(self, event):
        """Handle canvas resize - update image display."""
        if self.current_image:
            self._display_image(self.current_image)
        else:
            # Center placeholder text
            canvas_width = event.width
            canvas_height = event.height
            self.image_canvas.coords(self.placeholder_text, canvas_width // 2, canvas_height // 2)

    def set_image(self, image_path: str):
        """
        Display an image in the viewer.

        Args:
            image_path: Path to the image file
        """
        try:
            # Load image
            self.current_image = Image.open(image_path)

            # Hide placeholder
            self.image_canvas.itemconfigure(self.placeholder_text, state="hidden")

            # Display image
            self._display_image(self.current_image)

        except Exception as e:
            self.set_status(f"Error loading image: {e}", error=True)

    def _display_image(self, image: Image.Image):
        """
        Display a PIL image on the canvas, scaled to fit.

        Args:
            image: PIL Image object
        """
        # Get canvas size
        canvas_width = self.image_canvas.winfo_width()
        canvas_height = self.image_canvas.winfo_height()

        # Handle initial sizing
        if canvas_width <= 1 or canvas_height <= 1:
            canvas_width = 800
            canvas_height = 600

        # Calculate scaling to fit canvas while preserving aspect ratio
        img_width, img_height = image.size
        scale_x = canvas_width / img_width
        scale_y = canvas_height / img_height
        scale = min(scale_x, scale_y, 1.0)  # Don't scale up, only down

        # Calculate new size
        new_width = int(img_width * scale)
        new_height = int(img_height * scale)

        # Resize image
        if scale < 1.0:
            resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        else:
            resized_image = image

        # Convert to PhotoImage
        self.photo_image = ImageTk.PhotoImage(resized_image)

        # Clear canvas and display image
        self.image_canvas.delete("image")

        # Center image on canvas
        x = canvas_width // 2
        y = canvas_height // 2

        self.image_canvas.create_image(
            x, y,
            image=self.photo_image,
            anchor="center",
            tags="image"
        )

    def clear_image(self):
        """Clear the image viewer."""
        self.current_image = None
        self.photo_image = None
        self.image_canvas.delete("image")
        self.image_canvas.itemconfigure(self.placeholder_text, state="normal")

    def set_status(self, message: str, error: bool = False):
        """
        Set the status label text.

        Args:
            message: Status message
            error: If True, display in error color
        """
        self.status_label.config(
            text=message,
            foreground=theme.ERROR_COLOR if error else theme.TEXT_SECONDARY
        )

    def set_target_layer(self, layer_name: Optional[str]):
        """
        Set the target layer name for color replace operations.

        Args:
            layer_name: Name of the target layer, or None if no layer selected
        """
        if layer_name:
            self.target_layer_label.config(text=layer_name, foreground=theme.TEXT_PRIMARY)
            self.apply_button.config(state=tk.NORMAL)
        else:
            self.target_layer_label.config(text="(No layer selected)", foreground=theme.TEXT_SECONDARY)
            self.apply_button.config(state=tk.DISABLED)
