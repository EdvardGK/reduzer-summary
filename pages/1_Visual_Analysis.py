# -*- coding: utf-8 -*-
"""
Page 2: Visual Analysis
Answer the key question: Is Scenario C better than Scenario A?
"""

import streamlit as st
import pandas as pd
import logging
from typing import Dict, Any, List, Tuple

# Import utilities
from utils.data_parser import (
    aggregate_by_mapping,
    compare_scenarios,
    get_mapping_statistics
)
from utils.visualizations import (
    create_scenario_stacked_bar,
    create_scenario_comparison_chart,
    create_mmi_distribution_pie,
    create_mmi_distribution_by_discipline_pie,
    create_discipline_contribution_pie,
    create_discipline_comparison_chart
)
from utils.report_generator import (
    generate_excel_report,
    generate_csv_report,
    generate_pdf_report
)
from utils.predefined_structure import SCENARIOS, DISCIPLINES

logger = logging.getLogger(__name__)

st.set_page_config(page_title="Visual Analysis", page_icon="📊", layout="wide")

# Check if data exists
if 'df' not in st.session_state or st.session_state['df'] is None:
    st.warning("⚠️ No data loaded. Go back to the main page to upload data.")
    st.stop()

df = st.session_state['df']

# Filter to mapped rows only
mapped_df = df[
    (~df['excluded']) &
    (df['mapped_scenario'].notna()) &
    (df['mapped_discipline'].notna()) &
    (df['mapped_mmi_code'].notna())
].copy()

if len(mapped_df) == 0:
    st.warning("⚠️ No mapped data available. Go back to the main page to complete mapping.")
    st.stop()

# Aggregate structure
try:
    structure = aggregate_by_mapping(mapped_df)
except Exception as e:
    st.error(f"Error aggregating data: {e}")
    logger.error(f"Aggregation error: {e}", exc_info=True)
    st.stop()

# Get available scenarios
available_scenarios = sorted([s for s in structure.keys() if structure[s]['total']['total_gwp'] > 0])

if not available_scenarios:
    st.warning("⚠️ No scenarios with data found.")
    st.stop()

# ==============================================================================
# HERO SECTION - C vs A COMPARISON
# ==============================================================================
def calculate_top_drivers(structure: Dict, scenario_c: str, scenario_a: str, top_n: int = 3) -> List[Tuple[str, float, float, float]]:
    """
    Calculate top N disciplines driving the difference between C and A
    Returns list of (discipline, diff_kg, pct_of_total_diff, c_vs_a_ratio)
    """
    drivers = []

    c_disciplines = structure.get(scenario_c, {}).get('disciplines', {})
    a_disciplines = structure.get(scenario_a, {}).get('disciplines', {})

    all_disciplines = set(list(c_disciplines.keys()) + list(a_disciplines.keys()))

    for disc in all_disciplines:
        c_gwp = c_disciplines.get(disc, {}).get('total', {}).get('total_gwp', 0)
        a_gwp = a_disciplines.get(disc, {}).get('total', {}).get('total_gwp', 0)
        diff = c_gwp - a_gwp

        if a_gwp > 0:
            ratio = (c_gwp / a_gwp) * 100
        else:
            ratio = 100 if c_gwp > 0 else 0

        drivers.append((disc, diff, ratio))

    # Sort by absolute difference (most impact)
    drivers.sort(key=lambda x: abs(x[1]), reverse=True)

    # Calculate percentage of total difference
    total_diff = structure[scenario_c]['total']['total_gwp'] - structure[scenario_a]['total']['total_gwp']

    result = []
    for disc, diff, ratio in drivers[:top_n]:
        if total_diff != 0:
            pct_of_diff = (diff / total_diff) * 100
        else:
            pct_of_diff = 0
        result.append((disc, diff, pct_of_diff, ratio))

    return result


st.title("📊 Visual Analysis")

# Show hero only if C and A exist
if 'C' in available_scenarios and 'A' in available_scenarios:
    try:
        comparison = compare_scenarios(structure, 'A', 'C')

        # Hero metrics
        total_c = structure['C']['total']['total_gwp']
        total_a = structure['A']['total']['total_gwp']
        diff = total_c - total_a
        ratio = (total_c / total_a * 100) if total_a > 0 else 100
        pct_change = ratio - 100

        # Determine if better or worse
        is_better = pct_change < 0
        hero_color = "green" if is_better else "red"
        hero_emoji = "✓" if is_better else "✗"
        hero_text = "BETTER" if is_better else "WORSE"

        # Hero section
        st.markdown(f"## Scenario C vs Scenario A")

        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        with col1:
            st.markdown(f"""
            <div style="padding: 2rem; background: linear-gradient(135deg, {'#e8f5e9' if is_better else '#ffebee'} 0%, {'#c8e6c9' if is_better else '#ffcdd2'} 100%); border-radius: 8px; text-align: center;">
                <div style="font-size: 3.5rem; font-weight: 800; color: {hero_color}; margin-bottom: 0.5rem;">
                    {abs(pct_change):.1f}% {hero_text}
                </div>
                <div style="font-size: 1.2rem; color: #424242;">
                    Scenario C has {abs(pct_change):.1f}% {'lower' if is_better else 'higher'} climate impact
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.metric("Construction (A)",
                     f"{(structure['C']['total']['construction_a'] - structure['A']['total']['construction_a']) / structure['A']['total']['construction_a'] * 100:+.1f}%",
                     help="Lifecycle Phase A: Construction emissions")
        with col3:
            st.metric("Operation (B)",
                     f"{(structure['C']['total']['operation_b'] - structure['A']['total']['operation_b']) / structure['A']['total']['operation_b'] * 100 if structure['A']['total']['operation_b'] > 0 else 0:+.1f}%",
                     help="Lifecycle Phase B: Operation emissions")
        with col4:
            st.metric("End-of-life (C)",
                     f"{(structure['C']['total']['end_of_life_c'] - structure['A']['total']['end_of_life_c']) / structure['A']['total']['end_of_life_c'] * 100 if structure['A']['total']['end_of_life_c'] > 0 else 0:+.1f}%",
                     help="Lifecycle Phase C: End-of-life emissions")

        st.markdown("---")

        # Top Drivers section
        st.markdown("### 🎯 Top Drivers")
        st.caption("Which disciplines are responsible for the difference?")

        top_drivers = calculate_top_drivers(structure, 'C', 'A', top_n=3)

        cols = st.columns(3)
        for idx, (discipline, diff_kg, pct_of_diff, ratio_pct) in enumerate(top_drivers):
            with cols[idx]:
                is_positive = diff_kg < 0
                color = "green" if is_positive else "red"
                sign = "−" if is_positive else "+"

                st.markdown(f"""
                <div style="padding: 1.5rem; background: #f5f5f5; border-left: 4px solid {color}; border-radius: 4px;">
                    <div style="font-size: 1.8rem; font-weight: 700; color: {color};">
                        {idx + 1}. {discipline}
                    </div>
                    <div style="font-size: 1.4rem; color: #424242; margin-top: 0.5rem;">
                        {sign}{abs(diff_kg):,.0f} kg CO2e
                    </div>
                    <div style="font-size: 0.9rem; color: #757575; margin-top: 0.25rem;">
                        {abs(pct_of_diff):.1f}% of total difference
                    </div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("---")

    except Exception as e:
        st.error(f"Error creating C vs A comparison: {e}")
        logger.error(f"C vs A comparison error: {e}", exc_info=True)

else:
    st.info("Upload data with Scenarios C and A to see comparison.")

# ==============================================================================
# TABBED DEEP DIVE
# ==============================================================================
tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "🏗️ Discipline Breakdown", "📦 MMI Analysis", "📥 Download Reports"])

# TAB 1: OVERVIEW
with tab1:
    st.markdown("### All Scenarios")

    if len(available_scenarios) > 1:
        try:
            fig_all_scenarios = create_scenario_stacked_bar(structure)
            st.plotly_chart(fig_all_scenarios, use_container_width=True, key='chart_all_scenarios')
        except Exception as e:
            st.error(f"Error creating scenarios comparison: {e}")
            logger.error(f"Scenarios comparison error: {e}", exc_info=True)

    # Scenario selector for details
    st.markdown("### Scenario Details")
    selected_scenario = st.selectbox("Select Scenario", available_scenarios, index=0)

    scenario_data = structure[selected_scenario]['total']
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total GWP", f"{scenario_data['total_gwp']:,.0f} kg CO2e")
    with col2:
        st.metric("Construction (A)", f"{scenario_data['construction_a']:,.0f} kg")
    with col3:
        st.metric("Operation (B)", f"{scenario_data['operation_b']:,.0f} kg")
    with col4:
        st.metric("End-of-life (C)", f"{scenario_data['end_of_life_c']:,.0f} kg")

    # MMI Distribution for selected scenario
    st.markdown(f"#### MMI Distribution - Scenario {selected_scenario}")
    try:
        fig_scenario_mmi = create_mmi_distribution_pie(structure, selected_scenario)
        st.plotly_chart(fig_scenario_mmi, use_container_width=True, key=f'chart_mmi_tab1_{selected_scenario}')
    except Exception as e:
        st.error(f"Error creating scenario MMI chart: {e}")
        logger.error(f"Scenario MMI chart error: {e}", exc_info=True)

    # C vs A detailed comparison chart (if both exist)
    if 'C' in available_scenarios and 'A' in available_scenarios:
        st.markdown("### Detailed C vs A Comparison")
        try:
            fig_comparison = create_scenario_comparison_chart(structure, 'A', 'C')
            st.plotly_chart(fig_comparison, use_container_width=True, key='chart_c_vs_a_comparison')
        except Exception as e:
            st.error(f"Error creating comparison chart: {e}")

# TAB 2: DISCIPLINE BREAKDOWN
with tab2:
    st.markdown("### Discipline Analysis")

    # Discipline selector
    available_disciplines = set()
    for scenario in available_scenarios:
        available_disciplines.update(structure[scenario]['disciplines'].keys())
    available_disciplines = sorted(available_disciplines)

    selected_scenario_disc = st.selectbox("Select Scenario for Discipline Analysis", available_scenarios, key='disc_scenario')

    # Discipline contribution pie
    st.markdown(f"#### Discipline Contributions - Scenario {selected_scenario_disc}")
    try:
        fig_disciplines = create_discipline_contribution_pie(structure, selected_scenario_disc)
        st.plotly_chart(fig_disciplines, use_container_width=True, key=f'chart_disciplines_{selected_scenario_disc}')
    except Exception as e:
        st.error(f"Error creating discipline breakdown: {e}")
        logger.error(f"Discipline breakdown error: {e}", exc_info=True)

    # MMI by discipline tabs
    st.markdown(f"#### MMI Distribution by Discipline")

    scenario_disciplines = [
        disc for disc in available_disciplines
        if disc in structure[selected_scenario_disc]['disciplines'] and
        structure[selected_scenario_disc]['disciplines'][disc]['total']['total_gwp'] > 0
    ]

    if scenario_disciplines:
        disc_tabs = st.tabs([f"{disc}" for disc in scenario_disciplines])

        for idx, discipline in enumerate(scenario_disciplines):
            with disc_tabs[idx]:
                disc_data = structure[selected_scenario_disc]['disciplines'][discipline]['total']
                scenario_total = structure[selected_scenario_disc]['total']['total_gwp']

                # Metrics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total GWP", f"{disc_data['total_gwp']:,.0f} kg CO2e")
                with col2:
                    pct_of_scenario = (disc_data['total_gwp'] / scenario_total * 100) if scenario_total > 0 else 0
                    st.metric("% of Scenario", f"{pct_of_scenario:.1f}%")
                with col3:
                    st.metric("Construction (A)", f"{disc_data['construction_a']:,.0f} kg")
                with col4:
                    st.metric("Rows", disc_data['count'])

                # Pie chart
                try:
                    fig_disc_mmi = create_mmi_distribution_by_discipline_pie(
                        structure,
                        selected_scenario_disc,
                        discipline
                    )
                    st.plotly_chart(fig_disc_mmi, use_container_width=True, key=f'chart_mmi_disc_{selected_scenario_disc}_{discipline}')
                except Exception as e:
                    st.error(f"Error creating {discipline} MMI chart: {e}")
                    logger.error(f"Discipline {discipline} MMI chart error: {e}", exc_info=True)
    else:
        st.info("No discipline data available for this scenario.")

# TAB 3: MMI ANALYSIS
with tab3:
    st.markdown("### MMI Component Analysis")

    selected_scenario_mmi = st.selectbox("Select Scenario for MMI Analysis", available_scenarios, key='mmi_scenario')

    # Show MMI breakdown
    st.markdown(f"#### MMI Distribution - Scenario {selected_scenario_mmi}")
    try:
        fig_scenario_mmi = create_mmi_distribution_pie(structure, selected_scenario_mmi)
        st.plotly_chart(fig_scenario_mmi, use_container_width=True, key=f'chart_mmi_tab3_{selected_scenario_mmi}')
    except Exception as e:
        st.error(f"Error creating MMI chart: {e}")

    # MMI Stats table
    st.markdown("#### MMI Statistics")
    # Aggregate MMI totals across all disciplines
    mmi_totals = {}
    for discipline, disc_data in structure[selected_scenario_mmi]['disciplines'].items():
        for mmi_code, mmi_data in disc_data['mmi_categories'].items():
            if mmi_code not in mmi_totals:
                mmi_totals[mmi_code] = {
                    'total_gwp': 0,
                    'construction_a': 0,
                    'operation_b': 0,
                    'end_of_life_c': 0,
                    'count': 0
                }
            mmi_totals[mmi_code]['total_gwp'] += mmi_data['total_gwp']
            mmi_totals[mmi_code]['construction_a'] += mmi_data['construction_a']
            mmi_totals[mmi_code]['operation_b'] += mmi_data['operation_b']
            mmi_totals[mmi_code]['end_of_life_c'] += mmi_data['end_of_life_c']
            mmi_totals[mmi_code]['count'] += mmi_data['count']

    mmi_data = []
    for mmi_code, mmi_info in mmi_totals.items():
        mmi_data.append({
            'MMI Code': mmi_code,
            'Total GWP (kg CO2e)': f"{mmi_info['total_gwp']:,.0f}",
            'Construction (A)': f"{mmi_info['construction_a']:,.0f}",
            'Operation (B)': f"{mmi_info['operation_b']:,.0f}",
            'End-of-life (C)': f"{mmi_info['end_of_life_c']:,.0f}",
            'Rows': mmi_info['count']
        })

    if mmi_data:
        st.dataframe(pd.DataFrame(mmi_data), use_container_width=True, hide_index=True)
    else:
        st.info("No MMI data available.")

# TAB 4: DOWNLOAD REPORTS
with tab4:
    st.markdown("### 📥 Download Reports")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**📊 Excel Export**")
        st.caption("Multi-sheet workbook")
        if st.button("Generate Excel", key='generate_excel'):
            try:
                with st.spinner("Generating Excel..."):
                    scenario_summary = pd.DataFrame([
                        {
                            'Scenario': scenario,
                            'Konstruksjon (A)': data['total']['construction_a'],
                            'Drift (B)': data['total']['operation_b'],
                            'Avslutning (C)': data['total']['end_of_life_c'],
                            'Total GWP': data['total']['total_gwp'],
                            'Antall rader': data['total']['count']
                        }
                        for scenario, data in structure.items()
                    ]).sort_values('Scenario')

                    excel_bytes = generate_excel_report(mapped_df, structure, scenario_summary)

                    from datetime import datetime
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M")

                    st.download_button(
                        label="📥 Download Excel",
                        data=excel_bytes,
                        file_name=f"lca_rapport_{timestamp}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key='download_excel'
                    )
                    st.success("✓ Excel ready")
            except Exception as e:
                st.error(f"Error generating Excel: {e}")
                logger.error(f"Excel generation error: {e}", exc_info=True)

    with col2:
        st.markdown("**📄 CSV Export**")
        st.caption("Complete dataset")
        if st.button("Generate CSV", key='generate_csv'):
            try:
                with st.spinner("Generating CSV..."):
                    csv_string = generate_csv_report(mapped_df)

                    from datetime import datetime
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M")

                    st.download_button(
                        label="📥 Download CSV",
                        data=csv_string,
                        file_name=f"lca_data_{timestamp}.csv",
                        mime="text/csv",
                        key='download_csv'
                    )
                    st.success("✓ CSV ready")
            except Exception as e:
                st.error(f"Error generating CSV: {e}")
                logger.error(f"CSV generation error: {e}", exc_info=True)

    with col3:
        st.markdown("**📑 PDF Report**")
        st.caption("Visual insights")
        if st.button("Generate PDF", key='generate_pdf'):
            try:
                with st.spinner("Generating PDF..."):
                    scenario_summary = pd.DataFrame([
                        {
                            'Scenario': scenario,
                            'Konstruksjon (A)': data['total']['construction_a'],
                            'Drift (B)': data['total']['operation_b'],
                            'Avslutning (C)': data['total']['end_of_life_c'],
                            'Total GWP': data['total']['total_gwp'],
                            'Antall rader': data['total']['count']
                        }
                        for scenario, data in structure.items()
                    ]).sort_values('Scenario')

                    pdf_bytes = generate_pdf_report(mapped_df, structure, scenario_summary)

                    from datetime import datetime
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M")

                    st.download_button(
                        label="📥 Download PDF",
                        data=pdf_bytes,
                        file_name=f"lca_rapport_{timestamp}.pdf",
                        mime="application/pdf",
                        key='download_pdf'
                    )
                    st.success("✓ PDF ready")
            except Exception as e:
                st.error(f"Error generating PDF: {e}")
                logger.error(f"PDF generation error: {e}", exc_info=True)

    # Data quality info
    st.markdown("---")
    st.markdown("### 📋 Data Quality")
    stats = get_mapping_statistics(df)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Rows", len(df))
    with col2:
        st.metric("Mapped & Active", stats['active_rows'])
    with col3:
        st.metric("Mapping Completeness", f"{stats['mapping_completeness']:.0f}%")
    with col4:
        st.metric("Excluded", len(df) - stats['active_rows'])
