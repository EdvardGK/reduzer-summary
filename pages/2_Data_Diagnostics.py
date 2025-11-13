# -*- coding: utf-8 -*-
"""
Page 3: Data Diagnostics
Debug data detection and mapping issues
"""

import streamlit as st
import pandas as pd
from utils.data_diagnostics import (
    diagnose_mmi_distribution,
    get_sample_categories_by_mmi,
    check_unmapped_mmi_codes,
    get_detection_failures
)

st.set_page_config(page_title="Data Diagnostics", page_icon="🔍", layout="wide")

st.title("🔍 Data Diagnostics")
st.caption("Debug MMI detection and mapping issues")

# Check if data exists
if 'df' not in st.session_state or st.session_state['df'] is None:
    st.warning("⚠️ No data loaded. Go back to the main page to upload data.")
    st.stop()

df = st.session_state['df']

# ==============================================================================
# MMI DISTRIBUTION OVERVIEW
# ==============================================================================
st.markdown("## 📊 MMI Code Distribution")
st.markdown("This shows how many rows have each MMI code in your data.")

diag_df = diagnose_mmi_distribution(df)
st.dataframe(diag_df, use_container_width=True, hide_index=True)

st.markdown("### 📝 What This Means:")
st.markdown("""
- **Suggested**: Auto-detected from category names
- **Mapped**: What will be used in analysis (you can edit these)
- **Active**: Not excluded (summary rows, "utdatert", "copy", etc. are excluded)
- **With GWP > 0**: Rows that actually have climate impact data

**If "NY (New)" shows 0 in "With GWP > 0", then there's no MMI 300 data to display in the chart!**
""")

# ==============================================================================
# SAMPLES BY MMI CODE
# ==============================================================================
st.markdown("---")
st.markdown("## 📋 Sample Categories by MMI Code")
st.caption("See actual category strings for each MMI code")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 300 - NY (New)")
    samples_300 = get_sample_categories_by_mmi(df, '300', n=10)
    if samples_300:
        for sample in samples_300:
            st.text(f"• {sample}")
    else:
        st.warning("❌ No categories detected as MMI 300 (New)")

    st.markdown("### 800 - GJEN (Reuse)")
    samples_800 = get_sample_categories_by_mmi(df, '800', n=10)
    if samples_800:
        for sample in samples_800:
            st.text(f"• {sample}")
    else:
        st.info("No categories detected as MMI 800 (Reuse)")

with col2:
    st.markdown("### 700 - EKS (Existing)")
    samples_700 = get_sample_categories_by_mmi(df, '700', n=10)
    if samples_700:
        for sample in samples_700:
            st.text(f"• {sample}")
    else:
        st.info("No categories detected as MMI 700 (Existing)")

    st.markdown("### 900 - RIVES (Demolish)")
    samples_900 = get_sample_categories_by_mmi(df, '900', n=10)
    if samples_900:
        for sample in samples_900:
            st.text(f"• {sample}")
    else:
        st.info("No categories detected as MMI 900 (Demolish)")

# ==============================================================================
# DETECTION FAILURES
# ==============================================================================
st.markdown("---")
st.markdown("## ⚠️ Detection Failures")
st.caption("Rows where MMI code could not be auto-detected")

failures = get_detection_failures(df)
if not failures.empty:
    st.warning(f"Found {len(failures)} active rows with no suggested MMI code")
    st.dataframe(failures, use_container_width=True, hide_index=True)
    st.info("💡 **Fix**: Go to the main page and manually map these rows using the 'MMI' dropdown.")
else:
    st.success("✅ All active rows have suggested MMI codes!")

# ==============================================================================
# MAPPING MISMATCHES
# ==============================================================================
st.markdown("---")
st.markdown("## 🔄 Suggested vs Mapped Mismatches")
st.caption("Rows where you (or the system) mapped differently than the auto-suggestion")

mismatches = check_unmapped_mmi_codes(df)
if not mismatches.empty:
    st.info(f"Found {len(mismatches)} rows with mapping differences")
    st.dataframe(mismatches.head(20), use_container_width=True, hide_index=True)
else:
    st.success("✅ No mismatches - all mapped values match suggestions")

# ==============================================================================
# DETECTION HELP
# ==============================================================================
st.markdown("---")
st.markdown("## 💡 How MMI Detection Works")

st.markdown("""
The system looks for these patterns in your category names:

**MMI 300 (NY/New)**:
- Keywords: `New`, `Nybygg`, `NY`
- Direct codes: `300`, `MMI300`, `MMI 300`

**MMI 700 (EKS/Existing)**:
- Keywords: `Existing`, `Eksisterende`, `Beholdes`, `EKS`, `Kept`
- Direct codes: `700`, `MMI700`, `MMI 700`

**MMI 800 (GJEN/Reuse)**:
- Keywords: `Reused`, `Gjenbruk`, `GJEN`
- Direct codes: `800`, `MMI800`, `MMI 800`

**MMI 900 (RIVES/Demolish)**:
- Keywords: `Existing Waste`, `Rives`, `Riving`, `Demolish`, `Demo`
- Direct codes: `900`, `MMI900`, `MMI 900`

**Example category strings**:
- ✅ `Scenario A - RIV - New` → Scenario=A, Discipline=RIV, MMI=300
- ✅ `ScenarioC_ARK_Existing` → Scenario=C, Discipline=ARK, MMI=700
- ✅ `C-RIB-MMI800-Gjenbruk` → Scenario=C, Discipline=RIB, MMI=800

If your categories don't match these patterns, you need to manually map them on the main page.
""")

# ==============================================================================
# QUICK FIX SUGGESTIONS
# ==============================================================================
st.markdown("---")
st.markdown("## 🔧 Quick Fix Suggestions")

# Check if MMI 300 is missing
mmi_300_count = diag_df[diag_df['MMI Code'] == '300']['With GWP > 0'].values[0]
if mmi_300_count == 0:
    st.error("""
    **Problem**: No rows with MMI 300 (NY/New) found in your active mapped data!

    **Possible causes**:
    1. Your Excel file doesn't contain "New" or "Nybygg" in category names
    2. All MMI 300 rows are excluded (marked as summary/copy/utdatert)
    3. All MMI 300 rows have zero GWP (no climate impact)
    4. Detection isn't finding the pattern in your category strings

    **Solutions**:
    1. Check your Excel file - do you have any "New" components?
    2. Go to main page, filter "Excluded Only", see if MMI 300 rows are there
    3. Go to main page, manually map some rows to MMI 300 using the dropdown
    4. Check if your category names use different terminology (e.g., "Fresh", "Brand New", etc.)
    """)
else:
    st.success(f"✅ Found {mmi_300_count} rows with MMI 300 (NY/New)")

st.markdown("---")
st.markdown("### 🔙 Go back to the main page to edit mappings")
if st.button("← Back to Mapping"):
    st.switch_page("main.py")
