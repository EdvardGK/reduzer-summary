# -*- coding: utf-8 -*-
"""
Pytest configuration and shared fixtures for testing
"""

import pytest
import pandas as pd
from pathlib import Path


@pytest.fixture
def sample_excel_data():
    """Sample Excel data for testing"""
    return pd.DataFrame({
        'category': [
            'Scenario A - RIV - MMI300',
            'Scenario C - ARK - MMI700',
            'Scenario A - RIE - MMI800',
            'S8 - RAMBELL',  # Summary row
        ],
        'Construction (A)': [1000, 2000, 1500, 4500],
        'Operation (B)': [500, 1000, 750, 2250],
        'End-of-life (C)': [100, 200, 150, 450]
    })


@pytest.fixture
def fixtures_dir():
    """Path to test fixtures directory"""
    return Path(__file__).parent / 'fixtures'
