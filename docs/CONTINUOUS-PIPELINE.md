# Continuous Pipeline Design

**Date:** 2025-11-07
**Change:** Complete redesign from multi-page navigation to single continuous flow

---

## Problem

Previous design had multiple separate pages with independent I/O logic:
- 📁 Prosjekter (Projects)
- ⚠️ Validering (Validation)
- 📊 Innsikt (Insights)
- 🔧 Data (Data)
- ✓ Verifisering (Verification)
- 🏗️ IFC-Validering (IFC Validation)
- 📊 Material-Verifisering (Material Verification)

**Issues:**
- Users had to navigate between pages
- Context-aware clicks required
- Separate upload logic per page
- No continuous flow
- Confusing where to start

---

## Solution

**Single continuous pipeline:**

```
INPUT (Upload)
    ↓ automatic
Map & Validate
    ↓ automatic
Verify (optional)
    ↓ automatic
Analyze
    ↓ automatic
OUTPUT (Download)
```

**One page. Zero navigation. Just scroll.**

---

## Architecture

### Step 1: Upload (INPUT)
```python
# Required
excel_file = st.file_uploader("LCA data")

# Optional verification
verification_choice = ["None", "IFC files", "Takeoff CSV"]
verification_file = st.file_uploader(...)
```

**Automatic progression:**
- Upload Excel → Auto-detect mapping → Show Step 2

### Step 2: Validate Mapping
```python
# Show editable table
edited_df = st.data_editor(
    df[['category', 'suggested_*', 'mapped_*', 'excluded', 'gwp_values']],
    ...
)

# Update and continue
df.update(edited_df)
```

**Automatic progression:**
- Edits saved automatically
- Continue scrolling to Step 3

### Step 3: Verify Quantities (if provided)
```python
if verification_data is not None:
    metrics = calculate_verification_metrics(verif_df)

    if deviation < 5%:
        st.success("✅ PASS")
    else:
        st.error("❌ FAIL")
```

**Automatic progression:**
- Verification runs automatically
- Results displayed immediately
- Can continue regardless of PASS/FAIL

### Step 4: Analysis
```python
structure = aggregate_by_mapping(df)
comparison = compare_scenarios(structure, 'A', 'C')

# Hero verdict
if ratio < 100:
    st.success(f"✅ Scenario C is {100 - ratio}% BETTER")
else:
    st.error(f"⚠️ Scenario C is {ratio - 100}% WORSE")

# Charts
create_stacked_bar_chart(structure)
create_comparison_chart(structure, 'A', 'C')
create_discipline_comparison_bar(structure, 'A', 'C')
```

**Automatic progression:**
- Analysis runs automatically
- All charts displayed
- Continue scrolling to Step 5

### Step 5: Download (OUTPUT)
```python
# Primary report
st.download_button("📊 Full Report (Excel)")

# Supporting exports
st.download_button("📄 Mapped Data (CSV)")
st.download_button("🔍 Verification Report")  # if applicable
```

**End of pipeline:**
- Download reports
- Or "Start Over" button to reset

---

## User Journey

### Ideal Flow (No Issues)
```
1. Upload Excel file
   ↓ 2 seconds
2. See auto-detected mapping
   ↓ Scroll (0 clicks)
3. Skip verification (none provided)
   ↓ Automatic
4. See analysis & verdict
   ↓ Scroll (0 clicks)
5. Download report

Total: 1 click (upload) + 1 click (download) = 2 clicks
```

### With Verification
```
1. Upload Excel + Takeoff CSV
   ↓ 2 seconds each
2. See auto-detected mapping
   ↓ Scroll
3. See verification PASS/FAIL
   ↓ Automatic
4. See analysis & verdict
   ↓ Scroll
5. Download report + verification report

Total: 2 clicks (uploads) + 2 clicks (downloads) = 4 clicks
```

### With Corrections Needed
```
1. Upload Excel
   ↓ 2 seconds
2. See mapping with unmapped items
   ↓ Edit inline (3-4 clicks to fix)
3. Continue scrolling
   ↓ Automatic
4. See analysis
   ↓ Scroll
5. Download report

Total: 1 (upload) + 4 (edits) + 1 (download) = 6 clicks
```

---

## Progress Indicator

Visual feedback shows current step:

```html
① ② ③ ④ ⑤
Upload → Map → Verify → Analyze → Download

[Current step highlighted in orange]
[Completed steps in green]
[Future steps in blue]
```

Implemented with CSS animations:
- Current step: Pulsing orange
- Completed: Solid green
- Pending: Blue

---

## Session State Management

```python
st.session_state = {
    'pipeline_step': 1-5,           # Current step
    'df': DataFrame,                 # Main LCA data
    'verification_data': DataFrame,  # Verification data
    'verification_metrics': Dict     # Verification results
}
```

**Automatic progression:**
- Step advances automatically when data is ready
- No manual "Next" buttons
- User just scrolls

---

## Removed Files

All separate pages deleted:
```
pages/
├── 0_📁_Prosjekter.py          ❌ DELETED
├── 1_⚠️_Validering.py          ❌ DELETED
├── 2_📊_Innsikt.py              ❌ DELETED
├── 3_🔧_Data.py                 ❌ DELETED
├── 4_✓_Verifisering.py         ❌ DELETED
├── 5_🏗️_IFC-Validering.py      ❌ DELETED
└── 6_📊_Material-Verifisering.py ❌ DELETED
```

All functionality consolidated into `main.py`.

**No fallbacks. Single source of truth.**

---

## Key Design Decisions

### 1. Upload Everything Upfront
Users provide all inputs at the start:
- Required: Excel file
- Optional: Verification data

**Rationale:** No context switching, no going back to upload more

### 2. Inline Editing
Mapping validation happens in editable table:
- See suggestions vs actual mappings side-by-side
- Edit directly without separate forms
- Changes saved automatically

**Rationale:** Zero clicks to switch modes

### 3. Progressive Disclosure
Details hidden in expandables:
- Flagged verification items
- Full comparison tables
- Technical details

**Rationale:** Don't overwhelm, but keep accessible

### 4. Auto-Progression
Steps advance automatically:
- Upload → detect mapping
- Validate → run verification
- Verify → run analysis
- Analyze → show downloads

**Rationale:** Zero navigation decisions

### 5. Visual Progress
Always visible progress indicator:
- Shows current position
- Shows what's complete
- Shows what's remaining

**Rationale:** User always knows where they are

---

## Technical Implementation

### Single File Structure
```python
# main.py
# ├── Imports
# ├── Config & CSS
# ├── Session state init
# ├── Header & progress
# ├── Step 1: Upload
# ├── Step 2: Validate
# ├── Step 3: Verify
# ├── Step 4: Analyze
# ├── Step 5: Download
# └── Footer
```

**Total: 542 lines, single file**

### Key Functions Used
```python
# Data loading & processing
from utils.data_parser import (
    load_excel_file,
    aggregate_by_mapping,
    get_scenario_summary,
    compare_scenarios,
    get_mapping_statistics
)

# Visualization
from utils.visualizations import (
    create_stacked_bar_chart,
    create_comparison_chart,
    create_discipline_comparison_bar
)

# Verification (optional)
from utils.ifc_verification import (
    load_takeoff_data,
    validate_takeoff_data,
    calculate_verification_metrics
)

# Report generation
from utils.report_generator import generate_excel_report
```

All utility functions remain in `utils/` modules.

---

## Testing Strategy

### Manual Test
```bash
streamlit run main.py
```

**Test cases:**
1. Upload only Excel → complete pipeline
2. Upload Excel + CSV → with verification
3. Edit mappings → check persistence
4. Download all reports → verify contents
5. Start over → check reset

### Expected Behavior
- ✅ One upload triggers auto-detection
- ✅ Edits update dataframe immediately
- ✅ Verification runs automatically
- ✅ Analysis displays without navigation
- ✅ All downloads work
- ✅ Start over clears session state

---

## Future Enhancements

### Near-term
- [ ] Direct IFC processing (not just CSV)
- [ ] Save/load pipeline state
- [ ] Export pipeline to PDF

### Long-term
- [ ] Real-time collaboration
- [ ] Version control for mappings
- [ ] Template management

---

## Migration Notes

### What Changed for Users

**Before:**
```
1. Upload file
2. Click "Validering" page
3. Review mappings
4. Click "Material-Verifisering" page
5. Upload verification file
6. Click back to main page
7. Click "Innsikt" page
8. See results
9. Download report
```
**9 steps, multiple context switches**

**After:**
```
1. Upload files (all at once)
2. Scroll down
3. Download report
```
**3 steps, zero context switches**

### Data Format Unchanged
- Excel input format: same
- Verification CSV format: same
- Output reports: same
- All existing data compatible

---

## Success Criteria

✅ **Usability**
- Single page, zero navigation
- Clear visual progress
- Automatic flow advancement

✅ **Functionality**
- All features preserved
- Upload → Download pipeline complete
- Verification integrated seamlessly

✅ **Performance**
- Fast auto-detection
- Responsive editing
- Quick report generation

✅ **Maintainability**
- Single file architecture
- Clear step separation
- Reusable utility functions

---

## Summary

**From:** 7 separate pages with independent I/O
**To:** 1 continuous pipeline with unified flow

**User clicks:** 9 → 3 (67% reduction)
**Code files:** 7 → 1 (86% reduction)
**Navigation decisions:** Many → Zero

**Result:** Users get pulled through from INPUT to OUTPUT with zero context-aware clicks.
