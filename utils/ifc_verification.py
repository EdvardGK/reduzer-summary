"""
IFC Takeoff Verification Module

Verifies that material counts are consistent across scenarios:
Scenario A (MMI 300) = Scenario C (MMI 300 + 700 + 800)

This ensures both scenarios represent the same physical building.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Valid values for validation
VALID_DISCIPLINES = {"ARK", "RIV", "RIE", "RIB", "RIBp"}
VALID_SCENARIOS = {"A", "B", "C", "D"}
VALID_MMI_CATEGORIES = {300, 700, 800, 900}
VALID_UNITS = {"m2", "m3", "pcs", "kg", "m", "stk", "l", "ton"}

# Deviation thresholds
EXCELLENT_THRESHOLD = 2.0  # < 2%
ACCEPTABLE_THRESHOLD = 5.0  # < 5%


def load_takeoff_data(file_path: str) -> pd.DataFrame:
    """
    Load IFC takeoff data from CSV or Excel file.

    Args:
        file_path: Path to CSV or Excel file

    Returns:
        DataFrame with takeoff data

    Raises:
        ValueError: If file format is not supported or required columns are missing
    """
    if file_path.endswith('.csv'):
        df = pd.read_csv(file_path)
    elif file_path.endswith(('.xlsx', '.xls')):
        df = pd.read_excel(file_path)
    else:
        raise ValueError(f"Unsupported file format: {file_path}. Use CSV or Excel.")

    # Required columns
    required_cols = ['Object Type', 'Discipline', 'Scenario', 'MMI Category', 'Quantity', 'Unit']
    missing_cols = [col for col in required_cols if col not in df.columns]

    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    # Clean and standardize data
    df['Object Type'] = df['Object Type'].astype(str).str.strip()
    df['Discipline'] = df['Discipline'].astype(str).str.strip().str.upper()
    df['Scenario'] = df['Scenario'].astype(str).str.strip().str.upper()
    df['MMI Category'] = pd.to_numeric(df['MMI Category'], errors='coerce').astype('Int64')
    df['Quantity'] = pd.to_numeric(df['Quantity'], errors='coerce')
    df['Unit'] = df['Unit'].astype(str).str.strip().str.lower()

    # Remove rows with missing critical data
    df = df.dropna(subset=['Object Type', 'Discipline', 'Scenario', 'MMI Category', 'Quantity'])

    return df


def validate_takeoff_data(df: pd.DataFrame) -> List[str]:
    """
    Validate takeoff data for common issues.

    Args:
        df: DataFrame with takeoff data

    Returns:
        List of validation error messages (empty if all valid)
    """
    errors = []

    # Check for invalid disciplines
    invalid_disciplines = df[~df['Discipline'].isin(VALID_DISCIPLINES)]['Discipline'].unique()
    if len(invalid_disciplines) > 0:
        errors.append(f"Invalid disciplines found: {list(invalid_disciplines)}. Valid: {VALID_DISCIPLINES}")

    # Check for invalid scenarios
    invalid_scenarios = df[~df['Scenario'].isin(VALID_SCENARIOS)]['Scenario'].unique()
    if len(invalid_scenarios) > 0:
        errors.append(f"Invalid scenarios found: {list(invalid_scenarios)}. Valid: {VALID_SCENARIOS}")

    # Check for invalid MMI categories
    invalid_mmi = df[~df['MMI Category'].isin(VALID_MMI_CATEGORIES)]['MMI Category'].unique()
    if len(invalid_mmi) > 0:
        errors.append(f"Invalid MMI categories found: {list(invalid_mmi)}. Valid: {VALID_MMI_CATEGORIES}")

    # Check for negative or zero quantities
    if (df['Quantity'] <= 0).any():
        errors.append("Some quantities are zero or negative. All quantities must be positive.")

    # Check unit consistency per object type
    unit_check = df.groupby('Object Type')['Unit'].nunique()
    inconsistent_units = unit_check[unit_check > 1].index.tolist()
    if inconsistent_units:
        errors.append(f"Inconsistent units for object types: {inconsistent_units}")

    # Check if Scenario A only uses MMI 300
    scenario_a = df[df['Scenario'] == 'A']
    if not scenario_a.empty:
        non_300_in_a = scenario_a[scenario_a['MMI Category'] != 300]
        if not non_300_in_a.empty:
            errors.append(f"Scenario A must only use MMI 300 (New). Found: {non_300_in_a['MMI Category'].unique()}")

    # Check if Scenario C doesn't use MMI 900
    scenario_c = df[df['Scenario'] == 'C']
    if not scenario_c.empty:
        mmi_900_in_c = scenario_c[scenario_c['MMI Category'] == 900]
        if not mmi_900_in_c.empty:
            errors.append("Scenario C should not use MMI 900 (Existing Waste). Use MMI 300/700/800 only.")

    return errors


def calculate_verification_metrics(df: pd.DataFrame, tolerance: float = ACCEPTABLE_THRESHOLD) -> Dict:
    """
    Calculate verification metrics comparing Scenario A vs C.

    Args:
        df: DataFrame with takeoff data
        tolerance: Acceptable deviation percentage (default: 5%)

    Returns:
        Dictionary with verification metrics
    """
    # Separate scenarios
    scenario_a = df[df['Scenario'] == 'A'].copy()
    scenario_c = df[df['Scenario'] == 'C'].copy()

    if scenario_a.empty or scenario_c.empty:
        return {
            'status': 'error',
            'message': 'Both Scenario A and Scenario C data are required for verification.'
        }

    # Aggregate Scenario A by Object Type + Discipline
    a_grouped = scenario_a.groupby(['Object Type', 'Discipline', 'Unit']).agg({
        'Quantity': 'sum',
        'MMI Category': 'first'  # Should all be 300
    }).reset_index()
    a_grouped.rename(columns={'Quantity': 'Qty_A'}, inplace=True)

    # Aggregate Scenario C by Object Type + Discipline (sum across all MMI categories)
    c_grouped = scenario_c.groupby(['Object Type', 'Discipline', 'Unit']).agg({
        'Quantity': 'sum'
    }).reset_index()
    c_grouped.rename(columns={'Quantity': 'Qty_C_Total'}, inplace=True)

    # Also get MMI breakdown for Scenario C
    c_mmi_breakdown = scenario_c.pivot_table(
        index=['Object Type', 'Discipline', 'Unit'],
        columns='MMI Category',
        values='Quantity',
        aggfunc='sum',
        fill_value=0
    ).reset_index()

    # Rename MMI columns
    mmi_col_mapping = {
        300: 'Qty_C_MMI300',
        700: 'Qty_C_MMI700',
        800: 'Qty_C_MMI800',
        900: 'Qty_C_MMI900'
    }
    c_mmi_breakdown.rename(columns=mmi_col_mapping, inplace=True)

    # Merge all data
    comparison = a_grouped.merge(
        c_grouped,
        on=['Object Type', 'Discipline', 'Unit'],
        how='outer',
        suffixes=('_A', '_C')
    )

    comparison = comparison.merge(
        c_mmi_breakdown,
        on=['Object Type', 'Discipline', 'Unit'],
        how='left'
    )

    # Fill NaN with 0
    qty_cols = ['Qty_A', 'Qty_C_Total', 'Qty_C_MMI300', 'Qty_C_MMI700', 'Qty_C_MMI800', 'Qty_C_MMI900']
    for col in qty_cols:
        if col not in comparison.columns:
            comparison[col] = 0
        else:
            comparison[col] = comparison[col].fillna(0)

    # Calculate deviations
    comparison['Difference'] = comparison['Qty_C_Total'] - comparison['Qty_A']
    comparison['Deviation_Abs'] = comparison['Difference'].abs()

    # Avoid division by zero
    comparison['Deviation_Pct'] = np.where(
        comparison['Qty_A'] > 0,
        (comparison['Deviation_Abs'] / comparison['Qty_A']) * 100,
        np.where(comparison['Qty_C_Total'] > 0, 999.0, 0.0)  # 999% if A is 0 but C has value
    )

    # Status classification
    def classify_status(row):
        if row['Deviation_Pct'] < EXCELLENT_THRESHOLD:
            return 'Excellent'
        elif row['Deviation_Pct'] < ACCEPTABLE_THRESHOLD:
            return 'Acceptable'
        else:
            return 'Needs Review'

    comparison['Status'] = comparison.apply(classify_status, axis=1)

    # Overall metrics
    total_qty_a = comparison['Qty_A'].sum()
    total_qty_c = comparison['Qty_C_Total'].sum()
    total_deviation_abs = comparison['Deviation_Abs'].sum()
    overall_deviation_pct = (total_deviation_abs / total_qty_a * 100) if total_qty_a > 0 else 0

    # Discipline-level summary
    discipline_summary = comparison.groupby('Discipline').agg({
        'Qty_A': 'sum',
        'Qty_C_Total': 'sum',
        'Qty_C_MMI300': 'sum',
        'Qty_C_MMI700': 'sum',
        'Qty_C_MMI800': 'sum',
        'Deviation_Abs': 'sum'
    }).reset_index()

    discipline_summary['Deviation_Pct'] = np.where(
        discipline_summary['Qty_A'] > 0,
        (discipline_summary['Deviation_Abs'] / discipline_summary['Qty_A']) * 100,
        0
    )

    # MMI distribution for Scenario C (overall)
    total_c_300 = comparison['Qty_C_MMI300'].sum()
    total_c_700 = comparison['Qty_C_MMI700'].sum()
    total_c_800 = comparison['Qty_C_MMI800'].sum()
    total_c_sum = total_c_300 + total_c_700 + total_c_800

    mmi_distribution = {
        'MMI 300 (New)': total_c_300,
        'MMI 700 (Existing Kept)': total_c_700,
        'MMI 800 (Reused)': total_c_800
    }

    mmi_distribution_pct = {
        'MMI 300 (New)': (total_c_300 / total_c_sum * 100) if total_c_sum > 0 else 0,
        'MMI 700 (Existing Kept)': (total_c_700 / total_c_sum * 100) if total_c_sum > 0 else 0,
        'MMI 800 (Reused)': (total_c_800 / total_c_sum * 100) if total_c_sum > 0 else 0
    }

    # Flagged items (deviations > tolerance)
    flagged_items = comparison[comparison['Deviation_Pct'] > tolerance].copy()
    flagged_items = flagged_items.sort_values('Deviation_Pct', ascending=False)

    return {
        'status': 'success',
        'overall': {
            'total_qty_a': total_qty_a,
            'total_qty_c': total_qty_c,
            'total_deviation_abs': total_deviation_abs,
            'overall_deviation_pct': overall_deviation_pct,
            'tolerance': tolerance
        },
        'comparison_table': comparison,
        'discipline_summary': discipline_summary,
        'mmi_distribution': mmi_distribution,
        'mmi_distribution_pct': mmi_distribution_pct,
        'flagged_items': flagged_items
    }


def create_verification_charts(metrics: Dict) -> Dict[str, go.Figure]:
    """
    Create Plotly charts for verification visualization.

    Args:
        metrics: Dictionary returned from calculate_verification_metrics()

    Returns:
        Dictionary of Plotly figures
    """
    charts = {}

    if metrics['status'] != 'success':
        return charts

    discipline_summary = metrics['discipline_summary']
    mmi_distribution = metrics['mmi_distribution']
    comparison_table = metrics['comparison_table']

    # Chart 1: Discipline Comparison (Scenario A vs C)
    fig_discipline = go.Figure()

    fig_discipline.add_trace(go.Bar(
        name='Scenario A (All New)',
        x=discipline_summary['Discipline'],
        y=discipline_summary['Qty_A'],
        marker_color='#FF6B6B',
        text=discipline_summary['Qty_A'].round(1),
        textposition='auto'
    ))

    fig_discipline.add_trace(go.Bar(
        name='Scenario C (Total)',
        x=discipline_summary['Discipline'],
        y=discipline_summary['Qty_C_Total'],
        marker_color='#4ECDC4',
        text=discipline_summary['Qty_C_Total'].round(1),
        textposition='auto'
    ))

    fig_discipline.update_layout(
        title='Object Count Verification by Discipline',
        xaxis_title='Discipline',
        yaxis_title='Total Quantity (normalized)',
        barmode='group',
        template='plotly_white',
        height=400
    )

    charts['discipline_comparison'] = fig_discipline

    # Chart 2: MMI Distribution for Scenario C
    fig_mmi = go.Figure(data=[go.Pie(
        labels=list(mmi_distribution.keys()),
        values=list(mmi_distribution.values()),
        marker=dict(colors=['#FFD93D', '#6BCF7F', '#4D96FF']),
        textinfo='label+percent',
        hovertemplate='<b>%{label}</b><br>Quantity: %{value:.1f}<br>Percentage: %{percent}<extra></extra>'
    )])

    fig_mmi.update_layout(
        title='Scenario C: MMI Category Distribution',
        template='plotly_white',
        height=400
    )

    charts['mmi_distribution'] = fig_mmi

    # Chart 3: Deviation by Object Type (Top 10 worst)
    top_deviations = comparison_table.nlargest(10, 'Deviation_Pct').copy()

    if not top_deviations.empty:
        top_deviations['Label'] = top_deviations['Object Type'] + ' (' + top_deviations['Discipline'] + ')'

        colors = top_deviations['Status'].map({
            'Excellent': '#6BCF7F',
            'Acceptable': '#FFD93D',
            'Needs Review': '#FF6B6B'
        })

        fig_deviation = go.Figure(data=[go.Bar(
            x=top_deviations['Deviation_Pct'],
            y=top_deviations['Label'],
            orientation='h',
            marker_color=colors,
            text=top_deviations['Deviation_Pct'].round(1).astype(str) + '%',
            textposition='auto'
        )])

        fig_deviation.update_layout(
            title='Top 10 Deviations by Object Type',
            xaxis_title='Deviation (%)',
            yaxis_title='',
            template='plotly_white',
            height=400
        )

        # Add threshold lines
        fig_deviation.add_vline(x=EXCELLENT_THRESHOLD, line_dash="dash", line_color="green",
                               annotation_text="Excellent (<2%)")
        fig_deviation.add_vline(x=ACCEPTABLE_THRESHOLD, line_dash="dash", line_color="orange",
                               annotation_text="Acceptable (<5%)")

        charts['deviation_chart'] = fig_deviation

    # Chart 4: Stacked Bar for Scenario C MMI Breakdown by Discipline
    fig_stacked = go.Figure()

    fig_stacked.add_trace(go.Bar(
        name='MMI 300 (New)',
        x=discipline_summary['Discipline'],
        y=discipline_summary['Qty_C_MMI300'],
        marker_color='#FFD93D',
        text=discipline_summary['Qty_C_MMI300'].round(1),
        textposition='auto'
    ))

    fig_stacked.add_trace(go.Bar(
        name='MMI 700 (Existing Kept)',
        x=discipline_summary['Discipline'],
        y=discipline_summary['Qty_C_MMI700'],
        marker_color='#6BCF7F',
        text=discipline_summary['Qty_C_MMI700'].round(1),
        textposition='auto'
    ))

    fig_stacked.add_trace(go.Bar(
        name='MMI 800 (Reused)',
        x=discipline_summary['Discipline'],
        y=discipline_summary['Qty_C_MMI800'],
        marker_color='#4D96FF',
        text=discipline_summary['Qty_C_MMI800'].round(1),
        textposition='auto'
    ))

    fig_stacked.update_layout(
        title='Scenario C: MMI Category Breakdown by Discipline',
        xaxis_title='Discipline',
        yaxis_title='Quantity',
        barmode='stack',
        template='plotly_white',
        height=400
    )

    charts['mmi_breakdown_stacked'] = fig_stacked

    return charts


def export_verification_report(metrics: Dict, output_path: str) -> None:
    """
    Export verification report to Excel.

    Args:
        metrics: Dictionary returned from calculate_verification_metrics()
        output_path: Path to save Excel file
    """
    if metrics['status'] != 'success':
        raise ValueError("Cannot export report: metrics calculation failed")

    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        # Sheet 1: Summary
        summary_data = {
            'Metric': [
                'Total Quantity - Scenario A',
                'Total Quantity - Scenario C',
                'Total Absolute Deviation',
                'Overall Deviation (%)',
                'Tolerance Threshold (%)',
                'Status'
            ],
            'Value': [
                metrics['overall']['total_qty_a'],
                metrics['overall']['total_qty_c'],
                metrics['overall']['total_deviation_abs'],
                metrics['overall']['overall_deviation_pct'],
                metrics['overall']['tolerance'],
                'PASS' if metrics['overall']['overall_deviation_pct'] <= metrics['overall']['tolerance'] else 'FAIL'
            ]
        }
        pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)

        # Sheet 2: Detailed Comparison
        metrics['comparison_table'].to_excel(writer, sheet_name='Object Comparison', index=False)

        # Sheet 3: Discipline Summary
        metrics['discipline_summary'].to_excel(writer, sheet_name='Discipline Summary', index=False)

        # Sheet 4: MMI Distribution
        mmi_data = pd.DataFrame({
            'MMI Category': list(metrics['mmi_distribution'].keys()),
            'Quantity': list(metrics['mmi_distribution'].values()),
            'Percentage': list(metrics['mmi_distribution_pct'].values())
        })
        mmi_data.to_excel(writer, sheet_name='MMI Distribution', index=False)

        # Sheet 5: Flagged Items
        if not metrics['flagged_items'].empty:
            metrics['flagged_items'].to_excel(writer, sheet_name='Flagged Items', index=False)
