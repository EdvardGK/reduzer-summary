# -*- coding: utf-8 -*-
"""
Automatic detection of scenario, discipline, and MMI codes from category names
"""

import re
from typing import Optional, Dict


# MMI mapping to Norwegian terms
MMI_MAPPING = {
    "300": "NY",
    "700": "EKS",
    "800": "GJEN",
    "900": "RIVES"
}


def detect_scenario(category: str) -> Optional[str]:
    """
    Detect scenario (A, B, C, or D) from category string.

    Args:
        category: Category string from Excel

    Returns:
        Scenario letter (A/B/C/D) or None if not detected

    Examples:
        "Scenario A - RIV - Nybygg" -> "A"
        "A - Scenario C - RIE - MMI 700" -> "C"
        "Scenario C - ARK - MMI300" -> "C"
    """
    if not category or not isinstance(category, str):
        return None

    # Pattern 1: "Scenario X" format
    match = re.search(r'Scenario\s+([ABCD])', category, re.IGNORECASE)
    if match:
        return match.group(1).upper()

    # Pattern 2: "X - Scenario Y" format (take Y)
    match = re.search(r'[ABCD]\s*-\s*Scenario\s+([ABCD])', category, re.IGNORECASE)
    if match:
        return match.group(1).upper()

    # Pattern 3: Standalone letter at beginning
    match = re.match(r'^([ABCD])\s*-', category)
    if match:
        return match.group(1).upper()

    return None


def detect_discipline(category: str) -> Optional[str]:
    """
    Detect discipline from category string.

    Args:
        category: Category string from Excel

    Returns:
        Discipline code (RIV/ARK/RIE/RIB/RIBp) or None if not detected

    Examples:
        "Scenario A - RIV - Nybygg" -> "RIV"
        "Scenario C - ARK Fasade - MMI700" -> "ARK"
        "A - Scenario C - RIE - MMI 700" -> "RIE"
    """
    if not category or not isinstance(category, str):
        return None

    # Order matters: check RIBp before RIB
    disciplines = ["RIBp", "RIB", "RIV", "ARK", "RIE"]

    for discipline in disciplines:
        # Case-insensitive search with word boundaries
        pattern = r'\b' + discipline + r'\b'
        if re.search(pattern, category, re.IGNORECASE):
            return discipline

    return None


def detect_mmi(category: str) -> Optional[str]:
    """
    Detect MMI code (300/700/800/900) from category string.

    Args:
        category: Category string from Excel

    Returns:
        MMI code as string or None if not detected

    Examples:
        "Scenario C - ARK - MMI300" -> "300"
        "Scenario C - RIV - MMI 700" -> "700"
        "Scenario C - ARK - MMI800" -> "800"
    """
    if not category or not isinstance(category, str):
        return None

    # Pattern: "MMI" followed by optional space and 3-digit code
    match = re.search(r'MMI\s*([3789]00)', category, re.IGNORECASE)
    if match:
        return match.group(1)

    # Pattern: Standalone 3-digit code (300, 700, 800, 900)
    match = re.search(r'\b([3789]00)\b', category)
    if match:
        return match.group(1)

    # Special case: "Nybygg" typically means MMI 300 (new construction)
    if re.search(r'\bNybygg\b', category, re.IGNORECASE):
        return "300"

    return None


def get_mmi_label(mmi_code: Optional[str]) -> str:
    """
    Get Norwegian label for MMI code.

    Args:
        mmi_code: MMI code (300/700/800/900)

    Returns:
        Norwegian label or "UKJENT" if not found
    """
    if mmi_code in MMI_MAPPING:
        return MMI_MAPPING[mmi_code]
    return "UKJENT"


def detect_all(category: str) -> Dict[str, Optional[str]]:
    """
    Detect scenario, discipline, and MMI code from category string.

    Args:
        category: Category string from Excel

    Returns:
        Dictionary with detected values and labels
    """
    scenario = detect_scenario(category)
    discipline = detect_discipline(category)
    mmi_code = detect_mmi(category)
    mmi_label = get_mmi_label(mmi_code)

    return {
        "scenario": scenario,
        "discipline": discipline,
        "mmi_code": mmi_code,
        "mmi_label": mmi_label,
        "original_category": category
    }


def is_summary_row(category: str) -> bool:
    """
    Detect if this is a summary row (like "S8 - RAMBOELL") that should be excluded.

    Args:
        category: Category string from Excel

    Returns:
        True if this appears to be a summary row
    """
    if not category or not isinstance(category, str):
        return False

    # Summary indicators
    summary_patterns = [
        r'RAMB.?LL',  # Matches RAMBELL, RAMBOELL, etc.
        r'^S\d+\s*-',  # S8 -, S10 -, etc.
        r'Total',
        r'Sum',
        r'Totalt'
    ]

    for pattern in summary_patterns:
        if re.search(pattern, category, re.IGNORECASE):
            return True

    return False
