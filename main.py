# -*- coding: utf-8 -*-
"""
LCA Scenario Mapping - Upload & Map Your Data
"""

import streamlit as st
import pandas as pd
import logging
from pathlib import Path

# Import utilities
from utils.data_parser import (
    load_excel_file,
    get_mapping_statistics
)
from utils.predefined_structure import SCENARIOS, DISCIPLINES, MMI_CODES

# Setup logging
log_dir = Path("outputs/logs")
log_dir.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
logger.info("=== LCA Scenario Mapping Application Started ===")

st.set_page_config(
    page_title="LCA Scenario Mapping",
    page_icon="📊",
    layout="wide"
)

st.title("LCA Scenario Mapping")

# Initialize session state
if 'df' not in st.session_state:
    st.session_state['df'] = None

# ==============================================================================
# STEP 1: FILE UPLOAD
# ==============================================================================
st.markdown("### Step 1: Upload Excel File")

excel_file = st.file_uploader(
    "Upload Reduzer Excel export",
    type=['xlsx', 'xls'],
    help="Excel file with GWP data from Reduzer"
)

if excel_file:
    try:
        df = load_excel_file(excel_file)
        st.session_state['df'] = df
        st.success(f"✓ Loaded {len(df)} rows")

    except Exception as e:
        st.error(f"Error loading file: {e}")
        logger.error(f"File load error: {e}", exc_info=True)

# ==============================================================================
# STEP 2: MAPPING & VERIFICATION
# ==============================================================================
if st.session_state['df'] is not None:
    df = st.session_state['df']

    # Recalculate weighted values on every load to ensure display is current
    df['weighting'] = pd.to_numeric(df['weighting'], errors='coerce').fillna(100.0)
    df['weighting'] = df['weighting'].clip(lower=0, upper=100)

    # Apply weighting to phase values
    df['construction_a'] = df['construction_a_base'] * (df['weighting'] / 100.0)
    df['operation_b'] = df['operation_b_base'] * (df['weighting'] / 100.0)
    df['end_of_life_c'] = df['end_of_life_c_base'] * (df['weighting'] / 100.0)

    # Calculate weighted total GWP
    df['total_gwp'] = df['total_gwp_base'] * (df['weighting'] / 100.0)
    st.session_state['df'] = df

    st.markdown("---")
    st.markdown("### Step 2: Review Mappings")

    # Calculate statistics
    def calculate_stats(dataframe):
        """Calculate mapping statistics"""
        stats = get_mapping_statistics(dataframe)
        unmapped = dataframe[
            (~dataframe['excluded']) &
            (dataframe['mapped_scenario'].isna() | dataframe['mapped_discipline'].isna() | dataframe['mapped_mmi_code'].isna())
        ].shape[0]
        return stats, unmapped

    stats, unmapped_count = calculate_stats(df)

    # Quick stats
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Rows", len(df))
    with col2:
        st.metric("Active", stats['active_rows'])
    with col3:
        st.metric("Mapped", f"{stats['mapping_completeness']:.0f}%")
    with col4:
        if unmapped_count > 0:
            st.metric("⚠️ Needs Review", unmapped_count)
        else:
            st.metric("✅ Complete", stats['fully_mapped'])

    # Filter options
    col1, col2 = st.columns([3, 1])
    with col1:
        filter_view = st.radio(
            "View:",
            ["All Rows", "Unmapped Only", "Excluded Only"],
            horizontal=True,
            label_visibility="collapsed"
        )
    with col2:
        st.markdown("")  # Spacer

    # Apply filter
    if filter_view == "Unmapped Only":
        display_df = df[
            (~df['excluded']) &
            (df['mapped_scenario'].isna() | df['mapped_discipline'].isna() | df['mapped_mmi_code'].isna())
        ].copy()
    elif filter_view == "Excluded Only":
        display_df = df[df['excluded']].copy()
    else:
        display_df = df.copy()

    # Editable data editor
    st.caption(f"Showing {len(display_df)} of {len(df)} rows")

    # Create a copy with an index column for tracking
    display_df_with_idx = display_df.copy()
    display_df_with_idx['_idx'] = display_df_with_idx.index

    edited_df = st.data_editor(
        display_df_with_idx[[
            '_idx',
            'category',
            'suggested_scenario', 'mapped_scenario',
            'suggested_discipline', 'mapped_discipline',
            'suggested_mmi_code', 'mapped_mmi_code',
            'weighting',
            'excluded'
        ]],
        column_config={
            '_idx': st.column_config.NumberColumn('Row', width='small', disabled=True),
            'category': st.column_config.TextColumn('Kategori', width='large', disabled=True),
            'suggested_scenario': st.column_config.TextColumn('Forslag S', width='small', disabled=True),
            'mapped_scenario': st.column_config.SelectboxColumn('Scenario', options=SCENARIOS, width='small'),
            'suggested_discipline': st.column_config.TextColumn('Forslag D', width='small', disabled=True),
            'mapped_discipline': st.column_config.SelectboxColumn('Disiplin', options=DISCIPLINES, width='small'),
            'suggested_mmi_code': st.column_config.NumberColumn('Forslag M', width='small', disabled=True),
            'mapped_mmi_code': st.column_config.SelectboxColumn('MMI', options=list(MMI_CODES.keys()), width='small'),
            'weighting': st.column_config.NumberColumn('Vekting %', min_value=0, max_value=100, step=5, format="%.0f", width='small', help="0-100% vekting av GWP"),
            'excluded': st.column_config.CheckboxColumn('Ekskludert', width='small')
        },
        use_container_width=True,
        hide_index=True,
        num_rows="fixed",
        height=400,
        key='data_editor'
    )

    # Always update the main dataframe with edits from the data editor
    editable_cols = ['mapped_scenario', 'mapped_discipline', 'mapped_mmi_code', 'weighting', 'excluded']
    for idx, row in edited_df.iterrows():
        original_idx = int(row['_idx'])
        for col in editable_cols:
            if col in row:
                df.at[original_idx, col] = row[col]

    # Save any edits to session state
    st.session_state['df'] = df

    # Action buttons
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("🔄 Apply Changes", help="Apply your edits and refresh calculations"):
            st.rerun()
    with col2:
        if st.button("➡️ Continue to Visual Analysis", type="primary", use_container_width=True, help="Save changes and go to analysis page"):
            st.switch_page("pages/1_Visual_Analysis.py")

    # Recalculate unmapped count after edits
    _, unmapped_count_after = calculate_stats(df)

    if unmapped_count_after > 0:
        st.warning(f"⚠️ {unmapped_count_after} rows still need mapping. Edit above or continue with mapped data only.")
    else:
        st.success("✅ All active rows are mapped!")

    # Navigation prompt
    st.markdown("---")
    if unmapped_count_after == 0:
        st.success("✓ Ready for analysis → Navigate to **Visual Analysis**")
    else:
        st.info(f"⚠️ {unmapped_count_after} rows unmapped. Proceed to **Visual Analysis** or finish mapping first.")

else:
    st.info("👆 Upload an Excel file to get started")
