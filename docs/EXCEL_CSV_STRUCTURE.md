# Excel & CSV Export Structure

## Overview

The Excel and CSV exports serve as **pure data** supplementary documentation. NO CHARTS - only clean, well-formatted data tables that can be imported into other analysis tools.

**PDF** = Main visual report with charts and insights
**Excel** = Multi-sheet data workbook with metadata
**CSV** = Single-file complete dataset for analysis

---

## Excel Workbook Structure

### Sheet 1: 📋 Metadata
**Purpose:** Report information and column definitions

**Contents:**
- Generation timestamp
- Summary statistics:
  - Total rows in dataset
  - Mapped rows (active)
  - Excluded rows
  - Number of scenarios
  - Average weighting percentage
  - Rows with reduced weight
- Column definitions table explaining each field

**Use case:** Understand the dataset before analysis

---

### Sheet 2: 📊 Scenarioer (Scenarios)
**Purpose:** High-level scenario comparison

**Columns:**
- Scenario (A, B, C, D)
- Konstruksjon (A) - Construction phase GWP
- Drift (B) - Operation phase GWP
- Avslutning (C) - End-of-life phase GWP
- Total GWP
- Antall rader - Row count

**Sorting:** By scenario (A → D)

**Use case:** Quick scenario totals for executive summaries

---

### Sheet 3: 🔄 C vs A (Comparison)
**Purpose:** Detailed C vs A comparison

**Columns:**
- LCA-fase (Total, Construction, Operation, End-of-life)
- Scenario A (kg CO2e)
- Scenario C (kg CO2e)
- Differanse (C-A) - Absolute difference
- Ratio (C/A) % - Percentage ratio
- Vurdering - Assessment (✓ reduction / ✗ increase)

**Color coding:**
- Green cells: Ratio < 100% (reduction)
- Red cells: Ratio ≥ 100% (increase)

**Use case:** Analyze phase-by-phase differences between scenarios

---

### Sheet 4: 🏗️ MMI (Building Categories)
**Purpose:** MMI distribution per scenario

**Columns:**
- Scenario
- MMI (300/700/800/900)
- Status (NY/EKS/GJEN/RIVES)
- GWP (kg CO2e)
- Andel (%) - Percentage share
- Antall rader - Row count

**Sorting:** By scenario, then MMI code

**Use case:** Understand building component contributions

**MMI Codes:**
- 300 = NY (New construction)
- 700 = EKS (Existing kept)
- 800 = GJEN (Reused)
- 900 = RIVES (Demolished/waste)

---

### Sheet 5: 👷 Disipliner (Disciplines)
**Purpose:** Discipline breakdown per scenario

**Columns:**
- Scenario
- Disiplin (ARK/RIV/RIE/RIB/RIBp)
- Konstruksjon (A) (kg CO2e)
- Drift (B) (kg CO2e)
- Avslutning (C) (kg CO2e)
- Total GWP (kg CO2e)
- Antall rader - Row count

**Sorting:** By Total GWP descending (highest contributors first)

**Use case:** Identify which disciplines drive climate impact

**Disciplines:**
- ARK = Arkitekt (Architect)
- RIV = Heating, ventilation, air conditioning
- RIE = Electrical installations
- RIB = Structural engineering
- RIBp = Structural engineering - foundations

---

### Sheet 6: 📋 Komplett datasett (Complete Dataset)
**Purpose:** Row-level data with all mappings and weighting

**Columns:**
1. Kategori - Original category text
2. Scenario - Mapped scenario (A/B/C/D)
3. Disiplin - Mapped discipline
4. MMI - Mapped MMI code
5. Vekting (%) - Weighting percentage (0-100%)
6. Konstruksjon (A) (kg CO2e) - Construction phase GWP
7. Drift (B) (kg CO2e) - Operation phase GWP
8. Avslutning (C) (kg CO2e) - End-of-life phase GWP
9. GWP basis (kg CO2e) - Total unweighted GWP
10. GWP vektet (kg CO2e) - Total weighted GWP

**Filtering:**
- Only mapped rows (excluded rows removed)
- Only rows with valid scenario mapping

**Sorting:** By Scenario → Disiplin → MMI

**Use case:** Detailed analysis, pivot tables, filtering in Excel

---

## CSV Export Structure

### File: `lca_data_YYYYMMDD_HHMM.csv`

**Purpose:** Complete dataset in universal format

**Same columns as Excel Sheet 6, but with CSV-safe headers:**
1. `Kategori`
2. `Scenario`
3. `Disiplin`
4. `MMI`
5. `Vekting_pct`
6. `Konstruksjon_A_kg_CO2e`
7. `Drift_B_kg_CO2e`
8. `Avslutning_C_kg_CO2e`
9. `GWP_basis_kg_CO2e`
10. `GWP_vektet_kg_CO2e`

**Encoding:** UTF-8 with BOM (Excel-compatible)

**Sorting:** By Scenario → Disiplin → MMI

**Use case:** Import into Python, R, Power BI, Tableau, databases

---

## Data Dictionary

### Core Fields

| Field | Type | Description | Values |
|-------|------|-------------|--------|
| Kategori | Text | Original category from Reduzer | Free text |
| Scenario | Text | Project alternative | A, B, C, D |
| Disiplin | Text | Professional discipline | ARK, RIV, RIE, RIB, RIBp |
| MMI | Integer | Building component category | 300, 700, 800, 900 |
| Vekting (%) | Float | Weighting factor | 0-100 |

### GWP Fields (kg CO2e)

All GWP values are in **kilograms of CO2 equivalent (kg CO2e)**.

| Field | Description | Formula |
|-------|-------------|---------|
| Konstruksjon (A) | Emissions during construction phase | From Reduzer |
| Drift (B) | Emissions during operation phase | From Reduzer |
| Avslutning (C) | Emissions during end-of-life phase | From Reduzer |
| GWP basis | Total unweighted emissions | A + B + C |
| GWP vektet | Total weighted emissions | (A + B + C) × (Vekting / 100) |

**Note:** Lifecycle phases (A/B/C) are NOT the same as scenarios (A/B/C/D)!

---

## Formatting Details

### Excel Formatting
- **Headers:** White text on blue background (#1565C0)
- **Auto-sized columns:** Max 50 characters wide
- **Alternating rows:** Not applied (pure data tables)
- **Number format:** Default (no decimal restrictions)
- **Conditional formatting:** Only on C vs A ratio column

### CSV Formatting
- **Delimiter:** Comma (,)
- **Quote character:** Double quote (")
- **Line endings:** CRLF (Windows-compatible)
- **Decimal separator:** Period (.)
- **Encoding:** UTF-8 with BOM

---

## Usage Examples

### Excel: Pivot Table Analysis
1. Open **Sheet 6: Komplett datasett**
2. Insert → PivotTable
3. Rows: Scenario, Disiplin
4. Values: Sum of GWP vektet
5. Filter: MMI = 300 (new construction only)

### CSV: Python Analysis
```python
import pandas as pd

# Load CSV
df = pd.read_csv('lca_data_20250113_1400.csv')

# Group by scenario
scenario_totals = df.groupby('Scenario')['GWP_vektet_kg_CO2e'].sum()

# Find top disciplines
top_disciplines = df.groupby('Disiplin')['GWP_vektet_kg_CO2e'].sum().sort_values(ascending=False)
```

### Excel: Filter to Specific Discipline
1. Open **Sheet 5: Disipliner**
2. Click header row
3. Data → Filter
4. Filter Disiplin column to "RIV"
5. See only HVAC discipline data

---

## File Naming Convention

- **PDF:** `lca_rapport_YYYYMMDD_HHMM.pdf`
- **Excel:** `lca_rapport_YYYYMMDD_HHMM.xlsx`
- **CSV:** `lca_data_YYYYMMDD_HHMM.csv`

**Format:** `lca_{type}_{date}_{time}.{ext}`

**Example:** `lca_data_20250113_1430.csv` = Generated on Jan 13, 2025 at 14:30

---

## Quality Checks

### Before Using the Data

1. **Check Metadata sheet** - Verify mapping completeness
2. **Review excluded rows** - Ensure intentional exclusions
3. **Check weighting** - Average should be close to 100%
4. **Verify scenarios** - Confirm expected scenarios present
5. **Spot check GWP values** - Compare weighted vs basis

### Data Validation

- All Scenario values should be A, B, C, or D
- All Disiplin values should be ARK, RIV, RIE, RIB, or RIBp
- All MMI values should be 300, 700, 800, or 900
- Vekting should be 0-100
- GWP vektet should equal GWP basis × (Vekting / 100)

---

## Integration with PDF Report

The Excel/CSV exports contain the **exact same data** used to generate the PDF report. The PDF adds:
- Visual charts and graphs
- Color-coded metric boxes
- Executive summary insights
- Recommendations
- Professional formatting

**Workflow:**
1. **Excel/CSV** → Detailed analysis, custom calculations, database import
2. **PDF** → Presentation, stakeholder communication, decision-making

---

## Change Log

**v2.0 (2025-01-13)** - Pure Data Overhaul
- Removed all charts from Excel
- Added Metadata sheet with column definitions
- Sorted all sheets for easy navigation
- Improved CSV with clean headers
- Added UTF-8 BOM for Excel compatibility
- Auto-sized all columns

**v1.0 (Previous)** - Initial version
- Included embedded charts
- Less structured sheets
- Basic CSV export

---

Generated: 2025-01-13
Documentation by: Claude Code
