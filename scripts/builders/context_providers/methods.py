"""Context providers for Data & Methods pages."""
from ..config import ROOT
from ..data_loader import read_csv
from ..html_helpers import DEFAULT_PURPOSE


def methodology_context():
    """Return template context dict for methodology.html."""
    # Load evidence gaps if file exists
    gaps_path = ROOT / "data/evidence/evidence-gaps.csv"
    evidence_gaps = []
    severity_counts = {}
    if gaps_path.exists():
        evidence_gaps = read_csv(gaps_path)
        for g in evidence_gaps:
            sev = g.get("severity", "unknown")
            severity_counts[sev] = severity_counts.get(sev, 0) + 1

    return {
        "output_filename": "methodology.html",
        "title": "Methodology",
        "subhead": "Taxonomy, scoring model, evidence standards, and quality controls.",
        "active": "methodology",
        "context_text": "This page explains how datasets are scored, validated, and linked to evidence so findings are transparent and reproducible.",
        "purpose": DEFAULT_PURPOSE.get("methodology"),
        "show_trust_panel": False,
        "next_steps": [
            ("metric-methods.html", "Open metric methods appendix"),
            ("sources.html", "Open sources and citations"),
            ("exports.html", "Open data exports"),
            ("data-health.html", "Open data health monitoring"),
        ],
        "evidence_gaps": evidence_gaps,
        "severity_counts": severity_counts,
    }
