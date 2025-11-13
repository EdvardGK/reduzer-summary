# -*- coding: utf-8 -*-
"""
Diagnostic utilities for debugging data issues
"""

import pandas as pd
from typing import Dict, List


def diagnose_mmi_distribution(df: pd.DataFrame) -> pd.DataFrame:
    """
    Diagnose MMI code distribution in the dataset.

    Shows:
    - What MMI codes are detected (suggested)
    - What MMI codes are mapped
    - How many are excluded vs active
    - Which ones have zero GWP

    Args:
        df: Full dataframe with all columns

    Returns:
        DataFrame with MMI diagnostic information
    """
    results = []

    mmi_codes = ['300', '700', '800', '900']
    mmi_labels = {
        '300': 'NY (New)',
        '700': 'EKS (Existing)',
        '800': 'GJEN (Reuse)',
        '900': 'RIVES (Demolish)'
    }

    for code in mmi_codes:
        # Suggested
        suggested_total = (df['suggested_mmi_code'] == code).sum()
        suggested_active = ((df['suggested_mmi_code'] == code) & (~df['excluded'])).sum()

        # Mapped
        mapped_total = (df['mapped_mmi_code'] == code).sum()
        mapped_active = ((df['mapped_mmi_code'] == code) & (~df['excluded'])).sum()
        mapped_with_gwp = ((df['mapped_mmi_code'] == code) &
                           (~df['excluded']) &
                           (df['total_gwp'] > 0)).sum()

        # Total GWP for this MMI code (active & mapped only)
        total_gwp = df[(df['mapped_mmi_code'] == code) &
                       (~df['excluded'])]['total_gwp'].sum()

        results.append({
            'MMI Code': code,
            'Label': mmi_labels[code],
            'Suggested (Total)': suggested_total,
            'Suggested (Active)': suggested_active,
            'Mapped (Total)': mapped_total,
            'Mapped (Active)': mapped_active,
            'With GWP > 0': mapped_with_gwp,
            'Total GWP (kg CO2e)': f"{total_gwp:,.0f}"
        })

    return pd.DataFrame(results)


def get_sample_categories_by_mmi(df: pd.DataFrame, mmi_code: str, n: int = 5) -> List[str]:
    """
    Get sample category strings for a specific MMI code.

    Args:
        df: Full dataframe
        mmi_code: MMI code to filter by (e.g., '300')
        n: Number of samples to return

    Returns:
        List of category strings
    """
    # Try suggested first
    samples = df[df['suggested_mmi_code'] == mmi_code]['category'].head(n).tolist()

    # If not enough, try mapped
    if len(samples) < n:
        additional = df[df['mapped_mmi_code'] == mmi_code]['category'].head(n).tolist()
        samples.extend(additional)

    return list(set(samples))[:n]  # Remove duplicates


def check_unmapped_mmi_codes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Find rows where MMI was suggested but not mapped (or mapped differently).

    Args:
        df: Full dataframe

    Returns:
        DataFrame showing suggested vs mapped mismatches
    """
    mismatches = df[
        (df['suggested_mmi_code'].notna()) &
        (df['suggested_mmi_code'] != df['mapped_mmi_code']) &
        (~df['excluded'])
    ][['category', 'suggested_mmi_code', 'mapped_mmi_code', 'total_gwp']]

    return mismatches


def get_detection_failures(df: pd.DataFrame) -> pd.DataFrame:
    """
    Find rows where detection failed (no suggested MMI code).

    Args:
        df: Full dataframe

    Returns:
        DataFrame of rows with failed detection (active only)
    """
    failures = df[
        (df['suggested_mmi_code'].isna()) &
        (~df['excluded'])
    ][['category', 'mapped_scenario', 'mapped_discipline', 'mapped_mmi_code', 'total_gwp']]

    return failures.head(20)  # Limit to first 20 for display
