# UK Planning System Analysis and Reform - Implementation Plan (England Pilot Release)

## 1) Purpose and Outcome

This project will produce a citation-backed analysis of England's planning system and publish it as a website. The objective is to identify contradictions, delays, and unnecessary restrictions across legislation and plan layers, then propose actionable reforms and baseline standards for developers.

Primary outputs:
- A structured, source-linked inventory of planning legislation and policy.
- A mapped hierarchy of national to neighbourhood planning instruments for selected pilot authorities.
- A contradiction and bottleneck analysis with measurable impacts.
- A reform package with model drafting text and implementation pathways.
- A static website (localhost first, deployable to GitHub Pages).

## 2) Confirmed Scope and Decisions

Confirmed through clarification:
- Geography: England first.
- Depth: Acts and key regulations (plus policy instruments).
- Include policy corpus: Yes (`NPPF`, `PPG`, `NPS`, local SPDs, etc.).
- Plan levels in Pilot Release: national, regional/sub-regional, county, district/unitary, neighbourhood, sector overlays.
- Recommendation style: actionable reforms with model text.
- Audience: policy professionals.
- Evidence standard: citation-backed with metrics.
- Website architecture: static site.
- Hosting target: GitHub Pages.
- Delivery target: 6-8 week Pilot Release.
- Authority coverage approach: pilot LPAs plus scalable pipeline.

## 3) Seed Legislative and Policy Inventory (England)

This is the initial seed list for structured research and validation.

### Core planning legislation
- `Town and Country Planning Act 1990`
- `Planning and Compulsory Purchase Act 2004`
- `Planning Act 2008`
- `Localism Act 2011`
- `Neighbourhood Planning Act 2017`
- `Housing and Planning Act 2016`
- `Levelling-up and Regeneration Act 2023`

### Key regulations and statutory instruments
- `Town and Country Planning (Development Management Procedure) (England) Order 2015` (DMPO)
- `Town and Country Planning (General Permitted Development) (England) Order 2015` (GPDO)
- `Town and Country Planning (Use Classes) Order 1987` (as amended)
- `Community Infrastructure Levy Regulations 2010`
- `Town and Country Planning (Environmental Impact Assessment) Regulations 2017`

### Linked statutory controls and constraints
- `Planning (Listed Buildings and Conservation Areas) Act 1990`
- `Planning (Hazardous Substances) Act 1990`
- `Conservation of Habitats and Species Regulations 2017`
- `Environment Act 2021`

### National policy layer
- National Planning Policy Framework (`NPPF`)
- Planning Practice Guidance (`PPG`)
- Relevant National Policy Statements (`NPS`)
- Material ministerial statements and updates

### Local policy and statutory plan layer
- Local plans (core strategy/development plan documents)
- Site allocation documents
- Minerals and waste plans
- Neighbourhood plans
- Supplementary Planning Documents (`SPD`)

## 4) Method: How We Build the Plan for Best Outcomes

To maximize quality and avoid rework, the project will follow a strict sequence:

1. Establish taxonomy and legal-weight model first.
   - Separate: statute, regulation, national policy, development plan, guidance.
   - Record legal status and decision weight to avoid false equivalence.

2. Define source-of-truth data schema before ingestion.
   - Required fields: `id`, `title`, `type`, `jurisdiction`, `authority`, `status`, `adoption_date`, `in_force`, `decision_weight`, `source_url`, `citation`, `supersedes`, `conflicts_with`, `notes`.

3. Use dual-track evidence for each issue.
   - Legal/policy text evidence.
   - Operational evidence (timelines, refusal reasons, appeal outcomes, rework patterns).

4. Apply repeatable contradiction-scoring criteria.
   - Severity, frequency, legal risk, time-delay impact, and fixability.

5. Draft reforms only after contradiction mapping.
   - Test each proposed reform against representative pathways: housing, commercial, infrastructure.

## 5) Delivery Phases (6-8 Week Pilot Release)

## Phase 0 (Days 1-3): Project Foundations
- Set repo structure for data, content, methods, and site.
- Finalize citation style and source reliability protocol.
- Define pilot LPA selection criteria and shortlist.
- Create data dictionary and issue taxonomy.

Deliverables:
- Project charter.
- Data schema and dictionary.
- Research and citation protocol.

## Phase 1 (Week 1-2): Research Corpus Build
- Build legislation/regulation register for England.
- Build national policy register (`NPPF`, `PPG`, relevant `NPS`).
- Gather local plan documents for pilot LPAs at all required levels.

Deliverables:
- Machine-readable legal/policy inventory with provenance.
- Source links and update timestamps.

## Phase 2 (Week 2-3): Multi-Level Plan Mapping
- Map governance hierarchy and precedence rules.
- Build per-authority policy stack (national to neighbourhood, including overlays).
- Document points where interpretation or precedence is ambiguous.

Deliverables:
- Policy-stack maps for pilot LPAs.
- Dependency and precedence notes.

## Phase 3 (Week 3-4): Contradictions and Friction Analysis
- Identify cross-layer conflicts, duplications, and gaps.
- Map bottlenecks along process stages (pre-app, validation, consultation, committee, legal agreements, condition discharge).
- Quantify impacts with comparable indicators.

Deliverables:
- Contradiction register.
- Bottleneck heatmap.
- Initial metric baseline.

## Phase 4 (Week 4-5): Reform Package Design
- Draft targeted reforms to:
  - eliminate contradictions,
  - speed approvals,
  - remove unnecessary restrictions,
  - improve inter-authority and central-local coordination,
  - set baseline standards for local fit and design certainty.
- Include model drafting text and implementation owner per proposal.

Deliverables:
- Reform package with implementation mechanics.
- Model text and transition notes.

## Phase 5 (Week 5-6): Website Pilot Release (Localhost)
- Build static site with core sections:
  - Legislation Library
  - Plan Hierarchy Explorer
  - Contradictions Dashboard
  - Recommendations and Model Text
  - Methodology and Citations
- Add filters by authority, issue category, and document type.

Deliverables:
- Localhost static website Pilot Release.
- Structured content pipeline from markdown/data to pages.

## Phase 6 (Week 6-7): Validation and QA
- Citation integrity review.
- Legal/policy consistency check.
- Scenario testing of recommendations against representative development cases.

Deliverables:
- QA report.
- Revised final recommendations.

## Phase 7 (Week 7-8): Publish Readiness
- Configure GitHub Pages workflow.
- Prepare release notes and roadmap for scaling beyond pilot LPAs.
- Final professional editorial pass.

Deliverables:
- Deployable release candidate.
- Scale-out backlog for all LPAs.

## 6) Recommendation Template and KPI Framework

Each recommendation should follow:
- Problem statement.
- Evidence and citations.
- Proposed change.
- Legal/policy implementation vehicle.
- Owner and delivery timeline.
- KPI and expected impact range.

Core KPI set:
- Median decision time by application category.
- Validation failure/rework rate.
- Appeal overturn rate.
- Time from resolution to completed legal agreement.
- Time to discharge pre-commencement conditions.
- First-submission compliance with baseline local-fit standards.

## 7) Pilot LPA Selection Framework

Select pilot LPAs to maximize representativeness:
- Governance diversity (borough/unitary/district).
- Market pressure variation (high growth and moderate growth).
- Constraint variation (green belt, flood, heritage, infrastructure limitations).
- Data/document accessibility and update quality.
- Mix of urban and non-urban contexts.

## 8) Initial Website Information Architecture

Planned page structure:
- `index.md` - project overview and key findings.
- `legislation/` - legislation and regulations library.
- `plans/` - plan hierarchy and authority-specific stacks.
- `analysis/contradictions.md` - contradiction register and findings.
- `analysis/bottlenecks.md` - process-delay analysis.
- `recommendations/` - reform proposals and model text.
- `methodology/` - methods, scoring, quality controls, limitations.
- `sources/` - full citation index.

## 9) Risks and Mitigations

Key risks:
- Policy churn and rolling updates can quickly age findings.
- Inconsistent local document formats reduce automation reliability.
- Legal ambiguity between policy guidance and statutory weight.

Mitigations:
- Timestamp all sources and include version metadata.
- Build ingest pipeline with manual QA checkpoints.
- Explicitly model legal weight and precedence in all analyses.

## 10) Immediate Next Build Steps

1. Set up static site scaffold and folder structure for content and data.
2. Create templates for legal entries, plan entries, contradiction records, and recommendation pages.
3. Select and lock pilot LPA set.
4. Start research ingestion for core legislation and national policy.
5. Stand up localhost preview and deploy stub to GitHub Pages branch/workflow.

## 11) Open Decisions (To Finalize Early)

- Confirm pilot LPAs (final list and rationale).
- Confirm whether Pilot Release infrastructure scope includes NSIP pathways under `Planning Act 2008` in full or summary mode.
- Confirm whether recommendations should be split into:
  - rapid 12-month administrative changes, and
  - medium/longer-term statutory reform.
