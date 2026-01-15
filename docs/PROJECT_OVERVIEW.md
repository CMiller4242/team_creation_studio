# Team Creation Studio - Project Overview

## Vision

Team Creation Studio is a desktop application designed to streamline the creation of game-ready assets with a Photoshop-like editing experience. It provides a structured workspace for teams to collaborate on asset creation, manage layers, apply masks, and export production-ready graphics.

## Key Features

### Current Implementation (Milestone 1)

- **Workspace Management**: Hierarchical organization of teams and projects
- **CLI Tools**: Command-line interface for creating and managing workspace structures
- **Schema-Driven Architecture**: JSON schemas ensure consistent data structures
- **Cross-Platform**: Windows-compatible path handling with Python pathlib

### Planned Features

- **GUI Application**: Desktop interface with canvas-based editing
- **Layer Management**: Create, organize, and manipulate layers
- **Mask Tools**: Selection and masking for precise edits
- **Palette Management**: Color palette creation and management
- **Export Pipeline**: Multiple format support (PNG, JPG, SVG, etc.)
- **History/Undo**: Non-destructive editing with full history tracking
- **AI Integration**: Smart segmentation and background removal
- **Team Collaboration**: Shared projects and asset libraries

## Architecture

### Package Structure

```
team_creator_studio/
├── config/          # Configuration and settings
├── storage/         # Workspace and file management
├── utils/           # Utility functions (slugify, etc.)
├── gui/             # GUI components (future)
├── editor/          # Image editing core (future)
├── export/          # Export functionality (future)
└── ai/              # AI-powered features (future)
```

### Workspace Organization

```
workspace/
├── templates/       # JSON schemas
└── teams/           # Team directories
    └── <team-slug>/
        ├── team.json
        └── projects/
            └── <project-slug>/
                ├── source_uploads/   # Original assets
                ├── working/          # Temp files
                ├── layers/           # Layer data
                ├── masks/            # Mask data
                ├── exports/          # Final output
                ├── meta/             # Project metadata
                ├── palettes/         # Color palettes
                └── history/          # Edit history
```

## Design Principles

### 1. Scalability

- Modular architecture for easy extension
- Separation of concerns (storage, editing, UI)
- Plugin-ready design for future expansion

### 2. Data Integrity

- JSON schemas validate all metadata
- UTF-8 encoding for all text files
- Atomic file operations to prevent corruption

### 3. Cross-Platform Support

- pathlib for filesystem operations
- No OS-specific dependencies
- Windows, macOS, and Linux compatibility

### 4. Developer-Friendly

- Clean, readable code
- Comprehensive documentation
- Type hints for better IDE support
- Minimal dependencies in early stages

### 5. User-Centric

- Intuitive workspace organization
- Non-destructive editing
- Quick access to recent projects
- Customizable workflows

## Technology Stack

### Core

- **Python 3.10+**: Main programming language
- **pathlib**: Cross-platform filesystem operations
- **argparse**: CLI interface
- **json**: Metadata and configuration storage

### Future Dependencies

- **PyQt6 / PySide6**: GUI framework
- **Pillow**: Image manipulation
- **NumPy**: Array operations for image data
- **OpenCV**: Advanced image processing
- **Torch / TensorFlow**: AI-powered features (optional)

## Development Workflow

### Phase 1: Foundation (Current)

- Core workspace structure
- CLI tools for project management
- JSON schemas and documentation

### Phase 2: GUI Framework

- Desktop application shell
- Canvas rendering
- File browser and project navigation

### Phase 3: Editing Core

- Layer system implementation
- Basic drawing and painting tools
- Transform operations (scale, rotate, crop)

### Phase 4: Advanced Features

- Mask tools and selections
- Filters and effects
- Export pipeline

### Phase 5: AI Integration

- Smart segmentation
- Background removal
- Style transfer (optional)

### Phase 6: Collaboration

- Project sharing
- Team asset libraries
- Version control integration

## Target Users

### Primary

- **Indie Game Developers**: Small teams creating game assets
- **Graphic Designers**: Professionals working on digital art
- **Content Creators**: YouTube thumbnails, social media graphics

### Secondary

- **Hobbyists**: Learning digital art and game development
- **Students**: Educational use in game design courses
- **Prototype Artists**: Rapid asset creation for prototypes

## Success Metrics

### Technical

- Zero-dependency core installation
- < 100ms project load time
- Cross-platform compatibility (Windows, macOS, Linux)
- Stable API for future extensions

### User Experience

- < 5 minutes from installation to first project creation
- Intuitive workspace navigation
- Clear documentation and examples
- Active community engagement

## Roadmap

See [MILESTONES.md](MILESTONES.md) for detailed development timeline and feature breakdown.

## Contributing

This project welcomes contributions in the following areas:

- Core editing features
- GUI improvements
- Documentation and tutorials
- Performance optimizations
- Platform-specific testing

Please ensure all contributions:
- Follow the existing code style
- Include tests for new features
- Update documentation as needed
- Are cross-platform compatible

## License

MIT License - See [LICENSE](../LICENSE) for details.
