"""HTML rendering functions: badges, page shell, tables, filters, scripts."""

import html
import json

from .config import BUILD_VERSION, SECTION_CONFIG, PAGE_TO_SECTION
from .metrics import issue_detail_page, recommendation_detail_page


# --- Constants ---

URL_COLUMNS = {"source_url", "url"}
TRUNCATE_COLUMNS = {"summary", "inspector_finding"}


# --- Badge helpers ---


def badge(label, css_class):
    return f'<span class="badge badge-{css_class}">{html.escape(label)}</span>'


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
    escaped_desc = html.escape(description)
    method_link = ""
    if method_anchor:
        method_link = f' <a class="inline-help-link" href="metric-methods.html#{html.escape(method_anchor)}">method</a>'
    return (
        f"{html.escape(label)} "
        f'<span class="inline-help" tabindex="0" role="note" '
        f'aria-label="{escaped_desc}" title="{escaped_desc}">?</span>'
        f"{method_link}"
    )


# --- Page purpose and guidance ---


def render_page_purpose(purpose):
    return (
        '<section class="card card-guidance guided-only"><h2>Start here</h2><dl class="purpose-grid">'
        f"<dt>What this page shows</dt><dd>{html.escape(purpose['what'])}</dd>"
        f"<dt>Who this is for</dt><dd>{html.escape(purpose['who'])}</dd>"
        f"<dt>How to interpret</dt><dd>{html.escape(purpose['how'])}</dd>"
        f"<dt>Data trust and freshness</dt><dd>{html.escape(purpose['data'])}</dd>"
        "</dl></section>"
    )


def render_table_guide(title, bullets):
    body = f'<section class="card"><h3>{html.escape(title)}</h3><ul>'
    for item in bullets:
        body += f"<li>{html.escape(item)}</li>"
    body += "</ul></section>"
    return body


def render_next_steps(steps):
    body = '<section class="card guided-only"><h2>Next actions</h2><ul>'
    for href, label in steps:
        body += f'<li><a href="{html.escape(href)}">{html.escape(label)}</a></li>'
    body += "</ul></section>"
    return body


def render_data_trust_panel(active):
    if active not in {
        "benchmark",
        "reports",
        "coverage",
        "contradictions",
        "recommendations",
        "map",
        "data-health",
    }:
        return ""
    from .data_loader import (
        compute_data_health,
    )  # lazy import to avoid circular dependency

    rows, _counts = compute_data_health()
    if not rows:
        return ""
    oldest = sorted(
        rows,
        key=lambda r: r["age_days"] if isinstance(r["age_days"], int) else 9999,
        reverse=True,
    )[0]
    line = html.escape(
        f"Oldest monitored dataset: {oldest['dataset']} ({oldest['age_days']} days)"
    )
    return (
        '<section class="card card-guidance guided-only"><h3>Data trust panel</h3>'
        "<p><strong>Source tiers:</strong> Official statistics, administrative references, analytical estimates.</p>"
        "<p><strong>Known caveat:</strong> Some authority metrics are estimated proxies and should be interpreted directionally.</p>"
        f"<p><strong>Latest trust check:</strong> {line}</p>"
        '<p class="small">See methodology and metric-methods for full caveat details.</p>'
        "</section>"
    )


def render_mode_shell_script():
    return '\n<script src="assets/shell.js"></script>\n'


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


def default_purpose(active):
    return {
        "index": {
            "what": "A high-level summary of the England planning analysis, key findings, and where to go next.",
            "who": "First-time visitors, policy teams, local authority officers, and public readers.",
            "how": "Start with the summary cards, then choose a path for system issues, authority insights, recommendations, or data exports.",
            "data": "Metrics and evidence are compiled from GOV.UK statistics, Planning Inspectorate references, and project datasets. Check Data Health for recency.",
        },
        "legislation": {
            "what": "The legislation and policy library that underpins planning decisions in scope.",
            "who": "Policy professionals, legal reviewers, and users tracing legal context.",
            "how": "Filter by instrument type and status to find the relevant law or policy, then follow source links.",
            "data": "Official legal and policy references are linked to source URLs and retrieval dates.",
        },
        "plans": {
            "what": "The plan hierarchy across authorities, from national policy down to local and neighbourhood layers.",
            "who": "Users comparing policy stacks across LPAs.",
            "how": "Start with the authority list, then open a specific LPA profile for detailed document context.",
            "data": "Plan records are sourced from authority documents and tracked with status/date fields.",
        },
        "contradictions": {
            "what": "System contradictions and friction points scored by impact, risk, and frequency.",
            "who": "Policy leads, analysts, and non-specialists who need a ranked issue view.",
            "how": "Filter by pathway, stage, and type, then review high-scoring issues first.",
            "data": "Scores are derived from the published methodology and linked evidence records.",
        },
        "recommendations": {
            "what": "Reform recommendations with owners, vehicles, KPIs, and evidence links.",
            "who": "Policy and delivery teams prioritizing actionable changes.",
            "how": "Start with priority and confidence, then review implementation details and evidence traceability.",
            "data": "Every recommendation is linked to at least one evidence record in the evidence links dataset.",
        },
        "roadmap": {
            "what": "A sequenced implementation plan from near-term actions to longer reforms.",
            "who": "Program owners and stakeholders managing delivery order and dependencies.",
            "how": "Read milestones in order and use dependencies and owners to plan delivery cadence.",
            "data": "Roadmap records are maintained in the implementation dataset and updated as statuses evolve.",
        },
        "baselines": {
            "what": "Baseline performance metrics used to measure current planning outcomes.",
            "who": "Users benchmarking current performance before evaluating reforms.",
            "how": "Compare England-level and LPA-level values, then connect metrics to recommendations.",
            "data": "Baselines are sourced from GOV.UK and PINS tables with source table IDs and retrieval dates.",
        },
        "bottlenecks": {
            "what": "Delay hotspots across the six planning stages, with severity and pathway context.",
            "who": "Process improvement teams and users diagnosing where time is lost.",
            "how": "Use the heatmap to identify high-friction stages, then review detailed rows for causes.",
            "data": "Bottleneck records are maintained in the issues datasets with review dates and linked issue IDs.",
        },
        "appeals": {
            "what": "Appeal decisions used as practical evidence for contradiction patterns.",
            "who": "Users validating whether identified issues appear in real decisions.",
            "how": "Filter by issue, outcome, or LPA, then read inspector findings and linked policy citations.",
            "data": "Appeal examples are sourced from Planning Inspectorate references and tagged with retrieval dates.",
        },
        "map": {
            "what": "A geographic view of authorities in scope with headline performance overlays.",
            "who": "Users who prefer spatial exploration of authority performance.",
            "how": "Select markers for summary context, then drill to profile and compare pages.",
            "data": "Geo and performance overlays come from project authority and trend datasets.",
        },
        "compare": {
            "what": "A side-by-side authority comparison across profile, performance, and quality indicators.",
            "who": "Decision-makers comparing two LPAs for similarity, risk, or performance gaps.",
            "how": "Select two authorities or use presets, then scan differences metric by metric.",
            "data": "Comparison values come from trends, issue incidence, and data-quality datasets.",
        },
        "benchmark": {
            "what": "A ranked authority benchmark with percentile bands, trend deltas, and outlier signals.",
            "who": "Users needing a quick comparative performance view across all LPAs.",
            "how": "Filter by region, type, cohort, or band, then drill into report or compare links.",
            "data": "Uses quarterly trends plus analytical layers; provenance badges distinguish official vs estimated inputs.",
        },
        "trends": {
            "what": "Quarterly trend data for major decision speed across all LPAs in scope.",
            "who": "Policy teams, analysts, and stakeholders tracking performance trajectories.",
            "how": "Use the sparklines and change column to identify improving and declining authorities, then drill into profiles for context.",
            "data": "Trend data is sourced from GOV.UK P151 planning statistics. See Data Health for recency.",
        },
        "reports": {
            "what": "Downloadable per-authority report bundles and monthly snapshot outputs.",
            "who": "Analysts, policy teams, and stakeholders needing offline evidence packs.",
            "how": "Filter by authority type, region, or cohort, then download CSV or JSON bundles.",
            "data": "Reports include version stamps, generation dates, provenance tags, and source references.",
        },
        "coverage": {
            "what": "Authority coverage status with onboarding gates and evidence completeness.",
            "who": "Program teams and users checking which authorities are complete, partial, or estimate-led.",
            "how": "Review status counts first, then inspect authority rows and failed onboarding gates.",
            "data": "Coverage is derived from plan, trend, issue, and quality datasets plus generated authority profile pages.",
        },
        "data-health": {
            "what": "Freshness status for core datasets and update age in days.",
            "who": "Anyone assessing confidence before relying on metrics or rankings.",
            "how": "Check status badges and age values, then prioritize stale or critical datasets for refresh.",
            "data": "Health is computed from date fields in monitored datasets against configured thresholds.",
        },
        "consultation": {
            "what": "Submission status and consultation tracking for recommendations.",
            "who": "Stakeholders monitoring where recommendations have been sent and responses received.",
            "how": "Check status by recommendation ID, then review next actions.",
            "data": "Statuses are drawn from the recommendation-status dataset with current workflow fields.",
        },
        "search": {
            "what": "Cross-site search for legislation, issues, recommendations, LPAs, and evidence.",
            "who": "Users with a specific term or topic who need a fast entry point.",
            "how": "Enter plain-language terms and open matching pages by category.",
            "data": "Search index is generated from current site datasets at build time.",
        },
        "methodology": {
            "what": "How scoring, evidence standards, and quality controls are applied.",
            "who": "Users who need to validate analytical rigor and assumptions.",
            "how": "Read scoring dimensions first, then review quality checks and limitations.",
            "data": "Method definitions are versioned in schema and scoring files and reflected in generated outputs.",
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
        "policymakers": {
            "what": "A role-specific view of findings, actions, and relevant evidence for policy teams.",
            "who": "National and local policy makers.",
            "how": "Start with priority actions, then follow links to detailed pages and supporting evidence.",
            "data": "Content is drawn from shared datasets and reflects current build and version status.",
        },
        "lpas": {
            "what": "A role-specific view of findings, actions, and relevant evidence for LPAs.",
            "who": "Local planning authority officers and service managers.",
            "how": "Start with LPA actions, then drill into authority insights and recommendation details.",
            "data": "Content is drawn from shared datasets and reflects current build and version status.",
        },
        "developers": {
            "what": "A role-specific view of findings, actions, and relevant evidence for developers.",
            "who": "Developers and planning consultants.",
            "how": "Review key impacts first, then open recommendations and authority pages for detail.",
            "data": "Content is drawn from shared datasets and reflects current build and version status.",
        },
        "public": {
            "what": "A role-specific plain-language view of findings and proposed improvements.",
            "who": "Residents, community groups, and lay readers.",
            "how": "Read the plain-language summary first, then open recommendations and methodology pages for detail.",
            "data": "Content is drawn from shared datasets and reflects current build and version status.",
        },
    }.get(active)


# --- Page shell ---


def render_footer(active):
    """Site-wide footer with section links, version info, and data health."""
    section_links = " ".join(
        f'<a href="{cfg["href"]}">{cfg["label"]}</a>'
        for key, cfg in SECTION_CONFIG.items()
        if key != "audiences"
    )
    return (
        '<footer class="site-footer">'
        '<div class="footer-inner">'
        f'<nav class="footer-nav" aria-label="Footer navigation">{section_links}'
        '<a href="search.html">Search</a>'
        '<a href="audience-policymakers.html">For Audiences</a>'
        "</nav>"
        '<div class="footer-meta">'
        f"<p>{BUILD_VERSION} &middot; Built with open data &middot; "
        '<a href="methodology.html">Methodology</a> &middot; '
        '<a href="data-health.html">Data Health</a> &middot; '
        '<a href="exports.html">Exports</a></p>'
        "</div>"
        "</div>"
        "</footer>"
    )


def page(
    title,
    subhead,
    active,
    body,
    context=None,
    purpose=None,
    breadcrumbs=None,
    next_steps=None,
):
    section = PAGE_TO_SECTION.get(active, "overview")
    top_nav = "\n".join(
        f'<a class="top-tab{(" active" if key == section else "")}" href="{cfg["href"]}">{cfg["label"]}</a>'
        for key, cfg in SECTION_CONFIG.items()
        if key != "audiences"
    )
    sub_nav = "\n".join(
        f'<a{' class="active"' if key == active else ""} href="{href}">{label}</a>'
        for key, label, href in SECTION_CONFIG[section]["children"]
    )
    breadcrumb_data = (
        breadcrumbs if breadcrumbs is not None else default_breadcrumbs(active)
    )
    breadcrumb_html = (
        '<div class="breadcrumbs">'
        + " &gt; ".join(
            f'<a href="{html.escape(href)}">{html.escape(label)}</a>'
            for href, label in breadcrumb_data
        )
        + "</div>"
    )
    if purpose is None:
        purpose = default_purpose(active)
    purpose_html = render_page_purpose(purpose) if purpose else ""
    context_html = ""
    if context:
        context_html = (
            f'<section class="card guided-only"><p>{html.escape(context)}</p></section>'
        )
    next_html = render_next_steps(next_steps) if next_steps else ""
    trust_html = render_data_trust_panel(active)
    utility_html = (
        '<section class="shell-utilities">'
        '<button type="button" class="utility-toggle" aria-expanded="true">Settings &amp; trust info</button>'
        '<div class="utility-body">'
        '<div class="utility-row">'
        "<label>View mode "
        '<select id="view-mode-toggle" aria-label="Toggle guided or expert mode">'
        '<option value="guided">Guided</option><option value="expert">Expert</option>'
        "</select></label>"
        '<label><input type="checkbox" id="plain-language-toggle" /> Plain-language mode</label>'
        '<button type="button" data-copy-view>Copy this view</button>'
        "</div>"
        '<p class="small">Trust legend: '
        f"{provenance_badge('official')} Official statistic "
        f"{provenance_badge('estimated')} Analytical estimate "
        f"{confidence_badge('high')} Confidence example"
        "</p>"
        "</div>"
        "</section>"
    )
    plain_html = (
        '<section class="card plain-language-panel">'
        "<h2>Plain-language guide</h2>"
        f"<p>This page helps you understand <strong>{html.escape(title)}</strong> without specialist planning jargon. "
        "Use the start-here notes first, then open linked detail pages for evidence and next actions.</p>"
        '<p class="small">Common terms: <strong>s106</strong> (legal agreement on development obligations), '
        "<strong>NSIP</strong> (nationally significant infrastructure project), "
        "<strong>verification state</strong> (draft or reviewed data status).</p>"
        "</section>"
    )
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{html.escape(title)}</title>
    <link rel="stylesheet" href="assets/styles.css" />
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link href="https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@400;600;700&display=swap" rel="stylesheet" />
  </head>
  <body>
    <a class="skip-link" href="#main-content">Skip to main content</a>
    <a class="skip-link" href="#filters-start">Skip to filters</a>
    <a class="skip-link" href="#table-start">Skip to data table</a>
    <a class="skip-link" href="#evidence-start">Skip to evidence</a>
    <div class="layout">
      <header>
        <h1>{html.escape(title)}</h1>
        <p class="subhead">{html.escape(subhead)}</p>
        <div class="header-search"><span class="search-icon" aria-hidden="true">&#128269;</span><a href="search.html">Search</a></div>
      </header>
      <button class="nav-hamburger" aria-label="Toggle navigation" aria-expanded="true">&#9776;</button>
      <div class="nav-panel nav-panel--open">
        <nav class="top-nav" aria-label="Main sections">
{top_nav}
        </nav>
        <nav class="sub-nav" aria-label="Section pages">
{sub_nav}
        </nav>
      </div>
{breadcrumb_html}
      <button type="button" class="print-export" onclick="window.print()">Print / PDF</button>
{utility_html}
      <main id="main-content">
{plain_html}
{purpose_html}
{context_html}
{trust_html}
{body}
{next_html}
      </main>
{render_footer(active)}
    </div>
    <button id="back-to-top" class="back-to-top" aria-label="Back to top" style="display:none;">&uarr;</button>
{render_mode_shell_script()}
  </body>
</html>
"""


def write(path, content):
    path.write_text(content, encoding="utf-8")


# --- Table helpers ---


def render_cell(key, value):
    """Render a table cell, turning URL columns into clickable links."""
    if (
        key in URL_COLUMNS
        and value
        and (value.startswith("http://") or value.startswith("https://"))
    ):
        escaped = html.escape(value)
        return f'<td><a href="{escaped}" target="_blank" rel="noopener noreferrer">Link</a></td>'
    if key == "issue_id" and value:
        href = issue_detail_page(value)
        return f'<td><a href="{html.escape(href)}">{html.escape(value)}</a></td>'
    if key == "recommendation_id" and value:
        href = recommendation_detail_page(value)
        return f'<td><a href="{html.escape(href)}">{html.escape(value)}</a></td>'
    if key in TRUNCATE_COLUMNS and value:
        return f'<td><div class="cell-truncate">{html.escape(value)}</div></td>'
    return f"<td>{html.escape(value)}</td>"


def sparkline_svg(values, width=120, height=28):
    """Return a tiny inline SVG sparkline for a list of numeric values."""
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


def render_table(rows, columns):
    head = "".join(f"<th>{html.escape(label)}</th>" for _, label in columns)
    body = []
    for row in rows:
        cells = "".join(render_cell(key, row.get(key, "") or "") for key, _ in columns)
        body.append(f"<tr>{cells}</tr>")
    return (
        '<section class="card"><table><thead><tr>'
        + head
        + "</tr></thead><tbody>"
        + "".join(body)
        + "</tbody></table></section>"
    )


def render_filter_controls(table_id, text_label, filter_defs):
    controls = [
        '<section class="card" id="filters-start">',
        '<div class="filter-row">',
        f'<label class="filter-item">{html.escape(text_label)}'
        f'<input type="search" aria-label="{html.escape(text_label)}" data-table="{table_id}" data-filter="search" placeholder="Type to search..." /></label>',
    ]
    for field, label, options in filter_defs:
        opts = '<option value="">All</option>' + "".join(
            f"<option>{html.escape(o)}</option>" for o in options
        )
        controls.append(
            f'<label class="filter-item">{html.escape(label)}'
            f'<select data-table="{table_id}" data-filter="{field}">{opts}</select></label>'
        )
    controls.append("</div>")
    controls.append(
        f'<p class="small" data-filter-count-for="{table_id}" aria-live="polite" role="status"></p>'
    )
    controls.append("</section>")
    return "".join(controls)


def render_filterable_table(rows, columns, table_id, data_fields):
    head = "".join(f"<th>{html.escape(label)}</th>" for _, label in columns)
    body_rows = []
    for row in rows:
        attrs = " ".join(
            f'data-{f}="{html.escape((row.get(f, "") or "").strip().lower())}"'
            for f in data_fields
        )
        cells = "".join(render_cell(k, row.get(k, "") or "") for k, _ in columns)
        body_rows.append(f"<tr {attrs}>{cells}</tr>")
    return (
        f'<section class="card" id="table-start">'
        f'<p class="table-tap-hint">Tap any row to see full details</p>'
        f'<table id="{table_id}" class="dense-table"><thead><tr>'
        + head
        + "</tr></thead><tbody>"
        + "".join(body_rows)
        + "</tbody></table></section>"
    )


def render_filter_script(table_id, fields, shared_filters=None):
    fjs = ",".join(f'"{f}"' for f in fields)
    shared = shared_filters or []
    sjs = ",".join(f'"{f}"' for f in shared)
    return f"""
<script>
(function() {{
  var table = document.getElementById('{table_id}');
  if (!table) return;
  var rows = Array.from(table.querySelectorAll('tbody tr'));
  var controls = Array.from(document.querySelectorAll('[data-table="{table_id}"]'));
  var countEl = document.querySelector('[data-filter-count-for="{table_id}"]');
  var fields = [{fjs}];
  var sharedFilters = [{sjs}];
  var sharedKey = 'uk-planning-shared-filters-v1';

  function loadSharedState() {{
    try {{
      return JSON.parse(localStorage.getItem(sharedKey) || '{{}}');
    }} catch (e) {{
      return {{}};
    }}
  }}

  function applyInitialSharedFilters() {{
    var params = new URLSearchParams(window.location.search);
    if (!Array.from(params.keys()).length && window.location.hash) {{
      params = new URLSearchParams(window.location.hash.replace(/^#/, ''));
    }}
    var stored = loadSharedState();
    controls.forEach(function(control) {{
      var key = control.dataset.filter;
      var fromUrl = (params.get(key) || '').toLowerCase().trim();
      var fromStore = sharedFilters.indexOf(key) !== -1 ? (stored[key] || '').toLowerCase().trim() : '';
      var next = fromUrl || fromStore;
      if (!next) return;
      var hasOption = Array.from(control.options || []).some(function(opt) {{
        return (opt.value || '').toLowerCase() === next;
      }});
      if (hasOption) {{
        control.value = next;
      }} else if (control.dataset.filter === 'search') {{
        control.value = next;
      }}
    }});
  }}

  function persistSharedFilters() {{
    if (!sharedFilters.length) return;
    var params = new URLSearchParams(window.location.search);
    var stored = loadSharedState();
    controls.forEach(function(control) {{
      var key = control.dataset.filter;
      if (sharedFilters.indexOf(key) === -1) return;
      var value = (control.value || '').toLowerCase().trim();
      if (value) {{
        stored[key] = value;
        params.set(key, value);
      }} else {{
        delete stored[key];
        params.delete(key);
      }}
    }});
    localStorage.setItem(sharedKey, JSON.stringify(stored));
    var query = params.toString();
    history.replaceState(null, '', window.location.pathname + (query ? ('?' + query) : ''));
  }}

  applyInitialSharedFilters();

  function update() {{
    var visible = 0;
    var sc = controls.find(function(c) {{ return c.dataset.filter === 'search'; }});
    var st = sc ? sc.value.toLowerCase().trim() : '';
    var sel = {{}};
    controls.forEach(function(c) {{
      if (c.dataset.filter !== 'search' && c.value) sel[c.dataset.filter] = c.value.toLowerCase();
    }});
    rows.forEach(function(row) {{
      var show = true;
      for (var f in sel) {{ if ((row.dataset[f] || '') !== sel[f]) show = false; }}
      if (show && st) {{
        var blob = fields.map(function(f) {{ return row.dataset[f] || ''; }}).join(' ');
        if (blob.indexOf(st) === -1) show = false;
      }}
      row.classList.toggle('hidden-row', !show);
      if (show) visible++;
    }});
    if (countEl) countEl.textContent = visible + ' of ' + rows.length + ' rows shown';
    persistSharedFilters();
  }}
  controls.forEach(function(c) {{ c.addEventListener('input', update); c.addEventListener('change', update); }});
  update();
}})();
</script>
"""


def render_table_enhancements_script(table_id, presets=None):
    preset_cfg = json.dumps(presets or [], ensure_ascii=False)
    return f"""
<script>
(function() {{
  var table = document.getElementById('{table_id}');
  if (!table) return;
  var controls = Array.from(document.querySelectorAll('[data-table="{table_id}"]'));
  var cards = table.closest('.card');
  var presets = {preset_cfg};

  function ensureContainers() {{
    if (!cards) return;
    if (!cards.querySelector('.active-filter-chips')) {{
      var chips = document.createElement('p');
      chips.className = 'small active-filter-chips';
      cards.parentNode.insertBefore(chips, cards);
    }}
    if (presets.length && !cards.parentNode.querySelector('[data-presets-for="{table_id}"]')) {{
      var wrap = document.createElement('section');
      wrap.className = 'card';
      wrap.setAttribute('data-presets-for', '{table_id}');
      var html = '<h3>Quick presets</h3><div class="preset-row">';
      presets.forEach(function(p, idx) {{
        html += '<button type="button" data-preset-index="' + idx + '">' + p.label + '</button>';
      }});
      html += '<button type="button" data-preset-clear="1">Clear presets</button></div><p class="small" data-sort-state-for="{table_id}">Sort: none</p>';
      wrap.innerHTML = html;
      cards.parentNode.insertBefore(wrap, cards);
      wrap.querySelectorAll('[data-preset-index]').forEach(function(btn) {{
        btn.addEventListener('click', function() {{
          var p = presets[Number(btn.getAttribute('data-preset-index'))] || {{}};
          controls.forEach(function(c) {{
            var key = c.dataset.filter;
            if (key === 'search') return;
            c.value = (p.filters && p.filters[key]) || '';
          }});
          controls.forEach(function(c) {{ c.dispatchEvent(new Event('change', {{ bubbles: true }})); }});
        }});
      }});
      var clear = wrap.querySelector('[data-preset-clear]');
      if (clear) {{
        clear.addEventListener('click', function() {{
          controls.forEach(function(c) {{ c.value = ''; c.dispatchEvent(new Event('change', {{ bubbles: true }})); }});
        }});
      }}
    }}
  }}

  function renderChips() {{
    var chips = document.querySelector('.active-filter-chips');
    if (!chips) return;
    var active = [];
    controls.forEach(function(c) {{
      var key = c.dataset.filter;
      var value = (c.value || '').trim();
      if (!value) return;
      active.push(key + ': ' + value);
    }});
    chips.textContent = active.length ? ('Active filters - ' + active.join(' | ')) : 'Active filters - none';
  }}

  function sortableHeaders() {{
    var stateEl = document.querySelector('[data-sort-state-for="{table_id}"]');
    var headers = Array.from(table.querySelectorAll('thead th'));
    headers.forEach(function(th, idx) {{
      th.classList.add('sortable-th');
      th.setAttribute('aria-sort', 'none');
      th.addEventListener('click', function() {{
        var dir = th.dataset.sortDir === 'asc' ? 'desc' : 'asc';
        headers.forEach(function(h) {{ delete h.dataset.sortDir; h.setAttribute('aria-sort', 'none'); }});
        th.dataset.sortDir = dir;
        th.setAttribute('aria-sort', dir === 'asc' ? 'ascending' : 'descending');
        var rows = Array.from(table.querySelectorAll('tbody tr'));
        rows.sort(function(a, b) {{
          var av = (a.children[idx] && a.children[idx].innerText || '').trim();
          var bv = (b.children[idx] && b.children[idx].innerText || '').trim();
          var an = parseFloat(av.replace(/[^0-9.+-]/g, ''));
          var bn = parseFloat(bv.replace(/[^0-9.+-]/g, ''));
          var cmp = (!isNaN(an) && !isNaN(bn)) ? (an - bn) : av.localeCompare(bv);
          return dir === 'asc' ? cmp : -cmp;
        }});
        var body = table.querySelector('tbody');
        rows.forEach(function(r) {{ body.appendChild(r); }});
        if (stateEl) stateEl.textContent = 'Sort: ' + th.innerText.trim() + ' (' + dir + ')';
      }});
    }});
  }}

  ensureContainers();
  renderChips();
  sortableHeaders();
  controls.forEach(function(c) {{ c.addEventListener('input', renderChips); c.addEventListener('change', renderChips); }});
}})();
</script>
"""


def render_mobile_drawer_script(table_id, labels, max_width=900):
    ljs = json.dumps(labels)
    return f"""
<script>
(function() {{
  var table = document.getElementById('{table_id}');
  if (!table) return;
  var labels = {ljs};
  var media = window.matchMedia('(max-width: {max_width}px)');

  var drawer = document.createElement('div');
  drawer.className = 'mobile-drawer';
  drawer.innerHTML = '<div class="mobile-drawer-backdrop"></div><div class="mobile-drawer-panel"><button type="button" class="mobile-drawer-close" aria-label="Close details">Close</button><div class="mobile-drawer-body"></div></div>';
  document.body.appendChild(drawer);

  function closeDrawer() {{
    drawer.classList.remove('open');
  }}

  drawer.querySelector('.mobile-drawer-backdrop').addEventListener('click', closeDrawer);
  drawer.querySelector('.mobile-drawer-close').addEventListener('click', closeDrawer);

  function openRow(row) {{
    var cells = Array.from(row.children);
    var parts = [];
    cells.forEach(function(cell, idx) {{
      var label = labels[idx] || ('Column ' + (idx + 1));
      var value = (cell.innerText || '').trim();
      if (!value) return;
      parts.push('<div class="mobile-drawer-item"><h4>' + label + '</h4><p>' + value + '</p></div>');
    }});
    drawer.querySelector('.mobile-drawer-body').innerHTML = parts.join('');
    drawer.classList.add('open');
  }}

  table.addEventListener('click', function(evt) {{
    if (!media.matches) return;
    if (evt.target.closest('a')) return;
    var row = evt.target.closest('tbody tr');
    if (!row) return;
    if (row.classList.contains('hidden-row') || row.classList.contains('hidden-peer')) return;
    openRow(row);
  }});
}})();
</script>
"""


def render_detail_toc(items):
    links = "".join(
        f'<a href="#{html.escape(anchor)}">{html.escape(label)}</a>'
        for anchor, label in items
    )
    return (
        '<section class="card detail-toc" aria-label="Detail page sections">'
        "<h3>On this page</h3>"
        f'<div class="detail-toc-links">{links}</div>'
        "</section>"
    )


def render_metric_context_block(items):
    body = '<section class="card guided-only" id="evidence-start"><h3>Metric context</h3><table><thead><tr><th>Metric</th><th>Definition</th><th>Why it matters</th><th>Source and confidence</th></tr></thead><tbody>'
    for item in items:
        body += "<tr>"
        body += f"<td>{html.escape(item.get('metric', ''))}</td>"
        body += f"<td>{html.escape(item.get('definition', ''))}</td>"
        body += f"<td>{html.escape(item.get('why', ''))}</td>"
        body += f"<td>{html.escape(item.get('source', ''))}</td>"
        body += "</tr>"
    body += "</tbody></table></section>"
    return body


def render_plan_docs_table(rows):
    body = [
        '<section class="card"><table><thead><tr><th>Document</th><th>Level</th><th>Status</th>'
        "<th>Date</th><th>Notes</th><th>Source</th></tr></thead><tbody>"
    ]
    for row in rows:
        src = html.escape(row.get("source_url", ""))
        link = f'<a href="{src}">Link</a>' if src else ""
        body.append(
            "<tr>"
            + f"<td>{html.escape(row.get('document_title', ''))}</td>"
            + f"<td>{html.escape(row.get('plan_level', ''))}</td>"
            + f"<td>{html.escape(row.get('status', ''))}</td>"
            + f"<td>{html.escape(row.get('adoption_or_publication_date', ''))}</td>"
            + f"<td>{html.escape(row.get('notes', ''))}</td>"
            + f"<td>{link}</td></tr>"
        )
    body.append("</tbody></table></section>")
    return "".join(body)
