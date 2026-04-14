"""Context providers for Recommendations pages: recommendations, recommendation details,
roadmap, consultation."""

import html as html_lib
from collections import defaultdict

from ..config import ROOT
from ..data_loader import read_csv
from ..metrics import (
    split_pipe_values,
    issue_detail_page,
    recommendation_detail_page,
    query_value,
)
from ..html_utils import (
    confidence_badge,
    verification_badge,
    render_table,
    render_table_guide,
    render_filter_controls,
    render_filterable_table,
    render_filter_script,
    render_table_enhancements_script,
    render_detail_toc,
)


def recommendations_context(weights):
    """Return template context dict for recommendations.html."""
    rows = read_csv(ROOT / "data/issues/recommendations.csv")
    evidence = read_csv(ROOT / "data/evidence/recommendation_evidence_links.csv")
    ev_by_rec = defaultdict(list)
    for e in evidence:
        ev_by_rec[e["recommendation_id"]].append(e)

    columns = [
        ("recommendation_id", "ID"),
        ("priority", "Priority"),
        ("time_horizon", "Horizon"),
        ("policy_goal", "Goal"),
        ("title", "Recommendation"),
        ("implementation_vehicle", "Vehicle"),
        ("kpi_primary", "KPI"),
        ("target", "Target"),
        ("verification_state", "Status"),
        ("confidence", "Confidence"),
    ]
    priorities = sorted({r.get("priority", "") for r in rows if r.get("priority")})
    horizons = sorted(
        {r.get("time_horizon", "") for r in rows if r.get("time_horizon")}
    )

    filter_controls_html = render_filter_controls(
        "recs-table",
        "Search recommendations",
        [("priority", "Priority", priorities), ("time_horizon", "Horizon", horizons)],
    )
    table_guide_html = render_table_guide(
        "How to read this table",
        [
            "Each row is one actionable recommendation.",
            "Priority and confidence support triage and sequencing.",
            "Implementation vehicle identifies whether delivery is guidance, SI, or statutory change.",
            "KPI and target define the measurable intended impact.",
            "Click a Recommendation ID to open the full recommendation drill-down page.",
        ],
    )
    data_fields = [
        "recommendation_id",
        "priority",
        "time_horizon",
        "policy_goal",
        "title",
        "implementation_vehicle",
        "confidence",
        "verification_state",
    ]
    filterable_table_html = render_filterable_table(
        rows, columns, "recs-table", data_fields
    )
    filter_script = render_filter_script("recs-table", data_fields)
    enhancements_script = render_table_enhancements_script(
        "recs-table",
        presets=[
            {"label": "High priority only", "filters": {"priority": "High"}},
            {"label": "Near term (0-12)", "filters": {"time_horizon": "0-12 months"}},
            {"label": "High confidence", "filters": {"confidence": "high"}},
        ],
    )

    # Evidence traces: build per-rec evidence data for template
    evidence_guide_html = render_table_guide(
        "How to read the evidence tables",
        [
            "Source identifies the dataset or guidance used.",
            "Metric and baseline value explain the current-state evidence point.",
            "Baseline window shows the measurement period.",
            "Open source links to verify references directly.",
        ],
    )

    evidence_traces = []
    for row in rows:
        rid = row["recommendation_id"]
        evs = ev_by_rec.get(rid, [])
        trace = {
            "rid": rid,
            "title": row["title"],
            "detail_href": recommendation_detail_page(rid),
            "confidence_badge_html": confidence_badge(row.get("confidence", "")),
            "verification_badge_html": verification_badge(
                row.get("verification_state", "")
            ),
            "evidence": evs,
        }
        evidence_traces.append(trace)

    return {
        "output_filename": "recommendations.html",
        "title": "Recommendations and Model Text",
        "subhead": "Actionable reforms with evidence traces, confidence, and verification state.",
        "active": "recommendations",
        "context_text": "Each recommendation includes delivery details, expected outcomes, and direct links to supporting evidence rows.",
        "purpose": {
            "what": "Reform recommendations with owners, vehicles, KPIs, and evidence links.",
            "who": "Policy and delivery teams prioritizing actionable changes.",
            "how": "Start with priority and confidence, then review implementation details and evidence traceability.",
            "data": "Every recommendation is linked to at least one evidence record in the evidence links dataset.",
        },
        "show_trust_panel": False,
        "next_steps": [
            ("roadmap.html", "Open implementation roadmap"),
            ("consultation.html", "Open consultation tracker"),
            ("sources.html", "Review source evidence index"),
        ],
        "filter_controls_html": filter_controls_html,
        "table_guide_html": table_guide_html,
        "filterable_table_html": filterable_table_html,
        "filter_script": filter_script,
        "enhancements_script": enhancements_script,
        "evidence_guide_html": evidence_guide_html,
        "evidence_traces": evidence_traces,
    }


def recommendation_detail_contexts():
    """Return a list of context dicts, one per recommendation."""
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

    contexts = []
    for rec in recs:
        rid = rec.get("recommendation_id", "")
        linked_issue_ids = split_pipe_values(rec.get("linked_issues", ""))
        linked_issues = [
            issue_by_id[iid] for iid in linked_issue_ids if iid in issue_by_id
        ]
        linked_evidence = ev_by_rec.get(rid, [])
        linked_milestones = milestones_by_rec.get(rid, [])
        status = status_by_id.get(rid, {})

        # TOC
        toc_html = render_detail_toc(
            [
                ("summary", "Summary"),
                ("evidence", "Evidence"),
                ("connected-items", "Connected items"),
                ("actions", "Actions"),
            ]
        )

        # Badges
        verification_badge_html = verification_badge(rec.get("verification_state", ""))
        confidence_badge_html = confidence_badge(rec.get("confidence", ""))

        # Linked issues with detail page hrefs
        issues_data = []
        for issue in linked_issues:
            iid = issue.get("issue_id", "")
            issues_data.append(
                {
                    **issue,
                    "detail_href": issue_detail_page(iid),
                }
            )

        # Evidence links with source handling
        evidence_data = []
        for ev in linked_evidence:
            evidence_data.append(
                {
                    **ev,
                    "has_source": bool(ev.get("source_url", "")),
                }
            )

        # Affected authorities observed in linked issue appeals
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
                    authority_links.append(
                        {
                            "html": f'<a href="plans-{pid.lower()}.html">{html_lib.escape(lpa.get("lpa_name", ""))}</a>',
                        }
                    )
                else:
                    authority_links.append(
                        {
                            "html": html_lib.escape(ap.get("lpa", "")),
                        }
                    )

        # Connected recommendations (same issue graph)
        related_recs = []
        seen_ids = {rid}
        for issue_id in linked_issue_ids:
            for candidate in recs_by_issue.get(issue_id, []):
                cid = candidate.get("recommendation_id", "")
                if cid in seen_ids:
                    continue
                seen_ids.add(cid)
                related_recs.append(
                    {
                        **candidate,
                        "detail_href": recommendation_detail_page(cid),
                    }
                )
        related_recs.sort(key=lambda r: r.get("recommendation_id", ""))

        # Context links query params
        pr_q = html_lib.escape(query_value(rec.get("priority", "")))
        hz_q = html_lib.escape(query_value(rec.get("time_horizon", "")))

        ctx = {
            "output_filename": recommendation_detail_page(rid),
            "title": f"{rid} Detail",
            "subhead": "Detailed recommendation drill-down with status timeline and evidence links.",
            "active": "recommendations",
            "context_text": "Use this page to inspect implementation context, linked contradictions, and evidence rows for a single recommendation.",
            "purpose": {
                "what": "Reform recommendations with owners, vehicles, KPIs, and evidence links.",
                "who": "Policy and delivery teams prioritizing actionable changes.",
                "how": "Start with priority and confidence, then review implementation details and evidence traceability.",
                "data": "Every recommendation is linked to at least one evidence record in the evidence links dataset.",
            },
            "show_trust_panel": False,
            "breadcrumbs": [
                ("index.html", "Overview"),
                ("recommendations.html", "Recommendations"),
                ("recommendations.html", "Recommendations"),
                (recommendation_detail_page(rid), rid),
            ],
            "next_steps": [
                ("recommendations.html", "Back to recommendations"),
                ("roadmap.html", "Open implementation roadmap"),
                ("consultation.html", "Open consultation tracker"),
            ],
            "rec": rec,
            "rid": rid,
            "status": status,
            "toc_html": toc_html,
            "verification_badge_html": verification_badge_html,
            "confidence_badge_html": confidence_badge_html,
            "linked_issues": issues_data,
            "linked_evidence": evidence_data,
            "linked_milestones": linked_milestones,
            "authority_links": authority_links,
            "related_recs": related_recs,
            "pr_q": pr_q,
            "hz_q": hz_q,
        }
        contexts.append(ctx)

    return contexts


def roadmap_context():
    """Return template context dict for roadmap.html."""
    milestones = read_csv(ROOT / "data/issues/implementation-roadmap.csv")
    recs = read_csv(ROOT / "data/issues/recommendations.csv")
    quick = [m for m in milestones if m.get("phase") == "Quick Wins"]
    structural = [m for m in milestones if m.get("phase") == "Statutory and Structural"]

    quick_guide_html = render_table_guide(
        "How to read roadmap tables",
        [
            "Each row is a milestone or action in the implementation sequence.",
            "Read top-to-bottom to follow intended delivery order.",
            "Dependencies identify prerequisites for later milestones.",
            "Use owner and metric columns to assign accountability.",
        ],
    )
    quick_table_html = render_table(
        quick,
        [
            ("window", "Window"),
            ("action", "Action"),
            ("owner", "Owner"),
            ("linked_recommendations", "Recs"),
            ("status_metric", "Metric"),
        ],
    )
    structural_table_html = render_table(
        structural,
        [
            ("window", "Window"),
            ("action", "Action"),
            ("owner", "Owner"),
            ("dependencies", "Dependencies"),
            ("linked_recommendations", "Recs"),
        ],
    )
    horizon_table_html = render_table(
        recs,
        [
            ("recommendation_id", "Rec"),
            ("title", "Title"),
            ("time_horizon", "Horizon"),
            ("delivery_owner", "Owner"),
            ("implementation_vehicle", "Vehicle"),
        ],
    )

    return {
        "output_filename": "roadmap.html",
        "title": "Implementation Roadmap",
        "subhead": "Delivery sequence from quick wins to statutory reform.",
        "active": "roadmap",
        "context_text": "This timeline shows how reforms can be phased, who leads delivery, and which dependencies affect sequencing.",
        "purpose": {
            "what": "A sequenced implementation plan from near-term actions to longer reforms.",
            "who": "Program owners and stakeholders managing delivery order and dependencies.",
            "how": "Read milestones in order and use dependencies and owners to plan delivery cadence.",
            "data": "Roadmap records are maintained in the implementation dataset and updated as statuses evolve.",
        },
        "show_trust_panel": False,
        "next_steps": [
            ("consultation.html", "Open consultation and status"),
            ("recommendations.html", "Return to recommendations"),
            ("reports.html", "Open authority report bundles"),
        ],
        "quick_guide_html": quick_guide_html,
        "quick_table_html": quick_table_html,
        "structural_table_html": structural_table_html,
        "horizon_table_html": horizon_table_html,
    }


def consultation_context():
    """Return template context dict for consultation.html."""
    recs = read_csv(ROOT / "data/issues/recommendations.csv")
    statuses = read_csv(ROOT / "data/issues/recommendation-status.csv")
    status_map = {r["recommendation_id"]: r for r in statuses}

    # Status summary counts
    counts = defaultdict(int)
    for r in statuses:
        counts[r.get("submission_status", "Unknown")] += 1

    status_summary = sorted(counts.items())

    table_guide_html = render_table_guide(
        "How to read this table",
        [
            "Each row tracks consultation progress for one recommendation.",
            "Status indicates workflow stage for external submission.",
            "Submitted to and next action capture operational follow-up.",
            "Use recommendation ID to cross-reference recommendation details.",
        ],
    )

    # Build tracker rows for template
    tracker_rows = []
    for rec in recs:
        rid = rec["recommendation_id"]
        s = status_map.get(rid, {})
        status_val = s.get("submission_status", "Not submitted")
        css = {
            "Adopted": "badge-green",
            "Submitted": "badge-blue",
            "Response received": "badge-blue",
            "Rejected": "badge-red",
            "Not submitted": "badge-grey",
            "Under review": "badge-amber",
        }.get(status_val, "badge-grey")
        tracker_rows.append(
            {
                "rid": rid,
                "title": rec.get("title", ""),
                "status_val": status_val,
                "css": css,
                "submitted_to": s.get("submitted_to", "\u2014"),
                "next_action": s.get("next_action", ""),
            }
        )

    return {
        "output_filename": "consultation.html",
        "title": "Consultation and Status",
        "subhead": "Submission status tracker, disclaimer, and how to respond to this analysis.",
        "active": "consultation",
        "context_text": "Track recommendation submission progress, review disclaimers, and find routes for feedback or evidence contributions.",
        "purpose": {
            "what": "Submission status and consultation tracking for recommendations.",
            "who": "Stakeholders monitoring where recommendations have been sent and responses received.",
            "how": "Check status by recommendation ID, then review next actions.",
            "data": "Statuses are drawn from the recommendation-status dataset with current workflow fields.",
        },
        "show_trust_panel": False,
        "next_steps": [
            ("recommendations.html", "Open recommendation details"),
            ("roadmap.html", "Open implementation roadmap"),
            ("sources.html", "Open source evidence"),
        ],
        "status_summary": status_summary,
        "table_guide_html": table_guide_html,
        "tracker_rows": tracker_rows,
    }
