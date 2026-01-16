# Team Creation Studio - Development Milestones

This document outlines the development roadmap for Team Creation Studio, breaking the project into manageable milestones with clear deliverables.

## Milestone 1: Foundation & Scaffold ✅

**Status:** Complete
**Duration:** Initial implementation
**Goal:** Establish core project structure and workspace management

### Deliverables

- [x] Repository structure with src/ package layout
- [x] Python package configuration (pyproject.toml)
- [x] CLI tool with argparse
- [x] Workspace directory management
- [x] Team creation with metadata
- [x] Project creation with full directory structure
- [x] JSON schemas for projects and palettes
- [x] Slugify utility for safe naming
- [x] Cross-platform path handling
- [x] Documentation (README, schemas, overview)

### Technical Stack

- Python 3.10+
- pathlib (stdlib)
- argparse (stdlib)
- json (stdlib)

### Commands Implemented

```bash
python -m team_creator_studio where
python -m team_creator_studio create-team --team "Team Name"
python -m team_creator_studio create-project --team "Team Name" --project "Project Name"
```

### Success Criteria

- ✅ No external dependencies
- ✅ Works on Windows, macOS, and Linux
- ✅ Clean, documented code
- ✅ Full workspace structure creation

---

## Milestone 2: Editor Core - Image Load & Non-Destructive Color Replace ✅

**Status:** Complete
**Goal:** Implement first real editing pipeline (headless CLI)

### Deliverables

- [x] Add Pillow dependency for image processing
- [x] Core data models (ProjectState, SourceImage, Layer, OperationRecord)
- [x] Image I/O primitives (load/save with RGBA conversion)
- [x] Color parsing utilities (hex, RGB, validation)
- [x] Non-destructive color replacement operation
- [x] Project rendering and compositing system
- [x] Import image into project
- [x] Apply color replace operations
- [x] Export project to PNG
- [x] Display project information

### Technical Stack

- Python 3.10+
- Pillow (10.0+) for image processing
- NumPy (via Pillow) for efficient color operations
- Euclidean distance for color matching

### New Commands

```bash
# Import an image into a project
python -m team_creator_studio import-image \
  --team "Team Name" \
  --project "Project Name" \
  --path "/path/to/image.png"

# Replace a color (with tolerance)
python -m team_creator_studio color-replace \
  --team "Team Name" \
  --project "Project Name" \
  --target "#FFFFFF" \
  --new "#9CFF00" \
  --tolerance 25 \
  --preserve-alpha true

# Export final result
python -m team_creator_studio export \
  --team "Team Name" \
  --project "Project Name" \
  --name "output_filename" \
  --format png

# View project details
python -m team_creator_studio project-info \
  --team "Team Name" \
  --project "Project Name"
```

### Key Features

**Non-Destructive Operations**
- Operations are append-only in project history
- Each operation creates new output file
- Original images never modified
- Operations can be replayed/analyzed

**Color Replacement Algorithm**
- Euclidean distance in RGB space
- Configurable tolerance (0-255)
- Preserves alpha channel by default
- Vectorized with NumPy for performance

**Project State Management**
- JSON-serialized project metadata
- Tracks source images, layers, operations
- Relative paths for portability
- Timestamps for all changes

### Technical Implementation

**Module Structure:**
```
src/team_creator_studio/
├── core/
│   ├── models.py         # Data models (ProjectState, Layer, etc.)
│   └── renderer.py       # Compositing system
├── imaging/
│   ├── io.py            # Image load/save
│   └── color.py         # Color parsing and conversion
├── ops/
│   └── color_replace.py # Color replacement operation
└── storage/
    └── workspace.py     # Updated with ProjectState support
```

**Data Flow:**
1. Import: Copy to source_uploads/ → Create SourceImage → Create Layer in working/
2. Operation: Load input → Apply operation → Save to working/ops/ → Create OperationRecord
3. Render: Composite from last operation or base layer → Save to working/composite.png
4. Export: Copy composite to exports/ with proper naming

### Success Criteria

- ✅ Image import works with any PNG
- ✅ Color replace correctly identifies and replaces colors within tolerance
- ✅ Alpha channel preserved for transparent images
- ✅ Operations recorded in project.json
- ✅ Composite rendered after each operation
- ✅ Export creates game-ready PNG
- ✅ project-info displays complete project state
- ✅ All paths stored as relative (portable)

### Example Workflow

```bash
# Create project and import logo
python -m team_creator_studio create-project \
  --team "Pembroke Dominion" \
  --project "Logo Recolor"

python -m team_creator_studio import-image \
  --team "Pembroke Dominion" \
  --project "Logo Recolor" \
  --path "logo_white.png"

# Replace white with green
python -m team_creator_studio color-replace \
  --team "Pembroke Dominion" \
  --project "Logo Recolor" \
  --target "#FFFFFF" \
  --new "#00FF00" \
  --tolerance 10

# Export result
python -m team_creator_studio export \
  --team "Pembroke Dominion" \
  --project "Logo Recolor" \
  --name "logo_green"

# Check project status
python -m team_creator_studio project-info \
  --team "Pembroke Dominion" \
  --project "Logo Recolor"
```

---

## Milestone 3: Operation Management & Undo/Redo ✅

**Status:** Complete
**Goal:** Add operation stack management, undo/redo, and project maintenance commands

### Deliverables

- [x] Operation stack model with active_op_index
- [x] Undo/redo functionality
- [x] List teams command
- [x] List projects command
- [x] List operations command with active marker
- [x] Delete operation command
- [x] Reset project command
- [x] Metadata validation and auto-repair system
- [x] Migration support for Milestone 2 projects

### Technical Stack

- Pattern A: active_op_index (-1 = base layer, 0+ = operation index)
- Append-only operation history
- Non-destructive undo/redo (re-uses existing operation outputs)
- Automatic project state validation and repair

### New Commands

```bash
# List all teams
python -m team_creator_studio list-teams

# List projects for a team
python -m team_creator_studio list-projects --team "Team Name"

# List operations with active marker
python -m team_creator_studio list-ops --team "Team Name" --project "Project Name"

# Undo last operation
python -m team_creator_studio undo --team "Team Name" --project "Project Name"

# Redo next operation
python -m team_creator_studio redo --team "Team Name" --project "Project Name"

# Delete operation by ID (full or prefix >= 6 chars)
python -m team_creator_studio delete-op \
  --team "Team Name" \
  --project "Project Name" \
  --id "abc123"

# Reset project (preserves source uploads)
python -m team_creator_studio reset-project \
  --team "Team Name" \
  --project "Project Name"
```

### Key Features

**Undo/Redo Stack**
- Operations stored as append-only history
- `active_op_index` tracks current state (-1 to len-1)
- Undo: decrements index, re-renders from previous op
- Redo: increments index, re-renders from next op
- Adding operation after undo: truncates future operations (standard behavior)

**Operation Management**
- List operations with type, parameters, timestamps
- Active operation marked with `*`
- Delete by full UUID or unique prefix (>=6 chars)
- Safe deletion with active_op_index adjustment

**Project Reset**
- Deletes working/, layers/, masks/, history/ contents
- Preserves source_uploads/ (original images)
- Resets operations to empty, active_op_index to -1
- Requires confirmation prompt

**Validation & Repair**
- Auto-detects and fixes invalid active_op_index
- Migrates Milestone 2 projects (adds active_op_index)
- Validates operation output files exist
- Normalizes paths to relative
- Re-renders composite if missing/invalid

### Technical Implementation

**Operation Stack Model (Pattern A)**
```python
class ProjectState:
    operations: List[OperationRecord]  # Full history
    active_op_index: int  # -1 or 0..len-1

    # -1: No operations applied (use base layer)
    # 0: Apply first operation only
    # N: Apply operations 0 through N
```

**Undo/Redo Behavior**
- `can_undo()`: Returns True if active_op_index >= 0
- `can_redo()`: Returns True if active_op_index < len(operations) - 1
- Undo sets active_op_index -= 1, triggers re-render
- Redo sets active_op_index += 1, triggers re-render
- No re-processing: uses existing operation output files

**Delete Operation Logic**
```
If deleted_index < active_index:
    active_index -= 1  # Shift down
If deleted_index == active_index:
    active_index = deleted_index - 1  # Move to previous
If deleted_index > active_index:
    # No change to active_index
```

**Validation System**
- Called at start of every command that loads project state
- Automatically repairs common issues
- Saves repaired state if changes made
- Prints repair actions when verbose=True

### Migration

**Milestone 2 → Milestone 3:**
- Projects without `active_op_index` auto-migrated
- If operations exist: set to `len(operations) - 1`
- If no operations: set to `-1`
- No manual intervention required

### Success Criteria

- ✅ list-teams shows all teams with metadata
- ✅ list-projects shows projects for a team
- ✅ list-ops displays operations with active marker
- ✅ Undo moves backwards through operation history
- ✅ Redo moves forward through operation history
- ✅ Adding operation after undo truncates redo stack
- ✅ delete-op removes record and file, adjusts active_op_index
- ✅ reset-project preserves sources, deletes derived files
- ✅ Validation auto-repairs missing/invalid active_op_index
- ✅ Milestone 2 projects automatically migrated
- ✅ Renderer respects active_op_index
- ✅ All existing commands still work

### Example Workflows

**Undo/Redo Workflow:**
```bash
# Import and apply two color replacements
python -m team_creator_studio import-image --team "Team" --project "Logo" --path "logo.png"
python -m team_creator_studio color-replace --team "Team" --project "Logo" --target "#FFF" --new "#0F0" --tolerance 10
python -m team_creator_studio color-replace --team "Team" --project "Logo" --target "#000" --new "#00F" --tolerance 10

# List operations (active_op_index = 1)
python -m team_creator_studio list-ops --team "Team" --project "Logo"
# Output:
# Idx  Active  ID         Type           ...
# 0            abc12345   color_replace  ...
# 1    *       def67890   color_replace  ...

# Undo to first color replacement
python -m team_creator_studio undo --team "Team" --project "Logo"
# active_op_index now 0

# Apply different operation (truncates operation 1)
python -m team_creator_studio color-replace --team "Team" --project "Logo" --target "#000" --new "#F00" --tolerance 5
# Operations: [0, new_2], active_op_index = 1
```

**Project Cleanup:**
```bash
# List operations to find ID
python -m team_creator_studio list-ops --team "Team" --project "Logo"

# Delete specific operation
python -m team_creator_studio delete-op --team "Team" --project "Logo" --id "abc123"

# Or reset entire project
python -m team_creator_studio reset-project --team "Team" --project "Logo"
# Confirms before deletion
```

---

## Milestone 4: GUI Foundation (Tkinter) ✅

**Status:** Complete
**Goal:** Create desktop application with Tkinter that wraps existing core logic

### Deliverables

- [x] Service layer for shared logic between CLI and GUI
- [x] Main application window (Tkinter)
- [x] Project browser with teams and projects list
- [x] Image viewer with scaling
- [x] Toolbar (Import, Undo, Redo, Refresh, Export)
- [x] Color Replace panel with HEX/RGB inputs
- [x] Tolerance slider (0-100)
- [x] Preserve alpha checkbox
- [x] Scrollable lists with mouse wheel support
- [x] Resize-safe layout
- [x] Error handling with messageboxes
- [x] Launch via `python -m team_creator_studio gui`

### Technical Stack

- Tkinter (stdlib) for GUI
- PIL.ImageTk for image display
- Service layer pattern for code reuse
- Existing core modules (no duplication)

### Architecture

**Service Layer** (`core/services.py`):
- `ProjectService` class with methods for all operations
- Used by both CLI and GUI
- Handles: import, color replace, undo, redo, export
- Returns structured data or raises ValueError

**UI Structure**:
```
src/team_creator_studio/ui/
├── __init__.py
├── app.py                 # Main application controller
├── theme.py              # Colors, fonts, spacing constants
├── views/
│   ├── project_browser.py   # Teams/projects list
│   └── editor_view.py       # Image viewer + controls
└── widgets/
    └── scrollable_frame.py  # Reusable scroll container
```

**Layout**:
```
┌──────────────────────────────────────────────────┐
│  Team Creation Studio                            │
├──────────────┬───────────────────────────────────┤
│ Project      │  [Import] [Undo] [Redo] [Refresh] │
│ Browser      │  [Export]           Status: Ready  │
│              ├───────────────────────────────────┤
│ Teams:       │                                    │
│ ┌──────────┐ │      Image Viewer                 │
│ │ Team 1   │ │      (scaled to fit)              │
│ │ Team 2   │ │                                    │
│ └──────────┘ │                                    │
│ [New Team]   │                                    │
│              ├───────────────────────────────────┤
│ Projects:    │  Color Replace Panel:              │
│ ┌──────────┐ │  Target: HEX [      ] RGB [     ] │
│ │ Project1 │ │  New:    HEX [      ] RGB [     ] │
│ │ Project2 │ │  Tolerance: [======] [50]         │
│ └──────────┘ │  [✓] Preserve alpha               │
│ [New Project]│  [Apply Color Replace]            │
│ [Open Proj]  │                                    │
└──────────────┴───────────────────────────────────┘
```

### Commands

**Launch GUI:**
```bash
python -m team_creator_studio gui
```

**CLI commands remain unchanged** - all Milestone 2-3 commands still work.

### Key Features

**Project Browser**
- Lists all teams with metadata
- Lists projects for selected team
- Double-click to open project
- New Team / New Project buttons
- Scrollable lists with mouse wheel

**Image Viewer**
- Displays current composite image
- Scales to fit canvas while preserving aspect ratio
- Updates automatically after operations
- Placeholder text when no image loaded

**Color Replace Panel**
- Target color: HEX or RGB input (HEX takes precedence)
- New color: HEX or RGB input
- Tolerance slider: 0-100 with synced numeric entry
- Preserve alpha checkbox (default: checked)
- Apply button calls existing core logic

**Toolbar Operations**
- Import Image: File dialog → calls `service.import_image()`
- Undo: Calls `service.undo_operation()` → refreshes display
- Redo: Calls `service.redo_operation()` → refreshes display
- Refresh: Reloads composite image from disk
- Export: Dialog for name → calls `service.export_project()`

**Error Handling**
- All errors shown in messagebox dialogs
- Status label shows current operation
- No raw tracebacks shown to user
- Clear error messages for common issues

### Technical Implementation

**Service Layer Pattern:**
```python
# GUI calls service
service = ProjectService()
operation = service.apply_color_replace_operation(
    team_name, project_name, target, new, tolerance, preserve_alpha
)

# Service uses existing core
from team_creator_studio.ops.color_replace import apply_color_replace
result_image = apply_color_replace(input_image, ...)
```

**Image Display:**
```python
# Load with PIL
image = Image.open(image_path)

# Scale to fit canvas
scale = min(canvas_width/img_width, canvas_height/img_height, 1.0)
resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

# Convert to PhotoImage and display
photo = ImageTk.PhotoImage(resized)
canvas.create_image(x, y, image=photo, anchor="center")
```

**Scroll Safety:**
```python
# Mouse wheel works on all platforms
canvas.bind_all("<MouseWheel>", self._on_mousewheel)  # Windows/macOS
canvas.bind_all("<Button-4>", self._on_mousewheel)    # Linux scroll up
canvas.bind_all("<Button-5>", self._on_mousewheel)    # Linux scroll down
```

### Success Criteria

- ✅ `python -m team_creator_studio gui` launches window
- ✅ Teams/projects populate from workspace
- ✅ Selecting project loads and displays composite
- ✅ Import image updates project and viewer
- ✅ Color replace applies and updates viewer + operations
- ✅ Undo/redo works and viewer updates
- ✅ Export writes PNG and shows success dialog
- ✅ Resizing window works without breaking layout
- ✅ Lists scroll with mouse wheel
- ✅ No UI elements become unreachable
- ✅ Runs on Windows without additional installs (beyond Pillow)
- ✅ Error dialogs show clear messages
- ✅ All padding/spacing values are integers
- ✅ Font fallbacks work correctly

### Common Issues & Fixes

**Issue: ImageTk reference garbage collected**
- Fix: Keep reference in instance variable (`self.photo_image = ...`)

**Issue: Path not found errors**
- Fix: Service layer normalizes all paths, validation runs on load

**Issue: Missing composite after undo**
- Fix: Renderer respects `active_op_index`, re-renders on undo/redo

**Issue: Mouse wheel doesn't work**
- Fix: Bind to `<MouseWheel>`, `<Button-4>`, `<Button-5>` for cross-platform

**Issue: Window resize breaks layout**
- Fix: Use `pack(fill="both", expand=True)` and `<Configure>` bindings

### Example Workflow

```bash
# Launch GUI
python -m team_creator_studio gui

# In GUI:
# 1. Select a team from the list (or create new team)
# 2. Select a project (or create new project)
# 3. Click "Import Image" to add an image
# 4. Enter target color (e.g., #FFFFFF or 255,255,255)
# 5. Enter new color (e.g., #00FF00 or 0,255,0)
# 6. Adjust tolerance slider
# 7. Click "Apply Color Replace"
# 8. Use Undo/Redo to navigate history
# 9. Click "Export" to save final image

# CLI still works for automation:
python -m team_creator_studio color-replace \
  --team "Team Name" \
  --project "Project Name" \
  --target "#FFFFFF" \
  --new "#00FF00" \
  --tolerance 25
```

### Migration Notes

- CLI commands unchanged - no breaking changes
- Service layer is new but optional (CLI can continue using inline code)
- GUI is additive - doesn't affect existing workflows
- Same project format - no migration needed
- Workspace structure unchanged

---

## Milestone 5: Canvas & Real Layer System ✅

**Status:** Complete
**Goal:** Implement multi-layer compositing with canvas settings and comprehensive layer management

### Deliverables

- [x] Multi-layer compositing engine with visibility/opacity/positioning
- [x] Canvas settings (width, height, background, DPI)
- [x] Layer panel UI in GUI (three-column layout)
- [x] Layer operations service layer
- [x] Layer-specific operation outputs
- [x] CLI layer management commands
- [x] Layer visibility toggle
- [x] Layer opacity control (0-100%)
- [x] Layer ordering (move up/down)
- [x] Layer positioning (x, y)
- [x] Layer renaming
- [x] Layer deletion with guardrails
- [x] Active layer selection (top-most visible)
- [x] Non-destructive per-layer operations
- [x] Backward compatibility with Milestones 2-4

### Technical Stack

- Pillow for RGBA compositing
- NumPy for opacity alpha blending
- Service layer pattern for shared logic
- UUID prefix matching (>=6 chars)
- Pattern A undo/redo with layer support

### Architecture

**Enhanced Data Models**:
```python
class ProjectState:
    # Canvas settings (added)
    canvas_width: int = 1024
    canvas_height: int = 1024
    canvas_background: str = "transparent"
    canvas_dpi: Optional[int] = None

    # Layer management methods (added)
    def get_sorted_layers() -> List[Layer]
    def move_layer_up/down(layer_id) -> bool
    def delete_layer(layer_id) -> Optional[Layer]
    def set_layer_visibility/opacity/position(...)
    def normalize_layer_order()

class Layer:
    # New fields
    order: int  # Layer stacking order (0=bottom, higher=top)
    x: int  # X position on canvas
    y: int  # Y position on canvas

class OperationRecord:
    # Layer-specific output
    output_layer_path: Optional[str]  # e.g., "working/layers/<layer_id>/<op_id>_color_replace.png"
```

**Service Layer** (`core/services.py`):
New methods for layer management:
- `resolve_layer_id(project_state, layer_id)` - Select active layer or resolve ID
- `add_layer_from_image(team, project, image_path, name)` - Add layer with auto-ordering
- `set_layer_visibility(team, project, layer_id, visible)` - Toggle visibility
- `set_layer_opacity(team, project, layer_id, opacity)` - Set 0.0-1.0 opacity
- `set_layer_position(team, project, layer_id, x, y)` - Reposition layer
- `rename_layer(team, project, layer_id, name)` - Rename layer
- `move_layer(team, project, layer_id, direction)` - Move up/down
- `delete_layer(team, project, layer_id)` - Delete with guardrail
- `apply_color_replace_to_layer(...)` - Layer-specific operations

**Renderer** (`core/renderer.py`):
Complete rewrite for multi-layer compositing:
```python
def render_project(project_state, project_path):
    # Create transparent RGBA canvas
    canvas = Image.new("RGBA", (canvas_width, canvas_height), (0, 0, 0, 0))

    # Composite layers bottom-to-top
    for layer in get_sorted_layers():
        if not layer.visible:
            continue

        # Load layer bitmap (respects active_op_index)
        layer_image = get_layer_bitmap_path(project_state, layer, project_path)

        # Apply opacity via NumPy alpha blending
        if layer.opacity < 1.0:
            # Multiply alpha channel by opacity

        # Paste at (x, y) position with alpha compositing
        canvas.paste(layer_image, (layer.x, layer.y), layer_image)

    # Save to working/composite.png
```

**UI Structure**:
```
src/team_creator_studio/ui/
├── views/
│   ├── layers_panel.py  # NEW: Layers management panel
│   └── editor_view.py   # Updated: Target layer indicator
└── app.py               # Updated: Three-column layout, layer callbacks
```

**Three-Column Layout**:
```
┌─────────────┬────────────────────────┬──────────────┐
│  Browser    │     Editor             │  Layers      │
│  (Teams &   │  [Toolbar]             │  Panel       │
│  Projects)  │  ┌──────────────────┐  │              │
│             │  │  Image Viewer    │  │  Layers List │
│             │  │  (composite)     │  │  ┌────────┐  │
│             │  └──────────────────┘  │  │☑ Layer1│  │
│             │  Color Replace Panel:  │  │☐ Layer2│  │
│             │  Target Layer: <name>  │  └────────┘  │
│             │  [Target/New colors]   │  [Add] [Del] │
│             │  [Apply] (disabled     │  [Up] [Down] │
│             │   if no layer)         │              │
│             │                        │  Properties: │
│             │                        │  Name: [   ] │
│             │                        │  Opacity: 50 │
│             │                        │  Pos: X Y    │
└─────────────┴────────────────────────┴──────────────┘
```

### New CLI Commands

```bash
# Add layer from image
python -m team_creator_studio add-layer \
  --team "Team" --project "Project" \
  --path "/path/to/image.png" \
  --name "Logo Layer"

# List all layers
python -m team_creator_studio layers \
  --team "Team" --project "Project"
# Output:
# Order  ID        Name           Visible  Opacity  X     Y
# 2      abc12345  Logo Layer     Yes      100%     0     0
# 1      def67890  Background     Yes      80%      0     0
# 0      ghi24680  Base           Yes      100%     0     0

# Set layer properties
python -m team_creator_studio set-layer \
  --team "Team" --project "Project" \
  --layer-id "abc123" \
  --visible true \
  --opacity 75 \
  --x 100 --y 50 \
  --name "New Name"

# Move layer in stack
python -m team_creator_studio move-layer \
  --team "Team" --project "Project" \
  --layer-id "abc123" \
  --direction up

# Delete layer
python -m team_creator_studio delete-layer \
  --team "Team" --project "Project" \
  --layer-id "abc123"

# Apply operation to specific layer
python -m team_creator_studio color-replace \
  --team "Team" --project "Project" \
  --target "#FFF" --new "#0F0" \
  --tolerance 10 \
  --layer-id "abc123"  # NEW: Optional layer targeting
```

### Key Features

**Multi-Layer Compositing**
- Bottom-to-top layer stacking with integer order
- Per-layer visibility toggle (show/hide)
- Per-layer opacity (0-100%, applied to alpha channel)
- Per-layer positioning (x, y coordinates)
- Alpha blending with NumPy for performance
- Transparent RGBA canvas

**Layer Management**
- Add layer: Uploads image, assigns order = max+1
- Delete layer: Guardrail prevents deleting last layer
- Move up/down: Swaps order, normalizes gaps
- Rename: In-place name change (no re-render)
- Set properties: Visibility, opacity, position (all trigger re-render)

**Active Layer Selection**
- Top-most visible layer selected by default
- Falls back to highest order if none visible
- Operations apply to active layer unless --layer-id specified
- GUI shows "Target Layer: <name>" in color replace panel

**Layer-Specific Operations**
- Operations save to `working/layers/<layer_id>/<op_id>_<type>.png`
- `OperationRecord.output_layer_path` tracks layer-specific outputs
- Renderer finds latest operation output per layer via `active_op_index`
- Undo/redo works correctly with layer operations

**Canvas Settings**
- Width, height (default 1024x1024)
- Background color (default transparent)
- DPI metadata (optional)
- Auto-inferred from first layer if not set

**Layers Panel (GUI)**
- Scrollable layers list (top to bottom)
- Visibility checkbox per layer
- Click layer name to select
- Selected layer highlighted
- Controls: Add Layer (file dialog), Delete Layer (with confirmation), Move Up, Move Down
- Properties panel: Name entry + Rename button, Opacity slider (0-100) with value label, X/Y position fields + Apply button
- Auto-updates on all operations

### Migration & Compatibility

**Automatic Migration**:
- Projects without canvas settings: infer from first layer image
- Projects with single layer at order=0: works unchanged
- Projects without layer order: normalized to 0, 1, 2...
- Legacy operations without `output_layer_path`: uses `output_path`

**Backward Compatibility**:
- All Milestone 2-4 projects load and work correctly
- Validation auto-repairs missing layer properties
- Single-layer projects continue working as before
- CLI commands from previous milestones unchanged (except color-replace gains optional --layer-id)

### Technical Implementation

**Layer Resolution Logic**:
```python
def resolve_layer_id(project_state, layer_id=None):
    if layer_id:
        # Exact match or prefix (>=6 chars)
        return matched_layer.id

    # Choose active layer
    sorted_layers = get_sorted_layers()  # Bottom to top
    visible_layers = [l for l in sorted_layers if l.visible]

    if visible_layers:
        return visible_layers[-1].id  # Top-most visible
    else:
        return sorted_layers[-1].id  # Highest order
```

**Get Layer Bitmap Path**:
```python
def get_layer_bitmap_path(project_state, layer, project_path):
    # Find latest operation for this layer up to active_op_index
    latest_op_path = None

    for i in range(project_state.active_op_index + 1):
        op = project_state.operations[i]
        if op.input_layer_id == layer.id:
            latest_op_path = op.output_layer_path or op.output_path

    # Use operation output if found, otherwise layer's original path
    return latest_op_path or layer.layer_path
```

**Opacity Application**:
```python
# NumPy-based alpha blending
if layer.opacity < 1.0:
    r, g, b, a = layer_image.split()
    alpha_array = np.array(a, dtype=np.float32)
    alpha_array = alpha_array * layer.opacity  # Multiply by 0.0-1.0
    a = Image.fromarray(alpha_array.astype(np.uint8), mode='L')
    layer_image = Image.merge("RGBA", (r, g, b, a))
```

**Layer Deletion Guardrail**:
```python
def delete_layer(self, team, project, layer_id):
    project_state, project_path = self.load_project(team, project)

    if len(project_state.layers) == 1:
        raise ValueError("Cannot delete the last remaining layer")

    # Delete layer, remove associated operations, delete working files
    # Re-render composite
```

### Success Criteria

- ✅ Multi-layer projects render correctly with visibility/opacity/position
- ✅ Add layer uploads image and assigns next order
- ✅ Delete layer removes layer + operations + working files
- ✅ Cannot delete last remaining layer
- ✅ Move up/down swaps order correctly
- ✅ Rename layer works without re-rendering
- ✅ Set opacity/position triggers re-render
- ✅ Visibility toggle shows/hides layers in composite
- ✅ Active layer auto-selected (top-most visible)
- ✅ Layer operations save to layer-specific paths
- ✅ Renderer respects active_op_index for each layer
- ✅ Undo/redo works with layer operations
- ✅ GUI layers panel lists all layers (scrollable)
- ✅ GUI layer selection updates properties panel
- ✅ GUI shows "Target Layer" in color replace panel
- ✅ GUI disables Apply if no layer selected
- ✅ CLI layers command lists all layers
- ✅ CLI layer commands support UUID prefix matching
- ✅ Milestone 2-4 projects load and work correctly
- ✅ Validation auto-repairs canvas settings and layer order

### Example Workflow

**Multi-Layer Workflow (CLI)**:
```bash
# Create project
python -m team_creator_studio create-project --team "Team" --project "Game Logo"

# Add base layer
python -m team_creator_studio add-layer --team "Team" --project "Game Logo" --path "background.png" --name "Background"

# Add logo layer
python -m team_creator_studio add-layer --team "Team" --project "Game Logo" --path "logo.png" --name "Logo"

# List layers
python -m team_creator_studio layers --team "Team" --project "Game Logo"
# Order  ID        Name        Visible  Opacity  X  Y
# 1      def123    Logo        Yes      100%     0  0
# 0      abc456    Background  Yes      100%     0  0

# Apply color replace to logo layer only
python -m team_creator_studio color-replace \
  --team "Team" --project "Game Logo" \
  --target "#FFFFFF" --new "#00FF00" \
  --tolerance 10 \
  --layer-id "def123"

# Adjust logo layer opacity
python -m team_creator_studio set-layer \
  --team "Team" --project "Game Logo" \
  --layer-id "def123" \
  --opacity 80

# Position logo layer
python -m team_creator_studio set-layer \
  --team "Team" --project "Game Logo" \
  --layer-id "def123" \
  --x 100 --y 50

# Export composite
python -m team_creator_studio export --team "Team" --project "Game Logo" --name "logo_final"
```

**Multi-Layer Workflow (GUI)**:
```
1. Launch: python -m team_creator_studio gui
2. Select team and project (or create new)
3. Click "Add Layer" → Select background.png
4. Click "Add Layer" → Select logo.png
5. Layers panel shows both layers (top to bottom)
6. Select "Logo" layer in layers panel
7. Editor shows "Target Layer: Logo"
8. Enter target/new colors in color replace panel
9. Click "Apply Color Replace" (applies to Logo layer only)
10. Adjust opacity slider in layers panel → 80%
11. Change position X=100, Y=50 → Click "Apply Position"
12. Composite updates automatically
13. Click "Export" to save final image
```

---

## Milestone 6: Basic Drawing Tools

**Status:** Planned
**Goal:** Implement fundamental drawing and painting tools

### Deliverables

- [ ] Brush tool (customizable size/hardness)
- [ ] Eraser tool
- [ ] Pencil tool
- [ ] Fill bucket tool
- [ ] Color picker
- [ ] Palette panel integration
- [ ] Stroke smoothing
- [ ] Pressure sensitivity (tablet support)
- [ ] Undo/redo system

### Technical Requirements

- Pillow or NumPy for image manipulation
- Efficient brush rendering
- Support graphics tablets (Wacom, etc.)
- History stack implementation

---

## Milestone 7: Transform & Selection Tools

**Status:** Planned
**Goal:** Add transform operations and selection tools

### Deliverables

- [ ] Move tool (layer positioning)
- [ ] Transform tool (scale, rotate, skew)
- [ ] Free transform
- [ ] Rectangle/ellipse selection
- [ ] Lasso selection
- [ ] Magic wand selection
- [ ] Selection operations (add, subtract, intersect)
- [ ] Crop tool
- [ ] Canvas resize

### Technical Requirements

- Implement affine transformations
- Selection mask rendering
- Anti-aliasing for transforms
- Interactive transform handles

---

## Milestone 8: Export Pipeline

**Status:** Planned
**Goal:** Implement comprehensive export functionality

### Deliverables

- [ ] Export dialog
- [ ] Multiple format support (PNG, JPG, SVG, WEBP)
- [ ] Quality/compression settings
- [ ] Batch export
- [ ] Sprite sheet generation
- [ ] Export presets (web, mobile, print)
- [ ] Metadata embedding
- [ ] Export history tracking

### Supported Formats

- **PNG**: With transparency, various bit depths
- **JPG**: Quality control, no transparency
- **SVG**: Vector export (for vector layers)
- **WEBP**: Modern web format
- **GIF**: Animated exports (future)

---

## Milestone 9: AI-Powered Features (Optional)

**Status:** Future
**Goal:** Integrate AI tools for enhanced productivity

### Potential Deliverables

- [ ] Background removal
- [ ] Smart segmentation
- [ ] Object detection and masking
- [ ] Style transfer
- [ ] Upscaling (super-resolution)
- [ ] Content-aware fill
- [ ] Auto-color correction

### Technical Requirements

- PyTorch or TensorFlow
- Pre-trained models (SAM, U-Net, etc.)
- GPU acceleration (CUDA support)
- Model download management

### Considerations

- Large dependency footprint
- GPU requirements
- Privacy concerns (local vs. cloud)
- Performance on various hardware

---

## Milestone 10: Collaboration Features

**Status:** Future
**Goal:** Enable team collaboration and asset sharing

### Potential Deliverables

- [ ] Project sharing
- [ ] Team asset library
- [ ] Version control integration (Git)
- [ ] Comments and annotations
- [ ] Change tracking
- [ ] Conflict resolution
- [ ] Cloud sync (optional)
- [ ] Real-time collaboration (optional)

---

## Milestone 11: Polish & Release

**Status:** Future
**Goal:** Prepare for public release

### Deliverables

- [ ] Comprehensive test suite
- [ ] Performance optimization
- [ ] Keyboard shortcuts
- [ ] Tutorial system
- [ ] Example projects
- [ ] Video tutorials
- [ ] Plugin API
- [ ] Installer packages (Windows, macOS, Linux)
- [ ] Documentation website
- [ ] Community forums

---

## Long-Term Vision

### Year 1
- Complete Milestones 1-8
- Stable 1.0 release
- Active user community
- Regular bug fix releases

### Year 2
- Plugin ecosystem
- AI feature integration
- Mobile companion app (viewer)
- Cloud storage integration

### Year 3
- Advanced vector tools
- Animation support
- 3D integration (optional)
- Enterprise features

---

## Contributing

We welcome contributions to any milestone. Priority areas:

1. **Current Focus**: Milestone 6 (Basic Drawing Tools)
2. **High Impact**: Milestone 7 (Transform & Selection Tools)
3. **Future Work**: Milestones 8+ (in order)

### How to Contribute

1. Check the current milestone deliverables
2. Pick an unassigned task
3. Open an issue to discuss approach
4. Submit pull request with tests and docs
5. Respond to code review feedback

### Development Workflow

```bash
# Create feature branch
git checkout -b feature/milestone-2-list-teams

# Implement feature
# Write tests
# Update documentation

# Submit PR
git push origin feature/milestone-2-list-teams
```

---

## Questions?

For milestone planning questions or suggestions, please:

- Open a GitHub issue with the `milestone` label
- Tag with specific milestone number (e.g., `milestone-3`)
- Provide detailed use cases and requirements

---

**Last Updated:** 2026-01-16
**Current Milestone:** 5 (Complete - Canvas & Real Layer System)
**Next Milestone:** 6 (Basic Drawing Tools)
