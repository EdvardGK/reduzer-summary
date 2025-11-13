# IFC Takeoff Verification Guide

## Purpose

Verify that material counts are consistent across scenarios to ensure both Scenario A and Scenario C represent **the same physical building** with identical final material volumes.

**Verification Principle:**
```
Scenario A: MMI 300 (100% New)
    =
Scenario C: MMI 300 (New) + MMI 700 (Existing Kept) + MMI 800 (Reused)
```

**Deviation Tolerance:** ≤5% acceptable due to rounding, measurement differences, or minor design adjustments.

---

## Template Format

### File Format Options
1. **CSV** (recommended for simple exports): `ifc_takeoff_template.csv`
2. **Excel**: Multi-sheet or single sheet with all data

### Required Columns

| Column | Type | Required | Description | Example |
|--------|------|----------|-------------|---------|
| `Object Type` | Text | Yes | Material/object category name | "Innvendige skillevegger" |
| `IFC Class` | Text | No | IFC entity type from model | "IfcWall", "IfcDoor" |
| `Discipline` | Text | Yes | One of: ARK, RIV, RIE, RIB, RIBp | "ARK" |
| `Scenario` | Text | Yes | One of: A, B, C, D | "A" or "C" |
| `MMI Category` | Integer | Yes | One of: 300, 700, 800, 900 | 300 |
| `Quantity` | Number | Yes | Numeric count/volume/area | 120 |
| `Unit` | Text | Yes | Measurement unit | "m2", "m3", "pcs", "kg", "m" |
| `Description` | Text | No | Additional details | "Gipsplater type A" |
| `Notes` | Text | No | Comments/clarifications | "North wing only" |

### Data Rules

**Scenario A:**
- All objects must be in **MMI 300** (New materials)
- Represents conventional demolition to "Råbygg" + 100% new

**Scenario C:**
- Objects distributed across **MMI 300, 700, 800**
- MMI 700: Materials from this building kept beyond Råbygg
- MMI 800: Materials sourced from other projects
- MMI 300: New materials (minimized)

**Unit Consistency:**
- Same `Object Type` must use same `Unit` across both scenarios
- Example: If "Innvendige skillevegger" uses "m2" in Scenario A, it must use "m2" in Scenario C

---

## Example Data Structure

### Scenario A - Conventional (All New)
```csv
Object Type,IFC Class,Discipline,Scenario,MMI Category,Quantity,Unit
Innvendige skillevegger,IfcWall,ARK,A,300,120,m2
Dører,IfcDoor,ARK,A,300,45,pcs
Himling,IfcCovering,ARK,A,300,850,m2
```

### Scenario C - Circular (Mixed Sources)
```csv
Object Type,IFC Class,Discipline,Scenario,MMI Category,Quantity,Unit
Innvendige skillevegger,IfcWall,ARK,C,700,85,m2
Innvendige skillevegger,IfcWall,ARK,C,300,35,m2
Dører,IfcDoor,ARK,C,700,30,pcs
Dører,IfcDoor,ARK,C,800,10,pcs
Dører,IfcDoor,ARK,C,300,5,pcs
Himling,IfcCovering,ARK,C,700,600,m2
Himling,IfcCovering,ARK,C,300,250,m2
```

### Verification Calculation
```
Innvendige skillevegger:
  Scenario A: 120 m2 (MMI 300)
  Scenario C: 85 m2 (MMI 700) + 35 m2 (MMI 300) = 120 m2 ✓
  Deviation: 0%

Dører:
  Scenario A: 45 pcs (MMI 300)
  Scenario C: 30 pcs (MMI 700) + 10 pcs (MMI 800) + 5 pcs (MMI 300) = 45 pcs ✓
  Deviation: 0%

Himling:
  Scenario A: 850 m2 (MMI 300)
  Scenario C: 600 m2 (MMI 700) + 250 m2 (MMI 300) = 850 m2 ✓
  Deviation: 0%
```

---

## Data Preparation Workflow

### Option 1: Direct IFC Export (Recommended if tool supports it)
1. Export object quantities from BIM tool (Revit, ArchiCAD, etc.)
2. Include properties: Object type, IFC class, quantity, unit
3. Add columns manually: Discipline, Scenario, MMI Category
4. Save as CSV or Excel

### Option 2: Manual Takeoff from IFC Viewer
1. Open IFC file in viewer (Solibri, BIMcollab, Navisworks)
2. Filter by discipline/system
3. Export quantity schedules
4. Format according to template
5. Add scenario and MMI category assignments

### Option 3: Reduzer Export Enhancement
If Reduzer supports quantity export alongside GWP:
1. Export material lists with quantities
2. Map to template format
3. Ensure quantities match between GWP data and verification data

---

## Verification Metrics

The verification module will calculate:

### 1. Object-Level Deviation
For each object type:
```
Deviation % = |Qty_A - (Qty_C_300 + Qty_C_700 + Qty_C_800)| / Qty_A × 100
```

### 2. Discipline-Level Summary
Total quantities by discipline:
```
ARK Total: Scenario A vs Scenario C
RIV Total: Scenario A vs Scenario C
...
```

### 3. Overall Project Deviation
Aggregate across all disciplines:
```
Total Deviation % = Σ|Qty_A - Qty_C| / ΣQty_A × 100
```

### 4. MMI Distribution (Scenario C Only)
Percentage breakdown:
```
MMI 300 (New): X%
MMI 700 (Existing Kept): Y%
MMI 800 (Reused): Z%
---
Total: 100%
```

---

## Output Visualizations

The verification module will provide:

1. **Deviation Table**: Object-by-object comparison with color coding
   - Green: <2% deviation (excellent)
   - Yellow: 2-5% deviation (acceptable)
   - Red: >5% deviation (needs review)

2. **Discipline Comparison Chart**: Stacked bars showing Scenario A vs C by discipline

3. **MMI Distribution Pie Chart**: Scenario C breakdown (300 vs 700 vs 800)

4. **Detailed Report**: Excel export with:
   - Summary tab
   - Object-level deviation tab
   - Discipline-level summary tab
   - Flagged items (deviations >5%)

---

## Common Issues & Solutions

### Issue: Unit Mismatch
**Symptom:** "Innvendige skillevegger" shows 120 m2 in Scenario A, 120000 mm2 in Scenario C
**Solution:** Standardize units before import. Add unit conversion logic if needed.

### Issue: Object Type Naming Inconsistency
**Symptom:** "Innvendige vegger" in Scenario A, "Interior walls" in Scenario C
**Solution:** Use consistent Norwegian terminology. Provide mapping table if needed.

### Issue: Missing Data
**Symptom:** Object appears in Scenario A but not in Scenario C
**Solution:** Verify data completeness. Check if object was intentionally removed or is a data error.

### Issue: High Deviation (>10%)
**Symptom:** Verification shows large differences between scenarios
**Solution:**
- Check if both models represent same design stage
- Verify no elements were accidentally omitted
- Confirm Scenario C includes all necessary compensating materials

---

## Integration with LCA Tool

The verification data will:
1. Load alongside GWP data from Reduzer
2. Display in separate "Verification" tab in main UI
3. Allow filtering by discipline, scenario, MMI category
4. Export verification report together with LCA report

**Workflow:**
```
1. Upload Reduzer GWP data → Main analysis
2. Upload IFC takeoff CSV → Verification module
3. Review verification metrics → Flag issues
4. Generate combined report → GWP + Verification
```

---

## Template Files

- **Sample CSV**: `data/samples/ifc_takeoff_template.csv`
- **Blank Template**: `data/samples/ifc_takeoff_blank.csv`
- **Example with errors**: `data/samples/ifc_takeoff_example_errors.csv` (for testing)

---

## Next Steps for Implementation

1. Create Python module: `utils/ifc_verification.py`
2. Functions needed:
   - `load_takeoff_data(file_path)` → DataFrame
   - `validate_takeoff_data(df)` → List of validation errors
   - `calculate_verification_metrics(df)` → Dict of metrics
   - `generate_verification_charts(metrics)` → Plotly figures
3. Add UI tab in `main.py`
4. Create Excel export template
