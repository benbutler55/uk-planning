#!/usr/bin/env python3
"""Build static site from CSV datasets. Generates HTML pages with filtering,
weighted scoring, confidence badges, evidence traces, and split audience views."""
import csv
import html
import json
import shutil
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
EXPORTS = SITE / "exports"
SCORING_PATH = ROOT / "data/schemas/scoring.json"


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


# --- Page shell ---

def page(title, subhead, active, body):
    links = [
        ("index.html", "Overview", "index"),
        ("legislation.html", "Legislation", "legislation"),
        ("plans.html", "Plans", "plans"),
        ("contradictions.html", "Contradictions", "contradictions"),
        ("recommendations.html", "Recommendations", "recommendations"),
        ("roadmap.html", "Roadmap", "roadmap"),
        ("baselines.html", "Baselines", "baselines"),
        ("bottlenecks.html", "Bottlenecks", "bottlenecks"),
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


# --- Page builders ---

def build_index():
    body = """
      <section class="card">
        <h2>Current Phase</h2>
        <p>Pilot Release — citation-backed evidence, weighted scoring, and split audience views.</p>
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
    write(SITE / "index.html", page(
        "UK Planning System Analysis — England Pilot Release",
        "Citation-backed analysis of legislation, policy, and local plan layers with reform proposals.",
        "index", body))


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
        "legislation", body))


def build_plans():
    rows = read_csv(ROOT / "data/plans/pilot-lpas.csv")
    docs = read_csv(ROOT / "data/plans/pilot-plan-documents.csv")
    docs_by_lpa = defaultdict(list)
    for item in docs:
        docs_by_lpa[item["pilot_id"]].append(item)

    body = '<section class="card"><ul>'
    for level in ["National", "Regional/sub-regional", "County", "District/unitary", "Neighbourhood", "Sector overlays"]:
        body += f"<li>{html.escape(level)}</li>"
    body += "</ul></section>"

    body += '<section class="card"><table><thead><tr><th>Authority</th><th>Type</th><th>Region</th><th>Growth</th><th>Constraints</th><th>Profile</th></tr></thead><tbody>'
    for row in rows:
        lpa_page = f"plans-{row['pilot_id'].lower()}.html"
        body += "<tr>"
        for k in ["lpa_name", "lpa_type", "region", "growth_context", "constraint_profile"]:
            body += f"<td>{html.escape(row.get(k, ''))}</td>"
        body += f'<td><a href="{lpa_page}">View</a></td></tr>'
    body += "</tbody></table></section>"

    write(SITE / "plans.html", page(
        "Plan Hierarchy Explorer",
        "Mapped planning stack from national policy to neighbourhood plans and overlays.",
        "plans", body))

    for row in rows:
        lpa_docs = docs_by_lpa.get(row["pilot_id"], [])
        pb = '<section class="card">'
        pb += f"<h2>{html.escape(row.get('lpa_name', ''))}</h2>"
        pb += f"<p><strong>Type:</strong> {html.escape(row.get('lpa_type', ''))}</p>"
        pb += f"<p><strong>Region:</strong> {html.escape(row.get('region', ''))}</p>"
        pb += f"<p><strong>Rationale:</strong> {html.escape(row.get('selection_rationale', ''))}</p>"
        pb += f"<p><strong>Constraints:</strong> {html.escape(row.get('constraint_profile', ''))}</p>"
        pb += '<p><a href="plans.html">Back to pilot overview</a></p></section>'
        pb += render_plan_docs_table(lpa_docs)
        write(SITE / f"plans-{row['pilot_id'].lower()}.html", page(
            f"{row['lpa_name']} Plan Profile",
            "Pilot authority planning document stack.",
            "plans", pb))


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
        "contradictions", body))


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
        "recommendations", body))


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
        "roadmap", body))


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
        "baselines", body))


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
        "bottlenecks", body))


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
        "policymakers", body))


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
        "lpas", body))


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
        "developers", body))


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
        "public", body))


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
        "methodology", body))


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
        "sources", body))


def build_exports_index():
    body = '<section class="card"><h2>Machine-Readable Exports</h2>'
    body += "<p>All core datasets are available in CSV and JSON format for external analysis.</p>"
    body += "<ul>"
    for name in ["contradiction-register", "recommendations", "recommendation_evidence_links",
                  "official_baseline_metrics", "implementation-roadmap", "bottleneck-heatmap"]:
        body += f'<li><a href="exports/{name}.csv">{name}.csv</a> | <a href="exports/{name}.json">{name}.json</a></li>'
    body += "</ul></section>"
    write(SITE / "exports.html", page(
        "Data Exports",
        "Download datasets in CSV and JSON format.",
        "index", body))


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
    build_audience_policymakers()
    build_audience_lpas()
    build_audience_developers()
    build_audience_public()
    build_methodology()
    build_sources()
    build_exports_index()

    # Write exports
    write_exports({
        "contradiction-register": read_csv(ROOT / "data/issues/contradiction-register.csv"),
        "recommendations": read_csv(ROOT / "data/issues/recommendations.csv"),
        "recommendation_evidence_links": read_csv(ROOT / "data/evidence/recommendation_evidence_links.csv"),
        "official_baseline_metrics": read_csv(ROOT / "data/evidence/official_baseline_metrics.csv"),
        "implementation-roadmap": read_csv(ROOT / "data/issues/implementation-roadmap.csv"),
        "bottleneck-heatmap": read_csv(ROOT / "data/issues/bottleneck-heatmap.csv"),
    })

    print("Built site pages from CSV data.")


if __name__ == "__main__":
    main()
