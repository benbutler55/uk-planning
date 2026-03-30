"""Tests for builders.data_loader module."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from builders.data_loader import read_csv, load_scoring, compute_data_health

ROOT = Path(__file__).resolve().parent.parent.parent


def test_read_csv_returns_list():
    rows = read_csv(ROOT / "data/plans/pilot-lpas.csv")
    assert isinstance(rows, list)
    assert len(rows) > 0
    assert "pilot_id" in rows[0]


def test_load_scoring_returns_dict():
    weights = load_scoring()
    assert isinstance(weights, dict)
    assert len(weights) > 0


def test_compute_data_health_returns_rows_and_counts():
    rows, counts = compute_data_health()
    assert isinstance(rows, list)
    assert isinstance(counts, dict)
    assert len(rows) > 0
    assert "dataset" in rows[0]
    assert "status" in rows[0]
