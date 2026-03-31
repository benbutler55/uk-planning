"""Recommendation page builders: recommendations, recommendation details, roadmap, consultation."""
import html
from collections import defaultdict

from .config import ROOT, SITE
from .data_loader import read_csv
from .metrics import (
    split_pipe_values, issue_detail_page, recommendation_detail_page, query_value,
)
from .html_utils import (
    confidence_badge, verification_badge,
    render_table_guide, render_table,
    render_filter_controls, render_filterable_table, render_filter_script,
    render_table_enhancements_script, render_detail_toc, page, write,
)


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
