"""Jinja2 custom filters and globals for template rendering."""

import html as html_lib

from .config import BUILD_VERSION, PAGE_TO_SECTION, SECTION_CONFIG
from .metrics import issue_detail_page, recommendation_detail_page


# --- Badge filters ---


def badge(label, css_class):
    return f'<span class="badge badge-{css_class}">{html_lib.escape(label)}</span>'


def confidence_badge(level):
    colors = {"high": "green", "medium": "amber", "low": "red"}
    return badge(level, colors.get(level, "grey"))


def verification_badge(state):
    colors = {"draft": "grey", "verified": "green", "legal-reviewed": "blue"}
    return badge(state, colors.get(state, "grey"))


def provenance_badge(kind):
    labels = {
        "official": ("Official stats", "blue"),
        "estimated": ("Analytical estimate", "amber"),
    }
    label, css = labels.get(kind, ("Unknown provenance", "grey"))
    return badge(label, css)


def metric_help(label, description, method_anchor=None):
    escaped_desc = html_lib.escape(description)
    method_link = ""
    if method_anchor:
        method_link = (
            f' <a class="inline-help-link" '
            f'href="metric-methods.html#{html_lib.escape(method_anchor)}">method</a>'
        )
    return (
        f"{html_lib.escape(label)} "
        f'<span class="inline-help" tabindex="0" role="note" '
        f'aria-label="{escaped_desc}" title="{escaped_desc}">?</span>'
        f"{method_link}"
    )


# --- Chart helpers ---


def sparkline_svg(values, width=120, height=28):
    if not values:
        return ""
    nums = [float(v) for v in values]
    vmin = min(nums)
    vmax = max(nums)
    span = (vmax - vmin) if vmax != vmin else 1.0
    points = []
    for i, n in enumerate(nums):
        x = (i / (len(nums) - 1)) * (width - 2) + 1 if len(nums) > 1 else width / 2
        y = height - (((n - vmin) / span) * (height - 6) + 3)
        points.append(f"{x:.1f},{y:.1f}")
    pts = " ".join(points)
    return (
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
        f'xmlns="http://www.w3.org/2000/svg" role="img" aria-label="trend sparkline">'
        f'<polyline points="{pts}" fill="none" stroke="#00695c" stroke-width="2" />'
        f"</svg>"
    )


# --- Cell rendering ---

URL_COLUMNS = {"source_url", "url"}
TRUNCATE_COLUMNS = {"summary", "inspector_finding"}


def render_cell(key, value):
    if (
        key in URL_COLUMNS
        and value
        and (value.startswith("http://") or value.startswith("https://"))
    ):
        escaped = html_lib.escape(value)
        return f'<a href="{escaped}" target="_blank" rel="noopener noreferrer">Link</a>'
    if key == "issue_id" and value:
        href = issue_detail_page(value)
        return f'<a href="{html_lib.escape(href)}">{html_lib.escape(value)}</a>'
    if key == "recommendation_id" and value:
        href = recommendation_detail_page(value)
        return f'<a href="{html_lib.escape(href)}">{html_lib.escape(value)}</a>'
    if key in TRUNCATE_COLUMNS and value:
        return f'<div class="cell-truncate">{html_lib.escape(value)}</div>'
    return html_lib.escape(value)


# --- Navigation helpers ---


def default_breadcrumbs(active):
    section = PAGE_TO_SECTION.get(active, "overview")
    crumbs = [("index.html", "Overview")]
    if active == "index":
        return crumbs
    section_href = SECTION_CONFIG[section]["href"]
    crumbs.append((section_href, SECTION_CONFIG[section]["label"]))
    for key, label, href in SECTION_CONFIG[section]["children"]:
        if key == active:
            if href != section_href:
                crumbs.append((href, label))
            break
    return crumbs


DEFAULT_PURPOSE = {
    "methodology": {
        "what": "How scoring, evidence standards, and quality controls are applied.",
        "who": "Users who need to validate analytical rigor and assumptions.",
        "how": "Read scoring dimensions first, then review quality checks and limitations.",
        "data": "Method definitions are versioned in schema and scoring files and reflected in generated outputs.",
    },
    "metric-methods": {
        "what": "Per-metric definitions, formulas, provenance, and confidence rules used in benchmark and report outputs.",
        "who": "Analysts, policy teams, and reviewers validating interpretation and comparability.",
        "how": "Open a metric section from tooltip method links, then verify formula scope and provenance before comparing LPAs.",
        "data": "Formulas are implemented in scripts/build_site.py and draw from trend, issue, quality, and plan-document datasets.",
    },
    "sources": {
        "what": "Source index and citations used across the site.",
        "who": "Users verifying data origin and citation reliability.",
        "how": "Use source categories and links to verify a metric, issue, or recommendation claim.",
        "data": "Entries include source URLs and retrieval timestamps where available.",
    },
    "exports": {
        "what": "Machine-readable dataset downloads plus manifest metadata.",
        "who": "Analysts and technical users reusing the data externally.",
        "how": "Download CSV or JSON datasets, then check manifest.json for hashes and version metadata.",
        "data": "Export artifacts are generated during site build and tied to versioned source datasets.",
    },
    "data-health": {
        "what": "Freshness status for core datasets and update age in days.",
        "who": "Anyone assessing confidence before relying on metrics or rankings.",
        "how": "Check status badges and age values, then prioritize stale or critical datasets for refresh.",
        "data": "Health is computed from date fields in monitored datasets against configured thresholds.",
    },
}


def register_helpers(env):
    """Register all custom filters and globals on a Jinja2 Environment."""
    env.filters["badge"] = badge
    env.filters["confidence_badge"] = confidence_badge
    env.filters["verification_badge"] = verification_badge
    env.filters["provenance_badge"] = provenance_badge
    env.filters["render_cell"] = render_cell

    env.globals["badge"] = badge
    env.globals["confidence_badge"] = confidence_badge
    env.globals["verification_badge"] = verification_badge
    env.globals["provenance_badge"] = provenance_badge
    env.globals["metric_help"] = metric_help
    env.globals["sparkline_svg"] = sparkline_svg
    env.globals["render_cell"] = render_cell
    env.globals["default_breadcrumbs"] = default_breadcrumbs
    env.globals["DEFAULT_PURPOSE"] = DEFAULT_PURPOSE
    env.globals["BUILD_VERSION"] = BUILD_VERSION
    env.globals["SECTION_CONFIG"] = SECTION_CONFIG
    env.globals["PAGE_TO_SECTION"] = PAGE_TO_SECTION
