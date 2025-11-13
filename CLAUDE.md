# CLAUDE.md

This file provides guidance to Claude Code when working in this repository.

## Quick Start

```bash
pip install -r requirements.txt
streamlit run main.py
```

Application starts at http://localhost:8501

## What This Does

LCA Scenario Mapping tool for environmental decision-making. **Core question: Should I choose Scenario C over Scenario A?**

Users upload Excel files from Reduzer, map data to predefined structures (Scenario → Discipline → MMI), and get live charts + reports (Excel/PDF).

## ⚠️ CRITICAL: Terminology Confusion (A/B/C means TWO different things!)

**We have an unavoidable naming collision in the domain:**

### Scenarios (Project Alternatives)
- **Scenario A, B, C, D** = Different design alternatives for the project
- Example: "Scenario A = concrete structure, Scenario C = timber structure"
- **This is what users want to compare: Which scenario is better?**

### LCA Phases (Lifecycle Stages)
- **Phase A = Construction** (byggefase)
- **Phase B = Operation** (driftsfase)
- **Phase C = End-of-life** (avslutningsfase)
- Excel columns are typically: "Construction (A)", "Operation (B)", "End-of-life (C)"
- **The (A), (B), (C) in column names refer to lifecycle phases, NOT scenarios!**

### Disciplines (Professional Roles)
- **ARK** = Arkitekt (Architect)
- **RIV** = RIV (HVAC - heating, ventilation, air conditioning)
- **RIE** = RIE (Electrical power and data installations)
- **RIB** = RIB (Structural engineering)
- **RIBp** = RIBp (Structural engineering - foundations/geotechnical)

### Example to Clarify:
```
"Scenario C has 1000 kg CO2e in Construction (A) for RIV discipline"

Translation:
- Scenario C = Timber structure project alternative (scenario)
- Construction (A) = Building phase (lifecycle phase)
- RIV = HVAC discipline
```

**When coding:**
- Variable names use: `construction_a`, `operation_b`, `end_of_life_c` (lowercase, lifecycle phases)
- Scenario names: Capital letters A, B, C, D (project alternatives)
- Discipline names: ARK, RIV, RIE, RIB, RIBp (all caps)

**Do NOT confuse "Scenario C" with "Phase C"!**

## Project Structure

Follows `/home/edkjo/dev/.claude.md` standards + Cookiecutter Data Science best practices:

```
reduzer-summary/
├── main.py                  # Streamlit UI entry point
├── utils/                   # Core modules (detector, parser, viz, reports)
├── data/                    # Data files (NEW)
│   ├── raw/                # Original Reduzer exports (gitignored)
│   ├── processed/          # Cleaned data (gitignored)
│   ├── samples/            # Test data (committed)
│   └── README.md           # Data documentation
├── outputs/                 # Generated files (NEW, gitignored)
│   ├── reports/            # Excel/PDF exports
│   ├── charts/             # Saved visualizations
│   └── logs/               # Application logs
├── tests/                   # Test suite (NEW)
│   ├── test_detector.py    # Pattern recognition tests
│   ├── fixtures/           # Test data
│   └── conftest.py         # Pytest config
├── scripts/                 # Utility scripts (optional)
├── notebooks/               # Exploratory analysis (optional)
├── docs/                    # Documentation (worklog, plans, research, todos, knowledge)
├── requirements.txt         # Production dependencies
├── requirements-dev.txt     # Dev dependencies (pytest, black, etc.)
└── .env.example            # Config template
```

**Documentation naming**: `yyyy-mm-dd-HH-MM_Description.md`

**Data guidelines**: See `data/README.md`. Raw data gitignored, samples committed.

## Key Architectural Decisions

### 1. Suggestions vs Mappings
Auto-detection populates `suggested_*` columns; user controls `mapped_*` columns. **Never auto-apply** to prevent silent errors.

### 2. Exclusion over Deletion
Rows marked `excluded=True` rather than deleted. Preserves data integrity.

### 3. Three-Level Hierarchy
```
Scenario (A/B/C/D) ← PROJECT ALTERNATIVES
  └── Discipline (ARK/RIV/RIE/RIB/RIBp) ← PROFESSIONAL ROLES
      └── MMI Code (300/700/800/900) ← BUILDING COMPONENTS
          └── LCA Phases (A=Construction/B=Operation/C=End-of-life) ← LIFECYCLE STAGES
```

**Important:** Scenarios (top level) are project alternatives. LCA Phases (bottom level) are lifecycle stages. Both use A/B/C letters but mean different things!

Each level aggregates: `construction_a`, `operation_b`, `end_of_life_c`, `total_gwp`, `count`.

Example data flow:
- Row: "Scenario C - RIV - MMI700 - Ventilasjon"
- Maps to: Scenario=C, Discipline=RIV, MMI=700
- GWP measured in: Construction (Phase A), Operation (Phase B), End-of-life (Phase C)

### 4. Live Updates
`st.data_editor` triggers immediate re-aggregation via `st.rerun()`. Trade-off: slower but consistent UI.

## Error Handling Philosophy

Following dev standards:
- **Fail loudly** - No fallbacks that hide real issues
- **Surface errors** - Make problems visible immediately
- Validate inputs at boundaries
- Zero-division checks in ratio calculations

## Core Modules

- **`detector.py`**: Regex-based pattern matching (Scenario/Discipline/MMI extraction)
- **`data_parser.py`**: Load, validate, aggregate Excel → nested dict structure
- **`visualizations.py`**: Plotly charts (3 levels: Scenario/Discipline/MMI)
- **`report_generator.py`**: Excel (8 sheets) + PDF export
- **`predefined_structure.py`**: Domain constants

## Expected Data Format

Excel columns:
- `category` (or first column): Text with Scenario/Discipline/MMI patterns
  - Example: "Scenario C - RIV - MMI700 - Ventilasjon"
- `Construction (A)`: GWP for **lifecycle phase A** = Construction (kg CO2e)
- `Operation (B)`: GWP for **lifecycle phase B** = Operation (kg CO2e)
- `End-of-life (C)`: GWP for **lifecycle phase C** = End-of-life (kg CO2e)

**⚠️ Critical:** The (A), (B), (C) in column names = **lifecycle phases**, NOT project scenarios!
- "Construction (A)" = How much CO2e during the construction/building phase
- "Operation (B)" = How much CO2e during the use/operation phase (e.g., heating, cooling)
- "End-of-life (C)" = How much CO2e during demolition/recycling/disposal

Column detection handles variations: "construction", "Konstruksjon (A)", "(A)", etc.

## Analysis Capabilities

The tool analyzes at three hierarchical levels:

1. **Scenario Level** (Project alternatives: A/B/C/D)
   - Compare Scenario C vs Scenario A (main use case)
   - Ratio/difference calculations
   - Stacked bars showing all scenarios
   - Answer: "Which project alternative has lower climate impact?"

2. **Discipline Level** (Professional roles: ARK/RIV/RIE/RIB/RIBp)
   - **The Drivers:** Top 3 disciplines causing C vs A difference
   - Within-scenario contribution % (e.g., "RIV is 45% of Scenario A's total GWP")
   - Cross-scenario comparison (e.g., "RIV in Scenario C vs RIV in Scenario A")
   - Answer: "Which discipline/trade is driving the difference?"

3. **MMI Level** (Building component categories: 300/700/800/900)
   - Distribution pie charts
   - Breakdown by discipline
   - Stats tables
   - Answer: "Which building components contribute most?"

## Norwegian UI Terms

- **Scenario** = Scenario (same word!)
- **Kartlegging** = Mapping
- **Disiplin** = Discipline (professional role: ARK, RIV, RIE, RIB, RIBp)
- **Fase** = Phase (lifecycle phase)
- **Konstruksjon (A)** = Construction phase (lifecycle phase A, NOT Scenario A!)
- **Drift (B)** = Operation phase (lifecycle phase B, NOT Scenario B!)
- **Avslutning (C)** = End-of-life phase (lifecycle phase C, NOT Scenario C!)

## Detailed Documentation

- **Architecture**: `docs/knowledge/Architecture.md`
- **Structure guide**: `docs/knowledge/Project-Structure.md`
- **Session history**: `docs/worklog/`
- **Old code versions**: `docs/knowledge/versions/`

## Common Tasks

**Add visualization**:
1. Function in `utils/visualizations.py` (accept `structure`, return `go.Figure`)
2. Import and call in `main.py:show_results_panel()`
3. Test with empty data

**Update detection**:
1. Modify regex in `utils/detector.py`
2. Test with `detect_all()` on sample categories
3. Check `is_summary_row()` doesn't over-exclude

**Change domain model**:
1. Update `utils/predefined_structure.py` constants
2. Adjust `data_parser.py` if structure changes
3. Update viz labels/colors
4. Test aggregation and reports

## Testing

**Run tests:**
```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=utils --cov-report=html

# Run specific test file
pytest tests/test_detector.py

# Run in verbose mode
pytest -v
```

**Test structure:**
- `tests/test_detector.py` - Pattern recognition tests
- `tests/conftest.py` - Shared fixtures
- `tests/fixtures/` - Mock data and sample Excel files

**Edge cases to test:**
- Mixed case: "scenario c", "SCENARIO A"
- Variations: "Scenario A", "A - Scenario C", "A-RIV-MMI300"
- Summary rows: "S8 - RAMBELL", "Total", "Sum"
- Missing values, zero GWP, zero denominators

## Development Session Notes

Document in `docs/worklog/` using format: `yyyy-mm-dd-HH-MM_Description.md`

Focus on:
- Decisions made and why
- Problems encountered and solutions
- Architectural changes
- New features added

Keep it short - future sessions need context, not play-by-play.
