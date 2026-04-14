#!/usr/bin/env python3
"""Build static site from CSV datasets. Generates HTML pages with filtering,
weighted scoring, confidence badges, evidence traces, and split audience views."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from builders.config import ROOT
from builders.data_loader import read_csv, load_scoring
from builders.export_utils import write_exports, write_exports_manifest, build_ux_kpi_report
from builders.page_overview import build_search_index
from builders.context_providers.analysis import (
    legislation_context, contradictions_context,
    contradiction_detail_contexts, bottlenecks_context,
    appeals_context, baselines_context,
)
from builders.page_authorities import (
    build_plans, build_map, build_compare, build_benchmark,
    build_reports, build_coverage,
)
from builders.page_trends import build_trends
from builders.page_recommendations import (
    build_recommendations, build_recommendation_details,
    build_roadmap, build_consultation,
)
from builders.context_providers.methods import (
    methodology_context, metric_methods_context,
    sources_context, exports_context, data_health_context,
)
from builders.context_providers.overview import index_context, search_context
from site_builder import SiteBuilder
from builders.page_audiences import (
    build_audience_policymakers, build_audience_lpas,
    build_audience_developers, build_audience_public,
)


def main():
    weights = load_scoring()

    build_plans()
    build_recommendations(weights)
    build_recommendation_details()
    build_roadmap()
    build_map()
    build_compare()
    build_benchmark()
    build_trends()
    build_reports()
    build_coverage()
    build_consultation()
    build_search_index()
    build_audience_policymakers()
    build_audience_lpas()
    build_audience_developers()
    build_audience_public()
    # Jinja2-based pages
    builder = SiteBuilder()
    builder.register("index", "pages/index.html", index_context)
    builder.register("search", "pages/search.html", search_context)
    builder.register("methodology", "pages/methodology.html", methodology_context)
    builder.register("metric-methods", "pages/metric_methods.html", metric_methods_context)
    builder.register("sources", "pages/sources.html", sources_context)
    builder.register("exports", "pages/exports.html", exports_context)
    builder.register("data-health", "pages/data_health.html", data_health_context)
    builder.register("legislation", "pages/legislation.html", legislation_context)
    builder.register("contradictions", "pages/contradictions.html",
                     lambda: contradictions_context(weights))
    builder.register("bottlenecks", "pages/bottlenecks.html", bottlenecks_context)
    builder.register("appeals", "pages/appeals.html", appeals_context)
    builder.register("baselines", "pages/baselines.html", baselines_context)
    for detail_ctx in contradiction_detail_contexts(weights):
        page_name = detail_ctx["output_filename"].replace(".html", "")
        builder.register(page_name, "pages/contradiction_detail.html",
                         lambda c=detail_ctx: c)
    builder.render_all()

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
