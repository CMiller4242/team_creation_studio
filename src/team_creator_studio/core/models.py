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

    @staticmethod
    def create(
        name: str,
        layer_type: str,
        layer_path: str,
        source_image_id: Optional[str] = None,
        visible: bool = True,
        opacity: float = 1.0,
        blend_mode: str = "normal",
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
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Layer":
        """Create from dictionary."""
        return Layer(**data)


@dataclass
class OperationRecord:
    """Records a non-destructive editing operation."""

    id: str
    op_type: str  # "color_replace", etc.
    params: Dict[str, Any]  # Operation-specific parameters
    created_at: str  # ISO 8601 timestamp
    input_layer_id: str
    output_path: str  # Relative to project root
    note: Optional[str] = None

    @staticmethod
    def create(
        op_type: str,
        params: Dict[str, Any],
        input_layer_id: str,
        output_path: str,
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
            note=note,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "OperationRecord":
        """Create from dictionary."""
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
        """Add an operation record to the project."""
        self.operations.append(operation)
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
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "ProjectState":
        """Create from dictionary."""
        return ProjectState(
            team_name=data["team_name"],
            team_slug=data["team_slug"],
            project_name=data["project_name"],
            project_slug=data["project_slug"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            source_images=[
                SourceImage.from_dict(img) for img in data.get("source_images", [])
            ],
            layers=[Layer.from_dict(layer) for layer in data.get("layers", [])],
            operations=[
                OperationRecord.from_dict(op) for op in data.get("operations", [])
            ],
            active_composite_path=data.get("active_composite_path"),
        )

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
