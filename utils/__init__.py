# -*- coding: utf-8 -*-
"""
Utilities for LCA Scenario Comparison Tool
"""

from .data_parser import (
    load_excel_file,
    apply_user_mapping,
    aggregate_by_mapping,
    get_scenario_summary,
    get_discipline_summary,
    compare_scenarios,
    get_mapping_statistics
)
from .detector import detect_scenario, detect_discipline, detect_mmi, detect_all
from .predefined_structure import (
    SCENARIOS,
    DISCIPLINES,
    MMI_CODES,
    get_all_combinations,
    validate_combination
)
from .visualizations import (
    create_stacked_bar_chart,
    create_treemap,
    create_line_chart,
    create_comparison_chart,
    create_discipline_comparison_chart,
    create_mmi_breakdown_chart
)

__all__ = [
    'load_excel_file',
    'apply_user_mapping',
    'aggregate_by_mapping',
    'get_scenario_summary',
    'get_discipline_summary',
    'compare_scenarios',
    'get_mapping_statistics',
    'detect_scenario',
    'detect_discipline',
    'detect_mmi',
    'detect_all',
    'SCENARIOS',
    'DISCIPLINES',
    'MMI_CODES',
    'get_all_combinations',
    'validate_combination',
    'create_stacked_bar_chart',
    'create_treemap',
    'create_line_chart',
    'create_comparison_chart',
    'create_discipline_comparison_chart',
    'create_mmi_breakdown_chart'
]
