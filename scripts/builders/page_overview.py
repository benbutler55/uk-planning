"""Overview, search index, and search page builders."""
import html
import json
from collections import defaultdict

from .config import ROOT, SITE
from .data_loader import read_csv, compute_data_health
from .metrics import issue_detail_page, recommendation_detail_page
from .html_utils import badge, page, write


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
