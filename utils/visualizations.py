# -*- coding: utf-8 -*-
"""
Plotly visualizations for LCA scenario analysis
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import Dict, List, Any, Optional


# Color scheme for LCA phases
PHASE_COLORS = {
    'construction_a': '#2E7D32',  # Green
    'operation_b': '#1565C0',     # Blue
    'end_of_life_c': '#C62828'    # Red
}

PHASE_LABELS = {
    'construction_a': 'Konstruksjon (A)',
    'operation_b': 'Drift (B)',
    'end_of_life_c': 'Avslutning (C)'
}


def create_stacked_bar_chart(df: pd.DataFrame, group_by: str, title: str) -> go.Figure:
    """
    Create stacked bar chart showing LCA phases.

    Args:
        df: DataFrame with construction_a, operation_b, end_of_life_c columns
        group_by: Column name to group by
        title: Chart title

    Returns:
        Plotly figure
    """
    fig = go.Figure()

    phases = ['construction_a', 'operation_b', 'end_of_life_c']

    for phase in phases:
        fig.add_trace(go.Bar(
            name=PHASE_LABELS[phase],
            x=df[group_by],
            y=df[phase],
            marker_color=PHASE_COLORS[phase]
        ))

    fig.update_layout(
        title=title,
        barmode='stack',
        xaxis_title=group_by.capitalize(),
        yaxis_title='GWP (kg CO2e)',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        height=500
    )

    return fig


def create_treemap(structure: Dict[str, Any], title: str = "Hierarkisk visning") -> go.Figure:
    """
    Create treemap showing Scenario -> Discipline -> MMI hierarchy.

    Args:
        structure: Hierarchical structure from create_hierarchical_structure
        title: Chart title

    Returns:
        Plotly figure
    """
    labels = []
    parents = []
    values = []
    colors = []

    # Root
    labels.append("Alle scenarioer")
    parents.append("")
    total_sum = sum(s['total']['total_gwp'] for s in structure.values())
    values.append(total_sum)
    colors.append(0)

    # Scenarios
    for scenario, scenario_data in structure.items():
        scenario_label = f"Scenario {scenario}"
        labels.append(scenario_label)
        parents.append("Alle scenarioer")
        values.append(scenario_data['total']['total_gwp'])
        colors.append(1)

        # Disciplines
        for discipline, discipline_data in scenario_data['disciplines'].items():
            discipline_label = f"{scenario} - {discipline}"
            labels.append(discipline_label)
            parents.append(scenario_label)
            values.append(discipline_data['total']['total_gwp'])
            colors.append(2)

            # MMI categories
            for mmi_code, mmi_data in discipline_data['mmi_categories'].items():
                mmi_label = f"{discipline} - {mmi_data['label']} ({mmi_code})"
                labels.append(mmi_label)
                parents.append(discipline_label)
                values.append(mmi_data['total_gwp'])
                colors.append(3)

    fig = go.Figure(go.Treemap(
        labels=labels,
        parents=parents,
        values=values,
        marker=dict(
            colorscale='Viridis',
            cmid=1.5,
            line=dict(width=2)
        ),
        textposition="middle center",
        hovertemplate='<b>%{label}</b><br>GWP: %{value:,.0f} kg CO2e<extra></extra>'
    ))

    fig.update_layout(
        title=title,
        height=600
    )

    return fig


def create_line_chart(summary_df: pd.DataFrame, title: str = "Sammenligning av scenarioer") -> go.Figure:
    """
    Create line chart comparing scenarios across LCA phases.

    Args:
        summary_df: DataFrame with scenarios and their phase values
        title: Chart title

    Returns:
        Plotly figure
    """
    fig = go.Figure()

    phases = [
        ('Konstruksjon (A)', PHASE_COLORS['construction_a']),
        ('Drift (B)', PHASE_COLORS['operation_b']),
        ('Avslutning (C)', PHASE_COLORS['end_of_life_c']),
        ('Total GWP', '#424242')
    ]

    for phase_name, color in phases:
        if phase_name in summary_df.columns:
            fig.add_trace(go.Scatter(
                x=summary_df['Scenario'],
                y=summary_df[phase_name],
                mode='lines+markers',
                name=phase_name,
                line=dict(color=color, width=3),
                marker=dict(size=10)
            ))

    fig.update_layout(
        title=title,
        xaxis_title='Scenario',
        yaxis_title='GWP (kg CO2e)',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        height=500,
        hovermode='x unified'
    )

    return fig


def create_comparison_chart(comparison: Dict[str, Any], chart_type: str = 'difference') -> go.Figure:
    """
    Create comparison chart showing ratio or difference between scenarios.

    Args:
        comparison: Comparison data from compare_scenarios
        chart_type: 'difference' or 'ratio'

    Returns:
        Plotly figure
    """
    base = comparison['base_scenario']
    compare = comparison['compare_scenario']

    categories = ['Konstruksjon (A)', 'Drift (B)', 'Avslutning (C)', 'Total GWP']
    keys = ['construction_a', 'operation_b', 'end_of_life_c', 'total_gwp']

    if chart_type == 'difference':
        values = [comparison['difference'][key] for key in keys]
        title = f"Differanse: Scenario {compare} - Scenario {base}"
        yaxis_title = 'Differanse (kg CO2e)'
        colors = ['green' if v < 0 else 'red' for v in values]
    else:  # ratio
        values = [comparison['ratio'][key] if comparison['ratio'][key] is not None else 0 for key in keys]
        title = f"Ratio: Scenario {compare} / Scenario {base}"
        yaxis_title = 'Ratio (%)'
        colors = ['green' if v < 100 else 'red' for v in values]

    fig = go.Figure(go.Bar(
        x=categories,
        y=values,
        marker_color=colors,
        text=[f"{v:,.0f}" if chart_type == 'difference' else f"{v:.1f}%" for v in values],
        textposition='auto'
    ))

    fig.update_layout(
        title=title,
        xaxis_title='LCA-fase',
        yaxis_title=yaxis_title,
        height=500,
        showlegend=False
    )

    if chart_type == 'ratio':
        # Add reference line at 100%
        fig.add_hline(y=100, line_dash="dash", line_color="gray",
                      annotation_text="Baseline (100%)")

    return fig


def create_discipline_comparison_chart(structure: Dict[str, Any], scenario: str) -> go.Figure:
    """
    Create stacked bar chart comparing disciplines within a scenario.

    Args:
        structure: Hierarchical structure
        scenario: Scenario to visualize

    Returns:
        Plotly figure
    """
    if scenario not in structure:
        return go.Figure()

    disciplines = []
    construction = []
    operation = []
    end_of_life = []

    for discipline, data in structure[scenario]['disciplines'].items():
        disciplines.append(discipline)
        construction.append(data['total']['construction_a'])
        operation.append(data['total']['operation_b'])
        end_of_life.append(data['total']['end_of_life_c'])

    fig = go.Figure()

    fig.add_trace(go.Bar(
        name=PHASE_LABELS['construction_a'],
        x=disciplines,
        y=construction,
        marker_color=PHASE_COLORS['construction_a']
    ))

    fig.add_trace(go.Bar(
        name=PHASE_LABELS['operation_b'],
        x=disciplines,
        y=operation,
        marker_color=PHASE_COLORS['operation_b']
    ))

    fig.add_trace(go.Bar(
        name=PHASE_LABELS['end_of_life_c'],
        x=disciplines,
        y=end_of_life,
        marker_color=PHASE_COLORS['end_of_life_c']
    ))

    fig.update_layout(
        title=f"Disipliner i Scenario {scenario}",
        barmode='stack',
        xaxis_title='Disiplin',
        yaxis_title='GWP (kg CO2e)',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        height=500
    )

    return fig


def create_mmi_breakdown_chart(structure: Dict[str, Any], scenario: str, discipline: str) -> go.Figure:
    """
    Create bar chart showing MMI breakdown for a specific discipline in a scenario.

    Args:
        structure: Hierarchical structure
        scenario: Scenario name
        discipline: Discipline name

    Returns:
        Plotly figure
    """
    if scenario not in structure or discipline not in structure[scenario]['disciplines']:
        return go.Figure()

    mmi_data = structure[scenario]['disciplines'][discipline]['mmi_categories']

    mmi_labels = []
    construction = []
    operation = []
    end_of_life = []

    for mmi_code, data in mmi_data.items():
        mmi_labels.append(f"{data['label']} ({mmi_code})")
        construction.append(data['construction_a'])
        operation.append(data['operation_b'])
        end_of_life.append(data['end_of_life_c'])

    fig = go.Figure()

    fig.add_trace(go.Bar(
        name=PHASE_LABELS['construction_a'],
        x=mmi_labels,
        y=construction,
        marker_color=PHASE_COLORS['construction_a']
    ))

    fig.add_trace(go.Bar(
        name=PHASE_LABELS['operation_b'],
        x=mmi_labels,
        y=operation,
        marker_color=PHASE_COLORS['operation_b']
    ))

    fig.add_trace(go.Bar(
        name=PHASE_LABELS['end_of_life_c'],
        x=mmi_labels,
        y=end_of_life,
        marker_color=PHASE_COLORS['end_of_life_c']
    ))

    fig.update_layout(
        title=f"MMI-kategorier: {discipline} - Scenario {scenario}",
        barmode='stack',
        xaxis_title='MMI-kategori',
        yaxis_title='GWP (kg CO2e)',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        height=500
    )

    return fig


# MMI DISTRIBUTION COLORS
MMI_COLORS = {
    '300': '#4CAF50',  # Green - New
    '700': '#2196F3',  # Blue - Existing
    '800': '#FF9800',  # Orange - Reuse
    '900': '#F44336'   # Red - Demolish
}

MMI_LABELS_NO = {
    '300': 'NY',
    '700': 'EKS',
    '800': 'GJEN',
    '900': 'RIVES'
}


def create_mmi_distribution_pie(structure: Dict[str, Any], scenario: str) -> go.Figure:
    """
    Create pie chart showing MMI distribution (by GWP) within a scenario.

    Args:
        structure: Hierarchical structure
        scenario: Scenario to visualize

    Returns:
        Plotly figure
    """
    if scenario not in structure:
        return go.Figure()

    # Aggregate MMI totals across all disciplines
    mmi_totals = {}
    for discipline, disc_data in structure[scenario]['disciplines'].items():
        for mmi_code, mmi_data in disc_data['mmi_categories'].items():
            if mmi_code not in mmi_totals:
                mmi_totals[mmi_code] = 0
            mmi_totals[mmi_code] += mmi_data['total_gwp']

    if not mmi_totals:
        return go.Figure()

    # Prepare data
    labels = [f"{MMI_LABELS_NO.get(code, code)} ({code})" for code in mmi_totals.keys()]
    values = list(mmi_totals.values())
    colors_list = [MMI_COLORS.get(code, '#999999') for code in mmi_totals.keys()]

    # Calculate percentages
    total = sum(values)
    percentages = [(v/total)*100 for v in values]

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        marker=dict(colors=colors_list),
        textinfo='label+percent',
        textposition='auto',
        hovertemplate='<b>%{label}</b><br>GWP: %{value:,.0f} kg CO2e<br>Andel: %{percent}<extra></extra>'
    )])

    fig.update_layout(
        title=f"MMI-fordeling Scenario {scenario}",
        height=400,
        showlegend=True
    )

    return fig


def create_mmi_distribution_by_discipline(structure: Dict[str, Any], scenario: str) -> go.Figure:
    """
    Create stacked bar chart showing MMI breakdown per discipline.

    Args:
        structure: Hierarchical structure
        scenario: Scenario to visualize

    Returns:
        Plotly figure
    """
    if scenario not in structure:
        return go.Figure()

    # Collect data per discipline and MMI
    disciplines = []
    mmi_data_by_code = {}

    for discipline, disc_data in structure[scenario]['disciplines'].items():
        disciplines.append(discipline)

        # Get all MMI codes
        for mmi_code in disc_data['mmi_categories'].keys():
            if mmi_code not in mmi_data_by_code:
                mmi_data_by_code[mmi_code] = []

    # Fill in values (0 if discipline doesn't have that MMI)
    for discipline in disciplines:
        disc_data = structure[scenario]['disciplines'][discipline]
        for mmi_code in mmi_data_by_code.keys():
            if mmi_code in disc_data['mmi_categories']:
                mmi_data_by_code[mmi_code].append(
                    disc_data['mmi_categories'][mmi_code]['total_gwp']
                )
            else:
                mmi_data_by_code[mmi_code].append(0)

    fig = go.Figure()

    # Add trace for each MMI code
    for mmi_code, values in mmi_data_by_code.items():
        fig.add_trace(go.Bar(
            name=f"{MMI_LABELS_NO.get(mmi_code, mmi_code)} ({mmi_code})",
            x=disciplines,
            y=values,
            marker_color=MMI_COLORS.get(mmi_code, '#999999')
        ))

    fig.update_layout(
        title=f"MMI-fordeling per disiplin - Scenario {scenario}",
        barmode='stack',
        xaxis_title='Disiplin',
        yaxis_title='GWP (kg CO2e)',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        height=400
    )

    return fig


def get_mmi_summary_stats(structure: Dict[str, Any], scenario: str) -> pd.DataFrame:
    """
    Get MMI distribution statistics for a scenario.

    Args:
        structure: Hierarchical structure
        scenario: Scenario to analyze

    Returns:
        DataFrame with MMI statistics
    """
    if scenario not in structure:
        return pd.DataFrame()

    # Aggregate MMI totals
    mmi_totals = {}
    for discipline, disc_data in structure[scenario]['disciplines'].items():
        for mmi_code, mmi_data in disc_data['mmi_categories'].items():
            if mmi_code not in mmi_totals:
                mmi_totals[mmi_code] = {
                    'gwp': 0,
                    'count': 0,
                    'label': MMI_LABELS_NO.get(mmi_code, mmi_code)
                }
            mmi_totals[mmi_code]['gwp'] += mmi_data['total_gwp']
            mmi_totals[mmi_code]['count'] += mmi_data['count']

    # Calculate total
    total_gwp = sum(data['gwp'] for data in mmi_totals.values())

    # Build dataframe
    stats = []
    for mmi_code, data in mmi_totals.items():
        percentage = (data['gwp'] / total_gwp * 100) if total_gwp > 0 else 0
        stats.append({
            'MMI': mmi_code,
            'Status': data['label'],
            'GWP (kg CO2e)': data['gwp'],
            'Andel (%)': percentage,
            'Antall rader': data['count']
        })

    return pd.DataFrame(stats).sort_values('GWP (kg CO2e)', ascending=False)
