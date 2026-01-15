# Workspace Schema Documentation

This document describes the structure and schema for Team Creation Studio's workspace organization.

## Overview

The workspace uses a hierarchical structure to organize teams, projects, and assets. All metadata is stored in JSON format with UTF-8 encoding and 2-space indentation.

## Directory Structure

```
workspace/
├── templates/                          # JSON schema definitions
│   ├── project_meta.schema.json       # Project metadata schema
│   └── palette.schema.json            # Palette schema
└── teams/                              # Team directories
    └── <team-slug>/                    # Slugified team name
        ├── team.json                   # Team metadata
        └── projects/                   # Project directories
            └── <project-slug>/         # Slugified project name
                ├── source_uploads/     # Original uploaded assets
                ├── working/            # Temporary working files
                ├── layers/             # Layer data files
                ├── masks/              # Mask and selection data
                ├── exports/            # Final exported assets
                ├── meta/               # Project metadata
                │   └── project.json
                ├── palettes/           # Color palettes
                │   └── palette.json
                └── history/            # Edit history (future)
```

## Slug Generation

All team and project names are converted to slugs for filesystem safety:

**Rules:**
- Lowercase only
- Spaces and underscores become hyphens
- Remove accents and diacritics
- Keep only alphanumeric characters and hyphens
- Collapse multiple hyphens
- Strip leading/trailing hyphens

**Examples:**
```
"Pembroke Dominion"  → "pembroke-dominion"
"Primary Logo v1"    → "primary-logo-v1"
"Test___Project!!"   → "test-project"
```

## Team Schema

**File:** `workspace/teams/<team-slug>/team.json`

```json
{
  "name": "Human-readable team name",
  "slug": "team-slug",
  "created_at": "2026-01-15T12:00:00Z",
  "description": "Optional team description",
  "members": [
    {
      "name": "Member Name",
      "role": "admin|member|viewer",
      "email": "member@example.com"
    }
  ]
}
```

**Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | Yes | Original team name |
| slug | string | Yes | Filesystem-safe slug |
| created_at | string | Yes | ISO 8601 timestamp (UTC) |
| description | string | No | Team description |
| members | array | No | Team member list |

## Project Schema

**File:** `workspace/teams/<team-slug>/projects/<project-slug>/meta/project.json`

```json
{
  "name": "Project Name",
  "slug": "project-slug",
  "team": {
    "name": "Team Name",
    "slug": "team-slug"
  },
  "created_at": "2026-01-15T12:00:00Z",
  "updated_at": "2026-01-15T12:00:00Z",
  "version": "1.0",
  "description": "Project description",
  "tags": ["logo", "branding", "game-asset"],
  "canvas": {
    "width": 1024,
    "height": 1024,
    "background_color": "#FFFFFF"
  },
  "layers": [
    {
      "id": "layer-uuid",
      "name": "Layer Name",
      "type": "raster|vector|text|group",
      "visible": true,
      "opacity": 1.0,
      "blend_mode": "normal",
      "locked": false,
      "position": {"x": 0, "y": 0},
      "size": {"width": 1024, "height": 1024},
      "file_ref": "layers/layer-uuid.png"
    }
  ],
  "active_layer": "layer-uuid",
  "palette_id": "default"
}
```

**Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | Yes | Project name |
| slug | string | Yes | Filesystem-safe slug |
| team | object | Yes | Parent team reference |
| created_at | string | Yes | Creation timestamp (UTC) |
| updated_at | string | Yes | Last modified timestamp (UTC) |
| version | string | Yes | Schema version |
| description | string | No | Project description |
| tags | array | No | Searchable tags |
| canvas | object | Yes | Canvas dimensions and settings |
| layers | array | Yes | Layer definitions |
| active_layer | string | No | Currently active layer ID |
| palette_id | string | Yes | Active palette reference |

### Canvas Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| width | integer | Yes | Canvas width in pixels |
| height | integer | Yes | Canvas height in pixels |
| background_color | string | Yes | Hex color (e.g., "#FFFFFF") |

### Layer Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | string | Yes | Unique layer identifier (UUID) |
| name | string | Yes | Layer name |
| type | string | Yes | Layer type (raster, vector, text, group) |
| visible | boolean | Yes | Layer visibility |
| opacity | number | Yes | Opacity (0.0 to 1.0) |
| blend_mode | string | Yes | Blend mode |
| locked | boolean | Yes | Edit lock status |
| position | object | Yes | Layer position (x, y) |
| size | object | Yes | Layer size (width, height) |
| file_ref | string | Yes | Relative path to layer data file |

## Palette Schema

**File:** `workspace/teams/<team-slug>/projects/<project-slug>/palettes/palette.json`

```json
{
  "id": "palette-id",
  "name": "Palette Name",
  "created_at": "2026-01-15T12:00:00Z",
  "colors": [
    {
      "name": "Color Name",
      "hex": "#FF0000",
      "rgb": [255, 0, 0],
      "hsv": [0, 100, 100]
    }
  ]
}
```

**Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | string | Yes | Unique palette identifier |
| name | string | Yes | Palette name |
| created_at | string | Yes | Creation timestamp (UTC) |
| colors | array | Yes | Color definitions |

### Color Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | Yes | Color name |
| hex | string | Yes | Hex color code (e.g., "#FF0000") |
| rgb | array | Yes | RGB values [0-255, 0-255, 0-255] |
| hsv | array | No | HSV values [0-360, 0-100, 0-100] |

## Directory Usage

### source_uploads/

Original asset files uploaded by users. These files are never modified.

**Contents:**
- Raw images (PNG, JPG, SVG, etc.)
- Reference images
- Source PSDs or other native formats

### working/

Temporary files created during editing sessions. Safe to delete.

**Contents:**
- Auto-saves
- Temporary renders
- Cache files

### layers/

Layer data files referenced by project.json.

**Contents:**
- Raster layer images (PNG with transparency)
- Vector layer data (JSON)
- Text layer data (JSON with font info)

**Naming:** `<layer-id>.<ext>` (e.g., `layer-uuid.png`)

### masks/

Selection and mask data for layers.

**Contents:**
- Alpha masks (grayscale PNG)
- Selection data (JSON)

**Naming:** `<layer-id>-mask.<ext>`

### exports/

Final exported assets ready for production use.

**Contents:**
- Exported images in various formats
- Sprite sheets
- Asset bundles

**Naming:** User-defined, typically includes version or timestamp

### meta/

Project metadata and configuration.

**Contents:**
- `project.json` (required)
- Additional metadata files (future)

### palettes/

Color palette files for the project.

**Contents:**
- `palette.json` (default palette)
- Additional palette files (e.g., `palette-dark.json`)

### history/

Edit history for undo/redo functionality (future implementation).

**Contents:**
- History snapshots
- Delta files for efficient storage

## File Formats

### Image Files

- **PNG**: Primary format for raster layers (supports transparency)
- **JPG**: Optional for layers without transparency
- **SVG**: Vector graphics (future)

### Metadata Files

- **JSON**: All metadata files
- **Encoding**: UTF-8 with BOM
- **Indentation**: 2 spaces
- **Line endings**: LF (Unix-style)

## Best Practices

### Timestamps

- Always use UTC timezone
- ISO 8601 format: `YYYY-MM-DDTHH:MM:SSZ`
- Include 'Z' suffix to indicate UTC

### File References

- Use relative paths from project root
- Forward slashes (/) even on Windows
- Example: `layers/layer-uuid.png`

### Color Values

- Hex colors: Always include '#' prefix, uppercase letters
- RGB: Integer values 0-255
- HSV: H=0-360, S=0-100, V=0-100

### Identifiers

- Use UUIDs for layers, palettes, etc.
- Use slugs for teams and projects
- Never reuse identifiers

## Validation

All JSON files should validate against the schemas in `workspace/templates/`.

**Schema files:**
- `project_meta.schema.json` - Project metadata validation
- `palette.schema.json` - Palette validation

Use JSON Schema validators to ensure data integrity.

## Migration

When schema versions change:

1. Update the `version` field in project.json
2. Run migration scripts to update data structure
3. Backup original files before migration
4. Validate migrated files against new schema

## Examples

See the `workspace/templates/` directory for example files and JSON schemas.
