"""System analysis page builders: legislation, contradictions, bottlenecks, appeals, baselines."""
import html
from collections import defaultdict

from .config import ROOT, SITE
from .data_loader import read_csv
from .metrics import (
    weighted_score, split_pipe_values, issue_detail_page,
    recommendation_detail_page, query_value,
)
from .html_utils import (
    confidence_badge, verification_badge,
    render_table_guide, render_table,
    render_filter_controls, render_filterable_table, render_filter_script,
    render_table_enhancements_script, render_mobile_drawer_script,
    render_detail_toc, page, write,
)


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
