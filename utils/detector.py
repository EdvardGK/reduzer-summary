# -*- coding: utf-8 -*-
"""
Automatic detection of scenario, discipline, and MMI codes from category names
"""

import re
from typing import Optional, Dict


# MMI mapping to Norwegian terms
MMI_MAPPING = {
    "300": "NY",        # Nybygg / New
    "700": "EKS",       # Eksisterende / Existing Kept / Beholdes
    "800": "GJEN",      # Gjenbruk / Reused
    "900": "RIVES"      # Riving / Demolish / Existing Waste
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
        "ScenarioA_RIV_Nybygg" -> "A"
        "A - Scenario C - RIE - MMI 700" -> "C"
        "Scenario C - ARK - MMI300" -> "C"
    """
    if not category or not isinstance(category, str):
        return None

    # Pattern 1: "ScenarioX" format (no space, underscore delimiter)
    match = re.search(r'Scenario([ABCD])(?:[_\s-]|$)', category, re.IGNORECASE)
    if match:
        return match.group(1).upper()

    # Pattern 2: "Scenario X" format (with space)
    match = re.search(r'Scenario\s+([ABCD])', category, re.IGNORECASE)
    if match:
        return match.group(1).upper()

    # Pattern 3: "X - Scenario Y" format (take Y)
    match = re.search(r'[ABCD]\s*-\s*Scenario\s+([ABCD])', category, re.IGNORECASE)
    if match:
        return match.group(1).upper()

    # Pattern 4: Standalone letter at beginning
    match = re.match(r'^([ABCD])[\s_-]', category)
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
        "ScenarioA_RIV_Nybygg" -> "RIV"
        "Scenario C - ARK Fasade - MMI700" -> "ARK"
        "A - Scenario C - RIE - MMI 700" -> "RIE"
    """
    if not category or not isinstance(category, str):
        return None

    # Order matters: check RIBp before RIB
    disciplines = ["RIBp", "RIB", "RIV", "ARK", "RIE"]

    for discipline in disciplines:
        # Case-insensitive search with word boundaries or underscores
        # Match: RIV, _RIV_, -RIV-, etc.
        pattern = r'(?:^|[\s_-])' + discipline + r'(?:[\s_-]|$)'
        if re.search(pattern, category, re.IGNORECASE):
            return discipline

    return None


def detect_mmi(category: str) -> Optional[str]:
    """
    Detect MMI code (300/700/800/900) from category string.

    Reduzer canonical status terms:
    - "New" -> 300
    - "Existing" -> 700
    - "Reused" -> 800
    - "Existing Waste" -> 900

    Args:
        category: Category string from Excel

    Returns:
        MMI code as string or None if not detected

    Examples:
        "ScenarioA_RIV_New" -> "300"
        "ScenarioC_ARK_Existing" -> "700"
        "ScenarioB_RIB_Reused" -> "800"
        "ScenarioC_RIV_Existing Waste" -> "900"
        "ScenarioC_RIV_300" -> "300"
        "ScenarioA_RIV_Nybygg" -> "300"
    """
    if not category or not isinstance(category, str):
        return None

    # Pattern 1: "MMI" followed by optional space/underscore and 3-digit code
    match = re.search(r'MMI[\s_]?([3789]00)', category, re.IGNORECASE)
    if match:
        return match.group(1)

    # Pattern 2: Standalone 3-digit code with word boundaries or underscores
    # Match: _300_, -700-, " 800 ", etc.
    match = re.search(r'(?:^|[\s_-])([3789]00)(?:[\s_-]|$)', category)
    if match:
        return match.group(1)

    # Keyword-based detection (case-insensitive)
    # Priority: Reduzer canonical terms first, then Norwegian/variants
    # Note: Use (?:^|[\s_-]) instead of \b because underscore is a word character

    category_lower = category.lower()

    # MMI 900: "Existing Waste" (MUST check this before "Existing" to avoid false match)
    if 'existing waste' in category_lower:
        return "900"
    if re.search(r'(?:^|[\s_-])(rives|riving|demolish|demo)(?:[\s_-]|$)', category_lower):
        return "900"

    # MMI 800: "Reused" (Reduzer canonical term)
    if re.search(r'(?:^|[\s_-])reused(?:[\s_-]|$)', category_lower):
        return "800"
    if re.search(r'(?:^|[\s_-])(gjenbruk|gjen)(?:[\s_-]|$)', category_lower):
        return "800"

    # MMI 700: "Existing" (Reduzer canonical term - check after "Existing Waste")
    if re.search(r'(?:^|[\s_-])existing(?:[\s_-]|$)', category_lower):
        return "700"
    if re.search(r'(?:^|[\s_-])(eksisterende|beholdes|eks|kept)(?:[\s_-]|$)', category_lower):
        return "700"

    # MMI 300: "New" (Reduzer canonical term)
    if re.search(r'(?:^|[\s_-])new(?:[\s_-]|$)', category_lower):
        return "300"
    if re.search(r'(?:^|[\s_-])(nybygg|ny)(?:[\s_-]|$)', category_lower):
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
