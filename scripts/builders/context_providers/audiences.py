"""Context providers for Audience pages: policymakers, LPAs, developers, public."""

from ..config import ROOT
from ..data_loader import read_csv
from ..html_utils import render_table, render_table_guide


AUDIENCE_PURPOSES = {
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
}


def policymakers_context():
    """Return template context dict for audience-policymakers.html."""
    recs = read_csv(ROOT / "data/issues/recommendations.csv")
    issues = read_csv(ROOT / "data/issues/contradiction-register.csv")

    recs_guide_html = render_table_guide(
        "How to read this table",
        [
            "Priority and horizon show sequencing urgency.",
            "Owner and vehicle indicate delivery accountability and route.",
            "Confidence signals strength of supporting evidence.",
        ],
    )
    recs_table_html = render_table(
        recs,
        [
            ("recommendation_id", "ID"),
            ("priority", "Priority"),
            ("title", "Recommendation"),
            ("delivery_owner", "Owner"),
            ("implementation_vehicle", "Vehicle"),
            ("time_horizon", "Horizon"),
            ("confidence", "Confidence"),
        ],
    )
    issues_guide_html = render_table_guide(
        "How to read this table",
        [
            "Issue type and scope show where intervention is needed.",
            "Summary gives the practical policy conflict in plain language.",
            "Use confidence as a guide to evidence maturity.",
        ],
    )
    issues_table_html = render_table(
        issues,
        [
            ("issue_id", "Issue"),
            ("issue_type", "Type"),
            ("scope", "Scope"),
            ("summary", "Summary"),
            ("confidence", "Confidence"),
        ],
    )

    return {
        "output_filename": "audience-policymakers.html",
        "title": "For Policy Makers",
        "subhead": "Priority reforms, system friction, and implementation pathways.",
        "active": "policymakers",
        "context_text": "A policy-focused view of priority reforms, core friction points, and delivery routes for national and local action.",
        "purpose": AUDIENCE_PURPOSES["policymakers"],
        "show_trust_panel": False,
        "next_steps": [
            ("recommendations.html", "Open full recommendations"),
            ("roadmap.html", "Open implementation roadmap"),
            ("consultation.html", "Open consultation tracker"),
        ],
        "recs_guide_html": recs_guide_html,
        "recs_table_html": recs_table_html,
        "issues_guide_html": issues_guide_html,
        "issues_table_html": issues_table_html,
    }


def lpas_context():
    """Return template context dict for audience-lpas.html."""
    recs = read_csv(ROOT / "data/issues/recommendations.csv")
    lpa_recs = [r for r in recs if "LPA" in r.get("delivery_owner", "")]

    recs_guide_html = render_table_guide(
        "How to read this table",
        [
            "Each row is one LPA-relevant recommendation.",
            "KPI and target describe measurable outcomes.",
            "Use horizon to phase internal workplans.",
        ],
    )
    recs_table_html = render_table(
        lpa_recs if lpa_recs else recs,
        [
            ("recommendation_id", "ID"),
            ("title", "Recommendation"),
            ("time_horizon", "Horizon"),
            ("kpi_primary", "KPI"),
            ("target", "Target"),
        ],
    )

    baselines = read_csv(ROOT / "data/evidence/official_baseline_metrics.csv")
    pilot_baselines = [b for b in baselines if b.get("geography", "").startswith("LPA")]
    baselines_guide_html = ""
    baselines_table_html = ""
    if pilot_baselines:
        baselines_guide_html = render_table_guide(
            "How to read this table",
            [
                "Each metric shows a baseline for pilot authorities.",
                "Compare values by geography and unit only where equivalent.",
                "Use as starting point before assessing interventions.",
            ],
        )
        baselines_table_html = render_table(
            pilot_baselines,
            [
                ("metric_id", "ID"),
                ("metric_name", "Metric"),
                ("geography", "Authority"),
                ("value", "Value"),
                ("unit", "Unit"),
            ],
        )

    return {
        "output_filename": "audience-lpas.html",
        "title": "For Local Planning Authorities",
        "subhead": "LPA-specific actions, baselines, and KPI targets.",
        "active": "lpas",
        "context_text": "An operational view for LPAs showing actionable recommendations, local baselines, and measurable KPI targets.",
        "purpose": AUDIENCE_PURPOSES["lpas"],
        "show_trust_panel": False,
        "next_steps": [
            ("benchmark.html", "Open benchmark dashboard"),
            ("reports.html", "Download LPA report bundles"),
            ("data-health.html", "Check data freshness"),
        ],
        "recs_guide_html": recs_guide_html,
        "recs_table_html": recs_table_html,
        "has_pilot_baselines": bool(pilot_baselines),
        "baselines_guide_html": baselines_guide_html,
        "baselines_table_html": baselines_table_html,
    }


def developers_context():
    """Return template context dict for audience-developers.html."""
    recs = read_csv(ROOT / "data/issues/recommendations.csv")

    recs_table_html = render_table(
        recs,
        [
            ("recommendation_id", "ID"),
            ("title", "Recommendation"),
            ("time_horizon", "Timeline"),
            ("kpi_primary", "KPI"),
            ("target", "Target"),
        ],
    )

    return {
        "output_filename": "audience-developers.html",
        "title": "For Developers",
        "subhead": "How proposed reforms affect submission, timelines, and design certainty.",
        "active": "developers",
        "context_text": "A delivery-focused summary of reforms that affect application requirements, decision predictability, and project timelines.",
        "purpose": AUDIENCE_PURPOSES["developers"],
        "show_trust_panel": False,
        "next_steps": [
            ("plans.html", "Open authority plan profiles"),
            ("compare.html", "Open authority compare"),
            ("recommendations.html", "Open recommendation details"),
        ],
        "recs_table_html": recs_table_html,
    }


def public_context():
    """Return template context dict for audience-public.html."""
    return {
        "output_filename": "audience-public.html",
        "title": "For the Public",
        "subhead": "Plain-language summary of findings and proposed planning improvements.",
        "active": "public",
        "context_text": "A plain-language explanation of the problems identified, why they matter, and what changes are being proposed.",
        "purpose": AUDIENCE_PURPOSES["public"],
        "show_trust_panel": False,
        "next_steps": [
            ("contradictions.html", "Open contradiction summary"),
            ("recommendations.html", "Open recommendations"),
            ("consultation.html", "Open consultation status"),
        ],
    }
