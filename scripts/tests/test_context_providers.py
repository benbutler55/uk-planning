"""Tests for context provider functions — verify each returns correct dict shape."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from builders.data_loader import load_scoring

# Required keys that base.html expects from every context
BASE_KEYS = {"output_filename", "title", "subhead", "active"}


def assert_base_context(ctx, expected_active):
    """Verify a context dict has all required base.html keys."""
    for key in BASE_KEYS:
        assert key in ctx, f"Missing key '{key}' in context"
    assert ctx["active"] == expected_active
    assert ctx["output_filename"].endswith(".html")
    assert isinstance(ctx["title"], str) and ctx["title"]
    assert isinstance(ctx["subhead"], str) and ctx["subhead"]


# --- Methods ---


def test_methodology_context():
    from builders.context_providers.methods import methodology_context

    ctx = methodology_context()
    assert_base_context(ctx, "methodology")
    assert "evidence_gaps" in ctx
    assert "severity_counts" in ctx


def test_metric_methods_context():
    from builders.context_providers.methods import metric_methods_context

    ctx = metric_methods_context()
    assert_base_context(ctx, "metric-methods")


def test_sources_context():
    from builders.context_providers.methods import sources_context

    ctx = sources_context()
    assert_base_context(ctx, "sources")
    assert "evidence_links" in ctx
    assert "baselines" in ctx
    assert isinstance(ctx["evidence_links"], list)


def test_exports_context():
    from builders.context_providers.methods import exports_context

    ctx = exports_context()
    assert_base_context(ctx, "exports")
    assert "dataset_names" in ctx
    assert len(ctx["dataset_names"]) >= 10


def test_data_health_context():
    from builders.context_providers.methods import data_health_context

    ctx = data_health_context()
    assert_base_context(ctx, "data-health")
    assert "health_rows" in ctx
    assert "health_counts" in ctx
    assert isinstance(ctx["health_rows"], list)


# --- Overview ---


def test_index_context():
    from builders.context_providers.overview import index_context

    ctx = index_context()
    assert_base_context(ctx, "index")
    assert "metric_cards" in ctx
    assert "avg_delta" in ctx
    assert isinstance(ctx["metric_cards"], list)


def test_search_context():
    from builders.context_providers.overview import search_context

    ctx = search_context()
    assert_base_context(ctx, "search")


# --- Analysis ---


def test_legislation_context():
    from builders.context_providers.analysis import legislation_context

    ctx = legislation_context()
    assert_base_context(ctx, "legislation")


def test_contradictions_context():
    from builders.context_providers.analysis import contradictions_context

    weights = load_scoring()
    ctx = contradictions_context(weights)
    assert_base_context(ctx, "contradictions")


def test_contradiction_detail_contexts():
    from builders.context_providers.analysis import contradiction_detail_contexts

    weights = load_scoring()
    contexts = contradiction_detail_contexts(weights)
    assert isinstance(contexts, list)
    assert len(contexts) >= 22  # at least 22 contradiction records
    for ctx in contexts:
        assert "output_filename" in ctx
        assert ctx["output_filename"].startswith("contradiction-")


def test_bottlenecks_context():
    from builders.context_providers.analysis import bottlenecks_context

    ctx = bottlenecks_context()
    assert_base_context(ctx, "bottlenecks")


def test_appeals_context():
    from builders.context_providers.analysis import appeals_context

    ctx = appeals_context()
    assert_base_context(ctx, "appeals")


def test_baselines_context():
    from builders.context_providers.analysis import baselines_context

    ctx = baselines_context()
    assert_base_context(ctx, "baselines")


# --- Recommendations ---


def test_recommendations_context():
    from builders.context_providers.recommendations import recommendations_context

    weights = load_scoring()
    ctx = recommendations_context(weights)
    assert_base_context(ctx, "recommendations")


def test_recommendation_detail_contexts():
    from builders.context_providers.recommendations import (
        recommendation_detail_contexts,
    )

    contexts = recommendation_detail_contexts()
    assert isinstance(contexts, list)
    assert len(contexts) >= 11
    for ctx in contexts:
        assert "output_filename" in ctx
        assert ctx["output_filename"].startswith("recommendation-")


def test_roadmap_context():
    from builders.context_providers.recommendations import roadmap_context

    ctx = roadmap_context()
    assert_base_context(ctx, "roadmap")


def test_consultation_context():
    from builders.context_providers.recommendations import consultation_context

    ctx = consultation_context()
    assert_base_context(ctx, "consultation")


# --- Authorities ---


def test_plans_context():
    from builders.context_providers.authorities import plans_context

    ctx = plans_context()
    assert_base_context(ctx, "plans")


def test_plans_detail_contexts():
    from builders.context_providers.authorities import plans_detail_contexts

    contexts = plans_detail_contexts()
    assert isinstance(contexts, list)
    assert len(contexts) >= 34  # 34 LPAs
    for ctx in contexts:
        assert "output_filename" in ctx
        assert ctx["output_filename"].startswith("plans-")


def test_map_context():
    from builders.context_providers.authorities import map_context

    ctx = map_context()
    assert_base_context(ctx, "map")


def test_compare_context():
    from builders.context_providers.authorities import compare_context

    ctx = compare_context()
    assert_base_context(ctx, "compare")


def test_benchmark_context():
    from builders.context_providers.authorities import benchmark_context

    ctx = benchmark_context()
    assert_base_context(ctx, "benchmark")


def test_trends_context():
    from builders.context_providers.authorities import trends_context

    ctx = trends_context()
    assert_base_context(ctx, "trends")


def test_reports_context():
    from builders.context_providers.authorities import reports_context

    ctx = reports_context()
    assert_base_context(ctx, "reports")


def test_coverage_context():
    from builders.context_providers.authorities import coverage_context

    ctx = coverage_context()
    assert_base_context(ctx, "coverage")


# --- Audiences ---


def test_policymakers_context():
    from builders.context_providers.audiences import policymakers_context

    ctx = policymakers_context()
    assert_base_context(ctx, "policymakers")


def test_lpas_context():
    from builders.context_providers.audiences import lpas_context

    ctx = lpas_context()
    assert_base_context(ctx, "lpas")


def test_developers_context():
    from builders.context_providers.audiences import developers_context

    ctx = developers_context()
    assert_base_context(ctx, "developers")


def test_public_context():
    from builders.context_providers.audiences import public_context

    ctx = public_context()
    assert_base_context(ctx, "public")
