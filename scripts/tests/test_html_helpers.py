"""Tests for Jinja2 html_helpers."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from builders.html_helpers import (
    badge, confidence_badge, verification_badge, provenance_badge,
    sparkline_svg, render_cell, default_breadcrumbs,
)


def test_badge():
    result = badge("test", "green")
    assert 'class="badge badge-green"' in result
    assert "test" in result


def test_confidence_badge_high():
    result = confidence_badge("high")
    assert "badge-green" in result


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


def test_sparkline_svg_empty():
    assert sparkline_svg([]) == ""


def test_sparkline_svg_values():
    result = sparkline_svg([10, 20, 30])
    assert "<svg" in result
    assert "polyline" in result


def test_render_cell_plain():
    result = render_cell("name", "Test")
    assert result == "Test"


def test_render_cell_url():
    result = render_cell("source_url", "https://example.com")
    assert 'href="https://example.com"' in result
    assert "Link" in result


def test_render_cell_issue_id():
    result = render_cell("issue_id", "ISSUE-001")
    assert "contradiction-issue-001.html" in result


def test_default_breadcrumbs_index():
    crumbs = default_breadcrumbs("index")
    assert crumbs == [("index.html", "Overview")]


def test_default_breadcrumbs_methodology():
    crumbs = default_breadcrumbs("methodology")
    assert len(crumbs) >= 2
    assert crumbs[0] == ("index.html", "Overview")
