#!/usr/bin/env python3
"""Build static site from CSV datasets. Generates HTML pages with filtering,
weighted scoring, confidence badges, evidence traces, and split audience views."""
import csv
import hashlib
import html
import json
import math
import shutil
import sys
import urllib.parse
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from builders.config import (
    ROOT,
    SITE,
    EXPORTS,
    SCORING_PATH,
    BUILD_VERSION,
    SECTION_CONFIG,
    PAGE_TO_SECTION,
)
from builders.metrics import (
    weighted_score,
    cohort_for_pid,
    analytical_confidence_for_tier,
    peer_group_for_lpa,
    derive_plan_age_years,
    derive_metric_bundle,
    parse_iso_date,
    split_pipe_values,
    issue_detail_page,
    recommendation_detail_page,
    query_value,
)
from builders.data_loader import (
    read_csv,
    load_scoring,
    compute_data_health,
    compute_onboarding_status_rows,
)
from builders.html_utils import (
    badge,
    confidence_badge,
    verification_badge,
    provenance_badge,
    metric_help,
    render_page_purpose,
    render_table_guide,
    render_next_steps,
    render_data_trust_panel,
    render_mode_shell_script,
    default_breadcrumbs,
    default_purpose,
    render_footer,
    page,
    write,
    render_cell,
    sparkline_svg,
    render_table,
    render_filter_controls,
    render_filterable_table,
    render_filter_script,
    render_table_enhancements_script,
    render_mobile_drawer_script,
    render_detail_toc,
    render_metric_context_block,
    render_plan_docs_table,
    URL_COLUMNS,
    TRUNCATE_COLUMNS,
)


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
    latest = None
    for rows in datasets.values():
        for row in rows:
            for value in row.values():
                if not value:
                    continue
                candidate = None
                try:
                    candidate = date.fromisoformat(str(value)[:10])
                except ValueError:
                    candidate = None
                if candidate and (latest is None or candidate > latest):
                    latest = candidate
    if latest is None:
        latest = date.today()
    generated = datetime(latest.year, latest.month, latest.day, 0, 0, 0).isoformat() + "Z"
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
    baseline_rows = read_csv(ROOT / "data/evidence/official_baseline_metrics.csv")
    trend_rows = read_csv(ROOT / "data/evidence/lpa-quarterly-trends.csv")
    baseline_by_id = {r.get("metric_id", ""): r for r in baseline_rows}

    def metric_card(metric_id, label, unit_suffix=""):
        row = baseline_by_id.get(metric_id, {})
        value = row.get("value", "n/a")
        source_url = html.escape(row.get("source_url", ""))
        source_table = html.escape(row.get("source_table", ""))
        source_ref = html.escape(metric_id)
        value_label = html.escape(str(value)) + unit_suffix
        source_line = f'{source_ref} ({source_table})'
        if source_url:
            source_line = f'<a href="{source_url}" target="_blank" rel="noopener noreferrer">{source_line}</a>'
        return (
            '<article class="card card-kpi">'
            f'<h3>{html.escape(label)}</h3>'
            f'<p class="kpi-value">{value_label}</p>'
            f'<p class="small">Source: {source_line}</p>'
            '</article>'
        )

    # Trend delta card: average major speed movement from first to latest quarter across LPAs
    trend_by_lpa = defaultdict(list)
    for row in trend_rows:
        trend_by_lpa[row.get("pilot_id", "")].append(row)
    deltas = []
    for pid, series in trend_by_lpa.items():
        ordered = sorted(series, key=lambda x: x.get("quarter", ""))
        if len(ordered) < 2:
            continue
        try:
            delta = float(ordered[-1].get("major_in_time_pct", 0) or 0) - float(ordered[0].get("major_in_time_pct", 0) or 0)
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

    body = """
      <section class="card card-hero">
        <h2>Current Phase</h2>
        <p>Phase 6 — trust, monitoring, and decision readiness with drift checks and data health reporting.</p>
      </section>
      <h2 class="section-heading">Key Indicators</h2>
      <section class="card">
        <h2>England at a glance</h2>
        <p class="small">Headline indicators with direct source references for rapid triage.</p>
        <div class="grid">
    """
    body += metric_card("BAS-001", "Major decisions in time", "%")
    body += metric_card("BAS-002", "Non-major decisions in time", "%")
    body += metric_card("BAS-003", "Major appeals overturned", "%")
    body += metric_card("BAS-005", "NSIP examination median", " months")
    body += (
        '<article class="card card-kpi">'
        '<h3>LPA average 4Q movement</h3>'
        f'<p class="kpi-value">{html.escape(str(avg_delta))} pp ({delta_arrow})</p>'
        '<p class="small">Source: <a href="exports/lpa-quarterly-trends.csv">lpa-quarterly-trends.csv</a></p>'
        '</article>'
    )
    body += """
        </div>
      </section>
      <section class="grid">
        <article class="card card-guidance">
          <h3>Goal</h3>
          <p>Build a coherent cross-level planning framework that is faster, clearer, and more predictable.</p>
        </article>
        <article class="card card-guidance">
          <h3>Outputs</h3>
          <ul>
            <li>Legal and policy inventory</li>
            <li>Plan hierarchy mapping</li>
            <li>Contradiction register with weighted scoring</li>
            <li>Actionable reform package with evidence traces</li>
            <li>Machine-readable exports (CSV/JSON)</li>
          </ul>
        </article>
        <article class="card card-guidance">
          <h3>Delivery Horizon</h3>
          <p>Pilot Release for policy-professional audience. Static website on GitHub Pages.</p>
        </article>
      </section>
      <h2 class="section-heading">Explore by Goal</h2>
      <section class="card" id="filters-start">
        <div class="grid">
          <article class="card"><h3>Understand national issues</h3><p>Review contradictions, bottlenecks, and appeal evidence across the system.</p><p><a href="contradictions.html">Open system analysis &rarr;</a></p></article>
          <article class="card"><h3>Compare authorities</h3><p>Use benchmark, map, and compare tools to examine local performance differences.</p><p><a href="benchmark.html">Open authority insights &rarr;</a></p></article>
          <article class="card"><h3>Track recommendation delivery</h3><p>Follow recommendation status, milestones, and consultation progress.</p><p><a href="recommendations.html">Open recommendations &rarr;</a></p></article>
          <article class="card"><h3>Download data</h3><p>Get machine-readable exports and version metadata for external analysis.</p><p><a href="exports.html">Open data and methods &rarr;</a></p></article>
        </div>
      </section>
      <h2 class="section-heading">Audience Views</h2>
      <section class="grid">
        <article class="card"><h3>Policy Makers</h3><p>Priority actions, evidence, and reform tracking for policy teams.</p><p><a href="audience-policymakers.html">View &rarr;</a></p></article>
        <article class="card"><h3>Local Planning Authorities</h3><p>Authority-specific insights, benchmarks, and improvement actions.</p><p><a href="audience-lpas.html">View &rarr;</a></p></article>
        <article class="card"><h3>Developers</h3><p>Key impacts, recommendations, and authority comparisons.</p><p><a href="audience-developers.html">View &rarr;</a></p></article>
        <article class="card"><h3>Public</h3><p>Plain-language findings and proposed improvements.</p><p><a href="audience-public.html">View &rarr;</a></p></article>
      </section>
      <h2 class="section-heading">Data &amp; Health</h2>
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
        "Start here to understand what this pilot covers, who it is for, and which pages contain the detailed evidence and recommendations.",
        next_steps=[
            ("contradictions.html", "Go to contradictions dashboard"),
            ("benchmark.html", "Go to benchmark dashboard"),
            ("recommendations.html", "Go to recommendations"),
            ("data-health.html", "Go to data health"),
        ]))


def build_legislation():
    rows = read_csv(ROOT / "data/legislation/england-core-legislation.csv")
    policy_rows = read_csv(ROOT / "data/policy/england-national-policy.csv")
    body = render_table_guide("How to read this table", [
        "Each row is one legal or policy instrument used in planning decisions.",
        "Decision weight indicates practical influence in decision making.",
        "Use status and type together to separate in-force law from guidance.",
        "Source links open the originating official publication.",
    ])
    body += render_table(rows, [
        ("title", "Instrument"), ("type", "Type"), ("status", "Status"),
        ("decision_weight", "Decision Weight"), ("citation", "Citation"),
        ("source_url", "Source"),
    ])
    body += render_table_guide("How to read the policy index", [
        "This table complements legislation with national policy and guidance records.",
        "Scope helps identify whether a record applies to housing, infrastructure, or mixed pathways.",
        "Owner identifies the responsible body for updates.",
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
        "Use this page to trace the legal and policy instruments that shape planning decisions, including status, ownership, and source links.",
        next_steps=[
            ("plans.html", "Open plan hierarchy explorer"),
            ("contradictions.html", "Open contradictions dashboard"),
            ("sources.html", "Open source reference page"),
        ]))


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

    body += render_table_guide("How to read this table", [
        "Each row is one authority in scope.",
        "Growth and constraints summarise local context affecting planning decisions.",
        "Data quality tier indicates evidence coverage confidence.",
        "Use the profile link to drill down into detailed authority documents.",
    ])
    regions = sorted({r.get("region", "") for r in rows if r.get("region")})
    lpa_types = sorted({r.get("lpa_type", "") for r in rows if r.get("lpa_type")})
    cohorts = ["Cohort 1", "Cohort 2"]
    qualities = sorted({(quality_by_id.get(r["pilot_id"], {}).get("data_quality_tier", "") or "") for r in rows if quality_by_id.get(r["pilot_id"], {}).get("data_quality_tier", "")})

    body += '<section class="card"><div class="filter-row">'
    body += '<label class="filter-item">Search authorities<input type="search" data-table="plans-table" data-filter="search" placeholder="Type authority or context..." /></label>'
    body += '<label class="filter-item">Region<select data-table="plans-table" data-filter="region"><option value="">All</option>'
    for region in regions:
        body += f'<option value="{html.escape(region.lower())}">{html.escape(region)}</option>'
    body += '</select></label>'
    body += '<label class="filter-item">LPA type<select data-table="plans-table" data-filter="lpa_type"><option value="">All</option>'
    for lpa_type in lpa_types:
        body += f'<option value="{html.escape(lpa_type.lower())}">{html.escape(lpa_type)}</option>'
    body += '</select></label>'
    body += '<label class="filter-item">Cohort<select data-table="plans-table" data-filter="cohort"><option value="">All</option>'
    for cohort in cohorts:
        body += f'<option value="{html.escape(cohort.lower())}">{html.escape(cohort)}</option>'
    body += '</select></label>'
    body += '<label class="filter-item">Quality tier<select data-table="plans-table" data-filter="quality"><option value="">All</option>'
    for quality_tier in qualities:
        body += f'<option value="{html.escape(quality_tier.lower())}">{html.escape(quality_tier)}</option>'
    body += '</select></label>'
    body += '</div><p class="small" data-filter-count-for="plans-table"></p></section>'

    body += '<section class="card"><table id="plans-table"><thead><tr><th>Authority</th><th>Type</th><th>Region</th><th>Cohort</th><th>Growth</th><th>Constraints</th><th>Data Quality</th><th>Profile</th></tr></thead><tbody>'
    for row in rows:
        lpa_page = f"plans-{row['pilot_id'].lower()}.html"
        quality = quality_by_id.get(row["pilot_id"], {})
        cohort = cohort_for_pid(row["pilot_id"])
        search_blob = " ".join([
            row.get("lpa_name", ""),
            row.get("lpa_type", ""),
            row.get("region", ""),
            cohort,
            row.get("growth_context", ""),
            row.get("constraint_profile", ""),
            quality.get("data_quality_tier", ""),
        ]).strip().lower()
        attrs = (
            f'data-search="{html.escape(search_blob)}" '
            f'data-region="{html.escape(row.get("region", "").strip().lower())}" '
            f'data-cohort="{html.escape(cohort.strip().lower())}" '
            f'data-lpa_type="{html.escape(row.get("lpa_type", "").strip().lower())}" '
            f'data-quality="{html.escape((quality.get("data_quality_tier", "") or "").strip().lower())}"'
        )
        body += f"<tr {attrs}>"
        body += f"<td>{html.escape(row.get('lpa_name', ''))}</td>"
        body += f"<td>{html.escape(row.get('lpa_type', ''))}</td>"
        body += f"<td>{html.escape(row.get('region', ''))}</td>"
        body += f"<td>{html.escape(cohort)}</td>"
        body += f"<td>{html.escape(row.get('growth_context', ''))}</td>"
        body += f"<td>{html.escape(row.get('constraint_profile', ''))}</td>"
        body += f"<td>{html.escape(quality.get('data_quality_tier', ''))}</td>"
        body += f'<td><a href="{lpa_page}">View</a></td></tr>'
    body += "</tbody></table></section>"
    body += render_filter_script(
        "plans-table",
        ["search", "region", "cohort", "lpa_type", "quality"],
        shared_filters=["region", "lpa_type", "cohort", "quality"],
    )

    write(SITE / "plans.html", page(
        "Plan Hierarchy Explorer",
        "Mapped planning stack from national policy to neighbourhood plans and overlays.",
        "plans", body,
        "This page shows which authorities are in scope and how their planning documents align across national, local, and neighbourhood levels.",
        next_steps=[
            ("map.html", "Open authority map"),
            ("compare.html", "Open side-by-side compare"),
            ("reports.html", "Open downloadable reports"),
        ]))

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
        pb += render_table_guide("How to read this table", [
            "Each row is one tracked plan document for this authority.",
            "Status and date together indicate whether policy is current or transitional.",
            "Notes capture caveats that affect interpretation.",
            "Source links open the original authority publication where available.",
        ])
        pb += render_plan_docs_table(lpa_docs)
        write(SITE / f"plans-{row['pilot_id'].lower()}.html", page(
            f"{row['lpa_name']} Plan Profile",
            "Pilot authority planning document stack.",
            "plans", pb,
            "This authority profile summarises planning context, evidence quality, and tracked plan documents for the selected LPA.",
            purpose={
                "what": "A single authority planning profile with document stack and contextual evidence.",
                "who": "LPA teams, developers, and reviewers assessing authority-specific context.",
                "how": "Read the authority summary first, then review tracked documents and linked evidence.",
                "data": "Document and evidence records include source links, retrieval and review dates, and quality indicators.",
            },
            breadcrumbs=[
                ("index.html", "Overview"),
                ("plans.html", "Authority Insights"),
                ("plans.html", "Plans"),
                (f"plans-{row['pilot_id'].lower()}.html", row["lpa_name"]),
            ],
            next_steps=[
                ("compare.html", "Compare this authority with another"),
                ("benchmark.html", "View ranking context"),
                ("reports.html", "Download authority report bundle"),
            ]))


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
    body += render_table_guide("How to read this table", [
        "Each row is one contradiction record.",
        "Weighted score combines severity, frequency, legal risk, delay impact, and fixability.",
        "Higher scores indicate higher operational priority.",
        "Confidence and verification badges show evidence maturity.",
        "Click an Issue ID to open the full contradiction drill-down page.",
    ])
    body += render_filterable_table(rows, columns, "issues-table",
        ["issue_id", "scope", "issue_type", "affected_pathway", "summary", "confidence", "verification_state"])
    body += '<section class="card guided-only"><p class="small">Mobile tip: tap any table row to open a compact detail drawer.</p></section>'
    body += render_filter_script("issues-table",
        ["issue_id", "scope", "issue_type", "affected_pathway", "summary", "confidence", "verification_state"])
    body += render_table_enhancements_script("issues-table", presets=[
        {"label": "Housing only", "filters": {"affected_pathway": "housing"}},
        {"label": "National scope", "filters": {"scope": "national"}},
        {"label": "High confidence", "filters": {"confidence": "high"}},
    ])
    body += render_mobile_drawer_script("issues-table", [
        "Issue", "Scope", "Type", "Pathway", "Weighted Score", "Severity", "Delay", "Status", "Confidence", "Summary",
    ])

    write(SITE / "contradictions.html", page(
        "Contradictions and Bottlenecks",
        "Cross-layer conflicts scored with explicit weighting and confidence levels.",
        "contradictions", body,
        "Review the highest-friction conflicts in the planning system, with weighted scores and filters to focus on specific pathways or issue types.",
        next_steps=[
            ("bottlenecks.html", "Open bottleneck heatmap"),
            ("appeals.html", "Review appeal evidence"),
            ("recommendations.html", "Open linked recommendations"),
        ]))


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
    body += render_table_guide("How to read this table", [
        "Each row is one actionable recommendation.",
        "Priority and confidence support triage and sequencing.",
        "Implementation vehicle identifies whether delivery is guidance, SI, or statutory change.",
        "KPI and target define the measurable intended impact.",
        "Click a Recommendation ID to open the full recommendation drill-down page.",
    ])
    body += render_filterable_table(rows, columns, "recs-table",
        ["recommendation_id", "priority", "time_horizon", "policy_goal", "title",
         "implementation_vehicle", "confidence", "verification_state"])
    body += render_filter_script("recs-table",
        ["recommendation_id", "priority", "time_horizon", "policy_goal", "title",
         "implementation_vehicle", "confidence", "verification_state"])
    body += render_table_enhancements_script("recs-table", presets=[
        {"label": "High priority only", "filters": {"priority": "High"}},
        {"label": "Near term (0-12)", "filters": {"time_horizon": "0-12 months"}},
        {"label": "High confidence", "filters": {"confidence": "high"}},
    ])

    # Evidence traces
    body += '<section class="card"><h2>Evidence Traces</h2>'
    body += "<p>Each recommendation is linked to at least one official dataset row.</p></section>"
    body += render_table_guide("How to read the evidence tables", [
        "Source identifies the dataset or guidance used.",
        "Metric and baseline value explain the current-state evidence point.",
        "Baseline window shows the measurement period.",
        "Open source links to verify references directly.",
    ])
    for row in rows:
        rid = row["recommendation_id"]
        evs = ev_by_rec.get(rid, [])
        body += f'<section class="card"><h3><a href="{html.escape(recommendation_detail_page(rid))}">{html.escape(rid)}</a>: {html.escape(row["title"])}</h3>'
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
        "Each recommendation includes delivery details, expected outcomes, and direct links to supporting evidence rows.",
        next_steps=[
            ("roadmap.html", "Open implementation roadmap"),
            ("consultation.html", "Open consultation tracker"),
            ("sources.html", "Review source evidence index"),
        ]))


def build_contradiction_details(weights):
    issues = read_csv(ROOT / "data/issues/contradiction-register.csv")
    recs = read_csv(ROOT / "data/issues/recommendations.csv")
    evidence = read_csv(ROOT / "data/evidence/recommendation_evidence_links.csv")
    appeals = read_csv(ROOT / "data/evidence/appeal-decisions.csv")
    bottlenecks = read_csv(ROOT / "data/issues/bottleneck-heatmap.csv")
    lpas = read_csv(ROOT / "data/plans/pilot-lpas.csv")
    lpa_by_name = {r.get("lpa_name", "").strip().lower(): r for r in lpas}

    recs_by_issue = defaultdict(list)
    for rec in recs:
        for issue_id in split_pipe_values(rec.get("linked_issues", "")):
            recs_by_issue[issue_id].append(rec)

    ev_by_rec = defaultdict(list)
    for row in evidence:
        ev_by_rec[row.get("recommendation_id", "")].append(row)

    appeals_by_issue = defaultdict(list)
    for row in appeals:
        appeals_by_issue[row.get("linked_issue", "")].append(row)

    bottlenecks_by_issue = defaultdict(list)
    for row in bottlenecks:
        for issue_id in split_pipe_values(row.get("linked_issues", "")):
            bottlenecks_by_issue[issue_id].append(row)

    for issue in issues:
        issue_id = issue.get("issue_id", "")
        issue["weighted_score"] = f"{weighted_score(issue, weights):.2f}"
        linked_recs = recs_by_issue.get(issue_id, [])
        linked_appeals = appeals_by_issue.get(issue_id, [])
        linked_bottlenecks = bottlenecks_by_issue.get(issue_id, [])

        toc_html = render_detail_toc([
            ("summary", "Summary"),
            ("evidence", "Evidence"),
            ("connected-items", "Connected items"),
            ("actions", "Actions"),
        ])

        sidebar_meta = '<section class="card"><h3>At a glance</h3><ul>'
        sidebar_meta += f'<li><strong>Score:</strong> {html.escape(issue.get("weighted_score", ""))} / 5</li>'
        sidebar_meta += f'<li><strong>Type:</strong> {html.escape(issue.get("issue_type", ""))}</li>'
        sidebar_meta += f'<li><strong>Pathway:</strong> {html.escape(issue.get("affected_pathway", ""))}</li>'
        sidebar_meta += f'<li><strong>Confidence:</strong> {html.escape(issue.get("confidence", ""))}</li>'
        sidebar_meta += '</ul></section>'

        body = f'<div class="detail-layout"><div class="detail-sidebar">{toc_html}{sidebar_meta}</div><div class="detail-main">'

        body += '<section class="card" id="summary">'
        body += f'<h2>{html.escape(issue_id)}: {html.escape(issue.get("summary", ""))}</h2>'
        body += f'<p>{verification_badge(issue.get("verification_state", ""))} {confidence_badge(issue.get("confidence", ""))}</p>'
        body += '<ul>'
        body += f'<li><strong>Scope:</strong> {html.escape(issue.get("scope", ""))}</li>'
        body += f'<li><strong>Type:</strong> {html.escape(issue.get("issue_type", ""))}</li>'
        body += f'<li><strong>Pathway:</strong> {html.escape(issue.get("affected_pathway", ""))}</li>'
        body += f'<li><strong>Process stage:</strong> {html.escape(issue.get("process_stage", ""))}</li>'
        body += f'<li><strong>Weighted score:</strong> {html.escape(issue.get("weighted_score", ""))} / 5</li>'
        body += '</ul></section>'

        body += '<div class="detail-section-group"><p class="detail-section-group-heading">Scoring &amp; Classification</p>'
        body += '<section class="card"><h3>Score components</h3><ul>'
        body += f'<li>Severity: {html.escape(issue.get("severity_score", ""))}</li>'
        body += f'<li>Frequency: {html.escape(issue.get("frequency_score", ""))}</li>'
        body += f'<li>Legal risk: {html.escape(issue.get("legal_risk_score", ""))}</li>'
        body += f'<li>Delay impact: {html.escape(issue.get("delay_impact_score", ""))}</li>'
        body += f'<li>Fixability: {html.escape(issue.get("fixability_score", ""))}</li>'
        body += '</ul></section>'

        body += '<section class="card"><h3>Linked instruments</h3><p>'
        instruments = split_pipe_values(issue.get("linked_instruments", ""))
        body += ", ".join(html.escape(item) for item in instruments) if instruments else "n/a"
        body += '</p></section></div>'

        body += '<div class="detail-section-group"><p class="detail-section-group-heading">Connected Items</p>'
        body += '<section class="card" id="connected-items"><h3>Connected recommendations</h3>'
        if linked_recs:
            body += '<table><thead><tr><th>ID</th><th>Title</th><th>Priority</th><th>Horizon</th><th>Evidence links</th></tr></thead><tbody>'
            for rec in linked_recs:
                rid = rec.get("recommendation_id", "")
                body += '<tr>'
                body += f'<td><a href="{html.escape(recommendation_detail_page(rid))}">{html.escape(rid)}</a></td>'
                body += f'<td>{html.escape(rec.get("title", ""))}</td>'
                body += f'<td>{html.escape(rec.get("priority", ""))}</td>'
                body += f'<td>{html.escape(rec.get("time_horizon", ""))}</td>'
                body += f'<td>{html.escape(str(len(ev_by_rec.get(rid, []))))}</td>'
                body += '</tr>'
            body += '</tbody></table>'
        else:
            body += '<p><em>No linked recommendations recorded.</em></p>'
        body += '</section>'

        body += '<section class="card" id="evidence"><h3>Appeal evidence</h3>'
        if linked_appeals:
            body += '<table><thead><tr><th>Reference</th><th>LPA</th><th>Date</th><th>Outcome</th><th>Finding</th><th>Source</th></tr></thead><tbody>'
            for ap in linked_appeals:
                body += '<tr>'
                body += f'<td>{html.escape(ap.get("pins_reference", ""))}</td>'
                body += f'<td>{html.escape(ap.get("lpa", ""))}</td>'
                body += f'<td>{html.escape(ap.get("decision_date", ""))}</td>'
                body += f'<td>{html.escape(ap.get("outcome", ""))}</td>'
                body += f'<td>{html.escape(ap.get("inspector_finding", ""))}</td>'
                src = ap.get("source_url", "")
                if src:
                    body += f'<td><a href="{html.escape(src)}" target="_blank" rel="noopener noreferrer">Source</a></td>'
                else:
                    body += '<td>—</td>'
                body += '</tr>'
            body += '</tbody></table>'
        else:
            body += '<p><em>No direct appeal records linked.</em></p>'
        body += '</section>'

        body += '<section class="card"><h3>Related bottleneck stages</h3>'
        if linked_bottlenecks:
            body += '<table><thead><tr><th>ID</th><th>Stage</th><th>Pathway</th><th>Median delay (weeks)</th></tr></thead><tbody>'
            for b in linked_bottlenecks:
                body += '<tr>'
                body += f'<td>{html.escape(b.get("stage_id", ""))}</td>'
                body += f'<td>{html.escape(b.get("process_stage", ""))}</td>'
                body += f'<td>{html.escape(b.get("pathway", ""))}</td>'
                body += f'<td>{html.escape(b.get("median_delay_weeks", ""))}</td>'
                body += '</tr>'
            body += '</tbody></table>'
        else:
            body += '<p><em>No related bottleneck rows linked.</em></p>'
        body += '</section>'

        body += '<section class="card"><h3>Affected authorities observed in appeals</h3>'
        seen = set()
        authority_links = []
        for ap in linked_appeals:
            key = ap.get("lpa", "").strip().lower()
            if not key or key in seen:
                continue
            seen.add(key)
            lpa = lpa_by_name.get(key)
            if lpa:
                pid = lpa.get("pilot_id", "")
                authority_links.append(f'<a href="plans-{pid.lower()}.html">{html.escape(lpa.get("lpa_name", ""))}</a>')
            else:
                authority_links.append(html.escape(ap.get("lpa", "")))
        body += '<p>' + (", ".join(authority_links) if authority_links else "No in-scope authorities linked via appeals.") + '</p>'
        body += '</section></div>'

        type_q = html.escape(query_value(issue.get("issue_type", "")))
        path_q = html.escape(query_value(issue.get("affected_pathway", "")))
        scope_q = html.escape(query_value(issue.get("scope", "")))
        body += '<section class="card" id="actions"><h3>Context links</h3><ul>'
        body += f'<li><a href="contradictions.html#issue_type={type_q}">Back to contradictions filtered by type</a></li>'
        body += f'<li><a href="contradictions.html#affected_pathway={path_q}">Back to contradictions filtered by pathway</a></li>'
        body += f'<li><a href="contradictions.html#scope={scope_q}">Back to contradictions filtered by scope</a></li>'
        body += '</ul></section>'
        body += '<section class="card"><h3>Users also viewed</h3><ul>'
        body += '<li><a href="benchmark.html">Benchmark dashboard</a></li>'
        body += '<li><a href="reports.html">Authority reports</a></li>'
        body += '<li><a href="roadmap.html">Implementation roadmap</a></li>'
        body += '</ul></section>'
        body += '</div></div>'  # close .detail-main and .detail-layout

        write(SITE / issue_detail_page(issue_id), page(
            f"{issue_id} Detail",
            "Detailed contradiction drill-down with linked recommendations and evidence.",
            "contradictions", body,
            "Use this page to inspect scoring, evidence, and connected recommendations for a single contradiction record.",
            breadcrumbs=[
                ("index.html", "Overview"),
                ("contradictions.html", "System Analysis"),
                ("contradictions.html", "Contradictions"),
                (issue_detail_page(issue_id), issue_id),
            ],
            next_steps=[
                ("contradictions.html", "Back to contradiction register"),
                ("recommendations.html", "Open recommendations"),
                ("appeals.html", "Open appeal evidence"),
            ]))


def build_recommendation_details():
    recs = read_csv(ROOT / "data/issues/recommendations.csv")
    statuses = read_csv(ROOT / "data/issues/recommendation-status.csv")
    evidence = read_csv(ROOT / "data/evidence/recommendation_evidence_links.csv")
    issues = read_csv(ROOT / "data/issues/contradiction-register.csv")
    roadmap = read_csv(ROOT / "data/issues/implementation-roadmap.csv")
    appeals = read_csv(ROOT / "data/evidence/appeal-decisions.csv")
    lpas = read_csv(ROOT / "data/plans/pilot-lpas.csv")

    status_by_id = {row.get("recommendation_id", ""): row for row in statuses}
    issue_by_id = {row.get("issue_id", ""): row for row in issues}
    lpa_by_name = {r.get("lpa_name", "").strip().lower(): r for r in lpas}

    ev_by_rec = defaultdict(list)
    for row in evidence:
        ev_by_rec[row.get("recommendation_id", "")].append(row)

    milestones_by_rec = defaultdict(list)
    for row in roadmap:
        for rid in split_pipe_values(row.get("linked_recommendations", "")):
            milestones_by_rec[rid].append(row)

    recs_by_issue = defaultdict(list)
    for rec in recs:
        for issue_id in split_pipe_values(rec.get("linked_issues", "")):
            recs_by_issue[issue_id].append(rec)

    appeals_by_issue = defaultdict(list)
    for row in appeals:
        appeals_by_issue[row.get("linked_issue", "")].append(row)

    for rec in recs:
        rid = rec.get("recommendation_id", "")
        linked_issue_ids = split_pipe_values(rec.get("linked_issues", ""))
        linked_issues = [issue_by_id[iid] for iid in linked_issue_ids if iid in issue_by_id]
        linked_evidence = ev_by_rec.get(rid, [])
        linked_milestones = milestones_by_rec.get(rid, [])
        status = status_by_id.get(rid, {})

        toc_html = render_detail_toc([
            ("summary", "Summary"),
            ("evidence", "Evidence"),
            ("connected-items", "Connected items"),
            ("actions", "Actions"),
        ])

        sidebar_meta = '<section class="card"><h3>At a glance</h3><ul>'
        sidebar_meta += f'<li><strong>Priority:</strong> {html.escape(rec.get("priority", ""))}</li>'
        sidebar_meta += f'<li><strong>Horizon:</strong> {html.escape(rec.get("time_horizon", ""))}</li>'
        sidebar_meta += f'<li><strong>Goal:</strong> {html.escape(rec.get("policy_goal", ""))}</li>'
        sidebar_meta += f'<li><strong>Confidence:</strong> {html.escape(rec.get("confidence", ""))}</li>'
        sidebar_meta += '</ul></section>'

        body = f'<div class="detail-layout"><div class="detail-sidebar">{toc_html}{sidebar_meta}</div><div class="detail-main">'

        body += '<section class="card" id="summary">'
        body += f'<h2>{html.escape(rid)}: {html.escape(rec.get("title", ""))}</h2>'
        body += f'<p>{verification_badge(rec.get("verification_state", ""))} {confidence_badge(rec.get("confidence", ""))}</p>'
        body += '<ul>'
        body += f'<li><strong>Priority:</strong> {html.escape(rec.get("priority", ""))}</li>'
        body += f'<li><strong>Horizon:</strong> {html.escape(rec.get("time_horizon", ""))}</li>'
        body += f'<li><strong>Policy goal:</strong> {html.escape(rec.get("policy_goal", ""))}</li>'
        body += f'<li><strong>Owner:</strong> {html.escape(rec.get("delivery_owner", ""))}</li>'
        body += f'<li><strong>Vehicle:</strong> {html.escape(rec.get("implementation_vehicle", ""))}</li>'
        body += '</ul></section>'

        body += '<section class="card"><h3>Outcome target</h3>'
        body += f'<p><strong>KPI:</strong> {html.escape(rec.get("kpi_primary", ""))}</p>'
        body += f'<p><strong>Target:</strong> {html.escape(rec.get("target", ""))}</p>'
        body += '</section>'

        body += '<section class="card" id="actions"><h3>Status timeline</h3>'
        body += '<table><thead><tr><th>Stage</th><th>Value</th></tr></thead><tbody>'
        body += f'<tr><td>Submission status</td><td>{html.escape(status.get("submission_status", "Not set"))}</td></tr>'
        body += f'<tr><td>Submitted to</td><td>{html.escape(status.get("submitted_to", "")) or "—"}</td></tr>'
        body += f'<tr><td>Submission date</td><td>{html.escape(status.get("submission_date", "")) or "—"}</td></tr>'
        body += f'<tr><td>Response received</td><td>{html.escape(status.get("response_received", "")) or "—"}</td></tr>'
        body += f'<tr><td>Response summary</td><td>{html.escape(status.get("response_summary", "")) or "—"}</td></tr>'
        body += f'<tr><td>Next action</td><td>{html.escape(status.get("next_action", "")) or "—"}</td></tr>'
        body += '</tbody></table></section>'

        body += '<section class="card" id="connected-items"><h3>Linked contradictions</h3>'
        if linked_issues:
            body += '<table><thead><tr><th>ID</th><th>Summary</th><th>Stage</th><th>Pathway</th></tr></thead><tbody>'
            for issue in linked_issues:
                iid = issue.get("issue_id", "")
                body += '<tr>'
                body += f'<td><a href="{html.escape(issue_detail_page(iid))}">{html.escape(iid)}</a></td>'
                body += f'<td>{html.escape(issue.get("summary", ""))}</td>'
                body += f'<td>{html.escape(issue.get("process_stage", ""))}</td>'
                body += f'<td>{html.escape(issue.get("affected_pathway", ""))}</td>'
                body += '</tr>'
            body += '</tbody></table>'
        else:
            body += '<p><em>No linked contradictions recorded.</em></p>'
        body += '</section>'

        body += '<section class="card" id="evidence"><h3>Evidence links</h3>'
        if linked_evidence:
            body += '<table><thead><tr><th>Source</th><th>Metric</th><th>Baseline</th><th>Window</th><th>Source URL</th></tr></thead><tbody>'
            for ev in linked_evidence:
                body += '<tr>'
                body += f'<td>{html.escape(ev.get("source_dataset", ""))}</td>'
                body += f'<td>{html.escape(ev.get("metric_name", ""))}</td>'
                body += f'<td>{html.escape(ev.get("baseline_value", ""))}</td>'
                body += f'<td>{html.escape(ev.get("baseline_window", ""))}</td>'
                src = ev.get("source_url", "")
                if src:
                    body += f'<td><a href="{html.escape(src)}" target="_blank" rel="noopener noreferrer">Source</a></td>'
                else:
                    body += '<td>—</td>'
                body += '</tr>'
            body += '</tbody></table>'
        else:
            body += '<p><em>No evidence links recorded.</em></p>'
        body += '</section>'

        body += '<section class="card"><h3>Implementation milestones</h3>'
        if linked_milestones:
            body += '<table><thead><tr><th>Milestone</th><th>Phase</th><th>Window</th><th>Owner</th><th>Status metric</th></tr></thead><tbody>'
            for m in linked_milestones:
                body += '<tr>'
                body += f'<td>{html.escape(m.get("action", ""))}</td>'
                body += f'<td>{html.escape(m.get("phase", ""))}</td>'
                body += f'<td>{html.escape(m.get("window", ""))}</td>'
                body += f'<td>{html.escape(m.get("owner", ""))}</td>'
                body += f'<td>{html.escape(m.get("status_metric", ""))}</td>'
                body += '</tr>'
            body += '</tbody></table>'
        else:
            body += '<p><em>No roadmap milestones explicitly linked.</em></p>'
        body += '</section>'

        body += '<section class="card"><h3>Related authorities observed in linked issue appeals</h3>'
        seen = set()
        authority_links = []
        for issue_id in linked_issue_ids:
            for ap in appeals_by_issue.get(issue_id, []):
                key = ap.get("lpa", "").strip().lower()
                if not key or key in seen:
                    continue
                seen.add(key)
                lpa = lpa_by_name.get(key)
                if lpa:
                    pid = lpa.get("pilot_id", "")
                    authority_links.append(f'<a href="plans-{pid.lower()}.html">{html.escape(lpa.get("lpa_name", ""))}</a>')
                else:
                    authority_links.append(html.escape(ap.get("lpa", "")))
        body += '<p>' + (", ".join(authority_links) if authority_links else "No in-scope authority links observed.") + '</p>'
        body += '</section>'

        related_recs = []
        seen_ids = set([rid])
        for issue_id in linked_issue_ids:
            for candidate in recs_by_issue.get(issue_id, []):
                cid = candidate.get("recommendation_id", "")
                if cid in seen_ids:
                    continue
                seen_ids.add(cid)
                related_recs.append(candidate)

        body += '<section class="card"><h3>Connected recommendations</h3>'
        if related_recs:
            body += '<ul>'
            for candidate in sorted(related_recs, key=lambda r: r.get("recommendation_id", "")):
                cid = candidate.get("recommendation_id", "")
                body += f'<li><a href="{html.escape(recommendation_detail_page(cid))}">{html.escape(cid)}</a> — {html.escape(candidate.get("title", ""))}</li>'
            body += '</ul>'
        else:
            body += '<p><em>No additional connected recommendations found.</em></p>'
        body += '</section>'

        pr_q = html.escape(query_value(rec.get("priority", "")))
        hz_q = html.escape(query_value(rec.get("time_horizon", "")))
        body += '<section class="card"><h3>Context links</h3><ul>'
        body += f'<li><a href="recommendations.html#priority={pr_q}">Back to recommendations filtered by priority</a></li>'
        body += f'<li><a href="recommendations.html#time_horizon={hz_q}">Back to recommendations filtered by horizon</a></li>'
        body += '</ul></section>'
        body += '<section class="card"><h3>Users also viewed</h3><ul>'
        body += '<li><a href="coverage.html">Coverage tracker</a></li>'
        body += '<li><a href="consultation.html">Consultation status</a></li>'
        body += '<li><a href="metric-methods.html">Metric methods appendix</a></li>'
        body += '</ul></section>'
        body += '</div></div>'  # close .detail-main and .detail-layout

        write(SITE / recommendation_detail_page(rid), page(
            f"{rid} Detail",
            "Detailed recommendation drill-down with status timeline and evidence links.",
            "recommendations", body,
            "Use this page to inspect implementation context, linked contradictions, and evidence rows for a single recommendation.",
            breadcrumbs=[
                ("index.html", "Overview"),
                ("recommendations.html", "Recommendations"),
                ("recommendations.html", "Recommendations"),
                (recommendation_detail_page(rid), rid),
            ],
            next_steps=[
                ("recommendations.html", "Back to recommendations"),
                ("roadmap.html", "Open implementation roadmap"),
                ("consultation.html", "Open consultation tracker"),
            ]))


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
    body += render_table_guide("How to read roadmap tables", [
        "Each row is a milestone or action in the implementation sequence.",
        "Read top-to-bottom to follow intended delivery order.",
        "Dependencies identify prerequisites for later milestones.",
        "Use owner and metric columns to assign accountability.",
    ])
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
        "This timeline shows how reforms can be phased, who leads delivery, and which dependencies affect sequencing.",
        next_steps=[
            ("consultation.html", "Open consultation and status"),
            ("recommendations.html", "Return to recommendations"),
            ("reports.html", "Open authority report bundles"),
        ]))


def build_baselines():
    rows = read_csv(ROOT / "data/evidence/official_baseline_metrics.csv")
    body = '<section class="card"><p>Official baseline metrics from GOV.UK planning statistics and PINS casework data. Window: latest 4 quarters.</p></section>'
    body += render_table_guide("How to read this table", [
        "Each row is one baseline metric with source and period context.",
        "Compare geography and pathway before drawing conclusions.",
        "Period and retrieved_at dates help assess recency.",
        "Use these values as current-state benchmarks for reform impact.",
    ])
    body += render_table(rows, [
        ("metric_id", "ID"), ("metric_name", "Metric"), ("source_table", "Source"),
        ("geography", "Geography"), ("pathway", "Pathway"), ("value", "Value"),
        ("unit", "Unit"), ("period", "Period"),
    ])
    write(SITE / "baselines.html", page(
        "Official Baseline Metrics",
        "KPI baselines from GOV.UK planning statistics and Planning Inspectorate data.",
        "baselines", body,
        "Use these baseline metrics to understand current performance levels before assessing the impact of proposed reforms.",
        next_steps=[
            ("benchmark.html", "Open benchmark dashboard"),
            ("reports.html", "Open authority reports"),
            ("recommendations.html", "Open recommendations"),
        ]))


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
    body += '<p class="small">Stages are listed in pathway order from pre-application to condition discharge.</p>'
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
    body += render_table_guide("How to read this table", [
        "Each row is one process-stage bottleneck with pathway context.",
        "Median delay shows central delay impact for that bottleneck pattern.",
        "Frequency indicates how often the issue appears in tracked records.",
        "Use linked issues to cross-reference contradiction evidence.",
    ])
    body += render_table(rows, columns)

    write(SITE / "bottlenecks.html", page(
        "Bottleneck Heatmap",
        "Process delay analysis across all six planning stages with severity and pathway breakdown.",
        "bottlenecks", body,
        "This heatmap highlights where delays concentrate in the planning process and which pathways are most affected.",
        next_steps=[
            ("contradictions.html", "Open contradiction register"),
            ("appeals.html", "Review appeals evidence"),
            ("recommendations.html", "Open reform recommendations"),
        ]))


# --- Audience views ---

def build_audience_policymakers():
    recs = read_csv(ROOT / "data/issues/recommendations.csv")
    issues = read_csv(ROOT / "data/issues/contradiction-register.csv")
    body = '<section class="card"><h2>Priority Reform Actions</h2>'
    body += "<p>Recommendations ranked by priority with delivery ownership and implementation vehicle.</p></section>"
    body += '<section class="card"><h3>If you only do 3 things</h3><ol><li>Prioritise high-confidence recommendations with statutory blockers.</li><li>Use roadmap dependencies to sequence delivery commitments.</li><li>Track submission and response status via consultation page.</li></ol></section>'
    body += render_table_guide("How to read this table", [
        "Priority and horizon show sequencing urgency.",
        "Owner and vehicle indicate delivery accountability and route.",
        "Confidence signals strength of supporting evidence.",
    ])
    body += render_table(recs, [
        ("recommendation_id", "ID"), ("priority", "Priority"), ("title", "Recommendation"),
        ("delivery_owner", "Owner"), ("implementation_vehicle", "Vehicle"),
        ("time_horizon", "Horizon"), ("confidence", "Confidence"),
    ])
    body += '<section class="card"><h2>System Friction Summary</h2>'
    body += "<p>Top contradictions requiring policy intervention.</p></section>"
    body += render_table_guide("How to read this table", [
        "Issue type and scope show where intervention is needed.",
        "Summary gives the practical policy conflict in plain language.",
        "Use confidence as a guide to evidence maturity.",
    ])
    body += render_table(issues, [
        ("issue_id", "Issue"), ("issue_type", "Type"), ("scope", "Scope"),
        ("summary", "Summary"), ("confidence", "Confidence"),
    ])
    write(SITE / "audience-policymakers.html", page(
        "For Policy Makers",
        "Priority reforms, system friction, and implementation pathways.",
        "policymakers", body,
        "A policy-focused view of priority reforms, core friction points, and delivery routes for national and local action.",
        next_steps=[
            ("recommendations.html", "Open full recommendations"),
            ("roadmap.html", "Open implementation roadmap"),
            ("consultation.html", "Open consultation tracker"),
        ]))


def build_audience_lpas():
    recs = read_csv(ROOT / "data/issues/recommendations.csv")
    lpa_recs = [r for r in recs if "LPA" in r.get("delivery_owner", "")]
    body = '<section class="card"><h2>Actions for Local Planning Authorities</h2>'
    body += "<p>Recommendations where LPAs are lead or co-delivery owners.</p></section>"
    body += '<section class="card"><h3>If you only do 3 things</h3><ol><li>Prioritise validation and pre-application consistency actions.</li><li>Use benchmark and reports to compare peers.</li><li>Track data quality and update stale local records.</li></ol></section>'
    body += render_table_guide("How to read this table", [
        "Each row is one LPA-relevant recommendation.",
        "KPI and target describe measurable outcomes.",
        "Use horizon to phase internal workplans.",
    ])
    body += render_table(lpa_recs if lpa_recs else recs, [
        ("recommendation_id", "ID"), ("title", "Recommendation"),
        ("time_horizon", "Horizon"), ("kpi_primary", "KPI"), ("target", "Target"),
    ])
    baselines = read_csv(ROOT / "data/evidence/official_baseline_metrics.csv")
    pilot_baselines = [b for b in baselines if b.get("geography", "").startswith("LPA")]
    if pilot_baselines:
        body += '<section class="card"><h2>Pilot LPA Baselines</h2></section>'
        body += render_table_guide("How to read this table", [
            "Each metric shows a baseline for pilot authorities.",
            "Compare values by geography and unit only where equivalent.",
            "Use as starting point before assessing interventions.",
        ])
        body += render_table(pilot_baselines, [
            ("metric_id", "ID"), ("metric_name", "Metric"), ("geography", "Authority"),
            ("value", "Value"), ("unit", "Unit"),
        ])
    write(SITE / "audience-lpas.html", page(
        "For Local Planning Authorities",
        "LPA-specific actions, baselines, and KPI targets.",
        "lpas", body,
        "An operational view for LPAs showing actionable recommendations, local baselines, and measurable KPI targets.",
        next_steps=[
            ("benchmark.html", "Open benchmark dashboard"),
            ("reports.html", "Download LPA report bundles"),
            ("data-health.html", "Check data freshness"),
        ]))


def build_audience_developers():
    recs = read_csv(ROOT / "data/issues/recommendations.csv")
    body = '<section class="card"><h2>What This Means for Developers</h2>'
    body += "<p>Reforms that affect submission requirements, determination timelines, and design baseline certainty.</p></section>"
    body += '<section class="card"><h3>If you only do 3 things</h3><ol><li>Use compare and benchmark pages to understand authority variation.</li><li>Track recommendations affecting validation and design certainty.</li><li>Use plan profile pages before preparing major submissions.</li></ol></section>'
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
        "A delivery-focused summary of reforms that affect application requirements, decision predictability, and project timelines.",
        next_steps=[
            ("plans.html", "Open authority plan profiles"),
            ("compare.html", "Open authority compare"),
            ("recommendations.html", "Open recommendation details"),
        ]))


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
    body += '<section class="card"><h3>If you only do 3 things</h3><ol><li>Read the contradiction summary to understand core system issues.</li><li>Review recommendations to see proposed fixes.</li><li>Use consultation page to track submission progress.</li></ol></section>'
    write(SITE / "audience-public.html", page(
        "For the Public",
        "Plain-language summary of findings and proposed planning improvements.",
        "public", body,
        "A plain-language explanation of the problems identified, why they matter, and what changes are being proposed.",
        next_steps=[
            ("contradictions.html", "Open contradiction summary"),
            ("recommendations.html", "Open recommendations"),
            ("consultation.html", "Open consultation status"),
        ]))


def build_methodology():
    body = '<section class="card"><h2>Evidence Standard</h2>'
    body += "<p>Every recommendation references at least one official dataset row from GOV.UK planning statistics or PINS casework data.</p></section>"
    body += '<section class="card"><h2>Scoring Model</h2>'
    body += "<p>Issues scored on five dimensions with explicit weights. See <code>data/schemas/scoring.json</code>.</p></section>"
    body += '<section class="card"><h2>Verification States</h2>'
    body += "<p>Records carry a verification state: <strong>draft</strong>, <strong>verified</strong>, or <strong>legal-reviewed</strong>.</p></section>"
    body += '<section class="card"><h2>Confidence Levels</h2>'
    body += "<p>Findings carry confidence labels: <strong>high</strong>, <strong>medium</strong>, or <strong>low</strong>.</p></section>"
    body += '<section class="card"><h2>Derived authority metrics</h2>'
    body += '<p>Benchmark and report pages include derived indicators for validation rework, delegated share, plan age, consultation lag, and backlog pressure. These are analytical estimates and are shown with confidence labels tied to authority data-quality tier.</p></section>'
    body += '<section class="card"><p>See <a href="metric-methods.html">metric methods appendix</a> for formula notes and interpretation guidance.</p></section>'
    body += '<section class="card"><h2>Validation</h2>'
    body += "<p>Schema, FK, enum, and unique-ID checks run via <code>scripts/validate_data.py</code>. "
    body += "Internal links checked via <code>scripts/check_links.py</code>.</p></section>"
    body += '<section class="card"><h2>Governance cadence</h2>'
    body += '<ul>'
    body += '<li><strong>Monthly:</strong> refresh datasets, regenerate site, and review data health warnings.</li>'
    body += '<li><strong>Quarterly:</strong> publish methodology and metric provenance update notes with each GOV.UK statistics cycle.</li>'
    body += '<li><strong>Annually:</strong> reconcile legal and policy references against current in-force instruments and guidance.</li>'
    body += '</ul></section>'
    body += '<section class="card"><h2>Owner responsibilities</h2>'
    body += '<ul>'
    body += '<li><strong>Data lead:</strong> schema updates, quality thresholds, and freshness triage.</li>'
    body += '<li><strong>Data engineer:</strong> ingestion reliability and build automation.</li>'
    body += '<li><strong>Methodology lead:</strong> confidence rules, provenance policy, and publication notes.</li>'
    body += '<li><strong>Product/editorial lead:</strong> release notes, audience guidance, and change communication.</li>'
    body += '</ul></section>'
    body += '<section class="card"><h2>How scoring works in 3 steps</h2><ol><li>Collect issue-level values for severity, frequency, legal risk, delay impact, and fixability.</li><li>Apply explicit weighting from scoring.json.</li><li>Rank and review with confidence and verification labels.</li></ol></section>'
    write(SITE / "methodology.html", page(
        "Methodology",
        "Taxonomy, scoring model, evidence standards, and quality controls.",
        "methodology", body,
        "This page explains how datasets are scored, validated, and linked to evidence so findings are transparent and reproducible.",
        next_steps=[
            ("metric-methods.html", "Open metric methods appendix"),
            ("sources.html", "Open sources and citations"),
            ("exports.html", "Open data exports"),
            ("data-health.html", "Open data health monitoring"),
        ]))


def build_metric_methods():
    body = '<section class="card"><h2>Purpose</h2>'
    body += '<p>This appendix defines how benchmark and report metrics are calculated, what each metric signals, and which inputs are official versus analytical estimates.</p></section>'

    body += render_table_guide("How to use this appendix", [
        "Use metric definitions before comparing authorities.",
        "Check the provenance and confidence line for each metric.",
        "Treat analytical estimates as directional indicators, not statutory facts.",
        "Re-check formulas after major methodology releases.",
    ])

    body += '<section class="card" id="major-speed"><h2>Speed (%)</h2>'
    body += '<p><strong>Definition:</strong> Latest major applications determined in time for each authority.</p>'
    body += '<p><strong>Formula:</strong> value from latest quarter in <code>lpa-quarterly-trends.csv</code> (<code>major_in_time_pct</code>).</p>'
    body += '<p><strong>Provenance:</strong> official statistics (GOV.UK P151).</p></section>'

    body += '<section class="card" id="speed-delta"><h2>4Q Delta (pp)</h2>'
    body += '<p><strong>Definition:</strong> Change in major decision speed over the tracked window.</p>'
    body += '<p><strong>Formula:</strong> latest <code>major_in_time_pct</code> minus first available <code>major_in_time_pct</code> for each authority.</p>'
    body += '<p><strong>Provenance:</strong> official statistics (derived from GOV.UK P151 trend series).</p></section>'

    body += '<section class="card" id="appeal-rate"><h2>Appeal %</h2>'
    body += '<p><strong>Definition:</strong> Latest appeals overturned percentage.</p>'
    body += '<p><strong>Formula:</strong> value from latest quarter in <code>lpa-quarterly-trends.csv</code> (<code>appeals_overturned_pct</code>).</p>'
    body += '<p><strong>Provenance:</strong> official statistics (GOV.UK P152).</p></section>'

    body += '<section class="card" id="issues"><h2>Issues and High Severity</h2>'
    body += '<p><strong>Definition:</strong> Count of linked issues and high-severity subset for each authority.</p>'
    body += '<p><strong>Formula:</strong> direct values from <code>lpa-issue-incidence.csv</code> fields <code>total_linked_issues</code> and <code>high_severity_issues</code>.</p>'
    body += '<p><strong>Provenance:</strong> analytical estimate layer.</p></section>'

    body += '<section class="card" id="quality-tier"><h2>Quality tier and coverage score</h2>'
    body += '<p><strong>Definition:</strong> Evidence completeness and quality indicator for each authority.</p>'
    body += '<p><strong>Formula:</strong> values from <code>lpa-data-quality.csv</code> (<code>data_quality_tier</code>, <code>coverage_score</code>).</p>'
    body += '<p><strong>Provenance:</strong> analytical estimate layer.</p></section>'

    body += '<section class="card" id="validation-rework"><h2>Validation rework proxy (%)</h2>'
    body += '<p><strong>Definition:</strong> Estimated share of submissions requiring rework at validation stage.</p>'
    body += '<p><strong>Formula:</strong> <code>BAS-007 baseline + quality-tier adjustment + issue-pressure adjustment + trend-volatility adjustment</code>, lower-bounded at 5.0.</p>'
    body += '<p><strong>Provenance:</strong> analytical estimate seeded by official baseline metric.</p></section>'

    body += '<section class="card" id="delegated-share"><h2>Delegated decision share proxy (%)</h2>'
    body += '<p><strong>Definition:</strong> Estimated proportion of decisions made under delegated powers.</p>'
    body += '<p><strong>Formula:</strong> authority-type baseline adjusted by high-severity issue load, latest speed, and latest appeal rate; bounded to 70-95.</p>'
    body += '<p><strong>Provenance:</strong> analytical estimate.</p></section>'

    body += '<section class="card" id="plan-age"><h2>Plan age (years)</h2>'
    body += '<p><strong>Definition:</strong> Years since latest adopted or in-force tracked plan document.</p>'
    body += '<p><strong>Formula:</strong> <code>(today - max(adoption_or_publication_date of adopted/in-force docs)) / 365.25</code>.</p>'
    body += '<p><strong>Provenance:</strong> analytical derivation from authority plan-document records.</p></section>'

    body += '<section class="card" id="consult-lag"><h2>Consultation lag proxy (weeks)</h2>'
    body += '<p><strong>Definition:</strong> Estimated consultation-stage delay pressure.</p>'
    body += '<p><strong>Formula:</strong> baseline constant + high-severity adjustment + stage-risk adjustment + quality-tier adjustment; capped at 10.0 weeks.</p>'
    body += '<p><strong>Provenance:</strong> analytical estimate.</p></section>'

    body += '<section class="card" id="backlog-pressure"><h2>Backlog pressure index (0-100)</h2>'
    body += '<p><strong>Definition:</strong> Composite pressure indicator for authority planning throughput risk.</p>'
    body += '<p><strong>Formula:</strong> weighted sum of issue count, high-severity count, speed gap vs England average, and plan-age factor; capped at 100.</p>'
    body += '<p><strong>Provenance:</strong> analytical estimate.</p></section>'

    body += '<section class="card" id="analytical-confidence"><h2>Analytical confidence</h2>'
    body += '<p><strong>Definition:</strong> Confidence label for estimated metrics.</p>'
    body += '<p><strong>Formula:</strong> quality tier A -> high, B -> medium, C/other -> low.</p>'
    body += '<p><strong>Usage:</strong> confidence applies to analytical estimates only, not official series.</p></section>'

    write(SITE / "metric-methods.html", page(
        "Metric Methods Appendix",
        "Definitions, formulas, provenance, and confidence logic for benchmark and report metrics.",
        "metric-methods", body,
        "Use this appendix to interpret benchmark/report indicators correctly and to understand which values are official statistics versus analytical estimates.",
        purpose={
            "what": "Per-metric definitions, formulas, provenance, and confidence rules used in benchmark and report outputs.",
            "who": "Analysts, policy teams, and reviewers validating interpretation and comparability.",
            "how": "Open a metric section from tooltip method links, then verify formula scope and provenance before comparing LPAs.",
            "data": "Formulas are implemented in scripts/build_site.py and draw from trend, issue, quality, and plan-document datasets.",
        },
        next_steps=[
            ("benchmark.html", "Return to benchmark"),
            ("reports.html", "Return to reports"),
            ("methodology.html", "Return to methodology"),
        ]))


def build_sources():
    evidence = read_csv(ROOT / "data/evidence/recommendation_evidence_links.csv")
    baselines = read_csv(ROOT / "data/evidence/official_baseline_metrics.csv")
    body = '<section class="card"><h2>Evidence Links</h2></section>'
    body += '<section class="card"><h3>Source reliability tiers</h3><ul><li><strong>Tier 1:</strong> Official statistics and statutory publications.</li><li><strong>Tier 2:</strong> Formal policy guidance and ministerial publications.</li><li><strong>Tier 3:</strong> Analytical estimates and inferred operational evidence.</li></ul></section>'
    body += render_table_guide("How to read this table", [
        "Each row links a recommendation to a source record.",
        "Baseline values and windows describe current evidence levels.",
        "Use source URLs to verify references directly.",
    ])
    body += render_table(evidence, [
        ("link_id", "ID"), ("recommendation_id", "Rec"), ("source_dataset", "Source"),
        ("metric_name", "Metric"), ("baseline_value", "Baseline"), ("source_url", "URL"),
    ])
    body += '<section class="card"><h2>Official Baseline Metrics</h2></section>'
    body += render_table_guide("How to read this table", [
        "Each row is a baseline metric with source table and geography.",
        "Use values with period and source context for valid comparisons.",
        "Official source links provide direct verification.",
    ])
    body += render_table(baselines, [
        ("metric_id", "ID"), ("metric_name", "Metric"), ("source_table", "Table"),
        ("geography", "Geography"), ("value", "Value"), ("source_url", "URL"),
    ])
    write(SITE / "sources.html", page(
        "Sources and Citations",
        "Official data sources, evidence links, and baseline metrics.",
        "sources", body,
        "Use this reference page to verify evidence links, source tables, and citations used throughout the analysis.",
        next_steps=[
            ("methodology.html", "Open methodology"),
            ("recommendations.html", "Open recommendations"),
            ("exports.html", "Open data exports"),
        ]))


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
        "exports", body,
        "Download the core datasets in machine-readable form for external analysis, QA checks, or reuse in other tools.",
        next_steps=[
            ("data-health.html", "Open data health"),
            ("reports.html", "Open report bundles"),
            ("methodology.html", "Open methodology"),
        ]))


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
    body += render_table_guide("How to read this table", [
        "Each row is one appeal decision linked to a tracked issue.",
        "Outcome and inspector finding show how issues appear in practice.",
        "Linked issue connects this evidence to the contradiction register.",
        "These entries are illustrative evidence, not a full census of appeals.",
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
        "This page links appeal outcomes to specific contradiction records so users can inspect real-world decision evidence.",
        next_steps=[
            ("contradictions.html", "Open contradiction register"),
            ("bottlenecks.html", "Open bottleneck analysis"),
            ("recommendations.html", "Open recommendations"),
        ]))


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

    marker_features = []
    boundary_features = []

    def approx_boundary(lat, lng, radius_deg):
        points = []
        for i in range(6):
            ang = math.radians(60 * i)
            p_lat = lat + (radius_deg * math.sin(ang))
            p_lng = lng + (radius_deg * math.cos(ang))
            points.append([round(p_lng, 6), round(p_lat, 6)])
        points.append(points[0])
        return [points]

    for pid, g in geo_by_id.items():
        lpa = lpa_by_id.get(pid, {})
        speed = speed_by_lpa.get(pid)
        cohort = cohort_for_pid(pid)
        lat = float(g["lat"])
        lng = float(g["lng"])
        region = lpa.get("region", "")
        radius = 0.42
        if region == "London":
            radius = 0.24
        elif region in {"South East", "East of England"}:
            radius = 0.36
        elif region in {"North East", "North West", "Yorkshire and The Humber"}:
            radius = 0.48
        props = {
            "id": pid,
            "name": lpa.get("lpa_name", ""),
            "type": lpa.get("lpa_type", ""),
            "region": region,
            "growth": lpa.get("growth_context", ""),
            "constraints": lpa.get("constraint_profile", ""),
            "speed": speed,
            "quality_tier": quality_by_id.get(pid, {}).get("data_quality_tier", ""),
            "coverage_score": quality_by_id.get(pid, {}).get("coverage_score", ""),
            "cohort": cohort,
            "page": f"plans-{pid.lower()}.html",
        }
        marker_features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [lng, lat]},
            "properties": props,
        })
        boundary_features.append({
            "type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": approx_boundary(lat, lng, radius)},
            "properties": props,
        })

    marker_geojson = json.dumps({"type": "FeatureCollection", "features": marker_features}, indent=2)
    boundary_geojson = json.dumps({"type": "FeatureCollection", "features": boundary_features}, indent=2)

    body = f"""
      <section class="card">
        <p>All {len(marker_features)} LPAs in scope. The default view uses boundary-led choropleth cells (proxy geometry) coloured by major decision speed (green = above England average 74%, amber = 65-74%, red = below 65%). Use layer controls to toggle boundary fill and markers.</p>
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

        var markerData = {marker_geojson};
        var boundaryData = {boundary_geojson};

        function speedColor(speed) {{
          if (speed == null) return '#aaa';
          if (speed >= 74) return '#22a355';
          if (speed >= 65) return '#f59e0b';
          return '#ef4444';
        }}

        function popupHtml(p) {{
          var speedText = p.speed != null ? p.speed + '% major decisions in time' : 'No data';
          var qualityText = p.quality_tier ? ('Quality tier ' + p.quality_tier + ' (score ' + p.coverage_score + ')') : 'Quality tier n/a';
          return (
            '<strong><a href="' + p.page + '">' + p.name + '</a></strong>' +
            '<br>' + p.type + ' — ' + p.region +
            '<br><em>' + p.cohort + '</em>' +
            '<br>' + speedText +
            '<br>' + qualityText +
            '<br><small>' + p.constraints + '</small>'
          );
        }}

        var markerLayer = L.layerGroup();
        markerData.features.forEach(function(f) {{
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
          }});
          circle.bindPopup(popupHtml(p));
          markerLayer.addLayer(circle);
        }});

        function boundaryStyle(feature) {{
          return {{
            color: '#1f2937',
            weight: 1,
            fillColor: speedColor(feature.properties.speed),
            fillOpacity: 0.45,
          }};
        }}

        var boundaryLayer = L.geoJSON(boundaryData, {{
          style: boundaryStyle,
          onEachFeature: function(feature, layer) {{
            layer.bindPopup(popupHtml(feature.properties));
          }}
        }}).addTo(map);
        markerLayer.addTo(map);

        var overlays = {{
          'Boundary choropleth': boundaryLayer,
          'Point markers': markerLayer,
        }};
        L.control.layers(null, overlays, {{ collapsed: false }}).addTo(map);

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
        "Explore authorities geographically, compare performance at a glance, and open individual LPA profile pages from map markers.",
        next_steps=[
            ("plans.html", "Open plan hierarchy and profiles"),
            ("compare.html", "Open side-by-side compare"),
            ("benchmark.html", "Open benchmark rankings"),
        ]))


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
            "cohort": cohort_for_pid(pid),
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
          <label class="filter-item">Region<select id="cmp-region"><option value="">All</option></select></label>
          <label class="filter-item">LPA type<select id="cmp-type"><option value="">All</option></select></label>
          <label class="filter-item">Cohort<select id="cmp-cohort"><option value="">All</option></select></label>
          <label class="filter-item">Quality tier<select id="cmp-quality"><option value="">All</option></select></label>
        </div>
        <div class="filter-row" style="margin-top:10px;">
          <label class="filter-item">Authority A<select id="cmp-a"></select></label>
          <label class="filter-item">Authority B<select id="cmp-b"></select></label>
        </div>
        <div class="filter-row" style="margin-top:10px;">
          <button id="cmp-save" type="button">Save preset pair</button>
          <button id="cmp-clear" type="button">Clear saved presets</button>
        </div>
        <p class="small" id="cmp-filter-count"></p>
        <p class="small" id="cmp-status"></p>
        <div id="cmp-presets" class="small"></div>
      </section>
      <section class="card"><h3>How to read this table</h3><ul>
        <li>Rows compare a single metric across Authority A and Authority B.</li>
        <li>Use growth and constraint rows for contextual interpretation.</li>
        <li>Use speed and quality rows for headline performance contrast.</li>
        <li>Differences are directional signals, not causal proof.</li>
      </ul></section>
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
        var countEl = document.getElementById('cmp-filter-count');
        var regionSel = document.getElementById('cmp-region');
        var typeSel = document.getElementById('cmp-type');
        var cohortSel = document.getElementById('cmp-cohort');
        var qualitySel = document.getElementById('cmp-quality');
        var presetKey = 'uk-planning-compare-presets';
        var sharedKey = 'uk-planning-shared-filters-v1';

        function norm(v) { return (v || '').toLowerCase().trim(); }

        function mkOption(value, label) {
          var o = document.createElement('option');
          o.value = value;
          o.textContent = label;
          return o;
        }

        function appendUniqueOptions(select, values) {
          values.forEach(function(v) { select.appendChild(mkOption(v, v)); });
        }

        appendUniqueOptions(regionSel, Array.from(new Set(data.map(function(r) { return r.region; }).filter(Boolean))).sort());
        appendUniqueOptions(typeSel, Array.from(new Set(data.map(function(r) { return r.type; }).filter(Boolean))).sort());
        appendUniqueOptions(cohortSel, Array.from(new Set(data.map(function(r) { return r.cohort; }).filter(Boolean))).sort());
        appendUniqueOptions(qualitySel, Array.from(new Set(data.map(function(r) { return r.quality_tier; }).filter(Boolean))).sort());

        var byId = {};
        data.forEach(function(item) { byId[item.id] = true; });
        var params = new URLSearchParams(window.location.search);
        if (!params.get('a') && !params.get('b') && window.location.hash) {
          params = new URLSearchParams(window.location.hash.replace(/^#/, ''));
        }
        var presetA = (params.get('a') || '').toUpperCase();
        var presetB = (params.get('b') || '').toUpperCase();

        function loadSharedState() {
          try {
            return JSON.parse(localStorage.getItem(sharedKey) || '{}');
          } catch (e) {
            return {};
          }
        }

        function applySharedFilters() {
          var stored = loadSharedState();
          var byControl = {
            region: regionSel,
            lpa_type: typeSel,
            cohort: cohortSel,
            quality: qualitySel,
          };
          Object.keys(byControl).forEach(function(key) {
            var control = byControl[key];
            var value = norm(params.get(key)) || norm(stored[key]);
            if (!value) return;
            var option = Array.from(control.options).find(function(opt) { return norm(opt.value) === value; });
            if (option) control.value = option.value;
          });
        }

        function persistSharedFilters(aId, bId) {
          var next = new URLSearchParams(window.location.search);
          var shared = loadSharedState();
          var values = {
            region: norm(regionSel.value),
            lpa_type: norm(typeSel.value),
            cohort: norm(cohortSel.value),
            quality: norm(qualitySel.value),
          };
          Object.keys(values).forEach(function(key) {
            if (values[key]) {
              next.set(key, values[key]);
              shared[key] = values[key];
            } else {
              next.delete(key);
              delete shared[key];
            }
          });
          if (aId) next.set('a', aId);
          if (bId) next.set('b', bId);
          localStorage.setItem(sharedKey, JSON.stringify(shared));
          var query = next.toString();
          history.replaceState(null, '', window.location.pathname + (query ? ('?' + query) : ''));
        }

        function matchesSharedFilters(item) {
          if (norm(regionSel.value) && norm(item.region) !== norm(regionSel.value)) return false;
          if (norm(typeSel.value) && norm(item.type) !== norm(typeSel.value)) return false;
          if (norm(cohortSel.value) && norm(item.cohort) !== norm(cohortSel.value)) return false;
          if (norm(qualitySel.value) && norm(item.quality_tier) !== norm(qualitySel.value)) return false;
          return true;
        }

        function filteredData() {
          return data.filter(matchesSharedFilters);
        }

        function refillAuthoritySelect(select, rows, preferredValue, fallbackValue) {
          select.innerHTML = '';
          rows.forEach(function(item) {
            select.appendChild(mkOption(item.id, item.name + ' (' + item.id + ')'));
          });
          if (!rows.length) return;
          if (preferredValue && rows.some(function(item) { return item.id === preferredValue; })) {
            select.value = preferredValue;
            return;
          }
          if (fallbackValue && rows.some(function(item) { return item.id === fallbackValue; })) {
            select.value = fallbackValue;
            return;
          }
          select.value = rows[0].id;
        }

        function row(label, a, b) {
          return '<tr><th>' + label + '</th><td>' + a + '</td><td>' + b + '</td></tr>';
        }

        function render() {
          var visible = filteredData();
          countEl.textContent = visible.length + ' of ' + data.length + ' authorities match current filters';
          if (visible.length < 2) {
            out.innerHTML = '<h2>Comparison</h2><p>Select filters with at least two matching authorities.</p>';
            persistSharedFilters('', '');
            return;
          }

          refillAuthoritySelect(aSel, visible, aSel.value, presetA && byId[presetA] ? presetA : '');
          refillAuthoritySelect(bSel, visible, bSel.value, presetB && byId[presetB] ? presetB : '');
          if (aSel.value === bSel.value) {
            var alt = visible.find(function(item) { return item.id !== aSel.value; });
            if (alt) bSel.value = alt.id;
          }

          var a = visible.find(function(x){ return x.id === aSel.value; });
          var b = visible.find(function(x){ return x.id === bSel.value; });
          if (!a || !b) return;

          persistSharedFilters(a.id, b.id);

          out.innerHTML =
            '<h2>Comparison</h2>' +
            '<table><thead><tr><th>Metric</th><th>' + a.name + '</th><th>' + b.name + '</th></tr></thead><tbody>' +
            row('Type', a.type, b.type) +
            row('Region', a.region, b.region) +
            row('Cohort', a.cohort, b.cohort) +
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

        [regionSel, typeSel, cohortSel, qualitySel, aSel, bSel].forEach(function(control) {
          control.addEventListener('change', render);
        });

        applySharedFilters();
        renderPresets();
        render();
      })();
      </script>
""".replace("__DATA__", records_json)

    write(SITE / "compare.html", page(
        "LPA Comparison",
        "Side-by-side comparison of authorities, evidence quality, and baseline performance.",
        "compare", body,
        "Compare two authorities side by side across profile context, tracked plans, decision speed, and evidence quality.",
        next_steps=[
            ("benchmark.html", "Open benchmark ranking"),
            ("reports.html", "Download authority report bundles"),
            ("plans.html", "Open authority profiles"),
        ]))


def build_benchmark():
    lpas = read_csv(ROOT / "data/plans/pilot-lpas.csv")
    docs = read_csv(ROOT / "data/plans/pilot-plan-documents.csv")
    baselines = read_csv(ROOT / "data/evidence/official_baseline_metrics.csv")
    quality_rows = read_csv(ROOT / "data/plans/lpa-data-quality.csv")
    issue_rows = read_csv(ROOT / "data/issues/lpa-issue-incidence.csv")
    trend_rows = read_csv(ROOT / "data/evidence/lpa-quarterly-trends.csv")

    quality_by_id = {r["pilot_id"]: r for r in quality_rows}
    issues_by_id = {r["pilot_id"]: r for r in issue_rows}
    docs_by_lpa = defaultdict(list)
    for d in docs:
        docs_by_lpa[d["pilot_id"]].append(d)

    national_validation_proxy = 12.0
    for b in baselines:
        if b.get("metric_id") == "BAS-007":
            try:
                national_validation_proxy = float(b.get("value", "") or 12.0)
            except ValueError:
                national_validation_proxy = 12.0
            break

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
            "peer_group": peer_group_for_lpa(lpa),
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
        bench[-1].update(derive_metric_bundle(lpa, i, q, trows, docs_by_lpa, national_validation_proxy))

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
    quality_tiers = sorted({r.get("quality_tier", "") for r in bench if r.get("quality_tier") and r.get("quality_tier") != "n/a"})
    peer_groups = sorted({r.get("peer_group", "") for r in bench if r.get("peer_group")})
    bands = ["Top third", "Middle third", "Bottom third"]
    by_region = defaultdict(list)
    by_cohort = defaultdict(list)
    by_peer = defaultdict(list)
    for row in ranked:
        by_region[row["region"]].append(row["latest_speed"])
        by_cohort[row["cohort"]].append(row["latest_speed"])
        by_peer[row["peer_group"]].append(row["latest_speed"])
    england_major_speed = mean_speed
    for b in baselines:
        if b.get("metric_id") == "BAS-001":
            try:
                england_major_speed = float(b.get("value", "") or mean_speed)
            except ValueError:
                england_major_speed = mean_speed
            break
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
    body += render_metric_context_block([
        {
            "metric": "Speed (%)",
            "definition": "Latest major decisions in time for each authority.",
            "why": "Primary throughput signal for major applications.",
            "source": "Official P151 (high confidence)",
        },
        {
            "metric": "Appeal %",
            "definition": "Latest appeal overturn percentage.",
            "why": "Quality proxy for decision robustness.",
            "source": "Official P152 (high confidence)",
        },
        {
            "metric": "Backlog idx",
            "definition": "Composite index from issues, severity, speed gap, and plan age.",
            "why": "Highlights authorities facing higher processing pressure.",
            "source": "Analytical estimate (tier-based confidence)",
        },
    ])

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
    body += '<label class="filter-item">Quality tier<select data-table="benchmark-table" data-filter="quality"><option value="">All</option>'
    for quality_tier in quality_tiers:
        body += f'<option value="{html.escape(quality_tier.lower())}">{html.escape(quality_tier)}</option>'
    body += '</select></label>'
    body += '<label class="filter-item">Peer group<select data-table="benchmark-table" data-filter="peer_group"><option value="">All</option>'
    for group in peer_groups:
        body += f'<option value="{html.escape(group.lower())}">{html.escape(group)}</option>'
    body += '</select></label>'
    body += '<label class="filter-item">Percentile band<select data-table="benchmark-table" data-filter="band"><option value="">All</option>'
    for band in bands:
        body += f'<option value="{html.escape(band.lower())}">{html.escape(band)}</option>'
    body += '</select></label>'
    body += '</div><p class="small" data-filter-count-for="benchmark-table"></p></section>'
    body += '<section class="card"><div class="filter-row">'
    body += '<label class="filter-item">Benchmark mode<select id="benchmark-mode"><option value="all">All authorities</option><option value="peer">Peer group only</option></select></label>'
    body += '<label class="filter-item">Peer anchor authority<select id="benchmark-anchor"></select></label>'
    body += '</div><p class="small" id="benchmark-mode-status"></p></section>'

    body += f'<section class="card"><p class="small">Generated on {date.today().isoformat()} from quarterly trends and issue incidence datasets.</p></section>'
    body += render_table_guide("How to read this table", [
        "Each row is one authority ranked by latest major decision speed.",
        "4Q delta shows direction of change across the latest trend window.",
        "Outlier flags indicate unusual relative performance in the current cohort.",
        "Use preset pair links to drill into side-by-side comparisons.",
    ])
    body += '<section class="card"><p class="small"><strong>Metric definitions:</strong> '
    body += metric_help("Speed (%)", "Latest major decisions in time from GOV.UK P151 for each authority.", "major-speed") + ' '
    body += metric_help("4Q Delta", "Change in major decisions in time between first and latest quarter in the trend window.", "speed-delta") + ' '
    body += metric_help("Appeal %", "Latest appeals overturned percentage from GOV.UK P152 trend layer.", "appeal-rate") + ' '
    body += metric_help("Issues", "Linked issue count from analytical issue-incidence dataset.", "issues") + ' '
    body += metric_help("Quality", "Data quality tier and coverage score from analytical evidence-quality layer.", "quality-tier") + ' '
    body += metric_help("Val. rework", "Proxy validation rework rate combining BAS-007 baseline with local evidence-quality and issue-pressure adjustments.", "validation-rework") + ' '
    body += metric_help("Plan age", "Years since latest adopted or in-force tracked plan document for the authority.", "plan-age") + ' '
    body += metric_help("Consult lag", "Estimated consultation lag in weeks derived from severity and quality signals.", "consult-lag") + ' '
    body += metric_help("Backlog idx", "0-100 proxy index combining issue load, severity, and speed gap to England average.", "backlog-pressure") + ' '
    body += metric_help("Conf.", "Analytical confidence level derived from authority data-quality tier.", "analytical-confidence")
    body += '</p></section>'
    body += '<section class="card"><h2>LPA Benchmark Ranking</h2>'
    body += '<table id="benchmark-table"><thead><tr>'
    body += '<th>Rank</th><th>LPA</th><th>Cohort</th><th>Peer group</th><th>Type</th><th>Region</th>'
    body += f'<th>{metric_help("Speed (%)", "Latest major decisions in time from official P151 data.", "major-speed")}</th>'
    body += f'<th>{metric_help("4Q Delta (pp)", "Change from first to latest quarter in the tracked trend window.", "speed-delta")}</th>'
    body += '<th>Outlier</th><th>Percentile</th><th>Band</th><th>Trend</th>'
    body += f'<th>{metric_help("Appeal %", "Latest appeals overturned percentage from official P152 data.", "appeal-rate")}</th>'
    body += f'<th>{metric_help("Issues", "Total linked issues from analytical issue-incidence layer.", "issues")}</th>'
    body += f'<th>{metric_help("High Sev", "Count of high-severity issues from analytical issue-incidence layer.", "issues")}</th>'
    body += '<th>Risk Stage</th>'
    body += f'<th>{metric_help("Quality", "Data quality tier and coverage score from analytical evidence-quality layer.", "quality-tier")}</th>'
    body += f'<th>{metric_help("Val. rework", "Estimated validation rework proxy percentage.", "validation-rework")}</th>'
    body += f'<th>{metric_help("Delegated", "Estimated delegated decision share percentage.", "delegated-share")}</th>'
    body += f'<th>{metric_help("Plan age", "Years since latest adopted tracked plan document.", "plan-age")}</th>'
    body += f'<th>{metric_help("Consult lag", "Estimated consultation lag in weeks.", "consult-lag")}</th>'
    body += f'<th>{metric_help("Backlog idx", "Backlog pressure index (0-100).", "backlog-pressure")}</th>'
    body += f'<th>{metric_help("Conf.", "Analytical confidence based on data-quality tier.", "analytical-confidence")}</th>'
    body += '<th>Compare</th></tr></thead><tbody>'
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
            str(r.get("peer_group", "")),
            str(r.get("risk_stage", "")),
            str(r.get("quality_tier", "")),
            str(r.get("band", "")),
        ]).strip().lower()
        attrs = (
            f'data-pilot-id="{html.escape(str(r.get("pilot_id", "")))}" '
            f'data-search="{html.escape(search_blob)}" '
            f'data-region="{html.escape(r.get("region", "").strip().lower())}" '
            f'data-cohort="{html.escape(r.get("cohort", "").strip().lower())}" '
            f'data-lpa_type="{html.escape(r.get("lpa_type", "").strip().lower())}" '
            f'data-quality="{html.escape(str(r.get("quality_tier", "")).strip().lower())}" '
            f'data-peer_group="{html.escape(str(r.get("peer_group", "")).strip().lower())}" '
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
        body += f"<td>{html.escape(r['peer_group'])}</td>"
        body += f"<td>{html.escape(r['lpa_type'])}</td>"
        body += f"<td>{html.escape(r['region'])}</td>"
        speed_chip = ""
        if isinstance(r.get("latest_speed"), float):
            cohort_vals = by_cohort.get(r.get("cohort", ""), [])
            peer_vals = by_peer.get(r.get("peer_group", ""), [])
            cohort_avg = (sum(cohort_vals) / len(cohort_vals)) if cohort_vals else r["latest_speed"]
            peer_avg = (sum(peer_vals) / len(peer_vals)) if peer_vals else r["latest_speed"]
            speed_chip = (
                f'<div class="mini-chips"><span class="mini-chip">vs England {r["latest_speed"]-england_major_speed:+.1f}pp</span>'
                f'<span class="mini-chip">vs Cohort {r["latest_speed"]-cohort_avg:+.1f}pp</span>'
                f'<span class="mini-chip">vs Peer {r["latest_speed"]-peer_avg:+.1f}pp</span></div>'
            )
        body += f"<td>{speed} {provenance_badge('official')}{speed_chip}</td>"
        body += f"<td>{delta} {provenance_badge('official')}</td>"
        body += f"<td>{badge(r.get('outlier', 'In range'), outlier_css)}</td>"
        body += f"<td>{html.escape(str(r['percentile']))}</td>"
        body += f"<td>{html.escape(r['band'])}</td>"
        trend_text = "No trend"
        if isinstance(r.get("speed_delta"), float):
            trend_text = f"4Q movement {r['speed_delta']:+.1f}pp"
        body += f"<td>{r['trend_spark']}<p class=\"small\">{html.escape(trend_text)}</p></td>"
        body += f"<td>{appeal} {provenance_badge('official')}</td>"
        body += f"<td>{html.escape(str(r['total_issues']))} {provenance_badge('estimated')}</td>"
        body += f"<td>{html.escape(str(r['high_severity_issues']))}</td>"
        body += f"<td>{html.escape(str(r['risk_stage']))}</td>"
        body += f"<td>{html.escape(str(r['quality_tier']))} ({html.escape(str(r['quality_score']))}) {provenance_badge('estimated')}</td>"
        body += f"<td>{html.escape(str(r['validation_rework_proxy']))}% {provenance_badge('estimated')}</td>"
        body += f"<td>{html.escape(str(r['delegated_ratio_proxy']))}% {provenance_badge('estimated')}</td>"
        plan_age = "n/a" if r.get("plan_age_years") is None else f"{r['plan_age_years']}y"
        body += f"<td>{html.escape(plan_age)} {provenance_badge('estimated')}</td>"
        body += f"<td>{html.escape(str(r['consultation_lag_proxy']))}w {provenance_badge('estimated')}</td>"
        body += f"<td>{html.escape(str(r['backlog_pressure']))} {provenance_badge('estimated')}</td>"
        body += f"<td>{confidence_badge(r.get('analytical_confidence', 'low'))}</td>"
        body += f"<td>{compare_link}</td>"
        body += "</tr>"
    body += '</tbody></table></section>'
    body += '<section class="card guided-only"><p class="small">Mobile tip: tap a benchmark row for a compact, readable detail view.</p></section>'

    body += render_filter_script(
        "benchmark-table",
        ["search", "region", "cohort", "lpa_type", "quality", "peer_group", "band"],
        shared_filters=["region", "lpa_type", "cohort", "quality"],
    )
    body += render_mobile_drawer_script("benchmark-table", [
        "Rank", "LPA", "Cohort", "Peer group", "Type", "Region", "Speed", "4Q Delta", "Outlier", "Percentile", "Band", "Trend", "Appeal", "Issues", "High Severity", "Risk Stage", "Quality", "Validation rework", "Delegated", "Plan age", "Consult lag", "Backlog index", "Confidence", "Compare",
    ])
    body += render_table_enhancements_script("benchmark-table", presets=[
        {"label": "High priority pressure", "filters": {"band": "bottom third", "quality": "c"}},
        {"label": "Housing-focused peer", "filters": {"peer_group": "constrained housing-pressure authorities"}},
    ])
    body += """
<script>
(function() {
  var table = document.getElementById('benchmark-table');
  var modeEl = document.getElementById('benchmark-mode');
  var anchorEl = document.getElementById('benchmark-anchor');
  var statusEl = document.getElementById('benchmark-mode-status');
  if (!table || !modeEl || !anchorEl || !statusEl) return;
  var rows = Array.from(table.querySelectorAll('tbody tr'));
  var modeKey = 'uk-planning-benchmark-mode-v1';

  function visibleByBaseFilters(row) {
    return !row.classList.contains('hidden-row');
  }

  function getVisibleRows() {
    return rows.filter(visibleByBaseFilters);
  }

  function repopulateAnchor() {
    var visible = getVisibleRows();
    var prev = anchorEl.value;
    anchorEl.innerHTML = '';
    visible.forEach(function(row) {
      var id = row.dataset.pilotId || '';
      var nameCell = row.cells[1];
      var name = nameCell ? nameCell.textContent.trim() : id;
      var option = document.createElement('option');
      option.value = id;
      option.textContent = name + ' (' + id + ')';
      anchorEl.appendChild(option);
    });
    if (!visible.length) return;
    var keep = visible.some(function(row) { return (row.dataset.pilotId || '') === prev; });
    if (keep) {
      anchorEl.value = prev;
    }
  }

  function saveState() {
    var next = {
      mode: modeEl.value,
      anchor: anchorEl.value,
    };
    localStorage.setItem(modeKey, JSON.stringify(next));
  }

  function loadState() {
    try {
      return JSON.parse(localStorage.getItem(modeKey) || '{}');
    } catch (e) {
      return {};
    }
  }

  function applyMode() {
    var visible = getVisibleRows();
    var anchor = visible.find(function(row) { return (row.dataset.pilotId || '') === anchorEl.value; });
    var peerGroup = anchor ? (anchor.dataset.peerGroup || '') : '';
    var shown = 0;
    rows.forEach(function(row) {
      row.classList.remove('hidden-peer');
      if (!visibleByBaseFilters(row)) return;
      if (modeEl.value === 'peer' && peerGroup && (row.dataset.peerGroup || '') !== peerGroup) {
        row.classList.add('hidden-peer');
      }
      if (!row.classList.contains('hidden-peer') && !row.classList.contains('hidden-row')) shown++;
    });
    if (modeEl.value === 'peer' && peerGroup) {
      statusEl.textContent = shown + ' authorities shown in peer group: ' + peerGroup + '.';
    } else {
      statusEl.textContent = shown + ' authorities shown across all peer groups.';
    }
    saveState();
  }

  var state = loadState();
  if (state.mode === 'peer' || state.mode === 'all') {
    modeEl.value = state.mode;
  }

  function refresh() {
    repopulateAnchor();
    if (state.anchor && Array.from(anchorEl.options).some(function(o) { return o.value === state.anchor; })) {
      anchorEl.value = state.anchor;
      state.anchor = '';
    }
    applyMode();
  }

  modeEl.addEventListener('change', applyMode);
  anchorEl.addEventListener('change', applyMode);

  var observer = new MutationObserver(function() {
    refresh();
  });
  observer.observe(table.tBodies[0], { subtree: true, attributes: true, attributeFilter: ['class'] });
  refresh();
})();
</script>
"""

    write(SITE / "benchmark.html", page(
        "LPA Benchmark Dashboard",
        "Rankings, percentile bands, and trend sparklines across authorities.",
        "benchmark", body,
        "Use rankings, percentile bands, and trend indicators to see relative performance and jump to preset authority comparisons.",
        next_steps=[
            ("compare.html", "Open side-by-side compare"),
            ("reports.html", "Download report bundles"),
            ("metric-methods.html", "Review metric formulas"),
            ("data-health.html", "Review data health status"),
        ]))


def build_reports():
    lpas = read_csv(ROOT / "data/plans/pilot-lpas.csv")
    docs = read_csv(ROOT / "data/plans/pilot-plan-documents.csv")
    baselines = read_csv(ROOT / "data/evidence/official_baseline_metrics.csv")
    quality_rows = read_csv(ROOT / "data/plans/lpa-data-quality.csv")
    issue_rows = read_csv(ROOT / "data/issues/lpa-issue-incidence.csv")
    trend_rows = read_csv(ROOT / "data/evidence/lpa-quarterly-trends.csv")

    quality_by_id = {r["pilot_id"]: r for r in quality_rows}
    issues_by_id = {r["pilot_id"]: r for r in issue_rows}
    docs_by_lpa = defaultdict(list)
    for d in docs:
        docs_by_lpa[d["pilot_id"]].append(d)

    national_validation_proxy = 12.0
    for b in baselines:
        if b.get("metric_id") == "BAS-007":
            try:
                national_validation_proxy = float(b.get("value", "") or 12.0)
            except ValueError:
                national_validation_proxy = 12.0
            break

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
        derived = derive_metric_bundle(lpa, i, q, t, docs_by_lpa, national_validation_proxy)
        peer_group = peer_group_for_lpa(lpa)
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
            "peer_group": peer_group,
            "region": lpa.get("region", ""),
            "growth_context": lpa.get("growth_context", ""),
            "constraint_profile": lpa.get("constraint_profile", ""),
            "data_quality": q,
            "issue_incidence": i,
            "derived_metrics": derived,
            "quarterly_trends": t,
            "metric_provenance": {
                "major_in_time_pct": "official",
                "appeals_overturned_pct": "official",
                "issue_incidence": "estimated",
                "data_quality": "estimated",
                "validation_rework_proxy": "estimated",
                "delegated_ratio_proxy": "estimated",
                "plan_age_years": "estimated",
                "consultation_lag_proxy": "estimated",
                "backlog_pressure": "estimated",
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
            w.writerow(["peer_group", payload["peer_group"]])
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
            w.writerow(["validation_rework_proxy", derived.get("validation_rework_proxy", "")])
            w.writerow(["delegated_ratio_proxy", derived.get("delegated_ratio_proxy", "")])
            w.writerow(["plan_age_years", derived.get("plan_age_years", "")])
            w.writerow(["consultation_lag_proxy", derived.get("consultation_lag_proxy", "")])
            w.writerow(["backlog_pressure", derived.get("backlog_pressure", "")])
            w.writerow(["analytical_confidence", derived.get("analytical_confidence", "")])
            w.writerow(["latest_trend_source_table", trend_source])
            w.writerow(["latest_trend_source_url", trend_source_url])

        links.append({
            "pid": pid,
            "name": lpa.get("lpa_name", ""),
            "lpa_type": lpa.get("lpa_type", ""),
            "cohort": cohort_for_pid(pid),
            "region": lpa.get("region", ""),
            "peer_group": peer_group,
            "quality_tier": q.get("data_quality_tier", ""),
            "analytical_confidence": derived.get("analytical_confidence", "low"),
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
    quality_tiers = sorted({r["quality_tier"] for r in links if r.get("quality_tier")})
    peer_groups = sorted({r["peer_group"] for r in links if r.get("peer_group")})

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
    body += '<label class="filter-item">Quality tier<select data-table="reports-table" data-filter="quality"><option value="">All</option>'
    for quality_tier in quality_tiers:
        body += f'<option value="{html.escape(quality_tier.lower())}">{html.escape(quality_tier)}</option>'
    body += '</select></label>'
    body += '<label class="filter-item">Peer group<select data-table="reports-table" data-filter="peer_group"><option value="">All</option>'
    for group in peer_groups:
        body += f'<option value="{html.escape(group.lower())}">{html.escape(group)}</option>'
    body += '</select></label>'
    body += '</div><p class="small" data-filter-count-for="reports-table"></p></section>'

    body += render_table_guide("How to read this table", [
        "Each row provides downloadable report files for one authority.",
        "CSV is suited for spreadsheets; JSON is suited for automation.",
        "Provenance badges show official versus analytical estimate inputs.",
        "Trend source links identify the originating statistics table.",
    ])
    body += '<section class="card"><p class="small"><strong>Metric definitions:</strong> '
    body += metric_help("Metric provenance", "Shows whether included report metrics come from official statistics or analytical estimates.", "major-speed") + ' '
    body += metric_help("Trend source", "Originating statistical table for the latest trend snapshot in each report.", "speed-delta") + ' '
    body += metric_help("Analytical confidence", "Confidence level for estimated metrics derived from authority data-quality tier.", "analytical-confidence")
    body += '</p></section>'
    body += render_metric_context_block([
        {
            "metric": "Metric provenance",
            "definition": "Source classification for report indicators.",
            "why": "Helps users understand whether data is official or estimated.",
            "source": "Official + analytical provenance badges",
        },
        {
            "metric": "Analytical confidence",
            "definition": "High/medium/low confidence for estimated authority metrics.",
            "why": "Flags uncertainty before decisions are made.",
            "source": "Derived from authority quality tiers",
        },
        {
            "metric": "Trend source",
            "definition": "Originating table reference for latest trend values.",
            "why": "Supports traceability and evidence verification.",
            "source": "GOV.UK/PINS source table links",
        },
    ])
    body += '<section class="card"><table id="reports-table"><thead><tr>'
    body += '<th>ID</th><th>Authority</th><th>Cohort</th><th>Peer group</th><th>Type</th><th>Region</th>'
    body += f'<th>{metric_help("Metric provenance", "Official stats are from GOV.UK trend tables; estimates are analytical layers.", "major-speed")}</th>'
    body += f'<th>{metric_help("Analytical confidence", "Confidence level assigned to estimated metrics for this authority.", "analytical-confidence")}</th>'
    body += f'<th>{metric_help("Trend source", "Source table and URL used for the latest trend datapoint.", "speed-delta")}</th>'
    body += '<th>CSV</th><th>JSON</th></tr></thead><tbody>'
    for row in links:
        attrs = (
            f'data-search="{html.escape((row["name"] + " " + row["pid"]).strip().lower())}" '
            f'data-region="{html.escape(row["region"].strip().lower())}" '
            f'data-cohort="{html.escape(row["cohort"].strip().lower())}" '
            f'data-lpa_type="{html.escape(row["lpa_type"].strip().lower())}" '
            f'data-quality="{html.escape(row["quality_tier"].strip().lower())}" '
            f'data-peer_group="{html.escape(row["peer_group"].strip().lower())}"'
        )
        source_cell = html.escape(row["trend_source"]) if row["trend_source"] else "—"
        if row["trend_source_url"]:
            source_cell = f'<a href="{html.escape(row["trend_source_url"])}" target="_blank" rel="noopener noreferrer">{html.escape(row["trend_source"] or "Source")}</a>'
        body += f'<tr {attrs}>'
        body += f'<td>{html.escape(row["pid"])}</td>'
        body += f'<td>{html.escape(row["name"])}</td>'
        body += f'<td>{html.escape(row["cohort"])}</td>'
        body += f'<td>{html.escape(row["peer_group"])}</td>'
        body += f'<td>{html.escape(row["lpa_type"])}</td>'
        body += f'<td>{html.escape(row["region"])}</td>'
        body += f'<td>{provenance_badge("official")} {provenance_badge("estimated")}</td>'
        body += f'<td>{confidence_badge(row.get("analytical_confidence", "low"))}</td>'
        body += f'<td>{source_cell}</td>'
        body += f'<td><a href="{html.escape(row["csv"])}">Download CSV</a></td>'
        body += f'<td><a href="{html.escape(row["json"])}">Download JSON</a></td>'
        body += '</tr>'
    body += '</tbody></table></section>'
    body += '<section class="card guided-only"><p class="small">Mobile tip: tap a report row to inspect details without horizontal scrolling.</p></section>'

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

    body += render_filter_script(
        "reports-table",
        ["search", "region", "cohort", "lpa_type", "quality", "peer_group"],
        shared_filters=["region", "lpa_type", "cohort", "quality"],
    )
    body += render_table_enhancements_script("reports-table", presets=[
        {"label": "Tier C only", "filters": {"quality": "c"}},
        {"label": "Cohort 1", "filters": {"cohort": "cohort 1"}},
    ])
    body += render_mobile_drawer_script("reports-table", [
        "ID", "Authority", "Cohort", "Peer group", "Type", "Region", "Metric provenance", "Analytical confidence", "Trend source", "CSV", "JSON",
    ])

    write(SITE / "reports.html", page(
        "LPA Reports",
        "Downloadable authority-level comparison bundles.",
        "reports", body,
        "Filter and download per-authority report bundles that combine profile context, issue incidence, quality data, and trend snapshots.",
        next_steps=[
            ("benchmark.html", "Open benchmark dashboard"),
            ("metric-methods.html", "Review metric formulas"),
            ("exports.html", "Open machine-readable exports"),
            ("data-health.html", "Check data freshness"),
        ]))


def build_data_health():
    rows, counts = compute_data_health()
    body = '<section class="card"><p>Monitors freshness of core operational datasets and highlights stale or critical update risk windows.</p></section>'
    body += '<section class="grid">'
    body += f'<article class="card"><h3>Fresh datasets</h3><p>{counts.get("fresh", 0)}</p></article>'
    body += f'<article class="card"><h3>Stale datasets</h3><p>{counts.get("stale", 0)}</p></article>'
    body += f'<article class="card"><h3>Critical datasets</h3><p>{counts.get("critical", 0)}</p></article>'
    body += '</section>'

    body += render_table_guide("How to read this table", [
        "Each row is one monitored dataset.",
        "Age in days is measured from the most recent tracked date field.",
        "Fresh, stale, and critical statuses are threshold-based.",
        "Prioritise stale and critical datasets for update before high-stakes use.",
    ])
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
        "Use this page to assess whether evidence datasets are up to date before relying on benchmark outputs or recommendations.",
        next_steps=[
            ("benchmark.html", "Return to benchmark"),
            ("reports.html", "Return to reports"),
            ("sources.html", "Review source index"),
        ]))


def build_coverage():
    rows, counts = compute_onboarding_status_rows(profile_page_check=True)
    onboarding_dir = SITE / "reports" / "onboarding"
    onboarding_dir.mkdir(parents=True, exist_ok=True)
    summary_payload = []
    for row in rows:
        payload = {
            "pilot_id": row["pilot_id"],
            "lpa_name": row["lpa_name"],
            "region": row["region"],
            "cohort": row["cohort"],
            "quality_tier": row["quality_tier"],
            "coverage_status": row["coverage_status"],
            "checks": row["checks"],
            "failed_checks": row["failed_checks"],
            "documents_count": row["documents_count"],
            "trend_points": row["trend_points"],
            "profile_page": row["profile_page"],
        }
        summary_payload.append(payload)
        (onboarding_dir / f"{row['pilot_id'].lower()}-onboarding.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    (onboarding_dir / "onboarding-summary.json").write_text(json.dumps(summary_payload, indent=2), encoding="utf-8")

    regions = sorted({r["region"] for r in rows if r.get("region")})
    cohorts = sorted({r["cohort"] for r in rows if r.get("cohort")})
    statuses = ["complete", "partial", "estimated"]

    body = '<section class="card"><p>Coverage tracker shows onboarding gate status per authority. Statuses: complete (all gates passed and quality tier A/B), partial (some gates passed), estimated (limited onboarding evidence).</p></section>'
    body += '<section class="grid">'
    body += f'<article class="card"><h3>Complete</h3><p>{counts.get("complete", 0)}</p></article>'
    body += f'<article class="card"><h3>Partial</h3><p>{counts.get("partial", 0)}</p></article>'
    body += f'<article class="card"><h3>Estimated</h3><p>{counts.get("estimated", 0)}</p></article>'
    body += '</section>'

    body += '<section class="card"><div class="filter-row">'
    body += '<label class="filter-item">Search coverage<input type="search" data-table="coverage-table" data-filter="search" placeholder="Type authority..." /></label>'
    body += '<label class="filter-item">Region<select data-table="coverage-table" data-filter="region"><option value="">All</option>'
    for region in regions:
        body += f'<option value="{html.escape(region.lower())}">{html.escape(region)}</option>'
    body += '</select></label>'
    body += '<label class="filter-item">Cohort<select data-table="coverage-table" data-filter="cohort"><option value="">All</option>'
    for cohort in cohorts:
        body += f'<option value="{html.escape(cohort.lower())}">{html.escape(cohort)}</option>'
    body += '</select></label>'
    body += '<label class="filter-item">Status<select data-table="coverage-table" data-filter="status"><option value="">All</option>'
    for status in statuses:
        body += f'<option value="{status}">{status.title()}</option>'
    body += '</select></label>'
    body += '</div><p class="small" data-filter-count-for="coverage-table"></p></section>'

    body += render_table_guide("How to read this table", [
        "Coverage status combines onboarding gates and quality tier.",
        "Failed gates identify where onboarding work is required.",
        "Use profile links to inspect authority pages directly.",
        "Status should be reviewed after each monthly refresh cycle.",
    ])
    body += '<section class="card"><table id="coverage-table"><thead><tr><th>ID</th><th>Authority</th><th>Cohort</th><th>Type</th><th>Region</th><th>Quality</th><th>Status</th><th>Failed gates</th><th>Docs</th><th>Trend pts</th><th>Profile</th></tr></thead><tbody>'
    for row in rows:
        search_blob = " ".join([row["pilot_id"], row["lpa_name"], row["region"], row["cohort"], row["coverage_status"]]).strip().lower()
        attrs = (
            f'data-search="{html.escape(search_blob)}" '
            f'data-region="{html.escape(row["region"].strip().lower())}" '
            f'data-cohort="{html.escape(row["cohort"].strip().lower())}" '
            f'data-status="{html.escape(row["coverage_status"])}"'
        )
        status_css = "green" if row["coverage_status"] == "complete" else "amber" if row["coverage_status"] == "partial" else "red"
        failed = ", ".join(row["failed_checks"]) if row["failed_checks"] else "none"
        body += f'<tr {attrs}>'
        body += f'<td>{html.escape(row["pilot_id"])}</td>'
        body += f'<td>{html.escape(row["lpa_name"])}</td>'
        body += f'<td>{html.escape(row["cohort"])}</td>'
        body += f'<td>{html.escape(row["lpa_type"])}</td>'
        body += f'<td>{html.escape(row["region"])}</td>'
        body += f'<td>{html.escape(row["quality_tier"])}</td>'
        body += f'<td>{badge(row["coverage_status"], status_css)}</td>'
        body += f'<td>{html.escape(failed)}</td>'
        body += f'<td>{html.escape(str(row["documents_count"]))}</td>'
        body += f'<td>{html.escape(str(row["trend_points"]))}</td>'
        body += f'<td><a href="{html.escape(row["profile_page"])}">Open</a></td>'
        body += '</tr>'
    body += '</tbody></table></section>'
    body += render_filter_script(
        "coverage-table",
        ["search", "region", "cohort", "status"],
        shared_filters=["region", "cohort"],
    )

    write(SITE / "coverage.html", page(
        "Coverage Tracker",
        "Authority coverage and onboarding gate status across the current cohort.",
        "coverage", body,
        "Use this page to see which authorities are complete, partial, or estimate-led and which onboarding gates still need work.",
        next_steps=[
            ("plans.html", "Open authority profiles"),
            ("reports.html", "Open report bundles"),
            ("benchmark.html", "Open benchmark"),
        ]))


def build_ux_kpi_report():
    contradictions = read_csv(ROOT / "data/issues/contradiction-register.csv")
    recommendations = read_csv(ROOT / "data/issues/recommendations.csv")
    coverage_rows, coverage_counts = compute_onboarding_status_rows(profile_page_check=True)
    report = {
        "generated_at": date.today().isoformat(),
        "kpis": {
            "detail_page_coverage": {
                "contradictions_with_detail_pages": len(contradictions),
                "recommendations_with_detail_pages": len(recommendations),
            },
            "coverage_status": coverage_counts,
            "instrumentation": {
                "event_schema": ["page_view", "link_click"],
                "storage": "localStorage:uk-planning-ux-events-v1",
                "guided_mode_available": True,
                "plain_language_toggle_available": True,
            },
            "targets": {
                "time_to_first_insight_seconds": 45,
                "detail_page_click_through_rate": 0.35,
                "filter_use_success_rate": 0.8,
            },
        },
    }
    reports_dir = SITE / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    (reports_dir / "ux-kpi-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    with (reports_dir / "ux-kpi-report.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["metric", "value"])
        w.writerow(["contradiction_detail_pages", len(contradictions)])
        w.writerow(["recommendation_detail_pages", len(recommendations)])
        w.writerow(["coverage_complete", coverage_counts.get("complete", 0)])
        w.writerow(["coverage_partial", coverage_counts.get("partial", 0)])
        w.writerow(["coverage_estimated", coverage_counts.get("estimated", 0)])


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
    body += '<p class="small">Status terms: Not submitted, Submitted, Response received, Under review, Rejected, Adopted.</p>'
    body += render_table_guide("How to read this table", [
        "Each row tracks consultation progress for one recommendation.",
        "Status indicates workflow stage for external submission.",
        "Submitted to and next action capture operational follow-up.",
        "Use recommendation ID to cross-reference recommendation details.",
    ])
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
        "Track recommendation submission progress, review disclaimers, and find routes for feedback or evidence contributions.",
        next_steps=[
            ("recommendations.html", "Open recommendation details"),
            ("roadmap.html", "Open implementation roadmap"),
            ("sources.html", "Open source evidence"),
        ]))


def build_search_index():
    """Build a JSON search index from all key datasets for client-side search."""
    index = []

    def add(doc_id, page, title, category, text, facets=None):
        index.append({
            "id": doc_id, "page": page, "title": title,
            "category": category,
            "text": " ".join(str(v) for v in [title, text] if v).lower(),
            "facets": facets or {},
        })

    for r in read_csv(ROOT / "data/issues/contradiction-register.csv"):
        add(r["issue_id"], issue_detail_page(r["issue_id"]), r["issue_id"] + ": " + r["summary"],
            "Contradiction", r.get("summary", "") + " " + r.get("issue_type", "") + " " + r.get("process_stage", ""),
            facets={
                "type": "contradiction",
                "pathway": (r.get("affected_pathway", "") or "").lower(),
                "confidence": (r.get("confidence", "") or "").lower(),
                "status": (r.get("verification_state", "") or "").lower(),
                "authority": "",
            })

    for r in read_csv(ROOT / "data/issues/recommendations.csv"):
        add(r["recommendation_id"], recommendation_detail_page(r["recommendation_id"]), r["recommendation_id"] + ": " + r["title"],
            "Recommendation", r.get("title", "") + " " + r.get("policy_goal", "") + " " + r.get("kpi_primary", ""),
            facets={
                "type": "recommendation",
                "pathway": "",
                "confidence": (r.get("confidence", "") or "").lower(),
                "status": (r.get("verification_state", "") or "").lower(),
                "authority": "",
            })

    for r in read_csv(ROOT / "data/legislation/england-core-legislation.csv"):
        add(r["id"], "legislation.html", r["title"],
            "Legislation", r.get("type", "") + " " + r.get("status", "") + " " + r.get("citation", ""))

    for r in read_csv(ROOT / "data/policy/england-national-policy.csv"):
        add(r["id"], "legislation.html", r["title"],
            "Policy", r.get("type", "") + " " + r.get("scope", "") + " " + r.get("authority", ""))

    for r in read_csv(ROOT / "data/plans/pilot-lpas.csv"):
        add(r["pilot_id"], f"plans-{r['pilot_id'].lower()}.html", r["lpa_name"],
            "LPA", r.get("region", "") + " " + r.get("constraint_profile", "") + " " + r.get("growth_context", ""),
            facets={
                "type": "authority",
                "pathway": "",
                "confidence": "",
                "status": "",
                "authority": (r.get("lpa_name", "") or "").lower(),
            })

    for r in read_csv(ROOT / "data/issues/bottleneck-heatmap.csv"):
        add(r["stage_id"], "bottlenecks.html", r["process_stage"] + " — " + r["pathway"],
            "Bottleneck", r.get("delay_driver", "") + " " + r.get("process_stage", ""))

    for r in read_csv(ROOT / "data/evidence/appeal-decisions.csv"):
        add(r["appeal_id"], "appeals.html", r["pins_reference"] + " (" + r["lpa"] + ")",
            "Appeal", r.get("inspector_finding", "") + " " + r.get("policy_cited", ""),
            facets={
                "type": "appeal",
                "pathway": "",
                "confidence": "",
                "status": (r.get("outcome", "") or "").lower(),
                "authority": (r.get("lpa", "") or "").lower(),
            })

    idx_path = SITE / "search-index.json"
    idx_path.write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")
    return len(index)


def build_search():
    body = """
      <section class="card">
        <label for="search-input" class="sr-only">Search across all content</label>
        <input type="search" id="search-input" placeholder="Search legislation, issues, recommendations, LPAs, appeals..." style="width:100%;padding:12px;font-size:1rem;border:1px solid var(--line);border-radius:8px;" />
        <div class="filter-row" style="margin-top:10px;" id="filters-start">
          <label class="filter-item">Type<select id="facet-type"><option value="">All</option><option value="contradiction">Contradiction</option><option value="recommendation">Recommendation</option><option value="authority">Authority</option><option value="appeal">Appeal</option></select></label>
          <label class="filter-item">Pathway<select id="facet-pathway"><option value="">All</option><option value="housing">Housing</option><option value="commercial">Commercial</option><option value="infrastructure">Infrastructure</option><option value="mixed">Mixed</option></select></label>
          <label class="filter-item">Confidence<select id="facet-confidence"><option value="">All</option><option value="high">High</option><option value="medium">Medium</option><option value="low">Low</option></select></label>
          <label class="filter-item">Status<select id="facet-status"><option value="">All</option><option value="draft">Draft</option><option value="verified">Verified</option><option value="legal-reviewed">Legal-reviewed</option></select></label>
        </div>
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
        var typeEl = document.getElementById('facet-type');
        var pathwayEl = document.getElementById('facet-pathway');
        var confidenceEl = document.getElementById('facet-confidence');
        var statusEl = document.getElementById('facet-status');
        var index = null;

        fetch('search-index.json')
          .then(function(r) { return r.json(); })
          .then(function(data) {
            index = data;
            countEl.textContent = data.length + ' items indexed.';
          });

        function rankMatches(items, q) {
          return items.sort(function(a, b) {
            var aq = (a.id || '').toLowerCase() === q ? 1 : 0;
            var bq = (b.id || '').toLowerCase() === q ? 1 : 0;
            if (aq !== bq) return bq - aq;
            var aTitle = (a.title || '').toLowerCase().indexOf(q) === 0 ? 1 : 0;
            var bTitle = (b.title || '').toLowerCase().indexOf(q) === 0 ? 1 : 0;
            return bTitle - aTitle;
          });
        }

        function runSearch() {
          var q = input.value.toLowerCase().trim();
          if (!index || q.length < 2) {
            results.innerHTML = '<p class="small">Type at least 2 characters to search.</p>';
            return;
          }
          var fType = (typeEl.value || '').toLowerCase();
          var fPath = (pathwayEl.value || '').toLowerCase();
          var fConf = (confidenceEl.value || '').toLowerCase();
          var fStatus = (statusEl.value || '').toLowerCase();
          var matches = index.filter(function(item) {
            if (item.text.indexOf(q) === -1) return false;
            var facets = item.facets || {};
            if (fType && facets.type !== fType) return false;
            if (fPath && facets.pathway !== fPath) return false;
            if (fConf && facets.confidence !== fConf) return false;
            if (fStatus && facets.status !== fStatus) return false;
            return true;
          });
          matches = rankMatches(matches, q).slice(0, 50);

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
        }

        [input, typeEl, pathwayEl, confidenceEl, statusEl].forEach(function(control) {
          control.addEventListener('input', runSearch);
          control.addEventListener('change', runSearch);
        });
      })();
      </script>
"""
    write(SITE / "search.html", page(
        "Search",
        "Full-text search across legislation, issues, recommendations, LPAs, appeals, and bottlenecks.",
        "search", body,
        "Use keyword search to quickly find relevant records across legislation, plans, issues, recommendations, appeals, and evidence.",
        next_steps=[
            ("index.html", "Return to overview"),
            ("benchmark.html", "Open authority benchmark"),
            ("recommendations.html", "Open recommendations"),
        ]))


def main():
    weights = load_scoring()

    build_index()
    build_legislation()
    build_plans()
    build_contradictions(weights)
    build_recommendations(weights)
    build_contradiction_details(weights)
    build_recommendation_details()
    build_roadmap()
    build_baselines()
    build_bottlenecks()
    build_appeals()
    build_map()
    build_compare()
    build_benchmark()
    build_reports()
    build_coverage()
    build_data_health()
    build_consultation()
    build_search_index()
    build_search()
    build_audience_policymakers()
    build_audience_lpas()
    build_audience_developers()
    build_audience_public()
    build_methodology()
    build_metric_methods()
    build_sources()
    build_exports_index()
    build_ux_kpi_report()

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
