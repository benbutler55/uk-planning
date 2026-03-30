"""Pure metric and utility functions with no HTML or I/O dependencies."""
import urllib.parse
from datetime import date


def weighted_score(row, weights):
    total = 0.0
    for dim, spec in weights.items():
        raw = float(row.get(dim, 0) or 0)
        if dim == "fixability_score":
            raw = 6 - raw  # invert: higher fixability = lower weighted contribution
        total += raw * spec["weight"]
    return round(total, 2)


def cohort_for_pid(pid):
    cohort_1 = {"LPA-01", "LPA-02", "LPA-03", "LPA-04", "LPA-05", "LPA-06"}
    return "Cohort 1" if pid in cohort_1 else "Cohort 2"


def analytical_confidence_for_tier(tier):
    mapping = {
        "A": "high",
        "B": "medium",
        "C": "low",
    }
    return mapping.get((tier or "").strip().upper(), "low")


def peer_group_for_lpa(lpa):
    lpa_type = (lpa.get("lpa_type", "") or "").strip().lower()
    growth = (lpa.get("growth_context", "") or "").strip().lower()
    if "national park" in lpa_type:
        return "National park authorities"
    if "county" in lpa_type:
        return "County strategic authorities"
    if "london borough" in lpa_type:
        return "London urban authorities"
    if "metropolitan" in lpa_type or "high growth urban" in growth or "very high urban growth" in growth:
        return "High-growth urban authorities"
    if "high demand constrained" in growth or "green belt" in (lpa.get("constraint_profile", "") or "").lower():
        return "Constrained housing-pressure authorities"
    if "regeneration" in growth or "urban renewal" in growth:
        return "Regeneration-focused authorities"
    return "Mixed and dispersed authorities"


def derive_plan_age_years(pid, docs_by_lpa):
    records = docs_by_lpa.get(pid, [])
    adopted_dates = []
    for rec in records:
        if (rec.get("status", "") or "").lower() not in {"adopted", "in force"}:
            continue
        dt = parse_iso_date(rec.get("adoption_or_publication_date", ""))
        if dt:
            adopted_dates.append(dt)
    if not adopted_dates:
        return None
    latest = max(adopted_dates)
    return round((date.today() - latest).days / 365.25, 1)


def derive_metric_bundle(lpa, issue_row, quality_row, trend_rows, docs_by_lpa, national_validation_proxy):
    pid = lpa.get("pilot_id", "")
    quality_tier = quality_row.get("data_quality_tier", "")
    issue_count = int(issue_row.get("total_linked_issues", 0) or 0)
    high_sev = int(issue_row.get("high_severity_issues", 0) or 0)
    risk_stage = (issue_row.get("primary_risk_stage", "") or "").strip().lower()
    speed = None
    latest_appeal = None
    if trend_rows:
        try:
            speed = float(trend_rows[-1].get("major_in_time_pct", 0) or 0)
        except ValueError:
            speed = None
        try:
            latest_appeal = float(trend_rows[-1].get("appeals_overturned_pct", 0) or 0)
        except ValueError:
            latest_appeal = None

    speeds = []
    for row in trend_rows:
        try:
            speeds.append(float(row.get("major_in_time_pct", 0) or 0))
        except ValueError:
            continue
    volatility = 0.0
    if len(speeds) > 1:
        mean_speed = sum(speeds) / len(speeds)
        volatility = (sum((v - mean_speed) ** 2 for v in speeds) / len(speeds)) ** 0.5

    # 1) validation rework proxy
    tier_adjust = {"A": -1.5, "B": 0.0, "C": 2.0}.get(quality_tier, 0.0)
    issue_adjust = min(4.0, issue_count * 0.12)
    volatility_adjust = min(1.8, volatility * 0.6)
    validation_rework_proxy = round(max(5.0, national_validation_proxy + tier_adjust + issue_adjust + volatility_adjust), 1)

    # 2) delegated decision proxy
    lpa_type = (lpa.get("lpa_type", "") or "").lower()
    delegated_base = 90.0
    if "metropolitan" in lpa_type or "london borough" in lpa_type:
        delegated_base = 86.0
    elif "county" in lpa_type:
        delegated_base = 82.0
    elif "national park" in lpa_type:
        delegated_base = 84.0
    speed_adjust = 0.0 if speed is None else max(-3.0, min(2.0, (speed - 74.0) * 0.12))
    appeal_adjust = 0.0 if latest_appeal is None else max(-2.5, min(1.0, (1.9 - latest_appeal) * 1.4))
    delegated_ratio_proxy = round(max(70.0, min(95.0, delegated_base - (high_sev * 0.5) + speed_adjust + appeal_adjust)), 1)

    # 3) plan age metric
    plan_age_years = derive_plan_age_years(pid, docs_by_lpa)

    # 4) consultation lag proxy
    stage_adjust = {
        "consultation": 1.8,
        "committee": 1.2,
        "pre-application": 0.8,
        "validation": 0.6,
        "legal agreements": 1.0,
        "condition discharge": 1.1,
    }.get(risk_stage, 0.4)
    consultation_lag_proxy = round(min(10.0, 1.2 + (high_sev * 0.35) + stage_adjust + (0 if quality_tier == "A" else 0.8 if quality_tier == "B" else 1.6)), 1)

    # 5) backlog pressure index
    speed_gap = max(0.0, 74.0 - (speed if isinstance(speed, float) else 74.0))
    plan_age_factor = 0.0 if plan_age_years is None else max(0.0, (plan_age_years - 5.0) * 2.5)
    backlog_pressure = round(min(100.0, issue_count * 3.6 + high_sev * 5.8 + speed_gap * 2.0 + plan_age_factor), 1)

    return {
        "validation_rework_proxy": validation_rework_proxy,
        "delegated_ratio_proxy": delegated_ratio_proxy,
        "plan_age_years": plan_age_years,
        "consultation_lag_proxy": consultation_lag_proxy,
        "backlog_pressure": backlog_pressure,
        "analytical_confidence": analytical_confidence_for_tier(quality_tier),
    }


def parse_iso_date(raw):
    if not raw:
        return None
    try:
        return date.fromisoformat(raw)
    except ValueError:
        return None


def split_pipe_values(raw):
    if not raw:
        return []
    return [item.strip() for item in str(raw).split("|") if item.strip()]


def issue_detail_page(issue_id):
    return f"contradiction-{issue_id.lower()}.html"


def recommendation_detail_page(recommendation_id):
    return f"recommendation-{recommendation_id.lower()}.html"


def query_value(value):
    return urllib.parse.quote((value or "").strip().lower())
