"""
Data models for Team Creation Studio projects.

All models are JSON-serializable for persistence in project metadata.
"""

import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any


@dataclass
class SourceImage:
    """Represents an imported source image in a project."""

    id: str
    filename: str
    original_path: str  # Relative to project root
    imported_at: str  # ISO 8601 timestamp

    @staticmethod
    def create(filename: str, original_path: str) -> "SourceImage":
        """Create a new SourceImage with generated UUID and timestamp."""
        return SourceImage(
            id=str(uuid.uuid4()),
            filename=filename,
            original_path=original_path,
            imported_at=datetime.utcnow().isoformat() + "Z",
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "SourceImage":
        """Create from dictionary."""
        return SourceImage(**data)


@dataclass
class Layer:
    """Represents a layer in the project."""

    id: str
    name: str
    type: str  # "raster", "vector", "text", "group"
    source_image_id: Optional[str]
    layer_path: str  # Relative to project root
    visible: bool
    opacity: float  # 0.0 to 1.0
    blend_mode: str  # "normal", etc.
    order: int  # Layer order (lower = bottom, higher = top)
    x: int  # X position on canvas
    y: int  # Y position on canvas

    @staticmethod
    def create(
        name: str,
        layer_type: str,
        layer_path: str,
        source_image_id: Optional[str] = None,
        visible: bool = True,
        opacity: float = 1.0,
        blend_mode: str = "normal",
        order: int = 0,
        x: int = 0,
        y: int = 0,
    ) -> "Layer":
        """Create a new Layer with generated UUID."""
        return Layer(
            id=str(uuid.uuid4()),
            name=name,
            type=layer_type,
            source_image_id=source_image_id,
            layer_path=layer_path,
            visible=visible,
            opacity=opacity,
            blend_mode=blend_mode,
            order=order,
            x=x,
            y=y,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Layer":
        """Create from dictionary with migration support."""
        # Migrate: add missing fields with defaults
        if "order" not in data:
            data["order"] = 0
        if "x" not in data:
            data["x"] = 0
        if "y" not in data:
            data["y"] = 0
        if "opacity" not in data:
            data["opacity"] = 1.0
        if "visible" not in data:
            data["visible"] = True
        return Layer(**data)


@dataclass
class OperationRecord:
    """Records a non-destructive editing operation."""

    id: str
    op_type: str  # "color_replace", etc.
    params: Dict[str, Any]  # Operation-specific parameters
    created_at: str  # ISO 8601 timestamp
    input_layer_id: str
    output_path: str  # Relative to project root (legacy, kept for compatibility)
    output_layer_path: Optional[str] = None  # Path to the updated layer bitmap
    note: Optional[str] = None

    @staticmethod
    def create(
        op_type: str,
        params: Dict[str, Any],
        input_layer_id: str,
        output_path: str,
        output_layer_path: Optional[str] = None,
        note: Optional[str] = None,
    ) -> "OperationRecord":
        """Create a new OperationRecord with generated UUID and timestamp."""
        return OperationRecord(
            id=str(uuid.uuid4()),
            op_type=op_type,
            params=params,
            created_at=datetime.utcnow().isoformat() + "Z",
            input_layer_id=input_layer_id,
            output_path=output_path,
            output_layer_path=output_layer_path,
            note=note,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "OperationRecord":
        """Create from dictionary with migration support."""
        # Migrate: output_layer_path is optional
        if "output_layer_path" not in data:
            data["output_layer_path"] = None
        if "note" not in data:
            data["note"] = None
        return OperationRecord(**data)


@dataclass
class ProjectState:
    """Complete state of a project including images, layers, and operations."""

    team_name: str
    team_slug: str
    project_name: str
    project_slug: str
    created_at: str  # ISO 8601 timestamp
    updated_at: str  # ISO 8601 timestamp
    source_images: List[SourceImage] = field(default_factory=list)
    layers: List[Layer] = field(default_factory=list)
    operations: List[OperationRecord] = field(default_factory=list)
    active_composite_path: Optional[str] = None  # Relative to project root
    active_op_index: int = -1  # Index of active operation (-1 = none, use base layer)
    canvas_width: int = 1024  # Canvas width in pixels
    canvas_height: int = 1024  # Canvas height in pixels
    canvas_background: str = "transparent"  # Background color/style
    canvas_dpi: Optional[int] = None  # Optional DPI setting

    def update_timestamp(self):
        """Update the updated_at timestamp to now."""
        self.updated_at = datetime.utcnow().isoformat() + "Z"

    def add_source_image(self, source_image: SourceImage):
        """Add a source image to the project."""
        self.source_images.append(source_image)
        self.update_timestamp()

    def add_layer(self, layer: Layer):
        """Add a layer to the project."""
        self.layers.append(layer)
        self.update_timestamp()

    def add_operation(self, operation: OperationRecord):
        """
        Add an operation record to the project.

        If adding after undo (active_op_index < len-1), truncates future operations.
        Sets active_op_index to the new operation.
        """
        # If we're not at the end, truncate operations after current index
        if self.active_op_index < len(self.operations) - 1:
            self.operations = self.operations[:self.active_op_index + 1]

        # Add new operation
        self.operations.append(operation)

        # Set active index to the new operation
        self.active_op_index = len(self.operations) - 1

        self.update_timestamp()

    def get_base_layer(self) -> Optional[Layer]:
        """Get the base (first) layer if it exists."""
        return self.layers[0] if self.layers else None

    def get_layer_by_id(self, layer_id: str) -> Optional[Layer]:
        """Find a layer by its ID."""
        for layer in self.layers:
            if layer.id == layer_id:
                return layer
        return None

    def get_source_image_by_id(self, image_id: str) -> Optional[SourceImage]:
        """Find a source image by its ID."""
        for img in self.source_images:
            if img.id == image_id:
                return img
        return None

    def get_operation_by_id(self, op_id: str) -> Optional[tuple[int, OperationRecord]]:
        """
        Find an operation by ID or ID prefix.

        Args:
            op_id: Full UUID or unique prefix (>=6 chars)

        Returns:
            Tuple of (index, operation) or None if not found

        Raises:
            ValueError: If prefix matches multiple operations
        """
        matches = []
        for i, op in enumerate(self.operations):
            if op.id == op_id or op.id.startswith(op_id):
                matches.append((i, op))

        if len(matches) == 0:
            return None
        elif len(matches) == 1:
            return matches[0]
        else:
            raise ValueError(f"Ambiguous operation ID prefix '{op_id}' matches {len(matches)} operations")

    def get_active_operation(self) -> Optional[OperationRecord]:
        """Get the currently active operation, or None if no operations active."""
        if self.active_op_index < 0 or self.active_op_index >= len(self.operations):
            return None
        return self.operations[self.active_op_index]

    def can_undo(self) -> bool:
        """Check if undo is possible."""
        return self.active_op_index >= 0

    def can_redo(self) -> bool:
        """Check if redo is possible."""
        return self.active_op_index < len(self.operations) - 1

    def undo(self) -> bool:
        """
        Move to previous operation in the stack.

        Returns:
            True if undo was performed, False if nothing to undo
        """
        if not self.can_undo():
            return False

        self.active_op_index -= 1
        self.update_timestamp()
        return True

    def redo(self) -> bool:
        """
        Move to next operation in the stack.

        Returns:
            True if redo was performed, False if nothing to redo
        """
        if not self.can_redo():
            return False

        self.active_op_index += 1
        self.update_timestamp()
        return True

    def delete_operation(self, op_index: int) -> OperationRecord:
        """
        Delete an operation from the stack.

        Adjusts active_op_index:
        - If deleted op index < active: decrement active by 1
        - If deleted op index == active: set active to previous (index-1), or -1 if none
        - If deleted op index > active: no change to active

        Args:
            op_index: Index of operation to delete

        Returns:
            The deleted operation record

        Raises:
            IndexError: If op_index is out of range
        """
        if op_index < 0 or op_index >= len(self.operations):
            raise IndexError(f"Operation index {op_index} out of range")

        deleted_op = self.operations.pop(op_index)

        # Adjust active_op_index
        if op_index < self.active_op_index:
            # Deleted operation before active: shift active down
            self.active_op_index -= 1
        elif op_index == self.active_op_index:
            # Deleted the active operation: move to previous
            self.active_op_index = op_index - 1
        # If op_index > active_op_index: no change needed

        self.update_timestamp()
        return deleted_op

    def get_sorted_layers(self) -> List[Layer]:
        """Get layers sorted by order (ascending)."""
        return sorted(self.layers, key=lambda l: l.order)

    def get_layer_index(self, layer_id: str) -> Optional[int]:
        """Get the index of a layer in the layers list."""
        for i, layer in enumerate(self.layers):
            if layer.id == layer_id:
                return i
        return None

    def move_layer_up(self, layer_id: str) -> bool:
        """
        Move a layer up in the stack (increase order).
        Returns True if moved, False if already at top or not found.
        """
        layer = self.get_layer_by_id(layer_id)
        if not layer:
            return False

        sorted_layers = self.get_sorted_layers()
        current_pos = next((i for i, l in enumerate(sorted_layers) if l.id == layer_id), None)

        if current_pos is None or current_pos == len(sorted_layers) - 1:
            # Layer not found or already at top
            return False

        # Swap order with next layer
        next_layer = sorted_layers[current_pos + 1]
        layer.order, next_layer.order = next_layer.order, layer.order

        self.update_timestamp()
        return True

    def move_layer_down(self, layer_id: str) -> bool:
        """
        Move a layer down in the stack (decrease order).
        Returns True if moved, False if already at bottom or not found.
        """
        layer = self.get_layer_by_id(layer_id)
        if not layer:
            return False

        sorted_layers = self.get_sorted_layers()
        current_pos = next((i for i, l in enumerate(sorted_layers) if l.id == layer_id), None)

        if current_pos is None or current_pos == 0:
            # Layer not found or already at bottom
            return False

        # Swap order with previous layer
        prev_layer = sorted_layers[current_pos - 1]
        layer.order, prev_layer.order = prev_layer.order, layer.order

        self.update_timestamp()
        return True

    def delete_layer(self, layer_id: str) -> Optional[Layer]:
        """
        Delete a layer from the project.
        Returns the deleted layer or None if not found.
        """
        index = self.get_layer_index(layer_id)
        if index is None:
            return None

        deleted_layer = self.layers.pop(index)
        self.update_timestamp()
        return deleted_layer

    def set_layer_visibility(self, layer_id: str, visible: bool) -> bool:
        """
        Set layer visibility.
        Returns True if changed, False if not found.
        """
        layer = self.get_layer_by_id(layer_id)
        if not layer:
            return False

        layer.visible = visible
        self.update_timestamp()
        return True

    def set_layer_opacity(self, layer_id: str, opacity: float) -> bool:
        """
        Set layer opacity (clamped to 0.0-1.0).
        Returns True if changed, False if not found.
        """
        layer = self.get_layer_by_id(layer_id)
        if not layer:
            return False

        # Clamp opacity to valid range
        layer.opacity = max(0.0, min(1.0, opacity))
        self.update_timestamp()
        return True

    def set_layer_position(self, layer_id: str, x: int, y: int) -> bool:
        """
        Set layer position on canvas.
        Returns True if changed, False if not found.
        """
        layer = self.get_layer_by_id(layer_id)
        if not layer:
            return False

        layer.x = x
        layer.y = y
        self.update_timestamp()
        return True

    def rename_layer(self, layer_id: str, name: str) -> bool:
        """
        Rename a layer.
        Returns True if changed, False if not found.
        """
        layer = self.get_layer_by_id(layer_id)
        if not layer:
            return False

        layer.name = name
        self.update_timestamp()
        return True

    def normalize_layer_order(self):
        """Normalize layer order values to 0, 1, 2, ..., n-1 based on current ordering."""
        sorted_layers = self.get_sorted_layers()
        for i, layer in enumerate(sorted_layers):
            layer.order = i
        self.update_timestamp()

    def get_visible_layer_count(self) -> int:
        """Get the count of visible layers."""
        return sum(1 for layer in self.layers if layer.visible)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "team_name": self.team_name,
            "team_slug": self.team_slug,
            "project_name": self.project_name,
            "project_slug": self.project_slug,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "source_images": [img.to_dict() for img in self.source_images],
            "layers": [layer.to_dict() for layer in self.layers],
            "operations": [op.to_dict() for op in self.operations],
            "active_composite_path": self.active_composite_path,
            "active_op_index": self.active_op_index,
            "canvas_width": self.canvas_width,
            "canvas_height": self.canvas_height,
            "canvas_background": self.canvas_background,
            "canvas_dpi": self.canvas_dpi,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "ProjectState":
        """
        Create from dictionary with migration support.

        Handles missing active_op_index for Milestone 2 projects.
        Handles missing canvas settings for Milestone 4 projects.
        Handles missing layer order/position/opacity for Milestone 4 projects.
        """
        operations = [
            OperationRecord.from_dict(op) for op in data.get("operations", [])
        ]

        layers = [Layer.from_dict(layer) for layer in data.get("layers", [])]

        # Migrate: infer active_op_index if not present
        if "active_op_index" not in data:
            if operations:
                # Old project with operations: set to last operation
                active_op_index = len(operations) - 1
            else:
                # No operations: -1 (use base layer)
                active_op_index = -1
        else:
            active_op_index = data["active_op_index"]

        # Migrate: infer canvas settings if not present
        canvas_width = data.get("canvas_width")
        canvas_height = data.get("canvas_height")

        if canvas_width is None or canvas_height is None:
            # Infer from first image if available
            if layers:
                # Try to infer from first layer's source image
                # For now, use default; validation will correct this later
                canvas_width = 1024
                canvas_height = 1024
            else:
                # No layers yet, use default
                canvas_width = 1024
                canvas_height = 1024

        canvas_background = data.get("canvas_background", "transparent")
        canvas_dpi = data.get("canvas_dpi")

        # Migrate: normalize layer order if needed
        if layers:
            # Ensure all layers have order set (Layer.from_dict already handles defaults)
            # Normalize to 0, 1, 2, ... based on current list order
            for i, layer in enumerate(layers):
                if layer.order == 0 and i > 0:
                    # Likely all orders are 0 (old format), reassign
                    layer.order = i

        project_state = ProjectState(
            team_name=data["team_name"],
            team_slug=data["team_slug"],
            project_name=data["project_name"],
            project_slug=data["project_slug"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            source_images=[
                SourceImage.from_dict(img) for img in data.get("source_images", [])
            ],
            layers=layers,
            operations=operations,
            active_composite_path=data.get("active_composite_path"),
            active_op_index=active_op_index,
            canvas_width=canvas_width,
            canvas_height=canvas_height,
            canvas_background=canvas_background,
            canvas_dpi=canvas_dpi,
        )

        return project_state

    def save(self, project_path: Path):
        """Save project state to meta/project.json."""
        meta_path = project_path / "meta" / "project.json"
        meta_path.parent.mkdir(parents=True, exist_ok=True)

        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

    @staticmethod
    def load(project_path: Path) -> Optional["ProjectState"]:
        """Load project state from meta/project.json."""
        meta_path = project_path / "meta" / "project.json"

        if not meta_path.exists():
            return None

        with open(meta_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return ProjectState.from_dict(data)

    @staticmethod
    def create_new(
        team_name: str, team_slug: str, project_name: str, project_slug: str
    ) -> "ProjectState":
        """Create a new project state."""
        now = datetime.utcnow().isoformat() + "Z"
        return ProjectState(
            team_name=team_name,
            team_slug=team_slug,
            project_name=project_name,
            project_slug=project_slug,
            created_at=now,
            updated_at=now,
        )
