"""Audience-specific page builders: policymakers, LPAs, developers, public."""

from .config import ROOT, SITE
from .data_loader import read_csv
from .html_utils import render_table_guide, render_table, page, write


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
