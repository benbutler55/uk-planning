"""Tests for GOV.UK statistics ingest pipeline."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ingest_govuk_stats import (  # noqa: E402
    read_metrics,
    source_status_for_metrics,
    parse_iso_date,
    append_history,
    compute_diff,
    write_diff_report,
)


def test_read_metrics_returns_dict():
    metrics = read_metrics()
    assert isinstance(metrics, dict)
    assert "BAS-001" in metrics


def test_source_status_for_metrics_returns_list():
    metrics = read_metrics()
    statuses = source_status_for_metrics(metrics, ["BAS-001"])
    assert len(statuses) == 1
    assert statuses[0]["metric_id"] == "BAS-001"
    assert statuses[0]["status"] in {"fresh", "stale", "critical", "unknown"}


def test_parse_iso_date_valid():
    result = parse_iso_date("2026-03-15")
    assert result is not None
    assert result.year == 2026


def test_parse_iso_date_empty():
    assert parse_iso_date("") is None
    assert parse_iso_date(None) is None


def test_compute_diff_empty():
    changes = compute_diff({}, {})
    assert changes == []


def test_compute_diff_with_updates():
    metrics = {"BAS-001": {"retrieved_at": "2026-01-01"}}
    detected = {"P151": {"has_update": True, "dates_found": ["15 March 2026"]}}
    changes = compute_diff(metrics, detected)
    assert len(changes) > 0
    assert changes[0]["action"] == "check_for_update"


def test_write_diff_report(tmp_path):
    import ingest_govuk_stats
    original = ingest_govuk_stats.REPORT_JSON_PATH
    ingest_govuk_stats.REPORT_JSON_PATH = tmp_path / "report.json"
    try:
        changes = [{"metric_id": "BAS-001", "action": "check_for_update"}]
        report = write_diff_report(changes, "dry-run")
        assert report["mode"] == "dry-run"
        assert report["summary"]["checked"] == 1
        assert (tmp_path / "report.json").exists()
    finally:
        ingest_govuk_stats.REPORT_JSON_PATH = original


def test_append_history(tmp_path):
    import ingest_govuk_stats
    import json
    original = ingest_govuk_stats.HISTORY_PATH
    ingest_govuk_stats.HISTORY_PATH = tmp_path / "history.json"
    try:
        append_history({"test": True})
        data = json.loads((tmp_path / "history.json").read_text())
        assert len(data) == 1
        assert data[0]["test"] is True
    finally:
        ingest_govuk_stats.HISTORY_PATH = original
