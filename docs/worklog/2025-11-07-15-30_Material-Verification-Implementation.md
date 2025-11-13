# Material Count Verification - Implementation Summary

**Date:** 2025-11-07
**Task:** Integrate IFC file takeoff to verify material count consistency across scenarios

## Overview

Implemented a comprehensive material count verification system to ensure Scenario A and Scenario C represent **the same physical building** with identical material volumes.

**Core Principle:**
```
Scenario A: MMI 300 (100% New)
    =
Scenario C: MMI 300 (New) + MMI 700 (Existing Kept) + MMI 800 (Reused)
```

**Acceptable Deviation:** ≤5%

---

## What Was Built

### 1. Data Template System

**Files Created:**
- `data/samples/ifc_takeoff_template.csv` - Example data with realistic scenarios
- `data/samples/ifc_takeoff_blank.csv` - Blank template for users
- `docs/IFC_TAKEOFF_VERIFICATION.md` - Comprehensive documentation

**Template Columns:**
| Column | Type | Purpose |
|--------|------|---------|
| Object Type | Text | Material/object category name |
| IFC Class | Text | IFC entity type (optional) |
| Discipline | Text | ARK, RIV, RIE, RIB, RIBp |
| Scenario | Text | A or C |
| MMI Category | Integer | 300, 700, 800 (not 900 in verification) |
| Quantity | Number | Count/volume/area |
| Unit | Text | m2, m3, pcs, kg, m |
| Description | Text | Additional details (optional) |
| Notes | Text | Comments (optional) |

**Data Requirements:**
- **Scenario A:** All objects must be MMI 300 (conventional renovation = 100% new)
- **Scenario C:** Objects distributed across MMI 300/700/800 (circular renovation)
- **Unit Consistency:** Same object type must use same unit in both scenarios

### 2. Verification Engine

**File:** `utils/ifc_verification.py`

**Key Functions:**

#### `load_takeoff_data(file_path)`
- Loads CSV or Excel files
- Validates required columns
- Cleans and standardizes data
- Returns pandas DataFrame

#### `validate_takeoff_data(df)`
- Checks disciplines against `VALID_DISCIPLINES`
- Validates scenarios (A, B, C, D)
- Ensures MMI categories are valid (300, 700, 800, 900)
- Verifies Scenario A only uses MMI 300
- Warns if Scenario C uses MMI 900 (should not)
- Checks unit consistency per object type
- Validates positive quantities
- Returns list of error messages

#### `calculate_verification_metrics(df, tolerance=5.0)`
- Aggregates Scenario A totals
- Aggregates Scenario C totals across all MMI categories
- Calculates object-level deviations
- Computes discipline-level summaries
- Generates MMI distribution for Scenario C
- Flags items with deviation > tolerance
- Returns comprehensive metrics dictionary

**Metrics Calculated:**
```python
{
    'status': 'success',
    'overall': {
        'total_qty_a': float,
        'total_qty_c': float,
        'total_deviation_abs': float,
        'overall_deviation_pct': float,
        'tolerance': float
    },
    'comparison_table': DataFrame,      # Object-by-object comparison
    'discipline_summary': DataFrame,     # Discipline-level aggregates
    'mmi_distribution': dict,            # MMI 300/700/800 breakdown
    'mmi_distribution_pct': dict,        # Percentages
    'flagged_items': DataFrame           # Items exceeding tolerance
}
```

#### `create_verification_charts(metrics)`
- **Discipline Comparison:** Grouped bar chart (Scenario A vs C by discipline)
- **MMI Distribution:** Pie chart showing Scenario C breakdown (300/700/800)
- **Deviation Chart:** Horizontal bar chart of top 10 worst deviations
- **Stacked Bar:** MMI categories stacked by discipline for Scenario C
- Returns dictionary of Plotly figures

#### `export_verification_report(metrics, output_path)`
Generates Excel report with 5 sheets:
1. **Summary** - Overall metrics and PASS/FAIL verdict
2. **Object Comparison** - Full comparison table
3. **Discipline Summary** - Aggregated by discipline
4. **MMI Distribution** - Category breakdown
5. **Flagged Items** - Items requiring review

### 3. User Interface

**File:** `pages/6_📊_Material-Verifisering.py`

**Features:**

#### File Upload Section
- Supports CSV and Excel formats
- Links to template files and documentation
- Real-time validation with error messages

#### Hero Section - Verdict
- Large, prominent status indicator
- Color-coded: Green (excellent/acceptable), Red (needs review)
- Four key metrics displayed as cards:
  - Total Scenario A
  - Total Scenario C (with delta)
  - Absolute Deviation
  - Deviation % (with tolerance comparison)

#### Tab 1: Overview
- MMI distribution metrics (300/700/800) with percentages
- Discipline-level comparison table
- Quick summary statistics

#### Tab 2: Details
- Full object-by-object comparison table
- Color-coded rows by status:
  - Green: Excellent (<2% deviation)
  - Yellow: Acceptable (2-5% deviation)
  - Red: Needs Review (>5% deviation)
- Scrollable with 500px height
- Summary counts of status categories

#### Tab 3: Flagged Items
- Displays only items with deviation >5%
- Sorted by deviation (worst first)
- Provides troubleshooting guidance:
  - Unit mismatch
  - Missing elements
  - Different design stages
  - Data collection errors

#### Tab 4: Visualizations
- 4 interactive Plotly charts
- Responsive layout with columns
- All charts downloadable (Plotly feature)

#### Tab 5: Export
- Excel report generation
- Raw data CSV download
- Timestamped filenames

---

## Validation Logic

### Status Classification

For each object type:
```python
deviation_pct = |Qty_A - (Qty_C_300 + Qty_C_700 + Qty_C_800)| / Qty_A × 100

if deviation_pct < 2%:
    status = "Excellent"    # Green
elif deviation_pct < 5%:
    status = "Acceptable"   # Yellow
else:
    status = "Needs Review" # Red
```

### Overall Verdict

```python
overall_deviation = Σ|Qty_A - Qty_C| / ΣQty_A × 100

if overall_deviation < 5%:
    verdict = "PASS"
else:
    verdict = "FAIL"
```

---

## Data Flow

```
1. User exports quantities from BIM tool
   ↓
2. Format data according to template
   ↓
3. Upload to Material-Verifisering page
   ↓
4. System validates data
   ↓
5. Metrics calculated
   ↓
6. Results displayed with verdict
   ↓
7. User reviews flagged items
   ↓
8. Export final report
```

---

## Example Use Case

**Project:** Office building renovation

**Scenario A (Conventional):**
- Demo to "Råbygg" (load-bearing structure only)
- All interior: 100% new (MMI 300)
- Example: 120 m² interior walls, all new

**Scenario C (Circular):**
- Selective demolition
- Keep existing where possible
- Example: 120 m² interior walls breakdown:
  - 85 m² existing kept (MMI 700)
  - 35 m² new (MMI 300)
  - Total: 120 m² ✓ MATCH

**Verification:**
```
Object: Innvendige skillevegger
Scenario A: 120 m² (MMI 300)
Scenario C: 85 m² (MMI 700) + 35 m² (MMI 300) = 120 m²
Deviation: 0%
Status: ✅ Excellent
```

---

## Testing Recommendations

### Test Cases to Implement

1. **Perfect Match**
   - Scenario A = Scenario C exactly
   - Expected: 0% deviation, all green

2. **Small Deviation (2-4%)**
   - Rounding differences
   - Expected: Yellow status, acceptable

3. **Large Deviation (>5%)**
   - Missing elements
   - Expected: Red status, flagged

4. **Unit Mismatch**
   - Same object, different units
   - Expected: Validation error

5. **Invalid MMI in Scenario A**
   - Scenario A with MMI 700
   - Expected: Validation error

6. **Scenario C with MMI 900**
   - Should only use 300/700/800
   - Expected: Validation warning

7. **Missing Scenario**
   - Only A or only C provided
   - Expected: Error message

8. **Negative Quantities**
   - Quantity < 0
   - Expected: Validation error

### Manual Test Procedure

```bash
# 1. Start app
streamlit run main.py

# 2. Navigate to "📊 Material-Verifisering"

# 3. Download blank template
# 4. Fill with test data
# 5. Upload and verify results
# 6. Test each tab functionality
# 7. Generate Excel report
# 8. Verify report contents
```

---

## Integration Points

### With Existing System

The verification module is **standalone** and does not depend on:
- Reduzer GWP data
- Main LCA analysis
- Project save/load functionality

**Future Integration Possibilities:**
1. Link verification data to saved projects
2. Cross-reference with Reduzer quantities
3. Auto-populate from IFC files via `utils/ifc_processor.py`
4. Add verification status to project overview

### With IFC Processing

Current IFC validation (`pages/5_🏗️_IFC-Validering.py`) checks:
- Duplicate GUIDs
- ARK-RIB overlaps
- Material data completeness

**Potential Enhancement:**
Export quantities directly from IFC validator to verification format:

```python
# In ifc_processor.py
def export_quantities_for_verification(elements_df, scenario, output_path):
    """
    Convert IFC elements to verification template format
    """
    # Group by object type, discipline
    # Sum quantities by MMI category
    # Export to CSV in template format
```

---

## Known Limitations

1. **No Direct IFC Import**
   - Users must manually export from BIM tools
   - Future: Auto-extract from `.ifc` files

2. **Unit Conversion Not Automated**
   - User must ensure consistent units
   - Future: Add conversion logic (mm² → m²)

3. **Single File Upload**
   - Cannot merge multiple sources automatically
   - Future: Multi-file merge capability

4. **No Historical Tracking**
   - Each verification is standalone
   - Future: Link to project versions in Supabase

5. **Limited Object Matching**
   - Exact string match on "Object Type"
   - Future: Fuzzy matching, synonyms

---

## Files Added/Modified

### New Files
```
data/samples/ifc_takeoff_template.csv          # Example data
data/samples/ifc_takeoff_blank.csv             # Blank template
docs/IFC_TAKEOFF_VERIFICATION.md               # User documentation
utils/ifc_verification.py                      # Verification engine
pages/6_📊_Material-Verifisering.py            # UI page
docs/worklog/2025-11-07-15-30_Material-Verification-Implementation.md
```

### Modified Files
None - fully additive implementation

---

## Next Steps

### Immediate
- [ ] Test with real project data
- [ ] Create test fixtures in `tests/`
- [ ] Add pytest tests for verification logic

### Short-term
- [ ] Add auto-export from IFC processor
- [ ] Unit conversion support
- [ ] Template generator based on uploaded IFC

### Long-term
- [ ] Link verification to project save
- [ ] Historical deviation tracking
- [ ] Multi-file merge interface
- [ ] Fuzzy object matching
- [ ] AI-assisted data mapping

---

## Success Criteria

✅ Users can upload material count data
✅ System validates data format and content
✅ Calculates deviation metrics accurately
✅ Displays clear PASS/FAIL verdict
✅ Provides detailed breakdown by discipline
✅ Flags items requiring review
✅ Generates exportable Excel report
✅ Visualizes comparisons with charts

**Result:** Feature complete and ready for user testing.
