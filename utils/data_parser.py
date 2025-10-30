# -*- coding: utf-8 -*-
"""
Excel file parsing and mapping-based data aggregation
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from pathlib import Path
import io

from .detector import detect_all, is_summary_row
from .predefined_structure import validate_combination


def load_excel_file(file_path_or_buffer) -> pd.DataFrame:
    """
    Load Excel file from Reduzer export and normalize columns.

    Args:
        file_path_or_buffer: Path to Excel file or file buffer (for Streamlit upload)

    Returns:
        DataFrame with normalized columns and auto-detection suggestions
    """
    # Read Excel file
    if isinstance(file_path_or_buffer, (str, Path)):
        df = pd.read_excel(file_path_or_buffer)
    else:
        # Handle Streamlit uploaded file
        df = pd.read_excel(file_path_or_buffer)

    # Expected columns: category, Construction (A), Operation (B), End-of-life (C)
    # Rename for easier handling
    column_mapping = {}
    for col in df.columns:
        col_str = str(col).strip()
        if 'construction' in col_str.lower() or col_str.endswith('(A)'):
            column_mapping[col] = 'construction_a'
        elif 'operation' in col_str.lower() or col_str.endswith('(B)'):
            column_mapping[col] = 'operation_b'
        elif 'end' in col_str.lower() or col_str.endswith('(C)'):
            column_mapping[col] = 'end_of_life_c'
        elif 'category' in col_str.lower() or col == df.columns[0]:
            column_mapping[col] = 'category'

    df = df.rename(columns=column_mapping)

    # Ensure we have the required columns
    required_cols = ['category', 'construction_a', 'operation_b', 'end_of_life_c']
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Mangler obligatoriske kolonner: {missing}")

    # Remove rows where category is NaN or empty
    df = df[df['category'].notna()].copy()
    df = df[df['category'].astype(str).str.strip() != ''].copy()

    # Auto-detect summary rows
    df['is_summary'] = df['category'].apply(is_summary_row)

    # Apply automatic detection as SUGGESTIONS
    detected = df['category'].apply(detect_all)
    df['suggested_scenario'] = detected.apply(lambda x: x['scenario'])
    df['suggested_discipline'] = detected.apply(lambda x: x['discipline'])
    df['suggested_mmi_code'] = detected.apply(lambda x: x['mmi_code'])
    df['suggested_mmi_label'] = detected.apply(lambda x: x['mmi_label'])

    # Initialize mapping columns (user can override these)
    df['mapped_scenario'] = df['suggested_scenario']
    df['mapped_discipline'] = df['suggested_discipline']
    df['mapped_mmi_code'] = df['suggested_mmi_code']

    # Initialize excluded flag
    df['excluded'] = df['is_summary']  # Auto-exclude summary rows

    # Convert numeric columns to float
    for col in ['construction_a', 'operation_b', 'end_of_life_c']:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # Calculate total GWP
    df['total_gwp'] = df['construction_a'] + df['operation_b'] + df['end_of_life_c']

    # Add row ID for tracking
    df['row_id'] = range(len(df))

    # Reset index
    df = df.reset_index(drop=True)

    return df


def apply_user_mapping(df: pd.DataFrame, mapping_updates: Dict[int, Dict[str, Any]]) -> pd.DataFrame:
    """
    Apply user mapping changes to the dataframe.

    Args:
        df: DataFrame with data
        mapping_updates: Dictionary of {row_id: {'scenario': 'A', 'discipline': 'RIV', ...}}

    Returns:
        Updated DataFrame
    """
    df = df.copy()

    for row_id, updates in mapping_updates.items():
        if row_id in df['row_id'].values:
            idx = df[df['row_id'] == row_id].index[0]

            if 'scenario' in updates:
                df.at[idx, 'mapped_scenario'] = updates['scenario']
            if 'discipline' in updates:
                df.at[idx, 'mapped_discipline'] = updates['discipline']
            if 'mmi_code' in updates:
                df.at[idx, 'mapped_mmi_code'] = updates['mmi_code']
            if 'excluded' in updates:
                df.at[idx, 'excluded'] = updates['excluded']

    return df


def get_mapped_dataframe(df: pd.DataFrame, include_excluded: bool = False) -> pd.DataFrame:
    """
    Get dataframe with only mapped (not excluded) rows.

    Args:
        df: Full dataframe
        include_excluded: If True, include excluded rows

    Returns:
        Filtered dataframe
    """
    if include_excluded:
        return df.copy()
    else:
        return df[~df['excluded']].copy()


def aggregate_by_mapping(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Aggregate data based on user mapping (Scenario -> Discipline -> MMI).

    Args:
        df: DataFrame with mapping columns

    Returns:
        Nested dictionary with aggregated data
    """
    # Filter out excluded rows
    df_active = df[~df['excluded']].copy()

    # Filter out rows without complete mapping
    df_mapped = df_active[
        df_active['mapped_scenario'].notna() &
        df_active['mapped_discipline'].notna() &
        df_active['mapped_mmi_code'].notna()
    ].copy()

    structure = {}

    # Group by scenario
    for scenario in df_mapped['mapped_scenario'].dropna().unique():
        scenario_data = df_mapped[df_mapped['mapped_scenario'] == scenario]
        structure[scenario] = {
            'disciplines': {},
            'total': {
                'construction_a': float(scenario_data['construction_a'].sum()),
                'operation_b': float(scenario_data['operation_b'].sum()),
                'end_of_life_c': float(scenario_data['end_of_life_c'].sum()),
                'total_gwp': float(scenario_data['total_gwp'].sum()),
                'count': len(scenario_data)
            }
        }

        # Group by discipline within scenario
        for discipline in scenario_data['mapped_discipline'].dropna().unique():
            discipline_data = scenario_data[scenario_data['mapped_discipline'] == discipline]
            structure[scenario]['disciplines'][discipline] = {
                'mmi_categories': {},
                'total': {
                    'construction_a': float(discipline_data['construction_a'].sum()),
                    'operation_b': float(discipline_data['operation_b'].sum()),
                    'end_of_life_c': float(discipline_data['end_of_life_c'].sum()),
                    'total_gwp': float(discipline_data['total_gwp'].sum()),
                    'count': len(discipline_data)
                }
            }

            # Group by MMI within discipline
            for mmi_code in discipline_data['mapped_mmi_code'].dropna().unique():
                mmi_data = discipline_data[discipline_data['mapped_mmi_code'] == mmi_code]

                # Get MMI label
                from .predefined_structure import MMI_CODES
                mmi_label = MMI_CODES.get(str(mmi_code), "UKJENT")

                structure[scenario]['disciplines'][discipline]['mmi_categories'][mmi_code] = {
                    'label': mmi_label,
                    'construction_a': float(mmi_data['construction_a'].sum()),
                    'operation_b': float(mmi_data['operation_b'].sum()),
                    'end_of_life_c': float(mmi_data['end_of_life_c'].sum()),
                    'total_gwp': float(mmi_data['total_gwp'].sum()),
                    'count': len(mmi_data)
                }

    return structure


def get_scenario_summary(structure: Dict[str, Any]) -> pd.DataFrame:
    """
    Get summary DataFrame of all scenarios.

    Args:
        structure: Hierarchical structure from aggregate_by_mapping

    Returns:
        DataFrame with scenario summaries
    """
    summaries = []
    for scenario, data in structure.items():
        summaries.append({
            'Scenario': scenario,
            'Konstruksjon (A)': data['total']['construction_a'],
            'Drift (B)': data['total']['operation_b'],
            'Avslutning (C)': data['total']['end_of_life_c'],
            'Total GWP': data['total']['total_gwp'],
            'Antall rader': data['total']['count']
        })

    return pd.DataFrame(summaries)


def get_discipline_summary(structure: Dict[str, Any], scenario: str) -> pd.DataFrame:
    """
    Get summary DataFrame of disciplines for a specific scenario.

    Args:
        structure: Hierarchical structure
        scenario: Scenario to summarize

    Returns:
        DataFrame with discipline summaries
    """
    if scenario not in structure:
        return pd.DataFrame()

    summaries = []
    for discipline, data in structure[scenario]['disciplines'].items():
        summaries.append({
            'Disiplin': discipline,
            'Konstruksjon (A)': data['total']['construction_a'],
            'Drift (B)': data['total']['operation_b'],
            'Avslutning (C)': data['total']['end_of_life_c'],
            'Total GWP': data['total']['total_gwp'],
            'Antall rader': data['total']['count']
        })

    return pd.DataFrame(summaries)


def compare_scenarios(structure: Dict[str, Any], base_scenario: str, compare_scenario: str) -> Dict[str, Any]:
    """
    Compare two scenarios (ratio and difference).

    Args:
        structure: Hierarchical structure
        base_scenario: Base scenario (e.g., "A")
        compare_scenario: Scenario to compare (e.g., "C")

    Returns:
        Dictionary with comparison metrics
    """
    if base_scenario not in structure or compare_scenario not in structure:
        return {}

    base = structure[base_scenario]['total']
    compare = structure[compare_scenario]['total']

    comparison = {
        'base_scenario': base_scenario,
        'compare_scenario': compare_scenario,
        'difference': {},
        'ratio': {}
    }

    for key in ['construction_a', 'operation_b', 'end_of_life_c', 'total_gwp']:
        # Difference
        comparison['difference'][key] = compare[key] - base[key]

        # Ratio (avoid division by zero)
        if base[key] != 0:
            comparison['ratio'][key] = (compare[key] / base[key]) * 100
        else:
            comparison['ratio'][key] = None

    return comparison


def get_mapping_statistics(df: pd.DataFrame) -> Dict[str, int]:
    """
    Get statistics about mapping completeness.

    Args:
        df: DataFrame with mapping data

    Returns:
        Dictionary with statistics
    """
    total = len(df)
    excluded = df['excluded'].sum()
    active = total - excluded

    df_active = df[~df['excluded']]

    fully_mapped = df_active[
        df_active['mapped_scenario'].notna() &
        df_active['mapped_discipline'].notna() &
        df_active['mapped_mmi_code'].notna()
    ]

    partially_mapped = df_active[
        (df_active['mapped_scenario'].isna() |
         df_active['mapped_discipline'].isna() |
         df_active['mapped_mmi_code'].isna())
    ]

    return {
        'total_rows': int(total),
        'excluded_rows': int(excluded),
        'active_rows': int(active),
        'fully_mapped': len(fully_mapped),
        'partially_mapped': len(partially_mapped),
        'mapping_completeness': (len(fully_mapped) / active * 100) if active > 0 else 0
    }
