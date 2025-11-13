# Recommended Directory Structure

## Best Practice Layout for Data Science + Streamlit Projects

Combining:
- `/home/edkjo/dev/.claude.md` standards
- Cookiecutter Data Science best practices
- Streamlit conventions

## Proposed Structure

```
reduzer-summary/
├── main.py                  # Streamlit entry point (root per convention)
├── requirements.txt         # Production dependencies
├── requirements-dev.txt     # Development dependencies (NEW)
├── .env.example            # Environment config template
├── .gitignore              # Git exclusions
├── README.md               # User documentation
├── CLAUDE.md               # AI assistant guidance
│
├── utils/                   # Application core modules
│   ├── __init__.py
│   ├── detector.py
│   ├── data_parser.py
│   ├── visualizations.py
│   ├── report_generator.py
│   └── predefined_structure.py
│
├── data/                    # Data files (NEW)
│   ├── raw/                # Original, immutable data (gitignored)
│   ├── processed/          # Cleaned, transformed data (gitignored)
│   ├── samples/            # Sample/test data (committed for testing)
│   └── README.md           # Data documentation
│
├── outputs/                 # Generated files (NEW, gitignored)
│   ├── reports/            # Excel/PDF exports
│   ├── charts/             # Saved visualizations
│   └── logs/               # Application logs
│
├── tests/                   # Test suite (NEW)
│   ├── __init__.py
│   ├── test_detector.py
│   ├── test_data_parser.py
│   ├── test_visualizations.py
│   ├── fixtures/           # Test fixtures and mock data
│   └── conftest.py         # Pytest configuration
│
├── scripts/                 # Utility scripts (NEW, optional)
│   ├── seed_data.py        # Generate sample data
│   ├── validate_excel.py   # Validate Excel format
│   └── migrate_data.py     # Data migration scripts
│
├── notebooks/               # Exploratory analysis (NEW, optional)
│   └── exploration/        # Jupyter notebooks for prototyping
│
├── .streamlit/              # Streamlit config (optional)
│   └── config.toml         # Streamlit settings
│
└── docs/                    # Documentation (current)
    ├── worklog/            # Development session notes
    ├── plans/              # Planning documents
    ├── research/           # Research and investigations
    ├── todos/              # Task tracking
    └── knowledge/          # Architecture decisions
```

## Directory Purposes

### `data/` - Data Management
- **`raw/`**: Original, immutable data. Never edit. Always gitignored.
- **`processed/`**: Cleaned, transformed data ready for analysis. Gitignored.
- **`samples/`**: Small sample files for testing. **Committed to git**.
- **`README.md`**: Documents data sources, update frequency, schema.

### `outputs/` - Generated Artifacts
- **`reports/`**: Excel and PDF exports. Gitignored (user downloads).
- **`charts/`**: Saved visualizations if needed. Gitignored.
- **`logs/`**: Application logs for debugging. Gitignored.

### `tests/` - Test Suite
- Mirror `utils/` structure: `test_detector.py`, `test_data_parser.py`, etc.
- **`fixtures/`**: Mock data, sample Excel files for testing
- **`conftest.py`**: Pytest configuration and shared fixtures
- Use pytest conventions: `test_*.py` or `*_test.py`

### `scripts/` - Utility Scripts
- One-off tasks not part of main application
- Data generation, validation, migration
- Development helpers
- Can be run independently

### `notebooks/` - Exploratory Analysis (Optional)
- Jupyter notebooks for prototyping
- Exploratory data analysis
- Not part of production code
- Gitignored except for key notebooks

## .gitignore Updates

Add to `.gitignore`:
```
# Data
data/raw/
data/processed/

# Outputs
outputs/
reports/
*.xlsx
*.pdf

# Notebooks
notebooks/**
!notebooks/.gitkeep

# Testing
.pytest_cache/
.coverage
htmlcov/

# Logs
logs/
*.log
```

## Data Versioning (Advanced)

For production projects, consider:
- **DVC (Data Version Control)**: Track large datasets
- **Git LFS**: Store large files efficiently
- **S3/Cloud Storage**: Remote data storage with versioning

## Migration Plan

1. Create new directories
2. Add sample data to `data/samples/`
3. Update .gitignore
4. Create `data/README.md` documenting data sources
5. Set up pytest with basic tests
6. Update CLAUDE.md to reference new structure

## Benefits

✅ **Separation of concerns**: Code, data, outputs, docs all separated
✅ **Testing ready**: Proper test structure
✅ **Data safety**: Raw data protected, samples for testing
✅ **Clean git history**: Generated files excluded
✅ **Scalable**: Easy to add notebooks, scripts as needed
✅ **Standard**: Follows industry best practices

## When to Use Optional Folders

- **`notebooks/`**: Only if doing exploratory analysis
- **`scripts/`**: Only if you have utility scripts beyond main app
- **`.streamlit/`**: Only if customizing Streamlit config
- **`pages/`**: Only for multi-page Streamlit apps

## References

- Cookiecutter Data Science: https://cookiecutter-data-science.drivendata.org/
- Streamlit Best Practices: https://docs.streamlit.io/
- Dev Standards: `/home/edkjo/dev/.claude.md`
