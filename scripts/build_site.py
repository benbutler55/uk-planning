#!/usr/bin/env python3
"""Build static site from CSV datasets. Generates HTML pages with filtering,
weighted scoring, confidence badges, evidence traces, and split audience views."""
import csv
import hashlib
import html
import json
import shutil
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
EXPORTS = SITE / "exports"
SCORING_PATH = ROOT / "data/schemas/scoring.json"
BUILD_VERSION = "v6.0"


def read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_scoring():
    data = json.loads(SCORING_PATH.read_text(encoding="utf-8"))
    return data["scoring_model"]["dimensions"]


def weighted_score(row, weights):
    total = 0.0
    for dim, spec in weights.items():
        raw = float(row.get(dim, 0) or 0)
        if dim == "fixability_score":
            raw = 6 - raw  # invert: higher fixability = lower weighted contribution
        total += raw * spec["weight"]
    return round(total, 2)


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


def cohort_for_pid(pid):
    cohort_1 = {"LPA-01", "LPA-02", "LPA-03", "LPA-04", "LPA-05", "LPA-06"}
    return "Cohort 1" if pid in cohort_1 else "Cohort 2"


def parse_iso_date(raw):
    if not raw:
        return None
    try:
        return date.fromisoformat(raw)
    except ValueError:
        return None


def compute_data_health():
    specs = [
        {
            "dataset": "Official baseline metrics",
            "path": ROOT / "data/evidence/official_baseline_metrics.csv",
            "date_field": "retrieved_at",
            "stale_after_days": 100,
            "critical_after_days": 140,
        },
        {
            "dataset": "LPA quarterly trends",
            "path": ROOT / "data/evidence/lpa-quarterly-trends.csv",
            "date_field": "retrieved_at",
            "stale_after_days": 100,
            "critical_after_days": 140,
        },
        {
            "dataset": "Recommendation evidence links",
            "path": ROOT / "data/evidence/recommendation_evidence_links.csv",
            "date_field": "retrieved_at",
            "stale_after_days": 100,
            "critical_after_days": 140,
        },
        {
            "dataset": "Appeal decision evidence",
            "path": ROOT / "data/evidence/appeal-decisions.csv",
            "date_field": "retrieved_at",
            "stale_after_days": 120,
            "critical_after_days": 180,
        },
        {
            "dataset": "LPA issue incidence",
            "path": ROOT / "data/issues/lpa-issue-incidence.csv",
            "date_field": "last_reviewed",
            "stale_after_days": 45,
            "critical_after_days": 75,
        },
    ]

    rows = []
    for spec in specs:
        data = read_csv(spec["path"])
        values = [parse_iso_date(r.get(spec["date_field"], "")) for r in data]
        valid_dates = [d for d in values if d is not None]
        most_recent = max(valid_dates) if valid_dates else None
        age_days = (date.today() - most_recent).days if most_recent else 9999
        if age_days > spec["critical_after_days"]:
            status = "critical"
            css = "red"
        elif age_days > spec["stale_after_days"]:
            status = "stale"
            css = "amber"
        else:
            status = "fresh"
            css = "green"
        rows.append({
            "dataset": spec["dataset"],
            "row_count": len(data),
            "last_updated": most_recent.isoformat() if most_recent else "n/a",
            "age_days": age_days if most_recent else "n/a",
            "status": status,
            "status_badge": badge(status, css),
            "source_path": str(spec["path"].relative_to(ROOT)),
        })

    counts = defaultdict(int)
    for row in rows:
        counts[row["status"]] += 1
    return rows, dict(counts)


# --- Page shell ---

def page(title, subhead, active, body, context=None):
    links = [
        ("index.html", "Overview", "index"),
        ("legislation.html", "Legislation", "legislation"),
        ("plans.html", "Plans", "plans"),
        ("contradictions.html", "Contradictions", "contradictions"),
        ("recommendations.html", "Recommendations", "recommendations"),
        ("roadmap.html", "Roadmap", "roadmap"),
        ("baselines.html", "Baselines", "baselines"),
        ("bottlenecks.html", "Bottlenecks", "bottlenecks"),
        ("appeals.html", "Appeals", "appeals"),
        ("map.html", "Map", "map"),
        ("compare.html", "Compare", "compare"),
        ("benchmark.html", "Benchmark", "benchmark"),
        ("reports.html", "Reports", "reports"),
        ("data-health.html", "Data Health", "data-health"),
        ("consultation.html", "Consultation", "consultation"),
        ("search.html", "Search", "search"),
        ("audience-policymakers.html", "For Policy Makers", "policymakers"),
        ("audience-lpas.html", "For LPAs", "lpas"),
        ("audience-developers.html", "For Developers", "developers"),
        ("audience-public.html", "For Public", "public"),
        ("methodology.html", "Methodology", "methodology"),
        ("sources.html", "Sources", "sources"),
    ]
    nav = "\n".join(
        f'<a{" class=\"active\"" if key == active else ""} href="{href}">{label}</a>'
        for href, label, key in links
    )
    context_html = ""
    if context:
        context_html = (
            '<section class="card">'
            '<h2>About this page</h2>'
            f'<p>{html.escape(context)}</p>'
            '</section>'
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
    <div class="layout">
      <header>
        <h1>{html.escape(title)}</h1>
        <p class="subhead">{html.escape(subhead)}</p>
      </header>
      <nav>
{nav}
      </nav>
{context_html}
{body}
    </div>
  </body>
</html>
"""


def write(path, content):
    path.write_text(content, encoding="utf-8")


# --- Table helpers ---

URL_COLUMNS = {"source_url", "url"}


def render_cell(key, value):
    """Render a table cell, turning URL columns into clickable links."""
    if key in URL_COLUMNS and value and (value.startswith("http://") or value.startswith("https://")):
        escaped = html.escape(value)
        return f'<td><a href="{escaped}" target="_blank" rel="noopener noreferrer">Link</a></td>'
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
        f'</svg>'
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
        '<section class="card">',
        '<div class="filter-row">',
        f'<label class="filter-item">{html.escape(text_label)}'
        f'<input type="search" data-table="{table_id}" data-filter="search" placeholder="Type to search..." /></label>',
    ]
    for field, label, options in filter_defs:
        opts = '<option value="">All</option>' + "".join(f"<option>{html.escape(o)}</option>" for o in options)
        controls.append(
            f'<label class="filter-item">{html.escape(label)}'
            f'<select data-table="{table_id}" data-filter="{field}">{opts}</select></label>'
        )
    controls.append("</div>")
    controls.append(f'<p class="small" data-filter-count-for="{table_id}"></p>')
    controls.append("</section>")
    return "".join(controls)


def render_filterable_table(rows, columns, table_id, data_fields):
    head = "".join(f"<th>{html.escape(label)}</th>" for _, label in columns)
    body_rows = []
    for row in rows:
        attrs = " ".join(
            f'data-{f}="{html.escape((row.get(f, "") or "").strip().lower())}"' for f in data_fields
        )
        cells = "".join(render_cell(k, row.get(k, "") or "") for k, _ in columns)
        body_rows.append(f"<tr {attrs}>{cells}</tr>")
    return (
        f'<section class="card"><table id="{table_id}"><thead><tr>'
        + head
        + "</tr></thead><tbody>"
        + "".join(body_rows)
        + "</tbody></table></section>"
    )


def render_filter_script(table_id, fields):
    fjs = ",".join(f'"{f}"' for f in fields)
    return f"""
<script>
(function() {{
  var table = document.getElementById('{table_id}');
  if (!table) return;
  var rows = Array.from(table.querySelectorAll('tbody tr'));
  var controls = Array.from(document.querySelectorAll('[data-table="{table_id}"]'));
  var countEl = document.querySelector('[data-filter-count-for="{table_id}"]');
  var fields = [{fjs}];
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
  }}
  controls.forEach(function(c) {{ c.addEventListener('input', update); c.addEventListener('change', update); }});
  update();
}})();
</script>
"""


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


# --- Exports ---

def write_exports(datasets):
    EXPORTS.mkdir(parents=True, exist_ok=True)
    for name, rows in datasets.items():
        # CSV
        if rows:
            csv_path = EXPORTS / f"{name}.csv"
            with csv_path.open("w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=rows[0].keys())
                w.writeheader()
                w.writerows(rows)
            # JSON
            json_path = EXPORTS / f"{name}.json"
            json_path.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")


def write_exports_manifest(datasets):
    EXPORTS.mkdir(parents=True, exist_ok=True)
    generated = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    items = []
    for name, rows in datasets.items():
        encoded = json.dumps(rows, sort_keys=True, ensure_ascii=False).encode("utf-8")
        digest = hashlib.sha256(encoded).hexdigest()
        fields = list(rows[0].keys()) if rows else []
        items.append({
            "dataset": name,
            "row_count": len(rows),
            "fields": fields,
            "content_sha256": digest,
            "csv_path": f"exports/{name}.csv",
            "json_path": f"exports/{name}.json",
        })
    manifest = {
        "version": BUILD_VERSION,
        "generated_at": generated,
        "dataset_count": len(items),
        "datasets": sorted(items, key=lambda x: x["dataset"]),
    }
    (EXPORTS / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


# --- Page builders ---

def build_index():
    health_rows, health_counts = compute_data_health()
    body = """
      <section class="card">
        <h2>Current Phase</h2>
        <p>Phase 6 — trust, monitoring, and decision readiness with drift checks and data health reporting.</p>
      </section>
      <section class="grid">
        <article class="card">
          <h3>Goal</h3>
          <p>Build a coherent cross-level planning framework that is faster, clearer, and more predictable.</p>
        </article>
        <article class="card">
          <h3>Outputs</h3>
          <ul>
            <li>Legal and policy inventory</li>
            <li>Plan hierarchy mapping</li>
            <li>Contradiction register with weighted scoring</li>
            <li>Actionable reform package with evidence traces</li>
            <li>Machine-readable exports (CSV/JSON)</li>
          </ul>
        </article>
        <article class="card">
          <h3>Delivery Horizon</h3>
          <p>Pilot Release for policy-professional audience. Static website on GitHub Pages.</p>
        </article>
      </section>
      <section class="card">
        <h2>Audience Views</h2>
        <ul>
          <li><a href="audience-policymakers.html">For Policy Makers</a></li>
          <li><a href="audience-lpas.html">For LPAs</a></li>
          <li><a href="audience-developers.html">For Developers</a></li>
          <li><a href="audience-public.html">For the Public</a></li>
        </ul>
      </section>
      <section class="card">
        <h2>Data Exports</h2>
        <p>Download machine-readable datasets: <a href="exports/">CSV and JSON exports</a>.</p>
      </section>
    """
    body += '<section class="card"><h2>Data Health Snapshot</h2>'
    body += '<p>'
    body += f'{badge("fresh", "green")} {health_counts.get("fresh", 0)} '
    body += f'{badge("stale", "amber")} {health_counts.get("stale", 0)} '
    body += f'{badge("critical", "red")} {health_counts.get("critical", 0)} '
    body += '</p>'
    if health_rows:
        top = sorted(health_rows, key=lambda r: (r["age_days"] if isinstance(r["age_days"], int) else 9999), reverse=True)[0]
        body += f'<p class="small">Oldest monitored dataset: {html.escape(top["dataset"])} ({html.escape(str(top["age_days"]))} days).</p>'
    body += '<p><a href="data-health.html">Open full data health report</a></p></section>'
    write(SITE / "index.html", page(
        "UK Planning System Analysis — England Pilot Release",
        "Citation-backed analysis of legislation, policy, and local plan layers with reform proposals.",
        "index", body,
        "Start here to understand what this pilot covers, who it is for, and which pages contain the detailed evidence and recommendations."))


def build_legislation():
    rows = read_csv(ROOT / "data/legislation/england-core-legislation.csv")
    policy_rows = read_csv(ROOT / "data/policy/england-national-policy.csv")
    body = render_table(rows, [
        ("title", "Instrument"), ("type", "Type"), ("status", "Status"),
        ("decision_weight", "Decision Weight"), ("citation", "Citation"),
        ("source_url", "Source"),
    ])
    body += '\n<section class="card"><h2>National Policy and Guidance Index</h2></section>'
    body += render_table(policy_rows, [
        ("title", "Policy or Guidance"), ("type", "Type"), ("authority", "Owner"),
        ("status", "Status"), ("scope", "Scope"), ("source_url", "Source"),
    ])
    write(SITE / "legislation.html", page(
        "Legislation and Regulations Library",
        "England-first inventory of acts, regulations, and national policy.",
        "legislation", body,
        "Use this page to trace the legal and policy instruments that shape planning decisions, including status, ownership, and source links."))


def build_plans():
    rows = read_csv(ROOT / "data/plans/pilot-lpas.csv")
    docs = read_csv(ROOT / "data/plans/pilot-plan-documents.csv")
    quality_rows = read_csv(ROOT / "data/plans/lpa-data-quality.csv")
    quality_by_id = {r["pilot_id"]: r for r in quality_rows}
    docs_by_lpa = defaultdict(list)
    for item in docs:
        docs_by_lpa[item["pilot_id"]].append(item)

    body = '<section class="card"><ul>'
    for level in ["National", "Regional/sub-regional", "County", "District/unitary", "Neighbourhood", "Sector overlays"]:
        body += f"<li>{html.escape(level)}</li>"
    body += "</ul></section>"

    body += '<section class="card"><table><thead><tr><th>Authority</th><th>Type</th><th>Region</th><th>Growth</th><th>Constraints</th><th>Data Quality</th><th>Profile</th></tr></thead><tbody>'
    for row in rows:
        lpa_page = f"plans-{row['pilot_id'].lower()}.html"
        quality = quality_by_id.get(row["pilot_id"], {})
        body += "<tr>"
        for k in ["lpa_name", "lpa_type", "region", "growth_context", "constraint_profile"]:
            body += f"<td>{html.escape(row.get(k, ''))}</td>"
        body += f"<td>{html.escape(quality.get('data_quality_tier', ''))}</td>"
        body += f'<td><a href="{lpa_page}">View</a></td></tr>'
    body += "</tbody></table></section>"

    write(SITE / "plans.html", page(
        "Plan Hierarchy Explorer",
        "Mapped planning stack from national policy to neighbourhood plans and overlays.",
        "plans", body,
        "This page shows which authorities are in scope and how their planning documents align across national, local, and neighbourhood levels."))

    for row in rows:
        lpa_docs = docs_by_lpa.get(row["pilot_id"], [])
        pb = '<section class="card">'
        pb += f"<h2>{html.escape(row.get('lpa_name', ''))}</h2>"
        pb += f"<p><strong>Type:</strong> {html.escape(row.get('lpa_type', ''))}</p>"
        pb += f"<p><strong>Region:</strong> {html.escape(row.get('region', ''))}</p>"
        pb += f"<p><strong>Rationale:</strong> {html.escape(row.get('selection_rationale', ''))}</p>"
        pb += f"<p><strong>Constraints:</strong> {html.escape(row.get('constraint_profile', ''))}</p>"
        if row["pilot_id"] in quality_by_id:
            q = quality_by_id[row["pilot_id"]]
            pb += f"<p><strong>Data quality tier:</strong> {html.escape(q.get('data_quality_tier', ''))} (coverage score {html.escape(q.get('coverage_score', ''))})</p>"
            pb += f"<p><strong>Evidence mix:</strong> {html.escape(q.get('evidence_type_mix', ''))}</p>"
        pb += '<p><a href="plans.html">Back to pilot overview</a></p></section>'
        pb += render_plan_docs_table(lpa_docs)
        write(SITE / f"plans-{row['pilot_id'].lower()}.html", page(
            f"{row['lpa_name']} Plan Profile",
            "Pilot authority planning document stack.",
            "plans", pb,
            "This authority profile summarises planning context, evidence quality, and tracked plan documents for the selected LPA."))


def build_contradictions(weights):
    rows = read_csv(ROOT / "data/issues/contradiction-register.csv")
    for row in rows:
        row["weighted_score"] = str(weighted_score(row, weights))

    columns = [
        ("issue_id", "Issue"), ("scope", "Scope"), ("issue_type", "Type"),
        ("affected_pathway", "Pathway"), ("weighted_score", "Weighted Score"),
        ("severity_score", "Severity"), ("delay_impact_score", "Delay"),
        ("verification_state", "Status"), ("confidence", "Confidence"),
        ("summary", "Summary"),
    ]

    issue_count = len(rows)
    avg_ws = sum(float(r["weighted_score"]) for r in rows) / issue_count if issue_count else 0
    counts_by_type = defaultdict(int)
    for row in rows:
        counts_by_type[row.get("issue_type", "")] += 1

    body = '<section class="card"><h2>Scoring Model</h2><p>Weighted scores use explicit weights: '
    body += ", ".join(f"{dim} ({spec['weight']*100:.0f}%)" for dim, spec in weights.items())
    body += ".</p></section>"

    body += '<section class="grid">'
    body += f'<article class="card"><h3>Total Issues</h3><p>{issue_count}</p></article>'
    body += f'<article class="card"><h3>Average Weighted Score</h3><p>{avg_ws:.2f} / 5</p></article>'
    body += "</section>"

    body += '<section class="card"><h3>Issue Type Breakdown</h3><ul>'
    for t, c in sorted(counts_by_type.items()):
        body += f"<li>{html.escape(t)}: {c}</li>"
    body += "</ul></section>"

    issue_types = sorted({r.get("issue_type", "") for r in rows if r.get("issue_type")})
    pathways = sorted({r.get("affected_pathway", "") for r in rows if r.get("affected_pathway")})
    scopes = sorted({r.get("scope", "") for r in rows if r.get("scope")})
    body += render_filter_controls("issues-table", "Search issues", [
        ("issue_type", "Type", issue_types), ("affected_pathway", "Pathway", pathways), ("scope", "Scope", scopes)])
    body += render_filterable_table(rows, columns, "issues-table",
        ["issue_id", "scope", "issue_type", "affected_pathway", "summary", "confidence", "verification_state"])
    body += render_filter_script("issues-table",
        ["issue_id", "scope", "issue_type", "affected_pathway", "summary", "confidence", "verification_state"])

    write(SITE / "contradictions.html", page(
        "Contradictions and Bottlenecks",
        "Cross-layer conflicts scored with explicit weighting and confidence levels.",
        "contradictions", body,
        "Review the highest-friction conflicts in the planning system, with weighted scores and filters to focus on specific pathways or issue types."))


def build_recommendations(weights):
    rows = read_csv(ROOT / "data/issues/recommendations.csv")
    evidence = read_csv(ROOT / "data/evidence/recommendation_evidence_links.csv")
    ev_by_rec = defaultdict(list)
    for e in evidence:
        ev_by_rec[e["recommendation_id"]].append(e)

    columns = [
        ("recommendation_id", "ID"), ("priority", "Priority"), ("time_horizon", "Horizon"),
        ("policy_goal", "Goal"), ("title", "Recommendation"), ("implementation_vehicle", "Vehicle"),
        ("kpi_primary", "KPI"), ("target", "Target"),
        ("verification_state", "Status"), ("confidence", "Confidence"),
    ]
    priorities = sorted({r.get("priority", "") for r in rows if r.get("priority")})
    horizons = sorted({r.get("time_horizon", "") for r in rows if r.get("time_horizon")})

    body = render_filter_controls("recs-table", "Search recommendations", [
        ("priority", "Priority", priorities), ("time_horizon", "Horizon", horizons)])
    body += render_filterable_table(rows, columns, "recs-table",
        ["recommendation_id", "priority", "time_horizon", "policy_goal", "title",
         "implementation_vehicle", "confidence", "verification_state"])
    body += render_filter_script("recs-table",
        ["recommendation_id", "priority", "time_horizon", "policy_goal", "title",
         "implementation_vehicle", "confidence", "verification_state"])

    # Evidence traces
    body += '<section class="card"><h2>Evidence Traces</h2>'
    body += "<p>Each recommendation is linked to at least one official dataset row.</p></section>"
    for row in rows:
        rid = row["recommendation_id"]
        evs = ev_by_rec.get(rid, [])
        body += f'<section class="card"><h3>{html.escape(rid)}: {html.escape(row["title"])}</h3>'
        body += f'<p>{confidence_badge(row.get("confidence", ""))} {verification_badge(row.get("verification_state", ""))}</p>'
        if evs:
            body += "<table><thead><tr><th>Source</th><th>Metric</th><th>Baseline</th><th>Window</th><th>Link</th></tr></thead><tbody>"
            for e in evs:
                src_link = html.escape(e.get("source_url", ""))
                body += "<tr>"
                body += f"<td>{html.escape(e.get('source_dataset', ''))}</td>"
                body += f"<td>{html.escape(e.get('metric_name', ''))}</td>"
                body += f"<td>{html.escape(e.get('baseline_value', ''))}</td>"
                body += f"<td>{html.escape(e.get('baseline_window', ''))}</td>"
                body += f'<td><a href="{src_link}">Source</a></td></tr>'
            body += "</tbody></table>"
        else:
            body += "<p><em>No evidence links yet.</em></p>"
        body += "</section>"

    write(SITE / "recommendations.html", page(
        "Recommendations and Model Text",
        "Actionable reforms with evidence traces, confidence, and verification state.",
        "recommendations", body,
        "Each recommendation includes delivery details, expected outcomes, and direct links to supporting evidence rows."))


def build_roadmap():
    milestones = read_csv(ROOT / "data/issues/implementation-roadmap.csv")
    recs = read_csv(ROOT / "data/issues/recommendations.csv")
    quick = [m for m in milestones if m.get("phase") == "Quick Wins"]
    structural = [m for m in milestones if m.get("phase") == "Statutory and Structural"]

    body = '<section class="grid">'
    body += '<article class="card"><h3>Quick Wins (0-12 months)</h3><p>Guidance and process changes.</p></article>'
    body += '<article class="card"><h3>Statutory and Structural (12-24+ months)</h3><p>SI/legislative pathways.</p></article>'
    body += "</section>"
    body += '<section class="card"><h2>Quick Wins</h2></section>'
    body += render_table(quick, [("window", "Window"), ("action", "Action"), ("owner", "Owner"),
        ("linked_recommendations", "Recs"), ("status_metric", "Metric")])
    body += '<section class="card"><h2>Statutory and Structural</h2></section>'
    body += render_table(structural, [("window", "Window"), ("action", "Action"), ("owner", "Owner"),
        ("dependencies", "Dependencies"), ("linked_recommendations", "Recs")])
    body += '<section class="card"><h2>Recommendation to Horizon</h2></section>'
    body += render_table(recs, [("recommendation_id", "Rec"), ("title", "Title"),
        ("time_horizon", "Horizon"), ("delivery_owner", "Owner"), ("implementation_vehicle", "Vehicle")])

    write(SITE / "roadmap.html", page(
        "Implementation Roadmap",
        "Delivery sequence from quick wins to statutory reform.",
        "roadmap", body,
        "This timeline shows how reforms can be phased, who leads delivery, and which dependencies affect sequencing."))


def build_baselines():
    rows = read_csv(ROOT / "data/evidence/official_baseline_metrics.csv")
    body = '<section class="card"><p>Official baseline metrics from GOV.UK planning statistics and PINS casework data. Window: latest 4 quarters.</p></section>'
    body += render_table(rows, [
        ("metric_id", "ID"), ("metric_name", "Metric"), ("source_table", "Source"),
        ("geography", "Geography"), ("pathway", "Pathway"), ("value", "Value"),
        ("unit", "Unit"), ("period", "Period"),
    ])
    write(SITE / "baselines.html", page(
        "Official Baseline Metrics",
        "KPI baselines from GOV.UK planning statistics and Planning Inspectorate data.",
        "baselines", body,
        "Use these baseline metrics to understand current performance levels before assessing the impact of proposed reforms."))


def build_bottlenecks():
    rows = read_csv(ROOT / "data/issues/bottleneck-heatmap.csv")
    stages = ["Pre-application", "Validation", "Consultation", "Committee", "Legal Agreements", "Condition Discharge"]
    pathways = ["Housing", "Commercial", "Infrastructure", "Mixed"]

    # Summary stats
    total_delay = sum(float(r.get("median_delay_weeks", 0) or 0) for r in rows)
    worst = max(rows, key=lambda r: float(r.get("median_delay_weeks", 0) or 0)) if rows else {}

    body = '<section class="card"><h2>Process Stage Overview</h2>'
    body += "<p>Bottleneck analysis covering all six planning process stages across housing, commercial, and infrastructure pathways. Median delay figures are indicative based on official statistics and pilot LPA evidence.</p></section>"

    body += '<section class="grid">'
    body += f'<article class="card"><h3>Bottlenecks Identified</h3><p>{len(rows)}</p></article>'
    body += f'<article class="card"><h3>Cumulative Delay (weeks, all stages)</h3><p>{total_delay:.0f} weeks</p></article>'
    if worst:
        body += f'<article class="card"><h3>Worst Single Bottleneck</h3><p>{html.escape(worst.get("process_stage",""))} — {html.escape(worst.get("pathway",""))} ({worst.get("median_delay_weeks","")} weeks)</p></article>'
    body += "</section>"

    # Heatmap table: stages as rows, pathways as columns
    body += '<section class="card"><h2>Delay Heatmap (median weeks by stage and pathway)</h2>'
    body += "<table><thead><tr><th>Stage</th>"
    for pw in pathways:
        body += f"<th>{html.escape(pw)}</th>"
    body += "</tr></thead><tbody>"

    by_stage_pathway = {}
    for r in rows:
        key = (r.get("process_stage", ""), r.get("pathway", ""))
        by_stage_pathway[key] = r

    for stage in stages:
        body += f"<tr><td><strong>{html.escape(stage)}</strong></td>"
        for pw in pathways:
            entry = by_stage_pathway.get((stage, pw))
            if entry:
                weeks = float(entry.get("median_delay_weeks", 0) or 0)
                sev = entry.get("severity", "Low")
                css = {"High": "badge-red", "Medium": "badge-amber", "Low": "badge-green"}.get(sev, "badge-grey")
                body += f'<td><span class="badge {css}">{weeks:.0f}w</span></td>'
            else:
                body += "<td>—</td>"
        body += "</tr>"
    body += "</tbody></table></section>"

    # Detail table
    columns = [
        ("stage_id", "ID"), ("process_stage", "Stage"), ("pathway", "Pathway"),
        ("median_delay_weeks", "Median Delay (weeks)"), ("frequency", "Frequency"),
        ("severity", "Severity"), ("delay_driver", "Driver"), ("linked_issues", "Issues"),
    ]
    body += '<section class="card"><h2>Bottleneck Detail</h2></section>'
    body += render_table(rows, columns)

    write(SITE / "bottlenecks.html", page(
        "Bottleneck Heatmap",
        "Process delay analysis across all six planning stages with severity and pathway breakdown.",
        "bottlenecks", body,
        "This heatmap highlights where delays concentrate in the planning process and which pathways are most affected."))


# --- Audience views ---

def build_audience_policymakers():
    recs = read_csv(ROOT / "data/issues/recommendations.csv")
    issues = read_csv(ROOT / "data/issues/contradiction-register.csv")
    body = '<section class="card"><h2>Priority Reform Actions</h2>'
    body += "<p>Recommendations ranked by priority with delivery ownership and implementation vehicle.</p></section>"
    body += render_table(recs, [
        ("recommendation_id", "ID"), ("priority", "Priority"), ("title", "Recommendation"),
        ("delivery_owner", "Owner"), ("implementation_vehicle", "Vehicle"),
        ("time_horizon", "Horizon"), ("confidence", "Confidence"),
    ])
    body += '<section class="card"><h2>System Friction Summary</h2>'
    body += "<p>Top contradictions requiring policy intervention.</p></section>"
    body += render_table(issues, [
        ("issue_id", "Issue"), ("issue_type", "Type"), ("scope", "Scope"),
        ("summary", "Summary"), ("confidence", "Confidence"),
    ])
    write(SITE / "audience-policymakers.html", page(
        "For Policy Makers",
        "Priority reforms, system friction, and implementation pathways.",
        "policymakers", body,
        "A policy-focused view of priority reforms, core friction points, and delivery routes for national and local action."))


def build_audience_lpas():
    recs = read_csv(ROOT / "data/issues/recommendations.csv")
    lpa_recs = [r for r in recs if "LPA" in r.get("delivery_owner", "")]
    body = '<section class="card"><h2>Actions for Local Planning Authorities</h2>'
    body += "<p>Recommendations where LPAs are lead or co-delivery owners.</p></section>"
    body += render_table(lpa_recs if lpa_recs else recs, [
        ("recommendation_id", "ID"), ("title", "Recommendation"),
        ("time_horizon", "Horizon"), ("kpi_primary", "KPI"), ("target", "Target"),
    ])
    baselines = read_csv(ROOT / "data/evidence/official_baseline_metrics.csv")
    pilot_baselines = [b for b in baselines if b.get("geography", "").startswith("LPA")]
    if pilot_baselines:
        body += '<section class="card"><h2>Pilot LPA Baselines</h2></section>'
        body += render_table(pilot_baselines, [
            ("metric_id", "ID"), ("metric_name", "Metric"), ("geography", "Authority"),
            ("value", "Value"), ("unit", "Unit"),
        ])
    write(SITE / "audience-lpas.html", page(
        "For Local Planning Authorities",
        "LPA-specific actions, baselines, and KPI targets.",
        "lpas", body,
        "An operational view for LPAs showing actionable recommendations, local baselines, and measurable KPI targets."))


def build_audience_developers():
    recs = read_csv(ROOT / "data/issues/recommendations.csv")
    body = '<section class="card"><h2>What This Means for Developers</h2>'
    body += "<p>Reforms that affect submission requirements, determination timelines, and design baseline certainty.</p></section>"
    body += '<section class="card"><h3>Key Impacts</h3><ul>'
    body += "<li><strong>Validation standardisation</strong> reduces rework and front-end delay.</li>"
    body += "<li><strong>Precedence clarification</strong> increases decision predictability for housing schemes.</li>"
    body += "<li><strong>Coordinated evidence gateway</strong> reduces duplication for EIA/habitats-affected infrastructure.</li>"
    body += "<li><strong>Design code baselines</strong> provide measurable compliance checklist at submission.</li>"
    body += "</ul></section>"
    body += render_table(recs, [
        ("recommendation_id", "ID"), ("title", "Recommendation"),
        ("time_horizon", "Timeline"), ("kpi_primary", "KPI"), ("target", "Target"),
    ])
    write(SITE / "audience-developers.html", page(
        "For Developers",
        "How proposed reforms affect submission, timelines, and design certainty.",
        "developers", body,
        "A delivery-focused summary of reforms that affect application requirements, decision predictability, and project timelines."))


def build_audience_public():
    body = '<section class="card"><h2>What Is This Project?</h2>'
    body += "<p>This project analyses England's planning system to find where laws and policies conflict, "
    body += "cause unnecessary delays, or create confusion. It then proposes practical improvements.</p></section>"
    body += '<section class="card"><h2>Why It Matters</h2>'
    body += "<p>Planning decisions affect housing availability, infrastructure delivery, environmental protection, "
    body += "and local character. A clearer, faster system benefits everyone.</p></section>"
    body += '<section class="card"><h2>What We Found</h2><ul>'
    body += "<li>Validation requirements vary between councils, causing repeated submissions.</li>"
    body += "<li>National and local policies sometimes conflict, leading to unpredictable decisions.</li>"
    body += "<li>Environmental checks can duplicate across different legal regimes.</li>"
    body += "<li>Design standards are often vague, making it hard for applicants and communities to know what to expect.</li>"
    body += "</ul></section>"
    body += '<section class="card"><h2>What We Recommend</h2><ul>'
    body += "<li>Standardise submission requirements nationally.</li>"
    body += "<li>Clarify which policy takes precedence when they conflict.</li>"
    body += "<li>Create a single evidence gateway for environmental assessments.</li>"
    body += "<li>Introduce measurable design checklists so communities know what to expect.</li>"
    body += "</ul></section>"
    body += '<section class="card"><p>For full details, see the <a href="recommendations.html">Recommendations</a> and <a href="methodology.html">Methodology</a> pages.</p></section>'
    write(SITE / "audience-public.html", page(
        "For the Public",
        "Plain-language summary of findings and proposed planning improvements.",
        "public", body,
        "A plain-language explanation of the problems identified, why they matter, and what changes are being proposed."))


def build_methodology():
    body = '<section class="card"><h2>Evidence Standard</h2>'
    body += "<p>Every recommendation references at least one official dataset row from GOV.UK planning statistics or PINS casework data.</p></section>"
    body += '<section class="card"><h2>Scoring Model</h2>'
    body += "<p>Issues scored on five dimensions with explicit weights. See <code>data/schemas/scoring.json</code>.</p></section>"
    body += '<section class="card"><h2>Verification States</h2>'
    body += "<p>Records carry a verification state: <strong>draft</strong>, <strong>verified</strong>, or <strong>legal-reviewed</strong>.</p></section>"
    body += '<section class="card"><h2>Confidence Levels</h2>'
    body += "<p>Findings carry confidence labels: <strong>high</strong>, <strong>medium</strong>, or <strong>low</strong>.</p></section>"
    body += '<section class="card"><h2>Validation</h2>'
    body += "<p>Schema, FK, enum, and unique-ID checks run via <code>scripts/validate_data.py</code>. "
    body += "Internal links checked via <code>scripts/check_links.py</code>.</p></section>"
    write(SITE / "methodology.html", page(
        "Methodology",
        "Taxonomy, scoring model, evidence standards, and quality controls.",
        "methodology", body,
        "This page explains how datasets are scored, validated, and linked to evidence so findings are transparent and reproducible."))


def build_sources():
    evidence = read_csv(ROOT / "data/evidence/recommendation_evidence_links.csv")
    baselines = read_csv(ROOT / "data/evidence/official_baseline_metrics.csv")
    body = '<section class="card"><h2>Evidence Links</h2></section>'
    body += render_table(evidence, [
        ("link_id", "ID"), ("recommendation_id", "Rec"), ("source_dataset", "Source"),
        ("metric_name", "Metric"), ("baseline_value", "Baseline"), ("source_url", "URL"),
    ])
    body += '<section class="card"><h2>Official Baseline Metrics</h2></section>'
    body += render_table(baselines, [
        ("metric_id", "ID"), ("metric_name", "Metric"), ("source_table", "Table"),
        ("geography", "Geography"), ("value", "Value"), ("source_url", "URL"),
    ])
    write(SITE / "sources.html", page(
        "Sources and Citations",
        "Official data sources, evidence links, and baseline metrics.",
        "sources", body,
        "Use this reference page to verify evidence links, source tables, and citations used throughout the analysis."))


def build_exports_index():
    body = '<section class="card"><h2>Machine-Readable Exports</h2>'
    body += "<p>All core datasets are available in CSV and JSON format for external analysis.</p>"
    body += "<ul>"
    for name in ["contradiction-register", "recommendations", "recommendation_evidence_links",
                  "official_baseline_metrics", "implementation-roadmap", "bottleneck-heatmap",
                  "appeal-decisions", "lpa-data-quality", "lpa-quarterly-trends",
                  "lpa-issue-incidence"]:
        body += f'<li><a href="exports/{name}.csv">{name}.csv</a> | <a href="exports/{name}.json">{name}.json</a></li>'
    body += "</ul></section>"
    body += '<section class="card"><h2>Version Manifest</h2>'
    body += '<p>Build manifest includes dataset hashes, row counts, and generation timestamp.</p>'
    body += '<p><a href="exports/manifest.json">manifest.json</a></p></section>'
    write(SITE / "exports.html", page(
        "Data Exports",
        "Download datasets in CSV and JSON format.",
        "index", body,
        "Download the core datasets in machine-readable form for external analysis, QA checks, or reuse in other tools."))


def build_appeals():
    rows = read_csv(ROOT / "data/evidence/appeal-decisions.csv")
    issues = read_csv(ROOT / "data/issues/contradiction-register.csv")
    issue_map = {r["issue_id"]: r["summary"] for r in issues}

    body = '<section class="card"><p>Appeal decisions cited as evidence for identified contradictions and bottlenecks. References are illustrative examples drawn from Planning Inspectorate decision records.</p></section>'

    outcomes = sorted({r.get("outcome", "") for r in rows if r.get("outcome")})
    linked = sorted({r.get("linked_issue", "") for r in rows if r.get("linked_issue")})
    body += render_filter_controls("appeals-table", "Search appeals", [
        ("outcome", "Outcome", outcomes),
        ("linked_issue", "Linked Issue", linked),
    ])

    columns = [
        ("appeal_id", "ID"), ("pins_reference", "PINS Reference"), ("appeal_type", "Type"),
        ("lpa", "LPA"), ("decision_date", "Date"), ("outcome", "Outcome"),
        ("linked_issue", "Issue"), ("policy_cited", "Policy"), ("inspector_finding", "Inspector Finding"),
        ("source_url", "Source"),
    ]
    body += render_filterable_table(rows, columns, "appeals-table",
        ["appeal_id", "lpa", "outcome", "linked_issue", "policy_cited", "inspector_finding"])
    body += render_filter_script("appeals-table",
        ["appeal_id", "lpa", "outcome", "linked_issue", "policy_cited", "inspector_finding"])

    # Issue linkage panel
    body += '<section class="card"><h2>Issue to Appeal Cross-Reference</h2><table><thead><tr><th>Issue</th><th>Summary</th><th>Appeals</th></tr></thead><tbody>'
    linked_by_issue = defaultdict(list)
    for r in rows:
        linked_by_issue[r.get("linked_issue", "")].append(r["appeal_id"])
    for issue_id, appeal_ids in sorted(linked_by_issue.items()):
        summary = html.escape(issue_map.get(issue_id, ""))
        apps = html.escape(", ".join(appeal_ids))
        body += f"<tr><td>{html.escape(issue_id)}</td><td>{summary}</td><td>{apps}</td></tr>"
    body += "</tbody></table></section>"

    write(SITE / "appeals.html", page(
        "Appeal Decision Evidence",
        "Planning Inspectorate decisions cited as evidence for identified contradictions.",
        "appeals", body,
        "This page links appeal outcomes to specific contradiction records so users can inspect real-world decision evidence."))


def build_map():
    lpas = read_csv(ROOT / "data/plans/pilot-lpas.csv")
    geo = read_csv(ROOT / "data/plans/lpa-geo.csv")
    baselines = read_csv(ROOT / "data/evidence/official_baseline_metrics.csv")
    quality_rows = read_csv(ROOT / "data/plans/lpa-data-quality.csv")

    # Build speed lookup by pilot_id
    speed_by_lpa = {}
    for b in baselines:
        geo_field = b.get("geography", "")
        if geo_field.startswith("LPA-"):
            pid = geo_field.split(" ")[0]
            try:
                speed_by_lpa[pid] = float(b.get("value", 0) or 0)
            except ValueError:
                pass

    geo_by_id = {r["pilot_id"]: r for r in geo}
    lpa_by_id = {r["pilot_id"]: r for r in lpas}
    quality_by_id = {r["pilot_id"]: r for r in quality_rows}

    features = []
    for pid, g in geo_by_id.items():
        lpa = lpa_by_id.get(pid, {})
        speed = speed_by_lpa.get(pid)
        cohort = cohort_for_pid(pid)
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [float(g["lng"]), float(g["lat"])]},
            "properties": {
                "id": pid,
                "name": lpa.get("lpa_name", ""),
                "type": lpa.get("lpa_type", ""),
                "region": lpa.get("region", ""),
                "growth": lpa.get("growth_context", ""),
                "constraints": lpa.get("constraint_profile", ""),
                "speed": speed,
                "quality_tier": quality_by_id.get(pid, {}).get("data_quality_tier", ""),
                "coverage_score": quality_by_id.get(pid, {}).get("coverage_score", ""),
                "cohort": cohort,
                "page": f"plans-{pid.lower()}.html"
            }
        })

    geojson = json.dumps({"type": "FeatureCollection", "features": features}, indent=2)

    body = f"""
      <section class="card">
        <p>All {len(features)} LPAs in scope. Circle colour indicates speed of major decisions (green = above England average 74%, amber = 65-74%, red = below 65%). Click a marker for the LPA profile.</p>
      </section>
      <div id="map" style="height:560px;border-radius:14px;border:1px solid var(--line);"></div>
      <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
      <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
      <script>
      (function() {{
        var map = L.map('map').setView([52.5, -1.5], 6);
        L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
          attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
          maxZoom: 13
        }}).addTo(map);

        var data = {geojson};

        function speedColor(speed) {{
          if (speed == null) return '#aaa';
          if (speed >= 74) return '#22a355';
          if (speed >= 65) return '#f59e0b';
          return '#ef4444';
        }}

        data.features.forEach(function(f) {{
          var p = f.properties;
          var coords = f.geometry.coordinates;
          var color = speedColor(p.speed);
          var circle = L.circleMarker([coords[1], coords[0]], {{
            radius: 10,
            fillColor: color,
            color: '#fff',
            weight: 2,
            opacity: 1,
            fillOpacity: 0.85
          }}).addTo(map);

          var speedText = p.speed != null ? p.speed + '% major decisions in time' : 'No data';
          var qualityText = p.quality_tier ? ('Quality tier ' + p.quality_tier + ' (score ' + p.coverage_score + ')') : 'Quality tier n/a';
          circle.bindPopup(
            '<strong><a href="' + p.page + '">' + p.name + '</a></strong>' +
            '<br>' + p.type + ' — ' + p.region +
            '<br><em>' + p.cohort + '</em>' +
            '<br>' + speedText +
            '<br>' + qualityText +
            '<br><small>' + p.constraints + '</small>'
          );
        }});

        // Legend
        var legend = L.control({{position: 'bottomright'}});
        legend.onAdd = function() {{
          var d = L.DomUtil.create('div', 'info legend');
          d.style.background = '#fff';
          d.style.padding = '8px 12px';
          d.style.borderRadius = '8px';
          d.style.border = '1px solid #ccc';
          d.innerHTML =
            '<strong>Decision speed</strong><br>' +
            '<span style="color:#22a355">●</span> ≥74% (above average)<br>' +
            '<span style="color:#f59e0b">●</span> 65–73%<br>' +
            '<span style="color:#ef4444">●</span> <65% (below average)<br>' +
            '<span style="color:#aaa">●</span> No data';
          return d;
        }};
        legend.addTo(map);
      }})();
      </script>
"""
    write(SITE / "map.html", page(
        "LPA Map",
        "All authorities in scope with major decision speed and profile links.",
        "map", body,
        "Explore authorities geographically, compare performance at a glance, and open individual LPA profile pages from map markers."))


def build_compare():
    lpas = read_csv(ROOT / "data/plans/pilot-lpas.csv")
    docs = read_csv(ROOT / "data/plans/pilot-plan-documents.csv")
    baselines = read_csv(ROOT / "data/evidence/official_baseline_metrics.csv")
    quality_rows = read_csv(ROOT / "data/plans/lpa-data-quality.csv")

    docs_count = defaultdict(int)
    for d in docs:
        docs_count[d["pilot_id"]] += 1

    speed_by_id = {}
    for b in baselines:
        geo_field = b.get("geography", "")
        if geo_field.startswith("LPA-"):
            pid = geo_field.split(" ")[0]
            speed_by_id[pid] = b.get("value", "")

    quality_by_id = {r["pilot_id"]: r for r in quality_rows}

    records = []
    for lpa in lpas:
        pid = lpa["pilot_id"]
        q = quality_by_id.get(pid, {})
        records.append({
            "id": pid,
            "name": lpa.get("lpa_name", ""),
            "type": lpa.get("lpa_type", ""),
            "region": lpa.get("region", ""),
            "growth": lpa.get("growth_context", ""),
            "constraints": lpa.get("constraint_profile", ""),
            "documents": docs_count.get(pid, 0),
            "speed": speed_by_id.get(pid, "n/a"),
            "quality_tier": q.get("data_quality_tier", "n/a"),
            "quality_score": q.get("coverage_score", "n/a"),
            "page": f"plans-{pid.lower()}.html",
        })

    records_json = json.dumps(records, ensure_ascii=False)

    body = """
      <section class="card">
        <p>Select two authorities to compare policy context, evidence quality, and baseline performance metrics. You can also open this page with URL presets such as <code>?a=LPA-01&b=LPA-07</code>.</p>
        <div class="filter-row">
          <label class="filter-item">Authority A<select id="cmp-a"></select></label>
          <label class="filter-item">Authority B<select id="cmp-b"></select></label>
        </div>
        <div class="filter-row" style="margin-top:10px;">
          <button id="cmp-save" type="button">Save preset pair</button>
          <button id="cmp-clear" type="button">Clear saved presets</button>
        </div>
        <p class="small" id="cmp-status"></p>
        <div id="cmp-presets" class="small"></div>
      </section>
      <section class="card" id="compare-output"></section>
      <script>
      (function() {
        var data = __DATA__;
        var aSel = document.getElementById('cmp-a');
        var bSel = document.getElementById('cmp-b');
        var out = document.getElementById('compare-output');
        var saveBtn = document.getElementById('cmp-save');
        var clearBtn = document.getElementById('cmp-clear');
        var presetWrap = document.getElementById('cmp-presets');
        var statusEl = document.getElementById('cmp-status');
        var presetKey = 'uk-planning-compare-presets';

        function mkOption(item) {
          var o = document.createElement('option');
          o.value = item.id;
          o.textContent = item.name + ' (' + item.id + ')';
          return o;
        }

        data.forEach(function(item) {
          aSel.appendChild(mkOption(item));
          bSel.appendChild(mkOption(item));
        });

        var byId = {};
        data.forEach(function(item) { byId[item.id] = true; });
        var params = new URLSearchParams(window.location.search);
        if (!params.get('a') && !params.get('b') && window.location.hash) {
          params = new URLSearchParams(window.location.hash.replace(/^#/, ''));
        }
        var presetA = (params.get('a') || '').toUpperCase();
        var presetB = (params.get('b') || '').toUpperCase();

        if (data.length > 1) {
          aSel.value = data[0].id;
          bSel.value = data[1].id;
        }
        if (presetA && byId[presetA]) aSel.value = presetA;
        if (presetB && byId[presetB]) bSel.value = presetB;
        if (aSel.value === bSel.value && data.length > 1) {
          var fallback = data.find(function(item) { return item.id !== aSel.value; });
          if (fallback) bSel.value = fallback.id;
        }

        function row(label, a, b) {
          return '<tr><th>' + label + '</th><td>' + a + '</td><td>' + b + '</td></tr>';
        }

        function render() {
          var a = data.find(function(x){ return x.id === aSel.value; });
          var b = data.find(function(x){ return x.id === bSel.value; });
          if (!a || !b) return;

          var next = new URL(window.location.href);
          next.searchParams.set('a', a.id);
          next.searchParams.set('b', b.id);
          history.replaceState(null, '', next.pathname + '?' + next.searchParams.toString());

          out.innerHTML =
            '<h2>Comparison</h2>' +
            '<table><thead><tr><th>Metric</th><th>' + a.name + '</th><th>' + b.name + '</th></tr></thead><tbody>' +
            row('Type', a.type, b.type) +
            row('Region', a.region, b.region) +
            row('Growth context', a.growth, b.growth) +
            row('Constraint profile', a.constraints, b.constraints) +
            row('Plan documents tracked', String(a.documents), String(b.documents)) +
            row('Major decision speed (%)', String(a.speed), String(b.speed)) +
            row('Data quality tier', a.quality_tier + ' (' + a.quality_score + ')', b.quality_tier + ' (' + b.quality_score + ')') +
            row('Profile page', '<a href="' + a.page + '">Open</a>', '<a href="' + b.page + '">Open</a>') +
            '</tbody></table>';
        }

        function loadPresets() {
          try {
            return JSON.parse(localStorage.getItem(presetKey) || '[]');
          } catch (e) {
            return [];
          }
        }

        function savePresets(items) {
          localStorage.setItem(presetKey, JSON.stringify(items.slice(0, 8)));
        }

        function renderPresets() {
          var presets = loadPresets();
          if (!presets.length) {
            presetWrap.innerHTML = '<p>No saved presets yet.</p>';
            return;
          }
          var html = '<p>Saved preset pairs:</p><ul>';
          presets.forEach(function(p, idx) {
            html += '<li><a href="#" data-preset-index="' + idx + '">' + p.a + ' vs ' + p.b + '</a></li>';
          });
          html += '</ul>';
          presetWrap.innerHTML = html;
          Array.from(presetWrap.querySelectorAll('[data-preset-index]')).forEach(function(link) {
            link.addEventListener('click', function(evt) {
              evt.preventDefault();
              var preset = presets[Number(link.dataset.presetIndex)];
              if (!preset) return;
              aSel.value = preset.a;
              bSel.value = preset.b;
              render();
            });
          });
        }

        saveBtn.addEventListener('click', function() {
          var a = aSel.value;
          var b = bSel.value;
          if (!a || !b || a === b) return;
          var presets = loadPresets().filter(function(p) { return !(p.a === a && p.b === b); });
          presets.unshift({ a: a, b: b });
          savePresets(presets);
          statusEl.textContent = 'Saved preset: ' + a + ' vs ' + b;
          renderPresets();
        });

        clearBtn.addEventListener('click', function() {
          localStorage.removeItem(presetKey);
          statusEl.textContent = 'Saved presets cleared.';
          renderPresets();
        });

        aSel.addEventListener('change', render);
        bSel.addEventListener('change', render);
        renderPresets();
        render();
      })();
      </script>
""".replace("__DATA__", records_json)

    write(SITE / "compare.html", page(
        "LPA Comparison",
        "Side-by-side comparison of authorities, evidence quality, and baseline performance.",
        "compare", body,
        "Compare two authorities side by side across profile context, tracked plans, decision speed, and evidence quality."))


def build_benchmark():
    lpas = read_csv(ROOT / "data/plans/pilot-lpas.csv")
    quality_rows = read_csv(ROOT / "data/plans/lpa-data-quality.csv")
    issue_rows = read_csv(ROOT / "data/issues/lpa-issue-incidence.csv")
    trend_rows = read_csv(ROOT / "data/evidence/lpa-quarterly-trends.csv")

    quality_by_id = {r["pilot_id"]: r for r in quality_rows}
    issues_by_id = {r["pilot_id"]: r for r in issue_rows}

    trends_by_id = defaultdict(list)
    for r in trend_rows:
        trends_by_id[r["pilot_id"]].append(r)
    for pid in trends_by_id:
        trends_by_id[pid].sort(key=lambda x: x["quarter"])

    # Ranking by latest quarter major_in_time_pct
    bench = []
    for lpa in lpas:
        pid = lpa["pilot_id"]
        trows = trends_by_id.get(pid, [])
        latest_speed = float(trows[-1]["major_in_time_pct"]) if trows else None
        latest_appeal = float(trows[-1]["appeals_overturned_pct"]) if trows else None
        speeds = [float(t["major_in_time_pct"]) for t in trows]
        spark = sparkline_svg(speeds)
        q = quality_by_id.get(pid, {})
        i = issues_by_id.get(pid, {})
        bench.append({
            "pilot_id": pid,
            "lpa_name": lpa.get("lpa_name", ""),
            "lpa_type": lpa.get("lpa_type", ""),
            "cohort": cohort_for_pid(pid),
            "region": lpa.get("region", ""),
            "latest_speed": latest_speed,
            "latest_appeal": latest_appeal,
            "trend_spark": spark,
            "quality_tier": q.get("data_quality_tier", "n/a"),
            "quality_score": q.get("coverage_score", "n/a"),
            "total_issues": i.get("total_linked_issues", "n/a"),
            "high_severity_issues": i.get("high_severity_issues", "n/a"),
            "risk_stage": i.get("primary_risk_stage", "n/a"),
            "speed_delta": (float(trows[-1]["major_in_time_pct"]) - float(trows[0]["major_in_time_pct"])) if len(trows) > 1 else None,
        })

    ranked = [r for r in bench if r["latest_speed"] is not None]
    ranked.sort(key=lambda x: x["latest_speed"], reverse=True)
    n = len(ranked)
    for idx, r in enumerate(ranked, start=1):
        pct = 100.0 * (n - idx) / max(1, (n - 1))
        if pct >= 66:
            band = "Top third"
        elif pct >= 33:
            band = "Middle third"
        else:
            band = "Bottom third"
        r["rank"] = idx
        r["percentile"] = round(pct, 1)
        r["band"] = band

    # Add rank info back
    rank_by_id = {r["pilot_id"]: r for r in ranked}
    speeds = [r["latest_speed"] for r in ranked]
    mean_speed = (sum(speeds) / len(speeds)) if speeds else 0.0
    std_speed = (((sum((s - mean_speed) ** 2 for s in speeds) / len(speeds)) ** 0.5) if speeds else 0.0)
    for r in bench:
        rr = rank_by_id.get(r["pilot_id"], {})
        r["rank"] = rr.get("rank", "n/a")
        r["percentile"] = rr.get("percentile", "n/a")
        r["band"] = rr.get("band", "n/a")
        if isinstance(r.get("latest_speed"), float) and std_speed > 0:
            z = (r["latest_speed"] - mean_speed) / std_speed
            if z >= 1.2:
                r["outlier"] = "High outlier"
            elif z <= -1.2:
                r["outlier"] = "Low outlier"
            else:
                r["outlier"] = "In range"
        else:
            r["outlier"] = "In range"

    regions = sorted({r["region"] for r in bench if r.get("region")})
    lpa_types = sorted({r["lpa_type"] for r in bench if r.get("lpa_type")})
    cohorts = sorted({r["cohort"] for r in bench if r.get("cohort")})
    bands = ["Top third", "Middle third", "Bottom third"]
    by_region = defaultdict(list)
    by_cohort = defaultdict(list)
    for row in ranked:
        by_region[row["region"]].append(row["latest_speed"])
        by_cohort[row["cohort"]].append(row["latest_speed"])
    _, health_counts = compute_data_health()

    body = '<section class="card"><p>Benchmark dashboard compares LPAs on latest decision speed, appeal overturn trend, issue incidence, and evidence quality. Trend lines show 2024-Q4 to 2025-Q3.</p></section>'
    body += '<section class="card"><p>'
    body += f'Data health: {badge("fresh", "green")} {health_counts.get("fresh", 0)} '
    body += f'{badge("stale", "amber")} {health_counts.get("stale", 0)} '
    body += f'{badge("critical", "red")} {health_counts.get("critical", 0)} '
    body += ' — <a href="data-health.html">view details</a>.</p></section>'
    body += '<section class="grid">'
    if ranked:
        body += f'<article class="card"><h3>Top performer</h3><p>{html.escape(ranked[0]["lpa_name"])} ({ranked[0]["latest_speed"]:.1f}%)</p></article>'
        body += f'<article class="card"><h3>Median speed</h3><p>{ranked[n//2]["latest_speed"]:.1f}%</p></article>'
        body += f'<article class="card"><h3>Bottom performer</h3><p>{html.escape(ranked[-1]["lpa_name"])} ({ranked[-1]["latest_speed"]:.1f}%)</p></article>'
    body += '</section>'

    if ranked:
        best_delta = max([r for r in ranked if isinstance(r.get("speed_delta"), float)], key=lambda x: x["speed_delta"], default=None)
        if best_delta:
            body += '<section class="grid">'
            body += f'<article class="card"><h3>Top improver (4Q)</h3><p>{html.escape(best_delta["lpa_name"])} ({best_delta["speed_delta"]:+.1f} pp)</p></article>'
            body += f'<article class="card"><h3>Cohort 1 avg speed</h3><p>{(sum(by_cohort.get("Cohort 1", [])) / max(1, len(by_cohort.get("Cohort 1", [])))):.1f}%</p></article>'
            body += f'<article class="card"><h3>Cohort 2 avg speed</h3><p>{(sum(by_cohort.get("Cohort 2", [])) / max(1, len(by_cohort.get("Cohort 2", [])))):.1f}%</p></article>'
            body += '</section>'

    body += '<section class="card"><h2>Regional drilldown</h2><table><thead><tr><th>Region</th><th>Authorities</th><th>Average speed (%)</th></tr></thead><tbody>'
    for region in sorted(by_region.keys()):
        vals = by_region[region]
        body += f'<tr><td>{html.escape(region)}</td><td>{len(vals)}</td><td>{(sum(vals)/len(vals)):.1f}</td></tr>'
    body += '</tbody></table></section>'

    body += '<section class="card"><h2>Metric provenance</h2><p>'
    body += provenance_badge("official") + ' from GOV.UK planning statistics (P151/P152); '
    body += provenance_badge("estimated") + ' from analytical issue-incidence and evidence-quality scoring layers.'
    body += '</p></section>'

    top_pid = ranked[0]["pilot_id"] if ranked else ""
    median_pid = ranked[n // 2]["pilot_id"] if ranked else ""
    if top_pid == median_pid and n > 1:
        median_pid = ranked[1]["pilot_id"]

    body += '<section class="card"><div class="filter-row">'
    body += '<label class="filter-item">Search benchmark<input type="search" data-table="benchmark-table" data-filter="search" placeholder="Type authority or stage..." /></label>'
    body += '<label class="filter-item">Region<select data-table="benchmark-table" data-filter="region"><option value="">All</option>'
    for region in regions:
        body += f'<option value="{html.escape(region.lower())}">{html.escape(region)}</option>'
    body += '</select></label>'
    body += '<label class="filter-item">LPA type<select data-table="benchmark-table" data-filter="lpa_type"><option value="">All</option>'
    for lpa_type in lpa_types:
        body += f'<option value="{html.escape(lpa_type.lower())}">{html.escape(lpa_type)}</option>'
    body += '</select></label>'
    body += '<label class="filter-item">Cohort<select data-table="benchmark-table" data-filter="cohort"><option value="">All</option>'
    for cohort in cohorts:
        body += f'<option value="{html.escape(cohort.lower())}">{html.escape(cohort)}</option>'
    body += '</select></label>'
    body += '<label class="filter-item">Percentile band<select data-table="benchmark-table" data-filter="band"><option value="">All</option>'
    for band in bands:
        body += f'<option value="{html.escape(band.lower())}">{html.escape(band)}</option>'
    body += '</select></label>'
    body += '</div><p class="small" data-filter-count-for="benchmark-table"></p></section>'

    body += f'<section class="card"><p class="small">Generated on {date.today().isoformat()} from quarterly trends and issue incidence datasets.</p></section>'
    body += '<section class="card"><h2>LPA Benchmark Ranking</h2>'
    body += '<table id="benchmark-table"><thead><tr><th>Rank</th><th>LPA</th><th>Cohort</th><th>Type</th><th>Region</th><th>Speed (%)</th><th>4Q Delta (pp)</th><th>Outlier</th><th>Percentile</th><th>Band</th><th>Trend</th><th>Appeal %</th><th>Issues</th><th>High Sev</th><th>Risk Stage</th><th>Quality</th><th>Compare</th></tr></thead><tbody>'
    for r in sorted(bench, key=lambda x: (x["rank"] if isinstance(x["rank"], int) else 9999)):
        speed = f"{r['latest_speed']:.1f}" if isinstance(r["latest_speed"], float) else "n/a"
        appeal = f"{r['latest_appeal']:.1f}" if isinstance(r["latest_appeal"], float) else "n/a"
        compare_target = top_pid if r["pilot_id"] != top_pid else median_pid
        compare_link = "—"
        if compare_target and compare_target != r["pilot_id"]:
            href = f"compare.html#a={r['pilot_id']}&b={compare_target}"
            compare_link = f'<a href="{html.escape(href)}">Preset pair</a>'
        search_blob = " ".join([
            str(r.get("lpa_name", "")),
            str(r.get("cohort", "")),
            str(r.get("lpa_type", "")),
            str(r.get("region", "")),
            str(r.get("risk_stage", "")),
            str(r.get("quality_tier", "")),
            str(r.get("band", "")),
        ]).strip().lower()
        attrs = (
            f'data-search="{html.escape(search_blob)}" '
            f'data-region="{html.escape(r.get("region", "").strip().lower())}" '
            f'data-cohort="{html.escape(r.get("cohort", "").strip().lower())}" '
            f'data-lpa_type="{html.escape(r.get("lpa_type", "").strip().lower())}" '
            f'data-band="{html.escape(r.get("band", "").strip().lower())}"'
        )
        delta = "n/a"
        if isinstance(r.get("speed_delta"), float):
            delta = f"{r['speed_delta']:+.1f}"
        outlier_css = "green" if r.get("outlier") == "High outlier" else "red" if r.get("outlier") == "Low outlier" else "grey"
        body += f"<tr {attrs}>"
        body += f"<td>{html.escape(str(r['rank']))}</td>"
        body += f"<td>{html.escape(r['lpa_name'])}</td>"
        body += f"<td>{html.escape(r['cohort'])}</td>"
        body += f"<td>{html.escape(r['lpa_type'])}</td>"
        body += f"<td>{html.escape(r['region'])}</td>"
        body += f"<td>{speed} {provenance_badge('official')}</td>"
        body += f"<td>{delta} {provenance_badge('official')}</td>"
        body += f"<td>{badge(r.get('outlier', 'In range'), outlier_css)}</td>"
        body += f"<td>{html.escape(str(r['percentile']))}</td>"
        body += f"<td>{html.escape(r['band'])}</td>"
        body += f"<td>{r['trend_spark']}</td>"
        body += f"<td>{appeal} {provenance_badge('official')}</td>"
        body += f"<td>{html.escape(str(r['total_issues']))} {provenance_badge('estimated')}</td>"
        body += f"<td>{html.escape(str(r['high_severity_issues']))}</td>"
        body += f"<td>{html.escape(str(r['risk_stage']))}</td>"
        body += f"<td>{html.escape(str(r['quality_tier']))} ({html.escape(str(r['quality_score']))}) {provenance_badge('estimated')}</td>"
        body += f"<td>{compare_link}</td>"
        body += "</tr>"
    body += '</tbody></table></section>'

    body += """
<script>
(function() {
  var table = document.getElementById('benchmark-table');
  if (!table) return;
  var rows = Array.from(table.querySelectorAll('tbody tr'));
  var controls = Array.from(document.querySelectorAll('[data-table="benchmark-table"]'));
  var countEl = document.querySelector('[data-filter-count-for="benchmark-table"]');

  function update() {
    var visible = 0;
    var search = '';
    var selected = {};

    controls.forEach(function(control) {
      var key = control.dataset.filter;
      var value = (control.value || '').toLowerCase().trim();
      if (key === 'search') {
        search = value;
      } else if (value) {
        selected[key] = value;
      }
    });

    rows.forEach(function(row) {
      var show = true;
      for (var key in selected) {
        if ((row.dataset[key] || '') !== selected[key]) {
          show = false;
          break;
        }
      }
      if (show && search) {
        var blob = row.dataset.search || '';
        if (blob.indexOf(search) === -1) show = false;
      }
      row.classList.toggle('hidden-row', !show);
      if (show) visible++;
    });

    if (countEl) countEl.textContent = visible + ' of ' + rows.length + ' rows shown';
  }

  controls.forEach(function(control) {
    control.addEventListener('input', update);
    control.addEventListener('change', update);
  });
  update();
})();
</script>
"""

    write(SITE / "benchmark.html", page(
        "LPA Benchmark Dashboard",
        "Rankings, percentile bands, and trend sparklines across authorities.",
        "benchmark", body,
        "Use rankings, percentile bands, and trend indicators to see relative performance and jump to preset authority comparisons."))


def build_reports():
    lpas = read_csv(ROOT / "data/plans/pilot-lpas.csv")
    quality_rows = read_csv(ROOT / "data/plans/lpa-data-quality.csv")
    issue_rows = read_csv(ROOT / "data/issues/lpa-issue-incidence.csv")
    trend_rows = read_csv(ROOT / "data/evidence/lpa-quarterly-trends.csv")

    quality_by_id = {r["pilot_id"]: r for r in quality_rows}
    issues_by_id = {r["pilot_id"]: r for r in issue_rows}
    trends_by_id = defaultdict(list)
    for r in trend_rows:
        trends_by_id[r["pilot_id"]].append(r)
    for pid in trends_by_id:
        trends_by_id[pid].sort(key=lambda x: x["quarter"])

    reports_dir = SITE / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    generated_on = date.today().isoformat()
    data_version = BUILD_VERSION
    _, health_counts = compute_data_health()

    links = []
    latest_speed_rows = []
    for lpa in lpas:
        pid = lpa["pilot_id"]
        q = quality_by_id.get(pid, {})
        i = issues_by_id.get(pid, {})
        t = trends_by_id.get(pid, [])
        latest_trend = t[-1] if t else {}
        if latest_trend:
            try:
                latest_speed_rows.append({
                    "pilot_id": pid,
                    "lpa_name": lpa.get("lpa_name", ""),
                    "major_in_time_pct": float(latest_trend.get("major_in_time_pct", "")),
                })
            except ValueError:
                pass
        trend_source = latest_trend.get("source_table", "")
        trend_source_url = latest_trend.get("source_url", "")
        payload = {
            "report_generated_at": generated_on,
            "data_version": data_version,
            "pilot_id": pid,
            "lpa_name": lpa.get("lpa_name", ""),
            "lpa_type": lpa.get("lpa_type", ""),
            "cohort": cohort_for_pid(pid),
            "region": lpa.get("region", ""),
            "growth_context": lpa.get("growth_context", ""),
            "constraint_profile": lpa.get("constraint_profile", ""),
            "data_quality": q,
            "issue_incidence": i,
            "quarterly_trends": t,
            "metric_provenance": {
                "major_in_time_pct": "official",
                "appeals_overturned_pct": "official",
                "issue_incidence": "estimated",
                "data_quality": "estimated",
            },
            "latest_trend_source": {
                "source_table": trend_source,
                "source_url": trend_source_url,
            },
        }
        json_path = reports_dir / f"{pid.lower()}-report.json"
        json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

        csv_path = reports_dir / f"{pid.lower()}-report.csv"
        with csv_path.open("w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["field", "value"])
            w.writerow(["report_generated_at", generated_on])
            w.writerow(["data_version", data_version])
            w.writerow(["pilot_id", payload["pilot_id"]])
            w.writerow(["lpa_name", payload["lpa_name"]])
            w.writerow(["lpa_type", payload["lpa_type"]])
            w.writerow(["cohort", payload["cohort"]])
            w.writerow(["region", payload["region"]])
            w.writerow(["growth_context", payload["growth_context"]])
            w.writerow(["constraint_profile", payload["constraint_profile"]])
            w.writerow(["data_quality_tier", q.get("data_quality_tier", "")])
            w.writerow(["coverage_score", q.get("coverage_score", "")])
            w.writerow(["total_linked_issues", i.get("total_linked_issues", "")])
            w.writerow(["high_severity_issues", i.get("high_severity_issues", "")])
            w.writerow(["primary_risk_stage", i.get("primary_risk_stage", "")])
            w.writerow(["major_in_time_pct_provenance", "official"])
            w.writerow(["appeals_overturned_pct_provenance", "official"])
            w.writerow(["issue_incidence_provenance", "estimated"])
            w.writerow(["data_quality_provenance", "estimated"])
            w.writerow(["latest_trend_source_table", trend_source])
            w.writerow(["latest_trend_source_url", trend_source_url])

        links.append({
            "pid": pid,
            "name": lpa.get("lpa_name", ""),
            "lpa_type": lpa.get("lpa_type", ""),
            "cohort": cohort_for_pid(pid),
            "region": lpa.get("region", ""),
            "csv": f"reports/{pid.lower()}-report.csv",
            "json": f"reports/{pid.lower()}-report.json",
            "trend_source": trend_source,
            "trend_source_url": trend_source_url,
        })

    body = '<section class="card"><p>Download per-authority comparison bundles in CSV or JSON format. Each report contains profile, evidence quality, issue incidence, and quarterly trend snapshots.</p></section>'
    body += '<section class="card"><p>'
    body += f'Data health: {badge("fresh", "green")} {health_counts.get("fresh", 0)} '
    body += f'{badge("stale", "amber")} {health_counts.get("stale", 0)} '
    body += f'{badge("critical", "red")} {health_counts.get("critical", 0)} '
    body += ' — <a href="data-health.html">view details</a>.</p></section>'
    body += f'<section class="card"><p class="small">Report bundle version {data_version}; generated on {generated_on}.</p></section>'
    body += '<section class="card"><h2>Metric provenance</h2><p>'
    body += provenance_badge("official") + ' quarterly trend metrics from GOV.UK planning statistics; '
    body += provenance_badge("estimated") + ' issue-incidence and evidence-quality analytical layers.'
    body += '</p></section>'

    regions = sorted({r["region"] for r in links if r.get("region")})
    lpa_types = sorted({r["lpa_type"] for r in links if r.get("lpa_type")})
    cohorts = sorted({r["cohort"] for r in links if r.get("cohort")})

    body += '<section class="card"><div class="filter-row">'
    body += '<label class="filter-item">Search reports<input type="search" data-table="reports-table" data-filter="search" placeholder="Type authority..." /></label>'
    body += '<label class="filter-item">Region<select data-table="reports-table" data-filter="region"><option value="">All</option>'
    for region in regions:
        body += f'<option value="{html.escape(region.lower())}">{html.escape(region)}</option>'
    body += '</select></label>'
    body += '<label class="filter-item">LPA type<select data-table="reports-table" data-filter="lpa_type"><option value="">All</option>'
    for lpa_type in lpa_types:
        body += f'<option value="{html.escape(lpa_type.lower())}">{html.escape(lpa_type)}</option>'
    body += '</select></label>'
    body += '<label class="filter-item">Cohort<select data-table="reports-table" data-filter="cohort"><option value="">All</option>'
    for cohort in cohorts:
        body += f'<option value="{html.escape(cohort.lower())}">{html.escape(cohort)}</option>'
    body += '</select></label>'
    body += '</div><p class="small" data-filter-count-for="reports-table"></p></section>'

    body += '<section class="card"><table id="reports-table"><thead><tr><th>ID</th><th>Authority</th><th>Cohort</th><th>Type</th><th>Region</th><th>Metric provenance</th><th>Trend source</th><th>CSV</th><th>JSON</th></tr></thead><tbody>'
    for row in links:
        attrs = (
            f'data-search="{html.escape((row["name"] + " " + row["pid"]).strip().lower())}" '
            f'data-region="{html.escape(row["region"].strip().lower())}" '
            f'data-cohort="{html.escape(row["cohort"].strip().lower())}" '
            f'data-lpa_type="{html.escape(row["lpa_type"].strip().lower())}"'
        )
        source_cell = html.escape(row["trend_source"]) if row["trend_source"] else "—"
        if row["trend_source_url"]:
            source_cell = f'<a href="{html.escape(row["trend_source_url"])}" target="_blank" rel="noopener noreferrer">{html.escape(row["trend_source"] or "Source")}</a>'
        body += f'<tr {attrs}>'
        body += f'<td>{html.escape(row["pid"])}</td>'
        body += f'<td>{html.escape(row["name"])}</td>'
        body += f'<td>{html.escape(row["cohort"])}</td>'
        body += f'<td>{html.escape(row["lpa_type"])}</td>'
        body += f'<td>{html.escape(row["region"])}</td>'
        body += f'<td>{provenance_badge("official")} {provenance_badge("estimated")}</td>'
        body += f'<td>{source_cell}</td>'
        body += f'<td><a href="{html.escape(row["csv"])}">Download CSV</a></td>'
        body += f'<td><a href="{html.escape(row["json"])}">Download JSON</a></td>'
        body += '</tr>'
    body += '</tbody></table></section>'

    if latest_speed_rows:
        latest_speed_rows.sort(key=lambda x: x["major_in_time_pct"], reverse=True)
        snapshot = {
            "snapshot_period": generated_on[:7],
            "generated_on": generated_on,
            "data_version": data_version,
            "top_lpa": latest_speed_rows[0],
            "bottom_lpa": latest_speed_rows[-1],
            "average_major_in_time_pct": round(sum(r["major_in_time_pct"] for r in latest_speed_rows) / len(latest_speed_rows), 2),
            "authority_count": len(latest_speed_rows),
        }
        (reports_dir / "monthly-snapshot.json").write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
        with (reports_dir / "monthly-snapshot.csv").open("w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["field", "value"])
            for k, v in snapshot.items():
                if isinstance(v, dict):
                    w.writerow([k, json.dumps(v, ensure_ascii=False)])
                else:
                    w.writerow([k, v])
        body += '<section class="card"><h2>Monthly snapshot bundle</h2>'
        body += '<p><a href="reports/monthly-snapshot.csv">monthly-snapshot.csv</a> | '
        body += '<a href="reports/monthly-snapshot.json">monthly-snapshot.json</a></p></section>'

    body += """
<script>
(function() {
  var table = document.getElementById('reports-table');
  if (!table) return;
  var rows = Array.from(table.querySelectorAll('tbody tr'));
  var controls = Array.from(document.querySelectorAll('[data-table="reports-table"]'));
  var countEl = document.querySelector('[data-filter-count-for="reports-table"]');

  function update() {
    var visible = 0;
    var search = '';
    var selected = {};

    controls.forEach(function(control) {
      var key = control.dataset.filter;
      var value = (control.value || '').toLowerCase().trim();
      if (key === 'search') {
        search = value;
      } else if (value) {
        selected[key] = value;
      }
    });

    rows.forEach(function(row) {
      var show = true;
      for (var key in selected) {
        if ((row.dataset[key] || '') !== selected[key]) {
          show = false;
          break;
        }
      }
      if (show && search) {
        var blob = row.dataset.search || '';
        if (blob.indexOf(search) === -1) show = false;
      }
      row.classList.toggle('hidden-row', !show);
      if (show) visible++;
    });

    if (countEl) countEl.textContent = visible + ' of ' + rows.length + ' rows shown';
  }

  controls.forEach(function(control) {
    control.addEventListener('input', update);
    control.addEventListener('change', update);
  });
  update();
})();
</script>
"""

    write(SITE / "reports.html", page(
        "LPA Reports",
        "Downloadable authority-level comparison bundles.",
        "reports", body,
        "Filter and download per-authority report bundles that combine profile context, issue incidence, quality data, and trend snapshots."))


def build_data_health():
    rows, counts = compute_data_health()
    body = '<section class="card"><p>Monitors freshness of core operational datasets and highlights stale or critical update risk windows.</p></section>'
    body += '<section class="grid">'
    body += f'<article class="card"><h3>Fresh datasets</h3><p>{counts.get("fresh", 0)}</p></article>'
    body += f'<article class="card"><h3>Stale datasets</h3><p>{counts.get("stale", 0)}</p></article>'
    body += f'<article class="card"><h3>Critical datasets</h3><p>{counts.get("critical", 0)}</p></article>'
    body += '</section>'

    body += '<section class="card"><table><thead><tr><th>Dataset</th><th>Status</th><th>Rows</th><th>Last updated</th><th>Age (days)</th><th>Path</th></tr></thead><tbody>'
    for row in sorted(rows, key=lambda r: (r["age_days"] if isinstance(r["age_days"], int) else 9999), reverse=True):
        body += '<tr>'
        body += f'<td>{html.escape(row["dataset"])}</td>'
        body += f'<td>{row["status_badge"]}</td>'
        body += f'<td>{html.escape(str(row["row_count"]))}</td>'
        body += f'<td>{html.escape(str(row["last_updated"]))}</td>'
        body += f'<td>{html.escape(str(row["age_days"]))}</td>'
        body += f'<td><code>{html.escape(row["source_path"])}</code></td>'
        body += '</tr>'
    body += '</tbody></table></section>'

    write(SITE / "data-health.html", page(
        "Data Health",
        "Freshness and reliability monitoring for core operational datasets.",
        "data-health", body,
        "Use this page to assess whether evidence datasets are up to date before relying on benchmark outputs or recommendations."))


def build_consultation():
    recs = read_csv(ROOT / "data/issues/recommendations.csv")
    statuses = read_csv(ROOT / "data/issues/recommendation-status.csv")
    status_map = {r["recommendation_id"]: r for r in statuses}

    # Status summary counts
    counts = defaultdict(int)
    for r in statuses:
        counts[r.get("submission_status", "Unknown")] += 1

    body = '<section class="card">'
    body += '<h2>Disclaimer</h2>'
    body += '<p>This analysis is <strong>advisory only</strong>. It does not constitute legal advice. '
    body += 'All recommendations are at <em>draft</em> verification state and have not been legally reviewed. '
    body += 'Model drafting text is provided for discussion purposes and is not intended to be used as statutory language without independent legal review. '
    body += 'The analysis covers England only. The authors have no affiliation with MHCLG, PINS, or any local planning authority.</p>'
    body += '</section>'

    body += '<section class="grid">'
    for status, count in sorted(counts.items()):
        css = {"Adopted": "green", "Submitted": "blue", "Response received": "blue",
               "Rejected": "red", "Not submitted": "grey"}.get(status, "grey")
        body += f'<article class="card"><h3>{html.escape(status)}</h3><p>{count} recommendation(s)</p></article>'
    body += '</section>'

    body += '<section class="card"><h2>Submission Status Tracker</h2>'
    body += '<table><thead><tr><th>Recommendation</th><th>Title</th><th>Status</th><th>Submitted To</th><th>Next Action</th></tr></thead><tbody>'
    for rec in recs:
        rid = rec["recommendation_id"]
        s = status_map.get(rid, {})
        status_val = s.get("submission_status", "Not submitted")
        css = {"Adopted": "badge-green", "Submitted": "badge-blue", "Response received": "badge-blue",
               "Rejected": "badge-red", "Not submitted": "badge-grey", "Under review": "badge-amber"}.get(status_val, "badge-grey")
        body += f'<tr><td>{html.escape(rid)}</td>'
        body += f'<td>{html.escape(rec.get("title", ""))}</td>'
        body += f'<td><span class="badge {css}">{html.escape(status_val)}</span></td>'
        body += f'<td>{html.escape(s.get("submitted_to", "—"))}</td>'
        body += f'<td>{html.escape(s.get("next_action", ""))}</td></tr>'
    body += '</tbody></table></section>'

    body += '<section class="card"><h2>Download Recommendations Pack</h2>'
    body += '<p>Download the full recommendations as a machine-readable dataset for consultation purposes.</p>'
    body += '<ul>'
    body += '<li><a href="exports/recommendations.csv">recommendations.csv</a></li>'
    body += '<li><a href="exports/recommendations.json">recommendations.json</a></li>'
    body += '</ul>'
    body += '<button onclick="window.print()" style="margin-top:12px;padding:10px 20px;background:var(--accent);color:#fff;border:none;border-radius:8px;cursor:pointer;font-size:1rem;">Print / Save as PDF</button>'
    body += '</section>'

    body += '<section class="card"><h2>How to Respond</h2>'
    body += '<p>This analysis is published as open data. To contribute evidence, corrections, or policy responses:</p><ul>'
    body += '<li>Open an issue on the <a href="https://github.com/benbutler55/uk-planning/issues" target="_blank" rel="noopener">GitHub repository</a>.</li>'
    body += '<li>Download the datasets from the <a href="exports.html">Exports</a> page and submit a pull request with updated data.</li>'
    body += '<li>Cite this analysis using the repository URL and the version tag.</li>'
    body += '</ul></section>'

    write(SITE / "consultation.html", page(
        "Consultation and Status",
        "Submission status tracker, disclaimer, and how to respond to this analysis.",
        "consultation", body,
        "Track recommendation submission progress, review disclaimers, and find routes for feedback or evidence contributions."))


def build_search_index():
    """Build a JSON search index from all key datasets for client-side search."""
    index = []

    def add(doc_id, page, title, category, text):
        index.append({
            "id": doc_id, "page": page, "title": title,
            "category": category,
            "text": " ".join(str(v) for v in [title, text] if v).lower()
        })

    for r in read_csv(ROOT / "data/issues/contradiction-register.csv"):
        add(r["issue_id"], "contradictions.html", r["issue_id"] + ": " + r["summary"],
            "Contradiction", r.get("summary", "") + " " + r.get("issue_type", "") + " " + r.get("process_stage", ""))

    for r in read_csv(ROOT / "data/issues/recommendations.csv"):
        add(r["recommendation_id"], "recommendations.html", r["recommendation_id"] + ": " + r["title"],
            "Recommendation", r.get("title", "") + " " + r.get("policy_goal", "") + " " + r.get("kpi_primary", ""))

    for r in read_csv(ROOT / "data/legislation/england-core-legislation.csv"):
        add(r["id"], "legislation.html", r["title"],
            "Legislation", r.get("type", "") + " " + r.get("status", "") + " " + r.get("citation", ""))

    for r in read_csv(ROOT / "data/policy/england-national-policy.csv"):
        add(r["id"], "legislation.html", r["title"],
            "Policy", r.get("type", "") + " " + r.get("scope", "") + " " + r.get("authority", ""))

    for r in read_csv(ROOT / "data/plans/pilot-lpas.csv"):
        add(r["pilot_id"], f"plans-{r['pilot_id'].lower()}.html", r["lpa_name"],
            "LPA", r.get("region", "") + " " + r.get("constraint_profile", "") + " " + r.get("growth_context", ""))

    for r in read_csv(ROOT / "data/issues/bottleneck-heatmap.csv"):
        add(r["stage_id"], "bottlenecks.html", r["process_stage"] + " — " + r["pathway"],
            "Bottleneck", r.get("delay_driver", "") + " " + r.get("process_stage", ""))

    for r in read_csv(ROOT / "data/evidence/appeal-decisions.csv"):
        add(r["appeal_id"], "appeals.html", r["pins_reference"] + " (" + r["lpa"] + ")",
            "Appeal", r.get("inspector_finding", "") + " " + r.get("policy_cited", ""))

    idx_path = SITE / "search-index.json"
    idx_path.write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")
    return len(index)


def build_search():
    body = """
      <section class="card">
        <label for="search-input" class="sr-only">Search across all content</label>
        <input type="search" id="search-input" placeholder="Search legislation, issues, recommendations, LPAs, appeals..." style="width:100%;padding:12px;font-size:1rem;border:1px solid var(--line);border-radius:8px;" />
        <p class="small" id="search-count" style="margin-top:8px;"></p>
      </section>
      <section class="card" id="search-results">
        <p class="small">Start typing to search across all content.</p>
      </section>
      <script>
      (function() {
        var input = document.getElementById('search-input');
        var results = document.getElementById('search-results');
        var countEl = document.getElementById('search-count');
        var index = null;

        fetch('search-index.json')
          .then(function(r) { return r.json(); })
          .then(function(data) {
            index = data;
            countEl.textContent = data.length + ' items indexed.';
          });

        input.addEventListener('input', function() {
          var q = input.value.toLowerCase().trim();
          if (!index || q.length < 2) {
            results.innerHTML = '<p class="small">Type at least 2 characters to search.</p>';
            return;
          }
          var matches = index.filter(function(item) {
            return item.text.indexOf(q) !== -1;
          }).slice(0, 50);

          if (matches.length === 0) {
            results.innerHTML = '<p class="small">No results found.</p>';
            countEl.textContent = '0 results.';
            return;
          }

          countEl.textContent = matches.length + ' result(s).';
          var cats = {};
          matches.forEach(function(m) {
            if (!cats[m.category]) cats[m.category] = [];
            cats[m.category].push(m);
          });

          var html = '';
          Object.keys(cats).sort().forEach(function(cat) {
            html += '<h3>' + cat + '</h3><ul>';
            cats[cat].forEach(function(m) {
              html += '<li><a href="' + m.page + '">' + m.title + '</a></li>';
            });
            html += '</ul>';
          });
          results.innerHTML = html;
        });
      })();
      </script>
"""
    write(SITE / "search.html", page(
        "Search",
        "Full-text search across legislation, issues, recommendations, LPAs, appeals, and bottlenecks.",
        "search", body,
        "Use keyword search to quickly find relevant records across legislation, plans, issues, recommendations, appeals, and evidence."))


def main():
    weights = load_scoring()

    build_index()
    build_legislation()
    build_plans()
    build_contradictions(weights)
    build_recommendations(weights)
    build_roadmap()
    build_baselines()
    build_bottlenecks()
    build_appeals()
    build_map()
    build_compare()
    build_benchmark()
    build_reports()
    build_data_health()
    build_consultation()
    build_search_index()
    build_search()
    build_audience_policymakers()
    build_audience_lpas()
    build_audience_developers()
    build_audience_public()
    build_methodology()
    build_sources()
    build_exports_index()

    # Write exports
    exports_data = {
        "contradiction-register": read_csv(ROOT / "data/issues/contradiction-register.csv"),
        "recommendations": read_csv(ROOT / "data/issues/recommendations.csv"),
        "recommendation_evidence_links": read_csv(ROOT / "data/evidence/recommendation_evidence_links.csv"),
        "official_baseline_metrics": read_csv(ROOT / "data/evidence/official_baseline_metrics.csv"),
        "implementation-roadmap": read_csv(ROOT / "data/issues/implementation-roadmap.csv"),
        "bottleneck-heatmap": read_csv(ROOT / "data/issues/bottleneck-heatmap.csv"),
        "appeal-decisions": read_csv(ROOT / "data/evidence/appeal-decisions.csv"),
        "lpa-data-quality": read_csv(ROOT / "data/plans/lpa-data-quality.csv"),
        "lpa-quarterly-trends": read_csv(ROOT / "data/evidence/lpa-quarterly-trends.csv"),
        "lpa-issue-incidence": read_csv(ROOT / "data/issues/lpa-issue-incidence.csv"),
    }
    write_exports(exports_data)
    write_exports_manifest(exports_data)

    print("Built site pages from CSV data.")


if __name__ == "__main__":
    main()
