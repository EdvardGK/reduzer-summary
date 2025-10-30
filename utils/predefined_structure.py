# -*- coding: utf-8 -*-
"""
Predefined structure for Scenario/Discipline/MMI combinations
"""

from typing import List, Dict
import pandas as pd


# All possible scenarios
SCENARIOS = ['A', 'B', 'C', 'D']

# All disciplines (Fag)
DISCIPLINES = ['RIV', 'ARK', 'RIE', 'RIB', 'RIBp']

# All MMI codes
MMI_CODES = {
    '300': 'NY',
    '700': 'EKS',
    '800': 'GJEN',
    '900': 'RIVES'
}


def get_all_combinations() -> pd.DataFrame:
    """
    Get all possible combinations of Scenario/Discipline/MMI.

    Returns:
        DataFrame with all combinations
    """
    combinations = []
    for scenario in SCENARIOS:
        for discipline in DISCIPLINES:
            for mmi_code, mmi_label in MMI_CODES.items():
                combinations.append({
                    'scenario': scenario,
                    'discipline': discipline,
                    'mmi_code': mmi_code,
                    'mmi_label': mmi_label,
                    'combination_id': f"{scenario}_{discipline}_{mmi_code}"
                })

    return pd.DataFrame(combinations)


def get_scenario_options() -> List[str]:
    """Get list of scenario options for dropdown"""
    return [''] + SCENARIOS  # Empty option for unassigned


def get_discipline_options() -> List[str]:
    """Get list of discipline options for dropdown"""
    return [''] + DISCIPLINES


def get_mmi_options() -> List[Dict[str, str]]:
    """Get list of MMI options with labels for dropdown"""
    return [{'code': '', 'label': ''}] + [
        {'code': code, 'label': f"{code} - {label}"}
        for code, label in MMI_CODES.items()
    ]


def validate_combination(scenario: str, discipline: str, mmi_code: str) -> bool:
    """
    Validate if a combination is valid.

    Args:
        scenario: Scenario letter
        discipline: Discipline code
        mmi_code: MMI code

    Returns:
        True if valid combination
    """
    return (
        scenario in SCENARIOS and
        discipline in DISCIPLINES and
        mmi_code in MMI_CODES
    )
