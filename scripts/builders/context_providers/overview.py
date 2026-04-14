"""Context providers for Overview pages (index, search)."""
import html
from collections import defaultdict

from ..config import ROOT
from ..data_loader import compute_data_health, read_csv
from ..html_helpers import badge


def index_context():
    """Return template context dict for index.html."""
    health_rows, health_counts = compute_data_health()
    baseline_rows = read_csv(ROOT / "data/evidence/official_baseline_metrics.csv")
    trend_rows = read_csv(ROOT / "data/evidence/lpa-quarterly-trends.csv")
    baseline_by_id = {r.get("metric_id", ""): r for r in baseline_rows}

    # Build metric cards as data dicts
    def _metric_card(metric_id, label, unit_suffix=""):
        row = baseline_by_id.get(metric_id, {})
        value = row.get("value", "n/a")
        source_url = row.get("source_url", "")
        source_table = row.get("source_table", "")
        source_ref = metric_id
        value_label = str(value) + unit_suffix
        source_line = f"{html.escape(source_ref)} ({html.escape(source_table)})"
        if source_url:
            escaped_url = html.escape(source_url)
            source_line = (
                f'<a href="{escaped_url}" target="_blank" '
                f'rel="noopener noreferrer">{source_line}</a>'
            )
        return {
            "label": label,
            "value": value_label,
            "source_line": source_line,
            "source_url": source_url,
        }

    metric_cards = [
        _metric_card("BAS-001", "Major decisions in time", "%"),
        _metric_card("BAS-002", "Non-major decisions in time", "%"),
        _metric_card("BAS-003", "Major appeals overturned", "%"),
        _metric_card("BAS-005", "NSIP examination median", " months"),
    ]

    # Trend delta: average major speed movement from first to latest quarter
    trend_by_lpa = defaultdict(list)
    for row in trend_rows:
        trend_by_lpa[row.get("pilot_id", "")].append(row)
    deltas = []
    for _pid, series in trend_by_lpa.items():
        ordered = sorted(series, key=lambda x: x.get("quarter", ""))
        if len(ordered) < 2:
            continue
        try:
            delta = float(
                ordered[-1].get("major_in_time_pct", 0) or 0
            ) - float(ordered[0].get("major_in_time_pct", 0) or 0)
        except ValueError:
            continue
        deltas.append(delta)
    avg_delta = round(sum(deltas) / len(deltas), 1) if deltas else 0.0
    if avg_delta > 0:
        delta_arrow = "up"
    elif avg_delta < 0:
        delta_arrow = "down"
    else:
        delta_arrow = "flat"

    # Data health snapshot
    health_badges = (
        f'{badge("fresh", "green")} {health_counts.get("fresh", 0)} '
        f'{badge("stale", "amber")} {health_counts.get("stale", 0)} '
        f'{badge("critical", "red")} {health_counts.get("critical", 0)} '
    )
    health_top = None
    if health_rows:
        top = sorted(
            health_rows,
            key=lambda r: (
                r["age_days"] if isinstance(r["age_days"], int) else 9999
            ),
            reverse=True,
        )[0]
        health_top = {
            "dataset": top["dataset"],
            "age_days": str(top["age_days"]),
        }

    return {
        "output_filename": "index.html",
        "title": "UK Planning System Analysis \u2014 England Pilot Release",
        "subhead": (
            "Citation-backed analysis of legislation, policy, and local "
            "plan layers with reform proposals."
        ),
        "active": "index",
        "context_text": (
            "Start here to understand what this pilot covers, who it is for, "
            "and which pages contain the detailed evidence and recommendations."
        ),
        "purpose": {
            "what": (
                "A high-level summary of the England planning analysis, "
                "key findings, and where to go next."
            ),
            "who": (
                "First-time visitors, policy teams, local authority officers, "
                "and public readers."
            ),
            "how": (
                "Start with the summary cards, then choose a path for system "
                "issues, authority insights, recommendations, or data exports."
            ),
            "data": (
                "Metrics and evidence are compiled from GOV.UK statistics, "
                "Planning Inspectorate references, and project datasets. "
                "Check Data Health for recency."
            ),
        },
        "show_trust_panel": False,
        "next_steps": [
            ("contradictions.html", "Go to contradictions dashboard"),
            ("benchmark.html", "Go to benchmark dashboard"),
            ("recommendations.html", "Go to recommendations"),
            ("data-health.html", "Go to data health"),
        ],
        "metric_cards": metric_cards,
        "avg_delta": avg_delta,
        "delta_arrow": delta_arrow,
        "health_badges": health_badges,
        "health_counts": health_counts,
        "health_top": health_top,
    }


def search_context():
    """Return template context dict for search.html."""
    return {
        "output_filename": "search.html",
        "title": "Search",
        "subhead": (
            "Full-text search across legislation, issues, "
            "recommendations, LPAs, appeals, and bottlenecks."
        ),
        "active": "search",
        "context_text": (
            "Use keyword search to quickly find relevant records across "
            "legislation, plans, issues, recommendations, appeals, "
            "and evidence."
        ),
        "purpose": {
            "what": (
                "Cross-site search for legislation, issues, "
                "recommendations, LPAs, and evidence."
            ),
            "who": (
                "Users with a specific term or topic who need "
                "a fast entry point."
            ),
            "how": (
                "Enter plain-language terms and open matching "
                "pages by category."
            ),
            "data": (
                "Search index is generated from current site "
                "datasets at build time."
            ),
        },
        "show_trust_panel": False,
        "next_steps": [
            ("index.html", "Return to overview"),
            ("benchmark.html", "Open authority benchmark"),
            ("recommendations.html", "Open recommendations"),
        ],
    }
