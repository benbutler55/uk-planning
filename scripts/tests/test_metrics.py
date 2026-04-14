"""Tests for builders.metrics module."""

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from builders.metrics import (
    cohort_for_pid,
    parse_iso_date,
    split_pipe_values,
    issue_detail_page,
    recommendation_detail_page,
    query_value,
    analytical_confidence_for_tier,
    weighted_score,
)


def test_cohort_for_pid_cohort1():
    assert cohort_for_pid("LPA-01") == "Cohort 1"
    assert cohort_for_pid("LPA-06") == "Cohort 1"


def test_cohort_for_pid_cohort2():
    assert cohort_for_pid("LPA-07") == "Cohort 2"
    assert cohort_for_pid("LPA-16") == "Cohort 2"


def test_cohort_for_pid_cohort_3():
    assert cohort_for_pid("LPA-17") == "Cohort 3"
    assert cohort_for_pid("LPA-26") == "Cohort 3"


def test_cohort_for_pid_unknown():
    from builders.metrics import _COHORT_CACHE

    _COHORT_CACHE.clear()  # ensure fresh load
    assert cohort_for_pid("LPA-99") == "Unknown"


def test_parse_iso_date_valid():
    assert parse_iso_date("2024-06-15") == date(2024, 6, 15)


def test_parse_iso_date_empty():
    assert parse_iso_date("") is None
    assert parse_iso_date(None) is None


def test_parse_iso_date_invalid():
    assert parse_iso_date("not-a-date") is None


def test_split_pipe_values():
    assert split_pipe_values("a | b | c") == ["a", "b", "c"]
    assert split_pipe_values("") == []
    assert split_pipe_values(None) == []
    assert split_pipe_values("single") == ["single"]


def test_issue_detail_page():
    assert issue_detail_page("ISS-001") == "contradiction-iss-001.html"


def test_recommendation_detail_page():
    assert recommendation_detail_page("REC-001") == "recommendation-rec-001.html"


def test_query_value():
    assert query_value("Housing") == "housing"
    assert query_value("") == ""
    assert query_value(None) == ""


def test_analytical_confidence_for_tier():
    assert analytical_confidence_for_tier("A") == "high"
    assert analytical_confidence_for_tier("B") == "medium"
    assert analytical_confidence_for_tier("C") == "low"
    assert analytical_confidence_for_tier("") == "low"
    assert analytical_confidence_for_tier(None) == "low"


def test_weighted_score_basic():
    row = {"severity_score": "3", "fixability_score": "2"}
    weights = {
        "severity_score": {"weight": 0.5},
        "fixability_score": {"weight": 0.5},
    }
    # severity: 3 * 0.5 = 1.5, fixability: (6-2)*0.5 = 2.0, total = 3.5
    assert weighted_score(row, weights) == 3.5


def test_derive_metric_bundle_uses_official_validation():
    from builders.metrics import derive_metric_bundle, _COHORT_CACHE

    _COHORT_CACHE.clear()
    lpa = {
        "pilot_id": "LPA-01",
        "lpa_type": "Metropolitan District",
        "growth_context": "High growth urban",
        "constraint_profile": "",
    }
    issue_row = {
        "total_linked_issues": "5",
        "high_severity_issues": "2",
        "primary_risk_stage": "Committee",
    }
    quality_row = {"data_quality_tier": "A"}
    trend_rows = [
        {
            "major_in_time_pct": "75",
            "appeals_overturned_pct": "2.0",
            "official_validation_return_pct": "8.5",
            "official_delegated_pct": "",
        }
    ]
    result = derive_metric_bundle(lpa, issue_row, quality_row, trend_rows, {}, 12.0)
    assert result["validation_rework_proxy"] == 8.5
    assert result["validation_provenance"] == "official"


def test_derive_metric_bundle_falls_back_to_proxy():
    from builders.metrics import derive_metric_bundle, _COHORT_CACHE

    _COHORT_CACHE.clear()
    lpa = {
        "pilot_id": "LPA-01",
        "lpa_type": "Metropolitan District",
        "growth_context": "",
        "constraint_profile": "",
    }
    issue_row = {
        "total_linked_issues": "5",
        "high_severity_issues": "2",
        "primary_risk_stage": "Committee",
    }
    quality_row = {"data_quality_tier": "A"}
    trend_rows = [
        {
            "major_in_time_pct": "75",
            "appeals_overturned_pct": "2.0",
            "official_validation_return_pct": "",
            "official_delegated_pct": "",
        }
    ]
    result = derive_metric_bundle(lpa, issue_row, quality_row, trend_rows, {}, 12.0)
    assert result["validation_provenance"] == "estimated"
    assert isinstance(result["validation_rework_proxy"], float)
