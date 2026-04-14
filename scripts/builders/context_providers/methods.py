"""Context providers for Data & Methods pages."""
from ..config import ROOT
from ..data_loader import compute_data_health, read_csv
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


def metric_methods_context():
    """Return template context dict for metric-methods.html."""
    return {
        "output_filename": "metric-methods.html",
        "title": "Metric Methods Appendix",
        "subhead": "Definitions, formulas, provenance, and confidence logic for benchmark and report metrics.",
        "active": "metric-methods",
        "context_text": "Use this appendix to interpret benchmark/report indicators correctly and to understand which values are official statistics versus analytical estimates.",
        "purpose": DEFAULT_PURPOSE.get("metric-methods"),
        "show_trust_panel": False,
        "next_steps": [
            ("benchmark.html", "Return to benchmark"),
            ("reports.html", "Return to reports"),
            ("methodology.html", "Return to methodology"),
        ],
    }


def sources_context():
    """Return template context dict for sources.html."""
    evidence = read_csv(ROOT / "data/evidence/recommendation_evidence_links.csv")
    baselines = read_csv(ROOT / "data/evidence/official_baseline_metrics.csv")
    return {
        "output_filename": "sources.html",
        "title": "Sources and Citations",
        "subhead": "Official data sources, evidence links, and baseline metrics.",
        "active": "sources",
        "context_text": "Use this reference page to verify evidence links, source tables, and citations used throughout the analysis.",
        "purpose": DEFAULT_PURPOSE.get("sources"),
        "show_trust_panel": False,
        "next_steps": [
            ("methodology.html", "Open methodology"),
            ("recommendations.html", "Open recommendations"),
            ("exports.html", "Open data exports"),
        ],
        "evidence_links": evidence,
        "baselines": baselines,
    }


def exports_context():
    """Return template context dict for exports.html."""
    dataset_names = [
        "contradiction-register", "recommendations",
        "recommendation_evidence_links", "official_baseline_metrics",
        "implementation-roadmap", "bottleneck-heatmap",
        "appeal-decisions", "lpa-data-quality",
        "lpa-quarterly-trends", "lpa-issue-incidence",
    ]
    return {
        "output_filename": "exports.html",
        "title": "Data Exports",
        "subhead": "Download datasets in CSV and JSON format.",
        "active": "exports",
        "context_text": "Download the core datasets in machine-readable form for external analysis, QA checks, or reuse in other tools.",
        "purpose": DEFAULT_PURPOSE.get("exports"),
        "show_trust_panel": False,
        "next_steps": [
            ("data-health.html", "Open data health"),
            ("reports.html", "Open report bundles"),
            ("methodology.html", "Open methodology"),
        ],
        "dataset_names": dataset_names,
    }


def data_health_context():
    """Return template context dict for data-health.html."""
    rows, counts = compute_data_health()
    # Sort by age descending (n/a treated as 9999)
    sorted_rows = sorted(
        rows,
        key=lambda r: (r["age_days"] if isinstance(r["age_days"], int) else 9999),
        reverse=True,
    )
    # Prepare trust panel rows with sort_age for the partial template
    trust_panel_rows = [
        {**r, "sort_age": r["age_days"] if isinstance(r["age_days"], int) else 9999}
        for r in rows
    ]
    return {
        "output_filename": "data-health.html",
        "title": "Data Health",
        "subhead": "Freshness and reliability monitoring for core operational datasets.",
        "active": "data-health",
        "context_text": "Use this page to assess whether evidence datasets are up to date before relying on benchmark outputs or recommendations.",
        "purpose": DEFAULT_PURPOSE.get("data-health"),
        "show_trust_panel": True,
        "trust_panel_rows": trust_panel_rows,
        "next_steps": [
            ("benchmark.html", "Return to benchmark"),
            ("reports.html", "Return to reports"),
            ("sources.html", "Review source index"),
        ],
        "health_rows": sorted_rows,
        "health_counts": counts,
    }
