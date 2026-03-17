# Scale-Out Backlog: Beyond Pilot LPAs

This document defines the work required to expand analysis from the 6 pilot LPAs to all local planning authorities in England (approximately 317 LPAs).

---

## Cohort 2 — Next 20 LPAs

Selection criteria for the next cohort:
- Geographic spread (at least one LPA per region not already covered)
- Mix of National Park authorities and AONB-adjacent LPAs
- At least two authorities currently designated as Intervention/Notice LPAs under Planning Performance Framework
- At least two combined authority areas with strategic plan functions

Recommended additions:
- Leeds City Council (metropolitan, high growth, emerging regional spatial strategy)
- Bristol City Council (unitary, net zero ambitions, strong design policy)
- Guildford Borough Council (green belt constrained, high housing pressure)
- Newcastle City Council (regeneration focus, devolution context)
- Peak District National Park Authority (designated landscape, tourism development tension)
- Northumberland County Council (large rural unitary, minerals context)
- Southampton City Council (coastal, waterfront regeneration)
- Leicester City Council (urban renewal, heritage overlay)
- Cambridge City Council (Greater Cambridge shared plan, growth corridor)
- Medway Council (Thames Estuary, housing delivery zone)

---

## Data Automation Pipeline

Manual CSV ingestion is not scalable to 317 LPAs. The following automation work is required:

1. **Planning portal API integration** — extract application volumes, validation rates, and decision speed from Planning Portal data feeds where available.
2. **Local plan status scraper** — automate collection of local plan adoption dates, examination status, and last review date from Planning Inspectorate and LPA websites.
3. **PINS casework API** — integrate PINS casework database for appeal outcome data per LPA.
4. **GOV.UK statistics pipeline** — automated ingest of PS1/PS2/P151/P152/P153/P154 tables on each quarterly update.
5. **Freshness automation** — extend `scripts/check_freshness.py` to check local plan document URLs per new LPA cohort.

---

## QA Scaling Requirements

As LPA count grows:
- Introduce **confidence scoring automation** based on data source type (official statistic > proxy > estimate).
- Introduce **LPA data quality tier** (A = complete official data / B = partial / C = estimated) to flag reliability of per-LPA analysis.
- Peer review protocol for each new cohort before publication.

---

## Site Architecture Changes Needed

- Add LPA search and filter on `plans.html` (currently shows only 6 pilot rows).
- Add LPA profile pages for all new authorities (`plans-lpa-XX.html`).
- Add a **national map view** (SVG or Leaflet.js) showing LPA coverage, decision speed, and issue density.
- Add **comparison view** allowing two LPAs to be shown side by side.
- Add **RSS/email subscription** for policy changes and new recommendations.

---

## Governance for Scale-Out

- Monthly data refresh cycle (aligned with GOV.UK quarterly statistics releases).
- Quarterly editorial review of contradiction register and recommendations.
- Annual full policy review against current NPPF/PPG versions.
- Dedicated legal review channel for any records advancing to `legal-reviewed` status.
