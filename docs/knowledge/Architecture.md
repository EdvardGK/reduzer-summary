# LCA Scenario Mapping Architecture

## Core Design

### Three-Level Hierarchy
```
Scenario (A/B/C/D)
├── Discipline (RIV/ARK/RIE/RIB/RIBp)
    └── MMI Code (300/700/800/900)
        └── LCA Phases (Construction/Operation/End-of-life)
```

### Data Structure
```python
structure = {
    'A': {
        'total': {
            'construction_a': float,
            'operation_b': float,
            'end_of_life_c': float,
            'total_gwp': float,
            'count': int
        },
        'disciplines': {
            'RIV': {
                'total': {...},
                'mmi_categories': {
                    '300': {
                        'label': 'NY',
                        'construction_a': float,
                        ...
                    }
                }
            }
        }
    }
}
```

## Key Decisions

### Suggestions vs Mappings
- Auto-detection populates `suggested_*` columns
- User controls `mapped_*` columns
- Never auto-apply to prevent silent errors

### Exclusion over Deletion
- Rows marked `excluded=True` rather than deleted
- Preserves data integrity
- Allows re-inclusion if needed

### Live Updates
- `st.data_editor` triggers immediate re-aggregation
- Trade-off: Slightly slower but ensures consistency
- Uses `st.rerun()` to refresh UI

## Technology Stack
- **Streamlit**: Interactive web UI
- **Pandas**: Data manipulation
- **Plotly**: Interactive visualizations
- **ReportLab**: PDF generation
- **openpyxl**: Excel export with charts

## File Organization
- `main.py`: Streamlit UI and orchestration
- `utils/detector.py`: Pattern matching (regex-based)
- `utils/data_parser.py`: Data processing and aggregation
- `utils/visualizations.py`: Plotly chart generation
- `utils/report_generator.py`: Excel and PDF export
- `utils/predefined_structure.py`: Domain model constants
