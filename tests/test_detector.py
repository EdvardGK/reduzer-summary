# -*- coding: utf-8 -*-
"""
Tests for detector.py - pattern recognition
"""

import pytest
from utils.detector import (
    detect_scenario,
    detect_discipline,
    detect_mmi,
    is_summary_row,
    detect_all
)


class TestScenarioDetection:
    """Test scenario detection patterns"""

    def test_detect_scenario_standard(self):
        assert detect_scenario("Scenario A - RIV - MMI300") == "A"
        assert detect_scenario("Scenario C - ARK - MMI700") == "C"

    def test_detect_scenario_case_insensitive(self):
        assert detect_scenario("scenario a - RIV") == "A"
        assert detect_scenario("SCENARIO C - ARK") == "C"

    def test_detect_scenario_variations(self):
        assert detect_scenario("A - Scenario C - RIE") == "C"
        assert detect_scenario("A-RIV-MMI300") == "A"

    def test_detect_scenario_none(self):
        assert detect_scenario("Random text") is None
        assert detect_scenario("") is None


class TestDisciplineDetection:
    """Test discipline detection patterns"""

    def test_detect_discipline_standard(self):
        assert detect_discipline("Scenario A - RIV - MMI300") == "RIV"
        assert detect_discipline("Scenario C - ARK - MMI700") == "ARK"
        assert detect_discipline("Scenario A - RIE - MMI800") == "RIE"

    def test_detect_discipline_ribp_before_rib(self):
        """RIBp should match before RIB"""
        assert detect_discipline("Scenario A - RIBp - MMI300") == "RIBp"
        assert detect_discipline("Scenario A - RIB - MMI300") == "RIB"

    def test_detect_discipline_none(self):
        assert detect_discipline("Random text") is None


class TestMMIDetection:
    """Test MMI code detection"""

    def test_detect_mmi_standard(self):
        assert detect_mmi("Scenario A - RIV - MMI300") == "300"
        assert detect_mmi("Scenario C - ARK - MMI 700") == "700"
        assert detect_mmi("MMI800") == "800"

    def test_detect_mmi_nybygg(self):
        """Nybygg should map to 300"""
        assert detect_mmi("Scenario A - RIV - Nybygg") == "300"

    def test_detect_mmi_none(self):
        assert detect_mmi("Random text") is None


class TestSummaryRowDetection:
    """Test summary row detection"""

    def test_is_summary_row_true(self):
        assert is_summary_row("S8 - RAMBELL") is True
        assert is_summary_row("Total") is True
        assert is_summary_row("Sum") is True
        assert is_summary_row("RAMBOELL") is True

    def test_is_summary_row_false(self):
        assert is_summary_row("Scenario A - RIV") is False
        assert is_summary_row("Normal data") is False


class TestDetectAll:
    """Test combined detection"""

    def test_detect_all_complete(self):
        result = detect_all("Scenario C - ARK - MMI700")
        assert result['scenario'] == "C"
        assert result['discipline'] == "ARK"
        assert result['mmi_code'] == "700"
        assert result['mmi_label'] == "EKS"

    def test_detect_all_partial(self):
        result = detect_all("Scenario A - Random")
        assert result['scenario'] == "A"
        assert result['discipline'] is None
        assert result['mmi_code'] is None
