"""Context providers for System Analysis pages: legislation, contradictions,
contradiction details, bottlenecks, appeals, baselines."""
import html as html_lib
from collections import defaultdict

from ..config import ROOT
from ..data_loader import read_csv
from ..metrics import (
    weighted_score, split_pipe_values, issue_detail_page,
    recommendation_detail_page, query_value,
)
from ..html_utils import (
    confidence_badge, verification_badge,
    render_table, render_table_guide,
    render_filter_controls, render_filterable_table, render_filter_script,
    render_table_enhancements_script, render_mobile_drawer_script,
    render_detail_toc,
)


def legislation_context():
    """Return template context dict for legislation.html."""
    rows = read_csv(ROOT / "data/legislation/england-core-legislation.csv")
    policy_rows = read_csv(ROOT / "data/policy/england-national-policy.csv")

    legislation_columns = [
        ("title", "Instrument"), ("type", "Type"), ("status", "Status"),
        ("decision_weight", "Decision Weight"), ("citation", "Citation"),
        ("source_url", "Source"),
    ]
    policy_columns = [
        ("title", "Policy or Guidance"), ("type", "Type"), ("authority", "Owner"),
        ("status", "Status"), ("scope", "Scope"), ("source_url", "Source"),
    ]

    table_guide_html = render_table_guide("How to read this table", [
        "Each row is one legal or policy instrument used in planning decisions.",
        "Decision weight indicates practical influence in decision making.",
        "Use status and type together to separate in-force law from guidance.",
        "Source links open the originating official publication.",
    ])
    legislation_table_html = render_table(rows, legislation_columns)
    policy_guide_html = render_table_guide("How to read the policy index", [
        "This table complements legislation with national policy and guidance records.",
        "Scope helps identify whether a record applies to housing, infrastructure, or mixed pathways.",
        "Owner identifies the responsible body for updates.",
    ])
    policy_table_html = render_table(policy_rows, policy_columns)

    return {
        "output_filename": "legislation.html",
        "title": "Legislation and Regulations Library",
        "subhead": "England-first inventory of acts, regulations, and national policy.",
        "active": "legislation",
        "context_text": "Use this page to trace the legal and policy instruments that shape planning decisions, including status, ownership, and source links.",
        "purpose": {
            "what": "The legislation and policy library that underpins planning decisions in scope.",
            "who": "Policy professionals, legal reviewers, and users tracing legal context.",
            "how": "Filter by instrument type and status to find the relevant law or policy, then follow source links.",
            "data": "Official legal and policy references are linked to source URLs and retrieval dates.",
        },
        "show_trust_panel": False,
        "next_steps": [
            ("plans.html", "Open plan hierarchy explorer"),
            ("contradictions.html", "Open contradictions dashboard"),
            ("sources.html", "Open source reference page"),
        ],
        "table_guide_html": table_guide_html,
        "legislation_table_html": legislation_table_html,
        "policy_guide_html": policy_guide_html,
        "policy_table_html": policy_table_html,
    }


def contradictions_context(weights):
    """Return template context dict for contradictions.html."""
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
    type_breakdown = sorted(counts_by_type.items())

    # Scoring model description
    scoring_parts = ", ".join(
        f"{dim} ({spec['weight'] * 100:.0f}%)" for dim, spec in weights.items()
    )

    # Filter options
    issue_types = sorted({r.get("issue_type", "") for r in rows if r.get("issue_type")})
    pathways = sorted({r.get("affected_pathway", "") for r in rows if r.get("affected_pathway")})
    scopes = sorted({r.get("scope", "") for r in rows if r.get("scope")})

    # Pre-rendered HTML blocks from html_utils helpers
    filter_controls_html = render_filter_controls("issues-table", "Search issues", [
        ("issue_type", "Type", issue_types),
        ("affected_pathway", "Pathway", pathways),
        ("scope", "Scope", scopes),
    ])
    table_guide_html = render_table_guide("How to read this table", [
        "Each row is one contradiction record.",
        "Weighted score combines severity, frequency, legal risk, delay impact, and fixability.",
        "Higher scores indicate higher operational priority.",
        "Confidence and verification badges show evidence maturity.",
        "Click an Issue ID to open the full contradiction drill-down page.",
    ])
    data_fields = [
        "issue_id", "scope", "issue_type", "affected_pathway",
        "summary", "confidence", "verification_state",
    ]
    filterable_table_html = render_filterable_table(rows, columns, "issues-table", data_fields)
    filter_script = render_filter_script("issues-table", data_fields)
    enhancements_script = render_table_enhancements_script("issues-table", presets=[
        {"label": "Housing only", "filters": {"affected_pathway": "housing"}},
        {"label": "National scope", "filters": {"scope": "national"}},
        {"label": "High confidence", "filters": {"confidence": "high"}},
    ])
    drawer_script = render_mobile_drawer_script("issues-table", [
        "Issue", "Scope", "Type", "Pathway", "Weighted Score",
        "Severity", "Delay", "Status", "Confidence", "Summary",
    ])

    return {
        "output_filename": "contradictions.html",
        "title": "Contradictions and Bottlenecks",
        "subhead": "Cross-layer conflicts scored with explicit weighting and confidence levels.",
        "active": "contradictions",
        "context_text": "Review the highest-friction conflicts in the planning system, with weighted scores and filters to focus on specific pathways or issue types.",
        "purpose": {
            "what": "System contradictions and friction points scored by impact, risk, and frequency.",
            "who": "Policy leads, analysts, and non-specialists who need a ranked issue view.",
            "how": "Filter by pathway, stage, and type, then review high-scoring issues first.",
            "data": "Scores are derived from the published methodology and linked evidence records.",
        },
        "show_trust_panel": True,
        "next_steps": [
            ("bottlenecks.html", "Open bottleneck heatmap"),
            ("appeals.html", "Review appeal evidence"),
            ("recommendations.html", "Open linked recommendations"),
        ],
        "scoring_parts": scoring_parts,
        "issue_count": issue_count,
        "avg_ws": avg_ws,
        "type_breakdown": type_breakdown,
        "filter_controls_html": filter_controls_html,
        "table_guide_html": table_guide_html,
        "filterable_table_html": filterable_table_html,
        "filter_script": filter_script,
        "enhancements_script": enhancements_script,
        "drawer_script": drawer_script,
    }


def contradiction_detail_contexts(weights):
    """Return a list of context dicts, one per contradiction issue."""
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

    contexts = []
    for issue in issues:
        issue_id = issue.get("issue_id", "")
        ws = f"{weighted_score(issue, weights):.2f}"
        issue["weighted_score"] = ws
        linked_recs = recs_by_issue.get(issue_id, [])
        linked_appeals = appeals_by_issue.get(issue_id, [])
        linked_bottlenecks = bottlenecks_by_issue.get(issue_id, [])

        # Evidence counts per recommendation
        recs_with_ev = []
        for rec in linked_recs:
            rid = rec.get("recommendation_id", "")
            recs_with_ev.append({
                **rec,
                "detail_href": recommendation_detail_page(rid),
                "evidence_count": str(len(ev_by_rec.get(rid, []))),
            })

        # Linked appeals with source handling
        appeals_data = []
        for ap in linked_appeals:
            appeals_data.append({
                **ap,
                "has_source": bool(ap.get("source_url", "")),
            })

        # Affected authorities observed in appeals
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
                authority_links.append({
                    "html": f'<a href="plans-{pid.lower()}.html">{html_lib.escape(lpa.get("lpa_name", ""))}</a>',
                })
            else:
                authority_links.append({
                    "html": html_lib.escape(ap.get("lpa", "")),
                })

        # TOC
        toc_html = render_detail_toc([
            ("summary", "Summary"),
            ("evidence", "Evidence"),
            ("connected-items", "Connected items"),
            ("actions", "Actions"),
        ])

        # Badges
        verification_badge_html = verification_badge(issue.get("verification_state", ""))
        confidence_badge_html = confidence_badge(issue.get("confidence", ""))

        # Linked instruments
        instruments = split_pipe_values(issue.get("linked_instruments", ""))

        # Context links query params
        type_q = html_lib.escape(query_value(issue.get("issue_type", "")))
        path_q = html_lib.escape(query_value(issue.get("affected_pathway", "")))
        scope_q = html_lib.escape(query_value(issue.get("scope", "")))

        ctx = {
            "output_filename": issue_detail_page(issue_id),
            "title": f"{issue_id} Detail",
            "subhead": "Detailed contradiction drill-down with linked recommendations and evidence.",
            "active": "contradictions",
            "context_text": "Use this page to inspect scoring, evidence, and connected recommendations for a single contradiction record.",
            "purpose": {
                "what": "System contradictions and friction points scored by impact, risk, and frequency.",
                "who": "Policy leads, analysts, and non-specialists who need a ranked issue view.",
                "how": "Filter by pathway, stage, and type, then review high-scoring issues first.",
                "data": "Scores are derived from the published methodology and linked evidence records.",
            },
            "show_trust_panel": False,
            "breadcrumbs": [
                ("index.html", "Overview"),
                ("contradictions.html", "System Analysis"),
                ("contradictions.html", "Contradictions"),
                (issue_detail_page(issue_id), issue_id),
            ],
            "next_steps": [
                ("contradictions.html", "Back to contradiction register"),
                ("recommendations.html", "Open recommendations"),
                ("appeals.html", "Open appeal evidence"),
            ],
            "issue": issue,
            "issue_id": issue_id,
            "weighted_score": ws,
            "toc_html": toc_html,
            "verification_badge_html": verification_badge_html,
            "confidence_badge_html": confidence_badge_html,
            "instruments": instruments,
            "linked_recs": recs_with_ev,
            "linked_appeals": appeals_data,
            "linked_bottlenecks": linked_bottlenecks,
            "authority_links": authority_links,
            "type_q": type_q,
            "path_q": path_q,
            "scope_q": scope_q,
        }
        contexts.append(ctx)

    return contexts


def bottlenecks_context():
    """Return template context dict for bottlenecks.html."""
    rows = read_csv(ROOT / "data/issues/bottleneck-heatmap.csv")
    stages = ["Pre-application", "Validation", "Consultation", "Committee",
              "Legal Agreements", "Condition Discharge"]
    pathways = ["Housing", "Commercial", "Infrastructure", "Mixed"]

    total_delay = sum(float(r.get("median_delay_weeks", 0) or 0) for r in rows)
    worst = max(rows, key=lambda r: float(r.get("median_delay_weeks", 0) or 0)) if rows else {}

    # Build heatmap lookup
    by_stage_pathway = {}
    for r in rows:
        key = (r.get("process_stage", ""), r.get("pathway", ""))
        by_stage_pathway[key] = r

    # Build heatmap data for template
    heatmap_rows = []
    for stage in stages:
        cells = []
        for pw in pathways:
            entry = by_stage_pathway.get((stage, pw))
            if entry:
                weeks = float(entry.get("median_delay_weeks", 0) or 0)
                sev = entry.get("severity", "Low")
                css = {"High": "badge-red", "Medium": "badge-amber", "Low": "badge-green"}.get(sev, "badge-grey")
                cells.append({"weeks": f"{weeks:.0f}", "css": css, "has_data": True})
            else:
                cells.append({"has_data": False})
        heatmap_rows.append({"stage": stage, "cells": cells})

    detail_columns = [
        ("stage_id", "ID"), ("process_stage", "Stage"), ("pathway", "Pathway"),
        ("median_delay_weeks", "Median Delay (weeks)"), ("frequency", "Frequency"),
        ("severity", "Severity"), ("delay_driver", "Driver"), ("linked_issues", "Issues"),
    ]
    detail_guide_html = render_table_guide("How to read this table", [
        "Each row is one process-stage bottleneck with pathway context.",
        "Median delay shows central delay impact for that bottleneck pattern.",
        "Frequency indicates how often the issue appears in tracked records.",
        "Use linked issues to cross-reference contradiction evidence.",
    ])
    detail_table_html = render_table(rows, detail_columns)

    return {
        "output_filename": "bottlenecks.html",
        "title": "Bottleneck Heatmap",
        "subhead": "Process delay analysis across all six planning stages with severity and pathway breakdown.",
        "active": "bottlenecks",
        "context_text": "This heatmap highlights where delays concentrate in the planning process and which pathways are most affected.",
        "purpose": {
            "what": "Delay hotspots across the six planning stages, with severity and pathway context.",
            "who": "Process improvement teams and users diagnosing where time is lost.",
            "how": "Use the heatmap to identify high-friction stages, then review detailed rows for causes.",
            "data": "Bottleneck records are maintained in the issues datasets with review dates and linked issue IDs.",
        },
        "show_trust_panel": False,
        "next_steps": [
            ("contradictions.html", "Open contradiction register"),
            ("appeals.html", "Review appeals evidence"),
            ("recommendations.html", "Open reform recommendations"),
        ],
        "row_count": len(rows),
        "total_delay": total_delay,
        "worst": worst,
        "pathways": pathways,
        "heatmap_rows": heatmap_rows,
        "detail_guide_html": detail_guide_html,
        "detail_table_html": detail_table_html,
    }


def appeals_context():
    """Return template context dict for appeals.html."""
    rows = read_csv(ROOT / "data/evidence/appeal-decisions.csv")
    issues = read_csv(ROOT / "data/issues/contradiction-register.csv")
    issue_map = {r["issue_id"]: r["summary"] for r in issues}

    outcomes = sorted({r.get("outcome", "") for r in rows if r.get("outcome")})
    linked = sorted({r.get("linked_issue", "") for r in rows if r.get("linked_issue")})

    filter_controls_html = render_filter_controls("appeals-table", "Search appeals", [
        ("outcome", "Outcome", outcomes),
        ("linked_issue", "Linked Issue", linked),
    ])
    table_guide_html = render_table_guide("How to read this table", [
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
    data_fields = ["appeal_id", "lpa", "outcome", "linked_issue", "policy_cited", "inspector_finding"]
    filterable_table_html = render_filterable_table(rows, columns, "appeals-table", data_fields)
    filter_script = render_filter_script("appeals-table", data_fields)

    # Issue cross-reference
    linked_by_issue = defaultdict(list)
    for r in rows:
        linked_by_issue[r.get("linked_issue", "")].append(r["appeal_id"])
    cross_ref = []
    for issue_id, appeal_ids in sorted(linked_by_issue.items()):
        cross_ref.append({
            "issue_id": issue_id,
            "summary": issue_map.get(issue_id, ""),
            "appeal_ids": ", ".join(appeal_ids),
        })

    return {
        "output_filename": "appeals.html",
        "title": "Appeal Decision Evidence",
        "subhead": "Planning Inspectorate decisions cited as evidence for identified contradictions.",
        "active": "appeals",
        "context_text": "This page links appeal outcomes to specific contradiction records so users can inspect real-world decision evidence.",
        "purpose": {
            "what": "Appeal decisions used as practical evidence for contradiction patterns.",
            "who": "Users validating whether identified issues appear in real decisions.",
            "how": "Filter by issue, outcome, or LPA, then read inspector findings and linked policy citations.",
            "data": "Appeal examples are sourced from Planning Inspectorate references and tagged with retrieval dates.",
        },
        "show_trust_panel": False,
        "next_steps": [
            ("contradictions.html", "Open contradiction register"),
            ("bottlenecks.html", "Open bottleneck analysis"),
            ("recommendations.html", "Open recommendations"),
        ],
        "filter_controls_html": filter_controls_html,
        "table_guide_html": table_guide_html,
        "filterable_table_html": filterable_table_html,
        "filter_script": filter_script,
        "cross_ref": cross_ref,
    }


def baselines_context():
    """Return template context dict for baselines.html."""
    rows = read_csv(ROOT / "data/evidence/official_baseline_metrics.csv")

    table_guide_html = render_table_guide("How to read this table", [
        "Each row is one baseline metric with source and period context.",
        "Compare geography and pathway before drawing conclusions.",
        "Period and retrieved_at dates help assess recency.",
        "Use these values as current-state benchmarks for reform impact.",
    ])
    table_html = render_table(rows, [
        ("metric_id", "ID"), ("metric_name", "Metric"), ("source_table", "Source"),
        ("geography", "Geography"), ("pathway", "Pathway"), ("value", "Value"),
        ("unit", "Unit"), ("period", "Period"),
    ])

    return {
        "output_filename": "baselines.html",
        "title": "Official Baseline Metrics",
        "subhead": "KPI baselines from GOV.UK planning statistics and Planning Inspectorate data.",
        "active": "baselines",
        "context_text": "Use these baseline metrics to understand current performance levels before assessing the impact of proposed reforms.",
        "purpose": {
            "what": "Baseline performance metrics used to measure current planning outcomes.",
            "who": "Users benchmarking current performance before evaluating reforms.",
            "how": "Compare England-level and LPA-level values, then connect metrics to recommendations.",
            "data": "Baselines are sourced from GOV.UK and PINS tables with source table IDs and retrieval dates.",
        },
        "show_trust_panel": False,
        "next_steps": [
            ("benchmark.html", "Open benchmark dashboard"),
            ("reports.html", "Open authority reports"),
            ("recommendations.html", "Open recommendations"),
        ],
        "table_guide_html": table_guide_html,
        "table_html": table_html,
    }
