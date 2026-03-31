"""Authority insights page builders: plans, map, compare, benchmark, reports, coverage."""
import csv
import html
import json
import math
from collections import defaultdict
from datetime import date

from .config import ROOT, SITE, BUILD_VERSION
from .data_loader import read_csv, compute_data_health, compute_onboarding_status_rows
from .metrics import (
    cohort_for_pid, peer_group_for_lpa, derive_metric_bundle,
)
from .html_utils import (
    badge, confidence_badge, provenance_badge, metric_help,
    render_table_guide, render_filter_script, render_table_enhancements_script,
    render_mobile_drawer_script, render_metric_context_block,
    render_plan_docs_table, sparkline_svg, page, write,
)


def build_plans():
    rows = read_csv(ROOT / "data/plans/pilot-lpas.csv")
    docs = read_csv(ROOT / "data/plans/pilot-plan-documents.csv")
    quality_rows = read_csv(ROOT / "data/plans/lpa-data-quality.csv")
    quality_by_id = {r["pilot_id"]: r for r in quality_rows}
    docs_by_lpa = defaultdict(list)
    for item in docs:
        docs_by_lpa[item["pilot_id"]].append(item)

    trend_rows = read_csv(ROOT / "data/evidence/lpa-quarterly-trends.csv")
    trends_by_id = defaultdict(list)
    for tr in trend_rows:
        trends_by_id[tr["pilot_id"]].append(tr)
    for pid in trends_by_id:
        trends_by_id[pid].sort(key=lambda x: x["quarter"])

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

        # Performance history section
        lpa_trends = trends_by_id.get(row["pilot_id"], [])
        if lpa_trends:
            pb += '<section class="card"><h2 id="performance-history">Performance History</h2>'
            pb += '<table><thead><tr><th>Quarter</th><th>Major in time %</th><th>Appeals overturned %</th><th>Change</th></tr></thead><tbody>'
            prev_speed = None
            for tr in lpa_trends:
                speed = float(tr["major_in_time_pct"])
                appeal = tr.get("appeals_overturned_pct", "n/a")
                if prev_speed is not None:
                    diff = speed - prev_speed
                    arrow = "\u2191" if diff > 0 else ("\u2193" if diff < 0 else "\u2192")
                    change_str = f"{arrow} {diff:+.1f} pp"
                else:
                    change_str = "\u2014"
                pb += (
                    f'<tr><td>{html.escape(tr["quarter"])}</td>'
                    f'<td>{html.escape(tr["major_in_time_pct"])}</td>'
                    f'<td>{html.escape(str(appeal))}</td>'
                    f'<td>{change_str}</td></tr>'
                )
                prev_speed = speed
            pb += '</tbody></table>'
            speeds = [float(t["major_in_time_pct"]) for t in lpa_trends]
            pb += f'<p>Trend: {sparkline_svg(speeds)}</p>'
            pb += '<p class="small"><a href="trends.html">View full trend analysis</a></p>'
            pb += '</section>'

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
