"""Tests for builders.html_utils module."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from builders.html_utils import (
    badge,
    confidence_badge,
    verification_badge,
    provenance_badge,
    sparkline_svg,
    render_table,
)


def test_badge_basic():
    result = badge("high", "green")
    assert 'class="badge badge-green"' in result
    assert "high" in result


def test_confidence_badge_high():
    result = confidence_badge("high")
    assert "badge-green" in result
    assert "high" in result


def test_confidence_badge_unknown():
    result = confidence_badge("unknown")
    assert "badge-grey" in result


def test_verification_badge():
    result = verification_badge("verified")
    assert "badge-green" in result


def test_provenance_badge_official():
    result = provenance_badge("official")
    assert "Official stats" in result
    assert "badge-blue" in result


def test_provenance_badge_estimated():
    result = provenance_badge("estimated")
    assert "Analytical estimate" in result
    assert "badge-amber" in result


def test_sparkline_svg_empty():
    assert sparkline_svg([]) == ""


def test_sparkline_svg_values():
    result = sparkline_svg([10, 20, 30])
    assert "<svg" in result
    assert "polyline" in result
    assert "trend sparkline" in result


def test_render_table_basic():
    rows = [{"a": "1", "b": "2"}]
    columns = [("a", "Col A"), ("b", "Col B")]
    result = render_table(rows, columns)
    assert "<table>" in result
    assert "Col A" in result
    assert "Col B" in result
    assert "<td>1</td>" in result
