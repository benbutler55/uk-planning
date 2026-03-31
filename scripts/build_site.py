#!/usr/bin/env python3
"""Build static site from CSV datasets. Generates HTML pages with filtering,
weighted scoring, confidence badges, evidence traces, and split audience views."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from builders.config import ROOT
from builders.data_loader import read_csv, load_scoring
from builders.export_utils import write_exports, write_exports_manifest, build_ux_kpi_report
from builders.page_overview import build_index, build_search_index, build_search
from builders.page_analysis import (
    build_legislation, build_contradictions, build_contradiction_details,
    build_bottlenecks, build_appeals, build_baselines,
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
from builders.page_methods import (
    build_methodology, build_metric_methods, build_sources,
    build_exports_index, build_data_health,
)
from builders.page_audiences import (
    build_audience_policymakers, build_audience_lpas,
    build_audience_developers, build_audience_public,
)


def main():
    weights = load_scoring()

    build_index()
    build_legislation()
    build_plans()
    build_contradictions(weights)
    build_recommendations(weights)
    build_contradiction_details(weights)
    build_recommendation_details()
    build_roadmap()
    build_baselines()
    build_bottlenecks()
    build_appeals()
    build_map()
    build_compare()
    build_benchmark()
    build_trends()
    build_reports()
    build_coverage()
    build_data_health()
    build_consultation()
    build_search_index()
    build_search()
    build_audience_policymakers()
    build_audience_lpas()
    build_audience_developers()
    build_audience_public()
    build_methodology()
    build_metric_methods()
    build_sources()
    build_exports_index()
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
