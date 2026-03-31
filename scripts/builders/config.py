"""Site-wide configuration: paths, version, section navigation, and page-to-section mapping."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SITE = ROOT / "site"
EXPORTS = SITE / "exports"
SCORING_PATH = ROOT / "data/schemas/scoring.json"
BUILD_VERSION = "v12.0"

SECTION_CONFIG = {
    "overview": {
        "label": "Overview",
        "href": "index.html",
        "children": [
            ("index", "Overview", "index.html"),
            ("search", "Search", "search.html"),
        ],
    },
    "system-analysis": {
        "label": "System Analysis",
        "href": "contradictions.html",
        "children": [
            ("legislation", "Legislation", "legislation.html"),
            ("contradictions", "Contradictions", "contradictions.html"),
            ("bottlenecks", "Bottlenecks", "bottlenecks.html"),
            ("appeals", "Appeals", "appeals.html"),
            ("baselines", "Baselines", "baselines.html"),
        ],
    },
    "authority-insights": {
        "label": "Authority Insights",
        "href": "plans.html",
        "children": [
            ("plans", "Plans", "plans.html"),
            ("map", "Map", "map.html"),
            ("compare", "Compare", "compare.html"),
            ("benchmark", "Benchmark", "benchmark.html"),
            ("reports", "Reports", "reports.html"),
            ("coverage", "Coverage", "coverage.html"),
        ],
    },
    "recommendations": {
        "label": "Recommendations",
        "href": "recommendations.html",
        "children": [
            ("recommendations", "Recommendations", "recommendations.html"),
            ("roadmap", "Roadmap", "roadmap.html"),
            ("consultation", "Consultation", "consultation.html"),
        ],
    },
    "data-methods": {
        "label": "Data & Methods",
        "href": "methodology.html",
        "children": [
            ("methodology", "Methodology", "methodology.html"),
            ("metric-methods", "Metric Methods", "metric-methods.html"),
            ("sources", "Sources", "sources.html"),
            ("exports", "Exports", "exports.html"),
            ("data-health", "Data Health", "data-health.html"),
        ],
    },
    "audiences": {
        "label": "For Audiences",
        "href": "audience-policymakers.html",
        "children": [
            ("policymakers", "Policy Makers", "audience-policymakers.html"),
            ("lpas", "LPAs", "audience-lpas.html"),
            ("developers", "Developers", "audience-developers.html"),
            ("public", "Public", "audience-public.html"),
        ],
    },
}

PAGE_TO_SECTION = {
    "index": "overview",
    "search": "overview",
    "legislation": "system-analysis",
    "contradictions": "system-analysis",
    "bottlenecks": "system-analysis",
    "appeals": "system-analysis",
    "baselines": "system-analysis",
    "plans": "authority-insights",
    "map": "authority-insights",
    "compare": "authority-insights",
    "benchmark": "authority-insights",
    "reports": "authority-insights",
    "coverage": "authority-insights",
    "recommendations": "recommendations",
    "roadmap": "recommendations",
    "consultation": "recommendations",
    "methodology": "data-methods",
    "metric-methods": "data-methods",
    "sources": "data-methods",
    "exports": "data-methods",
    "data-health": "data-methods",
    "policymakers": "audiences",
    "lpas": "audiences",
    "developers": "audiences",
    "public": "audiences",
}
