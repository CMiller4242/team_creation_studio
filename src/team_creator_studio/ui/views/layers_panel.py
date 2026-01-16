"""
Layers panel for layer management.

Milestone 5: Multi-layer system UI.
"""

import tkinter as tk
from tkinter import ttk, filedialog
from typing import Optional, Callable, List
from pathlib import Path

from team_creator_studio.ui.theme import (
    PADDING,
    SMALL_PADDING,
    BUTTON_WIDTH,
    LABEL_WIDTH,
)
from team_creator_studio.ui.widgets.scrollable_frame import ScrollableFrame
from team_creator_studio.core.models import Layer


class LayersPanel(ttk.Frame):
    """
    Layers management panel.

    Features:
    - Scrollable layers list with visibility checkboxes
    - Layer selection (click layer name to select)
    - Controls: Add Layer, Delete Layer, Move Up, Move Down
    - Properties: Name entry, Opacity slider, X/Y position
    """

    def __init__(
        self,
        parent,
        on_layer_selected: Optional[Callable[[str], None]] = None,
        on_add_layer: Optional[Callable[[], None]] = None,
        on_delete_layer: Optional[Callable[[str], None]] = None,
        on_move_up: Optional[Callable[[str], None]] = None,
        on_move_down: Optional[Callable[[str], None]] = None,
        on_rename: Optional[Callable[[str, str], None]] = None,
        on_opacity_changed: Optional[Callable[[str, float], None]] = None,
        on_position_changed: Optional[Callable[[str, int, int], None]] = None,
        on_visibility_toggled: Optional[Callable[[str, bool], None]] = None,
    ):
        """
        Initialize layers panel.

        Args:
            parent: Parent widget
            on_layer_selected: Callback(layer_id) when layer clicked
            on_add_layer: Callback() when Add Layer clicked
            on_delete_layer: Callback(layer_id) when Delete Layer clicked
            on_move_up: Callback(layer_id) when Move Up clicked
            on_move_down: Callback(layer_id) when Move Down clicked
            on_rename: Callback(layer_id, new_name) when Rename clicked or Enter pressed
            on_opacity_changed: Callback(layer_id, opacity_0_to_1) when Apply Opacity clicked
            on_position_changed: Callback(layer_id, x, y) when Apply Position clicked
            on_visibility_toggled: Callback(layer_id, visible) when visibility checkbox toggled
        """
        super().__init__(parent)

        # Store callbacks
        self.on_layer_selected = on_layer_selected
        self.on_add_layer = on_add_layer
        self.on_delete_layer = on_delete_layer
        self.on_move_up = on_move_up
        self.on_move_down = on_move_down
        self.on_rename = on_rename
        self.on_opacity_changed = on_opacity_changed
        self.on_position_changed = on_position_changed
        self.on_visibility_toggled = on_visibility_toggled

        # State
        self.selected_layer_id: Optional[str] = None
        self.layers: List[Layer] = []
        self.layer_widgets: dict = {}  # layer_id -> {frame, label, checkbox}

        # Build UI
        self._build_ui()

    def _build_ui(self):
        """Build the layers panel UI."""
        # Title
        title_label = ttk.Label(self, text="Layers", font=("TkDefaultFont", 10, "bold"))
        title_label.pack(pady=(PADDING, SMALL_PADDING))

        # Layers list (scrollable)
        list_frame = ttk.LabelFrame(self, text="Layers List", padding=PADDING)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=PADDING, pady=SMALL_PADDING)

        self.layers_scroll = ScrollableFrame(list_frame)
        self.layers_scroll.pack(fill=tk.BOTH, expand=True)

        # Layer controls
        controls_frame = ttk.Frame(self)
        controls_frame.pack(fill=tk.X, padx=PADDING, pady=SMALL_PADDING)

        self.add_button = ttk.Button(
            controls_frame,
            text="Add Layer",
            command=self._handle_add_layer,
            width=BUTTON_WIDTH,
        )
        self.add_button.grid(row=0, column=0, padx=SMALL_PADDING, pady=SMALL_PADDING)

        self.delete_button = ttk.Button(
            controls_frame,
            text="Delete Layer",
            command=self._handle_delete_layer,
            width=BUTTON_WIDTH,
            state=tk.DISABLED,
        )
        self.delete_button.grid(row=0, column=1, padx=SMALL_PADDING, pady=SMALL_PADDING)

        self.move_up_button = ttk.Button(
            controls_frame,
            text="Move Up",
            command=self._handle_move_up,
            width=BUTTON_WIDTH,
            state=tk.DISABLED,
        )
        self.move_up_button.grid(row=1, column=0, padx=SMALL_PADDING, pady=SMALL_PADDING)

        self.move_down_button = ttk.Button(
            controls_frame,
            text="Move Down",
            command=self._handle_move_down,
            width=BUTTON_WIDTH,
            state=tk.DISABLED,
        )
        self.move_down_button.grid(row=1, column=1, padx=SMALL_PADDING, pady=SMALL_PADDING)

        # Layer properties (for selected layer)
        props_frame = ttk.LabelFrame(self, text="Layer Properties", padding=PADDING)
        props_frame.pack(fill=tk.X, padx=PADDING, pady=SMALL_PADDING)

        # Name
        name_frame = ttk.Frame(props_frame)
        name_frame.pack(fill=tk.X, pady=SMALL_PADDING)

        ttk.Label(name_frame, text="Name:", width=LABEL_WIDTH).pack(side=tk.LEFT, padx=SMALL_PADDING)

        self.name_var = tk.StringVar()
        self.name_entry = ttk.Entry(name_frame, textvariable=self.name_var, state=tk.DISABLED)
        self.name_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=SMALL_PADDING)
        self.name_entry.bind("<Return>", lambda e: self._handle_rename())

        self.rename_button = ttk.Button(
            name_frame,
            text="Rename",
            command=self._handle_rename,
            width=10,
            state=tk.DISABLED,
        )
        self.rename_button.pack(side=tk.LEFT, padx=SMALL_PADDING)

        # Opacity
        opacity_frame = ttk.Frame(props_frame)
        opacity_frame.pack(fill=tk.X, pady=SMALL_PADDING)

        ttk.Label(opacity_frame, text="Opacity:", width=LABEL_WIDTH).pack(side=tk.LEFT, padx=SMALL_PADDING)

        self.opacity_var = tk.IntVar(value=100)
        self.opacity_slider = ttk.Scale(
            opacity_frame,
            from_=0,
            to=100,
            orient=tk.HORIZONTAL,
            variable=self.opacity_var,
            state=tk.DISABLED,
        )
        self.opacity_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=SMALL_PADDING)

        self.opacity_label = ttk.Label(opacity_frame, text="100", width=5)
        self.opacity_label.pack(side=tk.LEFT, padx=SMALL_PADDING)

        # Update opacity label when slider moves
        self.opacity_var.trace_add("write", self._update_opacity_label)

        self.apply_opacity_button = ttk.Button(
            opacity_frame,
            text="Apply",
            command=self._handle_opacity_changed,
            width=10,
            state=tk.DISABLED,
        )
        self.apply_opacity_button.pack(side=tk.LEFT, padx=SMALL_PADDING)

        # Position
        position_frame = ttk.Frame(props_frame)
        position_frame.pack(fill=tk.X, pady=SMALL_PADDING)

        ttk.Label(position_frame, text="Position:", width=LABEL_WIDTH).pack(side=tk.LEFT, padx=SMALL_PADDING)

        ttk.Label(position_frame, text="X:").pack(side=tk.LEFT, padx=SMALL_PADDING)

        self.x_var = tk.IntVar(value=0)
        self.x_entry = ttk.Entry(position_frame, textvariable=self.x_var, width=8, state=tk.DISABLED)
        self.x_entry.pack(side=tk.LEFT, padx=SMALL_PADDING)

        ttk.Label(position_frame, text="Y:").pack(side=tk.LEFT, padx=SMALL_PADDING)

        self.y_var = tk.IntVar(value=0)
        self.y_entry = ttk.Entry(position_frame, textvariable=self.y_var, width=8, state=tk.DISABLED)
        self.y_entry.pack(side=tk.LEFT, padx=SMALL_PADDING)

        self.apply_position_button = ttk.Button(
            position_frame,
            text="Apply Position",
            command=self._handle_position_changed,
            width=15,
            state=tk.DISABLED,
        )
        self.apply_position_button.pack(side=tk.LEFT, padx=SMALL_PADDING)

    def set_layers(self, layers: List[Layer]):
        """
        Update layers list display.

        Args:
            layers: List of layers to display (should be sorted by order)
        """
        self.layers = layers

        # Clear existing widgets
        for widget_dict in self.layer_widgets.values():
            widget_dict["frame"].destroy()
        self.layer_widgets.clear()

        # Create widgets for each layer (reverse order for display: top to bottom)
        for layer in reversed(layers):
            self._create_layer_row(layer)

        # Update properties panel
        self._update_properties_panel()

    def _create_layer_row(self, layer: Layer):
        """Create a row for a layer in the scrollable list."""
        # Create frame for this layer
        layer_frame = ttk.Frame(self.layers_scroll.scrollable_frame)
        layer_frame.pack(fill=tk.X, pady=2)

        # Visibility checkbox
        visible_var = tk.BooleanVar(value=layer.visible)
        checkbox = ttk.Checkbutton(
            layer_frame,
            variable=visible_var,
            command=lambda: self._handle_visibility_toggled(layer.id, visible_var.get()),
        )
        checkbox.pack(side=tk.LEFT, padx=SMALL_PADDING)

        # Layer name label (clickable for selection)
        label = ttk.Label(layer_frame, text=layer.name, cursor="hand2")
        label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=SMALL_PADDING)
        label.bind("<Button-1>", lambda e: self._handle_layer_clicked(layer.id))

        # Store widgets
        self.layer_widgets[layer.id] = {
            "frame": layer_frame,
            "label": label,
            "checkbox": checkbox,
            "visible_var": visible_var,
        }

        # Highlight if selected
        if layer.id == self.selected_layer_id:
            self._highlight_layer(layer.id)

    def _handle_layer_clicked(self, layer_id: str):
        """Handle layer selection."""
        # Update selection
        old_selection = self.selected_layer_id
        self.selected_layer_id = layer_id

        # Update highlighting
        if old_selection and old_selection in self.layer_widgets:
            self._unhighlight_layer(old_selection)

        self._highlight_layer(layer_id)

        # Update properties panel
        self._update_properties_panel()

        # Notify callback
        if self.on_layer_selected:
            self.on_layer_selected(layer_id)

    def _highlight_layer(self, layer_id: str):
        """Highlight a layer row."""
        if layer_id in self.layer_widgets:
            label = self.layer_widgets[layer_id]["label"]
            label.configure(background="#d0d0d0", foreground="black")

    def _unhighlight_layer(self, layer_id: str):
        """Remove highlighting from a layer row."""
        if layer_id in self.layer_widgets:
            label = self.layer_widgets[layer_id]["label"]
            label.configure(background="", foreground="")

    def _update_properties_panel(self):
        """Update properties panel based on selected layer."""
        if not self.selected_layer_id:
            # No selection - disable all property controls
            self.name_entry.configure(state=tk.DISABLED)
            self.rename_button.configure(state=tk.DISABLED)
            self.opacity_slider.configure(state=tk.DISABLED)
            self.apply_opacity_button.configure(state=tk.DISABLED)
            self.x_entry.configure(state=tk.DISABLED)
            self.y_entry.configure(state=tk.DISABLED)
            self.apply_position_button.configure(state=tk.DISABLED)
            self.delete_button.configure(state=tk.DISABLED)
            self.move_up_button.configure(state=tk.DISABLED)
            self.move_down_button.configure(state=tk.DISABLED)

            self.name_var.set("")
            self.opacity_var.set(100)
            self.x_var.set(0)
            self.y_var.set(0)
            return

        # Find selected layer
        selected_layer = None
        for layer in self.layers:
            if layer.id == self.selected_layer_id:
                selected_layer = layer
                break

        if not selected_layer:
            return

        # Populate properties
        self.name_var.set(selected_layer.name)
        self.opacity_var.set(int(selected_layer.opacity * 100))
        self.x_var.set(selected_layer.x)
        self.y_var.set(selected_layer.y)

        # Enable controls
        self.name_entry.configure(state=tk.NORMAL)
        self.rename_button.configure(state=tk.NORMAL)
        self.opacity_slider.configure(state=tk.NORMAL)
        self.apply_opacity_button.configure(state=tk.NORMAL)
        self.x_entry.configure(state=tk.NORMAL)
        self.y_entry.configure(state=tk.NORMAL)
        self.apply_position_button.configure(state=tk.NORMAL)
        self.delete_button.configure(state=tk.NORMAL)
        self.move_up_button.configure(state=tk.NORMAL)
        self.move_down_button.configure(state=tk.NORMAL)

    def _update_opacity_label(self, *args):
        """Update opacity value label."""
        self.opacity_label.configure(text=str(self.opacity_var.get()))

    def _handle_add_layer(self):
        """Handle Add Layer button."""
        if self.on_add_layer:
            self.on_add_layer()

    def _handle_delete_layer(self):
        """Handle Delete Layer button."""
        if self.selected_layer_id and self.on_delete_layer:
            self.on_delete_layer(self.selected_layer_id)

    def _handle_move_up(self):
        """Handle Move Up button."""
        if self.selected_layer_id and self.on_move_up:
            self.on_move_up(self.selected_layer_id)

    def _handle_move_down(self):
        """Handle Move Down button."""
        if self.selected_layer_id and self.on_move_down:
            self.on_move_down(self.selected_layer_id)

    def _handle_rename(self):
        """Handle Rename button or Enter key."""
        if self.selected_layer_id and self.on_rename:
            new_name = self.name_var.get().strip()
            if new_name:
                self.on_rename(self.selected_layer_id, new_name)

    def _handle_opacity_changed(self):
        """Handle Apply Opacity button."""
        if self.selected_layer_id and self.on_opacity_changed:
            opacity_0_to_1 = self.opacity_var.get() / 100.0
            self.on_opacity_changed(self.selected_layer_id, opacity_0_to_1)

    def _handle_position_changed(self):
        """Handle Apply Position button."""
        if self.selected_layer_id and self.on_position_changed:
            try:
                x = self.x_var.get()
                y = self.y_var.get()
                self.on_position_changed(self.selected_layer_id, x, y)
            except tk.TclError:
                # Invalid integer input
                pass

    def _handle_visibility_toggled(self, layer_id: str, visible: bool):
        """Handle visibility checkbox toggle."""
        if self.on_visibility_toggled:
            self.on_visibility_toggled(layer_id, visible)

    def get_selected_layer_id(self) -> Optional[str]:
        """Get currently selected layer ID."""
        return self.selected_layer_id

    def set_enabled(self, enabled: bool):
        """Enable or disable the entire panel."""
        state = tk.NORMAL if enabled else tk.DISABLED

        self.add_button.configure(state=state)

        if not enabled:
            self.delete_button.configure(state=tk.DISABLED)
            self.move_up_button.configure(state=tk.DISABLED)
            self.move_down_button.configure(state=tk.DISABLED)
            self.name_entry.configure(state=tk.DISABLED)
            self.rename_button.configure(state=tk.DISABLED)
            self.opacity_slider.configure(state=tk.DISABLED)
            self.apply_opacity_button.configure(state=tk.DISABLED)
            self.x_entry.configure(state=tk.DISABLED)
            self.y_entry.configure(state=tk.DISABLED)
            self.apply_position_button.configure(state=tk.DISABLED)
