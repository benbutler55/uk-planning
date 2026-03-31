"""Data and methods page builders: methodology, metric methods, sources, exports index, data health."""
import html

from .config import ROOT, SITE
from .data_loader import read_csv, compute_data_health
from .html_utils import badge, render_table_guide, render_table, page, write


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

    # Evidence gaps summary
    gaps_path = ROOT / "data/evidence/evidence-gaps.csv"
    if gaps_path.exists():
        gaps = read_csv(gaps_path)
        severity_counts = {}
        for g in gaps:
            sev = g.get("severity", "unknown")
            severity_counts[sev] = severity_counts.get(sev, 0) + 1
        severity_colors = {"high": "red", "medium": "amber", "low": "green"}
        body += '<section class="card"><h2>Evidence Gaps</h2>'
        body += "<p>Known gaps in evidence coverage, tracked for remediation.</p>"
        body += "<p>"
        for sev in ["high", "medium", "low"]:
            if sev in severity_counts:
                body += f"{badge(sev, severity_colors[sev])} {severity_counts[sev]} &nbsp; "
        body += "</p>"
        body += '<table><thead><tr><th>Record</th><th>Type</th><th>Gap</th><th>Severity</th><th>Remediation</th></tr></thead><tbody>'
        for g in gaps:
            sev = g.get("severity", "unknown")
            color = severity_colors.get(sev, "grey")
            body += "<tr>"
            body += f"<td>{html.escape(g.get('record_id', ''))}</td>"
            body += f"<td>{html.escape(g.get('record_type', ''))}</td>"
            body += f"<td>{html.escape(g.get('gap_description', ''))}</td>"
            body += f"<td>{badge(sev, color)}</td>"
            body += f"<td>{html.escape(g.get('remediation_path', ''))}</td>"
            body += "</tr>"
        body += "</tbody></table></section>"

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
