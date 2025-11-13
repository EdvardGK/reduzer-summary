# Project Structure

## Directory Layout

```
reduzer-summary/
├── docs/                    # All documentation (dev standards compliant)
│   ├── worklog/            # Development session logs
│   │   └── 2025-11-04-09-43_Project-Restructure.md
│   ├── plans/              # Planning documents (empty)
│   ├── research/           # Research notes (empty)
│   ├── todos/              # Task tracking (empty)
│   └── knowledge/          # Architecture & domain knowledge
│       ├── Architecture.md
│       ├── REPORT_ENHANCEMENTS.md
│       ├── reduzer.zip     # Archive
│       └── versions/       # Historical code versions
│
├── utils/                   # Application core modules
│   ├── __init__.py
│   ├── detector.py         # Pattern recognition (regex)
│   ├── data_parser.py      # Data processing & aggregation
│   ├── visualizations.py   # Plotly chart generation
│   ├── report_generator.py # Excel/PDF export
│   └── predefined_structure.py # Domain model constants
│
├── main.py                  # Streamlit UI entry point
├── requirements.txt         # Python dependencies
├── .env.example            # Environment configuration template
├── .gitignore              # Git exclusions
├── README.md               # User documentation
└── CLAUDE.md               # Claude Code guidance

```

## Structure Principles

### Clean Root
- Only essential files in root directory
- Configuration files only
- Easy to navigate and understand

### Documentation Standards
Following `/home/edkjo/dev/.claude.md`:
- All docs in `docs/` subdirectories
- Filename format: `yyyy-mm-dd-HH-MM_Description.md`
- Worklog for session notes
- Knowledge for architecture decisions
- Plans for planning documents
- Research for investigations
- Todos for task tracking

### Code Organization
- **Streamlit convention**: `main.py` in root for `streamlit run main.py`
- **Modular design**: All utilities in `utils/` package
- **Historical code**: Archived in `docs/knowledge/versions/`

## File Purposes

### Root Files
- `main.py` - Streamlit app orchestration and UI
- `requirements.txt` - pip dependencies
- `.env.example` - Configuration template
- `README.md` - User-facing setup and usage
- `CLAUDE.md` - AI assistant guidance

### Utils Package
- `detector.py` - Extract Scenario/Discipline/MMI from text
- `data_parser.py` - Load, validate, aggregate Excel data
- `visualizations.py` - Create Plotly charts (3 levels: Scenario/Discipline/MMI)
- `report_generator.py` - Generate Excel (8 sheets) and PDF reports
- `predefined_structure.py` - Domain constants (A/B/C/D, disciplines, MMI codes)

### Documentation
- `docs/worklog/` - Session-by-session development notes
- `docs/knowledge/` - Architectural decisions and domain knowledge
- `docs/knowledge/versions/` - Old code versions for reference

## Design Rationale

### Why this structure?
1. **Discoverability**: Clear hierarchy, easy to find things
2. **Maintainability**: Modular code, well-documented decisions
3. **Standards compliance**: Follows dev directory guidelines
4. **Streamlit-friendly**: Keeps main.py in root as expected
5. **Clean separation**: Code vs documentation vs configuration

### Key Decisions
- Keep Streamlit `main.py` in root (convention)
- All documentation in `docs/` (standard)
- Archive old versions rather than delete (history)
- Flat `utils/` structure (project not complex enough for nesting)
