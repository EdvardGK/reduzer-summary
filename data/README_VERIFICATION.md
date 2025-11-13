# Material Verification - Quick Start

## What You'll Do

**3 Simple Steps:**
1. **Upload** CSV/Excel with material counts
2. **Review** PASS/FAIL verdict
3. **Export** report (if needed)

**Time required:** 5 minutes

---

## Step 1: Prepare Your Data

### Get Material Counts

Export from your BIM tool:
- Revit: Schedule → Export to CSV
- ArchiCAD: Element Schedule → Save as Excel
- IFC Viewer: Quantity Takeoff → Export

### Required Columns

Your file must have these columns:

| Column | Example | What It Means |
|--------|---------|---------------|
| **Object Type** | "Innvendige skillevegger" | Name of material/component |
| **Discipline** | "ARK" | ARK/RIV/RIE/RIB/RIBp |
| **Scenario** | "A" | A or C |
| **MMI Category** | 300 | 300/700/800 |
| **Quantity** | 120 | Number (count/area/volume) |
| **Unit** | "m2" | m2/m3/pcs/kg/m |

Optional: `IFC Class`, `Description`, `Notes`

### Download Template

Get the blank template: `data/samples/ifc_takeoff_blank.csv`

---

## Step 2: Fill in Your Data

### Scenario A (Conventional Renovation)
Everything is **NEW** (MMI 300)

```csv
Object Type,Discipline,Scenario,MMI Category,Quantity,Unit
Interior walls,ARK,A,300,120,m2
Doors,ARK,A,300,45,pcs
HVAC ducts,RIV,A,300,450,m
```

### Scenario C (Circular Renovation)
Split between **NEW (300)**, **KEPT (700)**, and **REUSED (800)**

```csv
Object Type,Discipline,Scenario,MMI Category,Quantity,Unit
Interior walls,ARK,C,700,85,m2
Interior walls,ARK,C,300,35,m2
Doors,ARK,C,700,30,pcs
Doors,ARK,C,800,10,pcs
Doors,ARK,C,300,5,pcs
HVAC ducts,RIV,C,700,280,m
HVAC ducts,RIV,C,800,100,m
HVAC ducts,RIV,C,300,70,m
```

**Important:** Totals must match!
```
Scenario A: Interior walls = 120 m²
Scenario C: 85 m² + 35 m² = 120 m² ✓
```

---

## Step 3: Upload & Verify

1. Start app: `streamlit run main.py`
2. Go to **📊 Material-Verifisering** page
3. Upload your CSV/Excel file
4. See verdict instantly

### If PASS ✅
You're done! Both scenarios are consistent.
- Download the report (optional)
- Continue with LCA analysis

### If FAIL ❌
Fix the data:
1. Check "Elementer som trenger gjennomgang" section
2. Look for common issues (see below)
3. Fix errors in your file
4. Upload again

---

## Common Issues & Fixes

### Issue: "Invalid disciplines found"
**Error:** Used "Architect" instead of "ARK"
**Fix:** Use exact codes: ARK, RIV, RIE, RIB, RIBp

### Issue: "Inconsistent units"
**Error:** Scenario A uses "m2", Scenario C uses "mm2"
**Fix:** Use same unit for same object (convert mm2 → m2)

### Issue: "Scenario A must only use MMI 300"
**Error:** Put MMI 700 in Scenario A
**Fix:** Scenario A = 100% new = all MMI 300

### Issue: High deviation (>10%)
**Error:** Scenario A has 500 m², Scenario C has 350 m²
**Causes:**
- Missing elements in Scenario C
- Different building versions
- Wrong quantities

**Fix:**
1. Check which objects have high deviation
2. Verify all objects exist in both scenarios
3. Confirm same design stage
4. Re-check your source data

---

## Example: Perfect Match

```
Object: Interior walls

Scenario A:
- Object Type: "Interior walls"
- Scenario: A
- MMI: 300 (all new)
- Quantity: 120 m²

Scenario C:
- Object Type: "Interior walls"
- Scenario: C
- MMI: 700 (kept) → 85 m²
- MMI: 300 (new) → 35 m²
- Total: 120 m²

Result: 0% deviation ✅ PASS
```

---

## What Gets Verified

**The Formula:**
```
Scenario A (MMI 300) = Scenario C (MMI 300 + 700 + 800)
```

**Why:** Both scenarios must produce the **exact same building**. If totals don't match, there's a data error that will invalidate your LCA comparison.

**Tolerance:** ≤5% acceptable (accounts for rounding)

---

## Output: The Verdict

### PASS ✅
```
Deviation: 2.1%

✓ Scenarios are consistent
✓ Same physical building
✓ Ready for LCA analysis
```

### FAIL ❌
```
Deviation: 12.5%

✗ Scenarios differ significantly
✗ Data requires review
✗ Fix before continuing

Flagged items:
- HVAC ducts: 15% deviation
- Electrical cables: 10% deviation
```

---

## Download Report

Click **"📊 Excel-rapport"** to get:
- Summary with verdict
- Full comparison table
- Discipline breakdown
- Flagged items list
- All metrics

---

## Need More Help?

**Example file:** `data/samples/ifc_takeoff_template.csv`
**Full docs:** `docs/IFC_TAKEOFF_VERIFICATION.md`
**Technical details:** `docs/worklog/2025-11-07-15-30_Material-Verification-Implementation.md`

---

## Quick Reference: MMI Categories

| MMI | Name | Used In |
|-----|------|---------|
| 300 | New materials | Scenario A (100%) + Scenario C (minimal) |
| 700 | Existing kept | Scenario C only |
| 800 | Reused from other projects | Scenario C only |
| 900 | Waste | Not used in verification |
