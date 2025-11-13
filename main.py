# -*- coding: utf-8 -*-
"""
LCA Scenario Mapping - Continuous Pipeline

INPUT → Auto-detect → Validate → Verify → Analyze → OUTPUT
One page. Zero navigation. Just scroll.
"""

import streamlit as st
import pandas as pd
import logging
from datetime import datetime
from io import BytesIO
from pathlib import Path

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

from utils.data_parser import (
    load_excel_file,
    aggregate_by_mapping,
    get_scenario_summary,
    compare_scenarios,
    get_mapping_statistics
)
from utils.detector import detect_all
from utils.predefined_structure import SCENARIOS, DISCIPLINES, MMI_CODES
from utils.visualizations import (
    create_scenario_stacked_bar,
    create_scenario_comparison_chart,
    create_all_disciplines_comparison
)

# IFC/Verification imports (optional)
try:
    from utils.ifc_verification import (
        load_takeoff_data,
        validate_takeoff_data,
        calculate_verification_metrics
    )
    VERIFICATION_AVAILABLE = True
except ImportError:
    VERIFICATION_AVAILABLE = False

st.set_page_config(page_title="LCA Scenario Mapping", page_icon="📊", layout="wide")

# Custom CSS
st.markdown("""
<style>
[data-testid="stMetricValue"] {
    font-size: 2.5rem;
    font-weight: 700;
}

/* Step headers */
.step-header {
    background: linear-gradient(90deg, #1976d2 0%, #2196f3 100%);
    color: white;
    padding: 1rem 1.5rem;
    border-radius: 8px;
    margin: 2rem 0 1rem 0;
    font-size: 1.3rem;
    font-weight: 600;
}

/* Progress indicator */
.progress-step {
    display: inline-block;
    width: 32px;
    height: 32px;
    line-height: 32px;
    text-align: center;
    background: #2196f3;
    color: white;
    border-radius: 50%;
    margin-right: 0.5rem;
    font-weight: 700;
}

.progress-step.completed {
    background: #4caf50;
}

.progress-step.current {
    background: #ff9800;
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.6; }
}

/* Better section spacing */
.pipeline-section {
    background: #fafafa;
    border-radius: 8px;
    padding: 1.5rem;
    margin: 1rem 0;
}
</style>
""", unsafe_allow_html=True)

# ============================================
# SESSION STATE INITIALIZATION
# ============================================
if 'pipeline_step' not in st.session_state:
    st.session_state['pipeline_step'] = 1
if 'df' not in st.session_state:
    st.session_state['df'] = None
if 'verification_data' not in st.session_state:
    st.session_state['verification_data'] = None
if 'verification_metrics' not in st.session_state:
    st.session_state['verification_metrics'] = None

# ============================================
# HEADER
# ============================================
st.title("📊 LCA Scenario Mapping")
st.markdown("""
**Continuous pipeline:** Upload → Map → Verify → Analyze → Download
""")

# Progress indicator
current_step = st.session_state['pipeline_step']
progress_html = f"""
<div style="margin: 1rem 0;">
    <span class="progress-step {'completed' if current_step > 1 else 'current' if current_step == 1 else ''}">1</span>
    <span class="progress-step {'completed' if current_step > 2 else 'current' if current_step == 2 else ''}">2</span>
    <span class="progress-step {'completed' if current_step > 3 else 'current' if current_step == 3 else ''}">3</span>
    <span class="progress-step {'completed' if current_step > 4 else 'current' if current_step == 4 else ''}">4</span>
    <span class="progress-step {'completed' if current_step >= 5 else 'current' if current_step == 5 else ''}">5</span>
    Upload → Map → Verify → Analyze → Download
</div>
"""
st.markdown(progress_html, unsafe_allow_html=True)

st.markdown("---")

# ============================================
# STEP 1: UPLOAD
# ============================================
st.markdown('<div class="step-header">📤 Step 1: Upload Data</div>', unsafe_allow_html=True)

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### Required: LCA Data")
    excel_file = st.file_uploader(
        "Excel file with LCA summaries (models 1,2,3,4)",
        type=['xlsx', 'xls'],
        help="Main data file from Reduzer"
    )

with col2:
    st.markdown("### Optional: Verification")
    verification_choice = st.radio(
        "Quantity verification:",
        ["None", "IFC files", "Takeoff CSV"],
        help="Optional - verify material quantities match across scenarios"
    )

# Upload verification files based on choice
verification_file = None
if verification_choice == "IFC files":
    verification_file = st.file_uploader(
        "Upload IFC file(s)",
        type=['ifc'],
        accept_multiple_files=True,
        help="IFC models for automatic quantity extraction"
    )
elif verification_choice == "Takeoff CSV":
    verification_file = st.file_uploader(
        "Upload takeoff CSV",
        type=['csv', 'xlsx'],
        help="Pre-exported material quantities"
    )

# Process Excel file
if excel_file is not None and st.session_state['df'] is None:
    try:
        with st.spinner("Loading LCA data..."):
            df = load_excel_file(excel_file)
            st.session_state['df'] = df
            st.session_state['pipeline_step'] = 2
            st.success(f"✅ Loaded {len(df)} rows")
            st.rerun()
    except Exception as e:
        st.error(f"❌ Error loading Excel: {str(e)}")
        st.stop()

# Process verification file
if verification_file is not None and VERIFICATION_AVAILABLE:
    if verification_choice == "Takeoff CSV":
        try:
            with st.spinner("Loading verification data..."):
                verif_df = load_takeoff_data(verification_file)
                errors = validate_takeoff_data(verif_df)

                if errors:
                    st.warning("⚠️ Verification data has issues:")
                    for error in errors:
                        st.caption(f"• {error}")
                else:
                    st.session_state['verification_data'] = verif_df
                    st.success("✅ Verification data loaded")
        except Exception as e:
            st.warning(f"⚠️ Could not load verification data: {e}")
    elif verification_choice == "IFC files":
        st.info("📋 IFC processing not yet implemented in continuous pipeline. Use Takeoff CSV for now.")

# Show welcome if no data yet
if st.session_state['df'] is None:
    st.info("""
    ### 🚀 Get Started

    **Upload your Excel file** with LCA data to begin the analysis.

    **What this tool does:**
    - Auto-detects scenarios, disciplines, and MMI categories
    - Validates your data mapping
    - Compares scenarios (C vs A)
    - Verifies material quantities (optional)
    - Generates comprehensive report

    **One continuous flow - no navigation needed.**
    """)
    st.stop()

# ============================================
# STEP 2: VALIDATE MAPPING
# ============================================
df = st.session_state['df']

st.markdown("---")
st.markdown('<div class="step-header">✅ Step 2: Validate Mapping</div>', unsafe_allow_html=True)

st.markdown("""
Auto-detected mapping shown below. **Edit inline if needed**, then continue scrolling.
""")

# Get statistics (will recalculate after edits)
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
    filter_option = st.radio(
        "Show:",
        ["All rows", "Unmapped only", "Mapped only", "Excluded only"],
        horizontal=True
    )

with col2:
    if st.button("🔄 Refresh", use_container_width=True):
        st.rerun()

# Apply filter
if filter_option == "Unmapped only":
    display_df = df[
        (~df['excluded']) &
        (df['mapped_scenario'].isna() | df['mapped_discipline'].isna() | df['mapped_mmi_code'].isna())
    ].copy()
elif filter_option == "Mapped only":
    display_df = df[
        (~df['excluded']) &
        df['mapped_scenario'].notna() &
        df['mapped_discipline'].notna() &
        df['mapped_mmi_code'].notna()
    ].copy()
elif filter_option == "Excluded only":
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
        'excluded',
        'construction_a', 'operation_b', 'end_of_life_c', 'total_gwp_base', 'total_gwp'
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
        'excluded': st.column_config.CheckboxColumn('Ekskludert', width='small'),
        'construction_a': st.column_config.NumberColumn('Konstr (A)', format="%.0f", disabled=True, width='small'),
        'operation_b': st.column_config.NumberColumn('Drift (B)', format="%.0f", disabled=True, width='small'),
        'end_of_life_c': st.column_config.NumberColumn('Avsl (C)', format="%.0f", disabled=True, width='small'),
        'total_gwp_base': st.column_config.NumberColumn('GWP basis', format="%.0f", disabled=True, width='small'),
        'total_gwp': st.column_config.NumberColumn('GWP vektet', format="%.0f", disabled=True, width='small')
    },
    use_container_width=True,
    hide_index=True,
    num_rows="fixed",
    height=400,
    key='data_editor'
)

# Update the main dataframe with edits using the index
editable_cols = ['mapped_scenario', 'mapped_discipline', 'mapped_mmi_code', 'weighting', 'excluded']
for idx, row in edited_df.iterrows():
    original_idx = int(row['_idx'])
    for col in editable_cols:
        if col in row:
            df.at[original_idx, col] = row[col]

# Recalculate all weighted GWP values after edits
df['weighting'] = pd.to_numeric(df['weighting'], errors='coerce').fillna(100.0)
df['weighting'] = df['weighting'].clip(lower=0, upper=100)  # Ensure 0-100 range
df['total_gwp'] = df['total_gwp_base'] * (df['weighting'] / 100.0)

st.session_state['df'] = df
st.session_state['pipeline_step'] = max(st.session_state['pipeline_step'], 3)

# Recalculate unmapped count after edits
_, unmapped_count_after = calculate_stats(df)

if unmapped_count_after > 0:
    st.warning(f"⚠️ {unmapped_count_after} rows still need mapping. Edit above or continue with mapped data only.")
else:
    st.success("✅ All active rows are mapped!")

# ============================================
# STEP 3: VERIFICATION (if data provided)
# ============================================
st.markdown("---")
st.markdown('<div class="step-header">🔍 Step 3: Quantity Verification</div>', unsafe_allow_html=True)

if st.session_state['verification_data'] is not None:
    with st.spinner("Calculating verification metrics..."):
        verif_df = st.session_state['verification_data']
        metrics = calculate_verification_metrics(verif_df)
        st.session_state['verification_metrics'] = metrics
        st.session_state['pipeline_step'] = max(st.session_state['pipeline_step'], 4)

    if metrics['status'] == 'success':
        overall = metrics['overall']
        deviation_pct = overall['overall_deviation_pct']

        # Verdict
        if deviation_pct < 5.0:
            st.success(f"""
            ### ✅ PASS - Quantities verified

            Scenario A and C are consistent (deviation: {deviation_pct:.2f}%)

            Both scenarios represent the same physical building.
            """)
        else:
            st.error(f"""
            ### ❌ FAIL - Quantities mismatch

            Scenarios differ by {deviation_pct:.2f}% (tolerance: <5%)

            Review flagged items below before continuing.
            """)

        # Quick metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Scenario A Total", f"{overall['total_qty_a']:,.0f}")
        with col2:
            st.metric("Scenario C Total", f"{overall['total_qty_c']:,.0f}")
        with col3:
            st.metric("Absolute Deviation", f"{overall['total_deviation_abs']:,.0f}")
        with col4:
            st.metric("Deviation %", f"{deviation_pct:.2f}%")

        # Show flagged items if any
        flagged_items = metrics['flagged_items']
        if not flagged_items.empty:
            with st.expander(f"⚠️ {len(flagged_items)} items need review"):
                st.dataframe(
                    flagged_items[['Object Type', 'Discipline', 'Qty_A', 'Qty_C_Total', 'Deviation_Pct']].head(10),
                    use_container_width=True,
                    hide_index=True
                )
    else:
        st.warning("⚠️ Verification calculation failed. Continuing without verification.")
else:
    st.info("ℹ️ No verification data provided. Skipping quantity verification.")
    st.session_state['pipeline_step'] = max(st.session_state['pipeline_step'], 4)

# ============================================
# STEP 4: ANALYSIS
# ============================================
st.markdown("---")
st.markdown('<div class="step-header">📊 Step 4: Analysis & Comparison</div>', unsafe_allow_html=True)

try:
    structure = aggregate_by_mapping(df)
    st.session_state['pipeline_step'] = max(st.session_state['pipeline_step'], 5)

    # Check if we have scenarios to compare
    if 'C' in structure and 'A' in structure:
        comparison = compare_scenarios(structure, 'A', 'C')

        if comparison and comparison['ratio']['total_gwp']:
            ratio = comparison['ratio']['total_gwp']
            diff = comparison['difference']['total_gwp']
            is_worse = ratio > 100

            # HERO VERDICT
            if is_worse:
                st.error(f"""
                ## ⚠️ Scenario C is {abs(ratio - 100):.1f}% WORSE

                **+{diff:,.0f} kg CO2e** more emissions than Scenario A
                """)
            else:
                st.success(f"""
                ## ✅ Scenario C is {abs(100 - ratio):.1f}% BETTER

                **{diff:,.0f} kg CO2e** less emissions than Scenario A
                """)

            # Quick metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Ratio C/A", f"{ratio:.1f}%")
            with col2:
                st.metric("Difference", f"{diff:,.0f} kg CO2e")
            with col3:
                st.metric("Data Quality", f"{stats['mapping_completeness']:.0f}%")

            # Charts
            st.markdown("### Scenario Comparison")

            col1, col2 = st.columns(2)

            with col1:
                # Stacked bar chart
                fig_stacked = create_scenario_stacked_bar(structure)
                if fig_stacked:
                    st.plotly_chart(fig_stacked, use_container_width=True)

            with col2:
                # Comparison chart
                fig_compare = create_scenario_comparison_chart(structure, 'A', 'C')
                if fig_compare:
                    st.plotly_chart(fig_compare, use_container_width=True)

            # Discipline breakdown
            st.markdown("### By Discipline")
            fig_disc = create_all_disciplines_comparison(structure, 'A', 'C')
            if fig_disc:
                st.plotly_chart(fig_disc, use_container_width=True)

        else:
            st.warning("⚠️ Cannot compare scenarios - insufficient data")

    else:
        st.info("ℹ️ Need both Scenario A and C for comparison. Available: " + ", ".join(structure.keys()))

except Exception as e:
    st.error(f"❌ Analysis error: {str(e)}")

# ============================================
# STEP 5: DOWNLOAD
# ============================================
st.markdown("---")
st.markdown('<div class="step-header">📥 Step 5: Download Report</div>', unsafe_allow_html=True)

st.markdown("Get your complete analysis report with all data, charts, and verification results.")

scenario_summary = get_scenario_summary(structure)

col1, col2 = st.columns(2)

with col1:
    # Excel report
    try:
        from utils.report_generator import generate_excel_report
        excel_data = generate_excel_report(df, structure, scenario_summary)

        st.download_button(
            "📊 Download Excel Report",
            data=excel_data,
            file_name=f"lca_rapport_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            type="primary"
        )
    except Exception as e:
        st.error(f"Excel generation error: {e}")

with col2:
    # PDF report
    try:
        from utils.report_generator import generate_pdf_report
        pdf_data = generate_pdf_report(df, structure, scenario_summary)

        st.download_button(
            "📄 Download PDF Report",
            data=pdf_data,
            file_name=f"lca_rapport_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
            mime="application/pdf",
            use_container_width=True,
            type="primary"
        )
    except ImportError as e:
        st.warning("⚠️ PDF generation requires 'reportlab' and 'kaleido' packages")
    except Exception as e:
        st.error(f"PDF generation error: {e}")

st.markdown("---")

col1, col2, col3 = st.columns(3)

with col1:
    # Export complete mapped data as CSV
    active_df = df[~df['excluded'] & df['mapped_scenario'].notna()].copy()

    export_cols = [
        'category',
        'mapped_scenario',
        'mapped_discipline',
        'mapped_mmi_code',
        'weighting',
        'construction_a',
        'operation_b',
        'end_of_life_c',
        'total_gwp_base',
        'total_gwp'
    ]

    csv_export = active_df[export_cols].rename(columns={
        'category': 'Kategori',
        'mapped_scenario': 'Scenario',
        'mapped_discipline': 'Disiplin',
        'mapped_mmi_code': 'MMI',
        'weighting': 'Vekting_pct',
        'construction_a': 'Konstruksjon_A_kg_CO2e',
        'operation_b': 'Drift_B_kg_CO2e',
        'end_of_life_c': 'Avslutning_C_kg_CO2e',
        'total_gwp_base': 'GWP_basis_kg_CO2e',
        'total_gwp': 'GWP_vektet_kg_CO2e'
    })

    # Sort for clean export
    csv_export = csv_export.sort_values(['Scenario', 'Disiplin', 'MMI'])
    csv_data = csv_export.to_csv(index=False, encoding='utf-8-sig')  # UTF-8 with BOM for Excel compatibility

    st.download_button(
        "📋 Download Complete Dataset (CSV)",
        data=csv_data,
        file_name=f"lca_data_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv",
        use_container_width=True,
        help="All mapped rows with weighting - ready for analysis"
    )

with col3:
    # Verification report if available
    if st.session_state['verification_metrics'] is not None:
        try:
            from utils.ifc_verification import export_verification_report

            output_path = f"/tmp/verification_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            export_verification_report(st.session_state['verification_metrics'], output_path)

            with open(output_path, 'rb') as f:
                verif_excel = f.read()

            st.download_button(
                "🔍 Verification Report",
                data=verif_excel,
                file_name=f"verification_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        except Exception as e:
            st.caption(f"Verification report unavailable: {e}")

# ============================================
# FOOTER
# ============================================
st.markdown("---")

col1, col2 = st.columns([3, 1])

with col1:
    st.caption("✅ Pipeline complete. Scroll up to review any section or adjust mappings.")

with col2:
    if st.button("🔄 Start Over", use_container_width=True):
        st.session_state.clear()
        st.rerun()
