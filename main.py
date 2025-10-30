# -*- coding: utf-8 -*-
"""
LCA Scenario Mapping - Simplified for decision-making
"""

import streamlit as st
import pandas as pd
from datetime import datetime

from utils.data_parser import (
    load_excel_file,
    aggregate_by_mapping,
    get_scenario_summary,
    compare_scenarios,
    get_mapping_statistics
)
from utils.predefined_structure import SCENARIOS, DISCIPLINES, MMI_CODES
from utils.visualizations import (
    create_stacked_bar_chart,
    create_comparison_chart,
    create_mmi_distribution_pie,
    create_mmi_distribution_by_discipline,
    get_mmi_summary_stats
)


st.set_page_config(page_title="LCA Scenario Mapping", page_icon=":bar_chart:", layout="wide")


def main():
    st.title(":bar_chart: LCA Scenario Mapping")

    # Initialize session state
    if 'df' not in st.session_state:
        st.session_state['df'] = None
    if 'auto_refresh' not in st.session_state:
        st.session_state['auto_refresh'] = True

    # File upload
    uploaded_file = st.file_uploader(
        "Last opp Excel-fil fra Reduzer",
        type=['xlsx', 'xls'],
        help="Excel-fil med LCA-data"
    )

    if uploaded_file is not None and st.session_state['df'] is None:
        try:
            with st.spinner("Laster..."):
                df = load_excel_file(uploaded_file)
                st.session_state['df'] = df
                st.rerun()
        except Exception as e:
            st.error(f"Feil: {str(e)}")
            return

    df = st.session_state.get('df')

    if df is None:
        show_welcome()
        return

    # MAIN VIEW - Split layout
    show_main_view(df)


def show_welcome():
    """Minimal welcome screen"""
    st.info("Last opp Excel-fil for aa starte")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**Scenarioer**")
        st.write(", ".join(SCENARIOS))
    with col2:
        st.markdown("**Disipliner**")
        st.write(", ".join(DISCIPLINES))
    with col3:
        st.markdown("**MMI**")
        for code, label in MMI_CODES.items():
            st.caption(f"{code}: {label}")


def show_main_view(df):
    """Single view with mapping + live results"""

    # KEY METRIC AT TOP
    try:
        structure = aggregate_by_mapping(df)

        if 'C' in structure and 'A' in structure:
            comparison = compare_scenarios(structure, 'A', 'C')
            if comparison and comparison['ratio']['total_gwp']:
                ratio = comparison['ratio']['total_gwp']
                diff = comparison['difference']['total_gwp']

                # Big number at top
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    indicator = "RED" if ratio > 100 else "GREEN"
                    delta_text = f"{indicator} {diff:,.0f} kg CO2e"
                    st.metric(
                        "Scenario C / Scenario A",
                        f"{ratio:.1f}%",
                        delta_text
                    )
                with col2:
                    stats = get_mapping_statistics(df)
                    st.metric("Kartlagt", f"{stats['mapping_completeness']:.0f}%")
                with col3:
                    st.metric("Aktive rader", stats['active_rows'])
        else:
            st.info("Kartlegg Scenario A og C for aa se sammenligning")

    except Exception as e:
        st.warning("Kartlegg data for aa se resultater")

    st.markdown("---")

    # TABS LAYOUT
    tab_data, tab_analysis = st.tabs(["📊 Data", "📈 Analysis"])

    with tab_data:
        show_mapping_panel(df)

    with tab_analysis:
        show_results_panel(df)


def show_mapping_panel(df):
    """Compact mapping interface"""
    st.subheader("Kartlegging")

    # BULK ACTIONS
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("Godta alle forslag", use_container_width=True, type="primary"):
            df['mapped_scenario'] = df['suggested_scenario']
            df['mapped_discipline'] = df['suggested_discipline']
            df['mapped_mmi_code'] = df['suggested_mmi_code']
            st.session_state['df'] = df
            st.success("Forslag godtatt!")
            st.rerun()

    with col2:
        if st.button("Ekskluder oppsummeringer", use_container_width=True):
            df.loc[df['is_summary'], 'excluded'] = True
            st.session_state['df'] = df
            st.success("Oppsummeringer ekskludert!")
            st.rerun()

    with col3:
        max_rows = st.number_input("Vis rader", 10, 500, 100, 10, label_visibility="collapsed")

    # Show all rows, prioritize unmapped
    unmapped = df[
        (~df['excluded']) &
        (df['mapped_scenario'].isna() |
         df['mapped_discipline'].isna() |
         df['mapped_mmi_code'].isna())
    ]

    excluded_count = df['excluded'].sum()
    unmapped_count = len(unmapped)

    st.caption(f"{len(df)} rader totalt | {unmapped_count} ukartlagt | {excluded_count} ekskludert")

    # Show unmapped first, then mapped, then excluded
    if len(unmapped) > 0:
        unmapped_display = unmapped.head(max_rows)
        remaining = max_rows - len(unmapped_display)
        if remaining > 0:
            others = df[~df.index.isin(unmapped_display.index)].head(remaining)
            display_df = pd.concat([unmapped_display, others])
        else:
            display_df = unmapped_display
    else:
        display_df = df.head(max_rows)

    # COMPACT TABLE with status indicator
    edit_cols = [
        'row_id',
        'category',
        'total_gwp',
        'mapped_scenario',
        'mapped_discipline',
        'mapped_mmi_code',
        'excluded'
    ]

    edit_df = display_df[edit_cols].copy()

    # Add visual status indicator
    def get_status(row):
        if row['excluded']:
            return "EKSKLUDERT"
        elif pd.isna(row['mapped_scenario']) or pd.isna(row['mapped_discipline']) or pd.isna(row['mapped_mmi_code']):
            return "Ukartlagt"
        else:
            return "OK"

    edit_df['Status'] = edit_df.apply(get_status, axis=1)

    # Reorder columns to put Status first
    edit_df = edit_df[['row_id', 'Status', 'category', 'total_gwp', 'mapped_scenario', 'mapped_discipline', 'mapped_mmi_code', 'excluded']]

    edit_df = edit_df.rename(columns={
        'row_id': 'ID',
        'category': 'Kategori',
        'total_gwp': 'GWP',
        'mapped_scenario': 'Scenario',
        'mapped_discipline': 'Fag',
        'mapped_mmi_code': 'MMI',
        'excluded': 'Ekskluder'
    })

    # EDITABLE TABLE
    edited_df = st.data_editor(
        edit_df,
        use_container_width=True,
        hide_index=True,
        height=600,
        column_config={
            "ID": st.column_config.NumberColumn("ID", width="small", disabled=True),
            "Status": st.column_config.TextColumn("Status", width="small", disabled=True),
            "Kategori": st.column_config.TextColumn("Kategori", width="large", disabled=True),
            "GWP": st.column_config.NumberColumn("GWP", format="%.0f", width="small", disabled=True),
            "Scenario": st.column_config.SelectboxColumn("Scenario", options=[''] + SCENARIOS, width="small"),
            "Fag": st.column_config.SelectboxColumn("Fag", options=[''] + DISCIPLINES, width="small"),
            "MMI": st.column_config.SelectboxColumn("MMI", options=[''] + list(MMI_CODES.keys()), width="small"),
            "Ekskluder": st.column_config.CheckboxColumn("Ekskluder", width="small")
        },
        key="editor"
    )

    # AUTO-SAVE on edit
    if not edited_df.equals(edit_df):
        # Map back (ignore Status column as it's derived)
        edited_df = edited_df.rename(columns={
            'ID': 'row_id',
            'Scenario': 'mapped_scenario',
            'Fag': 'mapped_discipline',
            'MMI': 'mapped_mmi_code',
            'Ekskluder': 'excluded'
        })

        for _, row in edited_df.iterrows():
            idx = df[df['row_id'] == row['row_id']].index
            if len(idx) > 0:
                idx = idx[0]
                df.at[idx, 'mapped_scenario'] = row['mapped_scenario']
                df.at[idx, 'mapped_discipline'] = row['mapped_discipline']
                df.at[idx, 'mapped_mmi_code'] = row['mapped_mmi_code']
                df.at[idx, 'excluded'] = row['excluded']

        st.session_state['df'] = df
        if st.session_state.get('auto_refresh', True):
            st.rerun()


def show_results_panel(df):
    """Live results as you map"""
    st.subheader("Resultater")

    try:
        structure = aggregate_by_mapping(df)

        if not structure:
            st.info("Kartlegg data for aa se resultater")
            return

        scenario_summary = get_scenario_summary(structure)

        # SCENARIO COMPARISON CHART
        if len(scenario_summary) > 0:
            # Add English column names for chart
            chart_df = scenario_summary.copy()
            chart_df['construction_a'] = chart_df['Konstruksjon (A)']
            chart_df['operation_b'] = chart_df['Drift (B)']
            chart_df['end_of_life_c'] = chart_df['Avslutning (C)']

            fig = create_stacked_bar_chart(
                chart_df,
                'Scenario',
                "GWP per Scenario"
            )
            st.plotly_chart(fig, use_container_width=True)

        # SCENARIO C vs A COMPARISON
        if 'C' in structure and 'A' in structure:
            st.markdown("### Scenario C vs A")

            comparison = compare_scenarios(structure, 'A', 'C')

            if comparison:
                col1, col2 = st.columns(2)

                with col1:
                    st.caption("Differanse")
                    fig_diff = create_comparison_chart(comparison, 'difference')
                    st.plotly_chart(fig_diff, use_container_width=True)

                with col2:
                    st.caption("Ratio")
                    fig_ratio = create_comparison_chart(comparison, 'ratio')
                    st.plotly_chart(fig_ratio, use_container_width=True)

        # MMI DISTRIBUTION ANALYSIS
        st.markdown("---")
        st.markdown("### MMI-sammensetning")

        # Select scenario to analyze
        mmi_scenario = st.selectbox(
            "Analyser MMI-fordeling for scenario:",
            options=sorted(structure.keys()),
            key="mmi_scenario_select"
        )

        if mmi_scenario:
            col1, col2 = st.columns(2)

            with col1:
                # Pie chart
                fig_pie = create_mmi_distribution_pie(structure, mmi_scenario)
                st.plotly_chart(fig_pie, use_container_width=True)

                # Stats table
                mmi_stats = get_mmi_summary_stats(structure, mmi_scenario)
                if not mmi_stats.empty:
                    st.dataframe(
                        mmi_stats,
                        use_container_width=True,
                        hide_index=True,
                        height=200
                    )

            with col2:
                # Stacked bar by discipline
                fig_disc_mmi = create_mmi_distribution_by_discipline(structure, mmi_scenario)
                st.plotly_chart(fig_disc_mmi, use_container_width=True)

        # SUMMARY TABLE
        st.markdown("### Oppsummering")
        st.dataframe(
            scenario_summary,
            use_container_width=True,
            hide_index=True,
            height=200
        )

        # EXPORT
        st.markdown("### Rapporter")
        col1, col2, col3 = st.columns(3)

        with col1:
            # Excel report
            try:
                from utils.report_generator import generate_excel_report
                excel_data = generate_excel_report(df, structure, scenario_summary)
                st.download_button(
                    "Excel Rapport",
                    data=excel_data,
                    file_name=f"lca_rapport_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                    type="primary"
                )
            except Exception as e:
                st.error(f"Excel feil: {str(e)}")

        with col2:
            # PDF report
            try:
                from utils.report_generator import generate_pdf_report
                pdf_data = generate_pdf_report(df, structure, scenario_summary)
                st.download_button(
                    "PDF Rapport",
                    data=pdf_data,
                    file_name=f"lca_rapport_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"PDF feil: {str(e)}")

        with col3:
            # CSV export (quick data)
            active_df = df[~df['excluded'] & df['mapped_scenario'].notna()]
            csv_active = active_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                "CSV Data",
                data=csv_active,
                file_name="lca_data.csv",
                mime="text/csv",
                use_container_width=True
            )

    except Exception as e:
        st.error(f"Feil i analyse: {str(e)}")


if __name__ == "__main__":
    main()
