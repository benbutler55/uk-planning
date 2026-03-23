# Next-Wave Delivery Roadmap (v7.x to v9.x)

## Objective

Turn the current pilot into a scalable decision-support platform by prioritizing:

1. Better user experience and interpretation safety
2. Broader, deeper evidence coverage
3. Staged expansion from 16 LPAs toward England-wide coverage

## Prioritization method

Each recommendation is ranked by:

- user impact (decision value for policy, LPA, and external users)
- delivery risk (complexity, data dependencies, QA burden)
- scale readiness (ability to support >50 LPAs without redesign)

## Ranked recommendations backlog

| Rank | Recommendation | Why now | Owner | Effort | Target window | Dependencies |
|---|---|---|---|---|---|---|
| 1 | Shared cross-page filters and URL state (`region`, `type`, `cohort`, `quality`) across `plans`, `benchmark`, `compare`, `reports` | Removes repeat filtering friction and improves analysis continuity | Data product lead + frontend engineer | M | 0-4 weeks | Existing page filter controls in `scripts/build_site.py` |
| 2 | England-at-a-glance KPI strip on `index.html` with trend arrows and links to source rows | Makes first-page value immediate and supports faster decision triage | Product editor + frontend engineer | S | 0-4 weeks | `official_baseline_metrics.csv`, `lpa-quarterly-trends.csv` |
| 3 | Expand metrics coverage (validation proxy, delegated/committee split, plan age, consultation lag, backlog pressure) | Current benchmark is useful but narrow; broader metrics reduce over-reliance on speed alone | Data lead + policy analyst | M | 2-8 weeks | Schema update in `data/schemas/datasets.json`; new/expanded source tables |
| 4 | Metric definitions and provenance tooltips on all benchmark/report tables | Reduces misinterpretation risk and increases trust in comparative outputs | UX/content lead + frontend engineer | S | 2-6 weeks | Existing provenance badges and page guide blocks |
| 5 | Map upgrade to boundary-led choropleth (retain markers as optional overlay) | Marker map does not scale well to larger cohorts; boundary view improves spatial interpretation | GIS/data engineer + frontend engineer | L | 4-12 weeks | Authority boundary dataset and simplification pipeline |
| 6 | Peer-group benchmark mode (compare against similar authorities rather than all authorities) | Makes comparisons fairer and more actionable for LPAs | Data scientist + policy analyst | M | 6-12 weeks | Authority clustering attributes and rules |
| 7 | Source reliability ladder and uncertainty display per metric | Clarifies confidence and supports cautious policy use where evidence is partial | Methodology lead + data engineer | M | 6-12 weeks | Extended schema fields for confidence/completeness |
| 8 | Automated ingestion expansion for GOV.UK planning statistics and PINS extracts (historical + quarterly refresh) | Manual updates will not scale to national coverage | Data engineer | L | 8-20 weeks | `scripts/ingest_govuk_stats.py`, source endpoint stability |
| 9 | Council onboarding pipeline (`ingest -> validate -> profile -> QA`) with cohort gating criteria | Standardizes growth from 16 LPAs to 50/150+ while protecting data quality | Data operations lead | M | 8-16 weeks | QA checklist, schema guardrails, cohort rules |
| 10 | Coverage tracker page (complete/partial/estimated per authority) | Sets clear user expectations during scale-out and improves transparency | Product editor + frontend engineer | S | 8-14 weeks | Onboarding status fields per authority |
| 11 | Mobile table detail drawer for dense pages (`benchmark`, `reports`, `contradictions`) | Improves practical usability for field users and stakeholders reviewing on phones | Frontend engineer | M | 10-16 weeks | Existing responsive styles in `site/assets/styles.css` |
| 12 | Release governance cadence (monthly refresh, quarterly methodology notes, annual policy reconciliation) | Prevents drift and keeps evidence base decision-ready | Project lead + methodology lead | S | 0-ongoing | Existing CI/freshness checks |

Effort key:

- `S`: up to 1 week
- `M`: 1 to 3 weeks
- `L`: 3+ weeks or multi-stream

## Delivery waves

### Wave A (0-6 weeks): User-value fast path

- R1 shared filters and URL state
- R2 index KPI strip
- R4 metric definition/provenance tooltips
- R12 governance cadence lock-in

Success checks:

- Users can apply one filter context and carry it across authority pages
- `index.html` links every KPI to a traceable data row/page
- Zero unsigned metric labels on benchmark/report tables

### Wave B (6-12 weeks): Evidence depth and interpretation quality

- R3 expanded metric coverage
- R6 peer-group benchmark mode
- R7 uncertainty and confidence presentation

Success checks:

- At least 5 new metrics with clear definitions and provenance
- Peer-group view available for every authority in scope
- Confidence/completeness visible for all non-official or estimated indicators

### Wave C (3-6 months): Scale engine

- R5 boundary-led national map
- R8 automated ingest expansion
- R9 council onboarding pipeline
- R10 coverage tracker
- R11 mobile dense-table improvements

Success checks:

- Cohort expansion to at least 50 LPAs with QA pass rates maintained
- Build and refresh cycle can run on schedule without manual recoding
- Coverage tracker publishes complete/partial/estimated status for every in-scope authority

## Owner model (recommended)

- Data product lead: cross-page UX priorities and release sequencing
- Data lead: dataset design, schema updates, quality controls
- Data engineer: ingestion, transforms, pipeline reliability
- Frontend engineer: interactive filters, map and responsive table UX
- Policy analyst: metric interpretation, authority comparability rules
- Methodology lead: confidence standards and publication governance

## Risks and mitigations

- Risk: expanded data sources introduce inconsistent fields and update cadences
- Mitigation: enforce schema-first additions and strict freshness thresholds in CI

- Risk: benchmark complexity reduces readability for non-technical audiences
- Mitigation: default simple views, progressive disclosure for advanced controls

- Risk: rapid LPA scale-out lowers confidence in weaker-source authorities
- Mitigation: publish quality tier, completeness score, and coverage status by default

## Immediate start list (this sprint)

1. Specify and implement shared filter-state contract (R1).
2. Add homepage KPI strip with source links (R2).
3. Add inline metric definitions/provenance helper pattern to benchmark/report tables (R4).
4. Publish monthly/quarterly governance cadence note and owner responsibilities (R12).

## Wave B implementation note

The current implementation adds Wave B features using a transparent proxy approach while additional official source integration is developed:

- Peer-group mode is now available in benchmark and report views for like-for-like authority comparison.
- Expanded authority indicators are shown for validation rework, delegated share, plan age, consultation lag, and backlog pressure.
- Expanded indicators are marked as analytical estimates and paired with confidence labels (`high`/`medium`/`low`) derived from authority data-quality tier.

Formula design intent for interim proxies:

- Keep directionality interpretable and monotonic (worse signals increase pressure metrics).
- Tie confidence to documented evidence quality.
- Prefer simple bounded transforms over opaque model outputs.

Future hardening tasks:

1. Replace proxy components with direct official series where available.
2. Publish per-metric methodology appendix with worked examples.
3. Add regression tests for metric stability across quarterly updates.

## Wave C implementation note

Wave C delivery is now scaffolded with operational components:

- Boundary-led choropleth map mode (with marker overlay toggle) is active for authority geography views.
- Ingest automation now emits richer source-level JSON output and optional quarterly run history.
- Council onboarding pipeline script is available to run ingest->validate->profile->QA gate checks and write authority onboarding artifacts.
- Coverage tracker page publishes complete/partial/estimated status with failed-gate visibility for each authority.
- Mobile table detail drawer is active on benchmark, reports, and contradictions for small screens.

Remaining scale-out dependency:

1. Add authoritative boundary geometry and ingestion for >50 LPAs before national rollout.
