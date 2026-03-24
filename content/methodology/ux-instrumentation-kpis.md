# UX Instrumentation KPI Spec

## Purpose

Define lightweight interaction events and reporting KPIs used to evaluate whether the site is becoming easier to navigate and interpret.

## Event schema

Client-side events are stored in local browser storage key `uk-planning-ux-events-v1`.

- `page_view`
  - `page`: current path
  - `mode`: guided or expert
  - `plain_language`: on/off
- `link_click`
  - `page`: current path
  - `href`: clicked destination

## Core KPI definitions

- `time_to_first_insight_seconds` (target: 45)
  - proxy: time from `page_view` to first click to detail/evidence pages
- `detail_page_click_through_rate` (target: 0.35)
  - proxy: detail-page clicks / all page views
- `filter_use_success_rate` (target: 0.80)
  - proxy: filtered sessions with at least one downstream click

## Reporting artifacts

Build process generates:

- `site/reports/ux-kpi-report.json`
- `site/reports/ux-kpi-report.csv`

These provide monthly KPI structure, targets, and build-time structural coverage counts.

## Notes

- Current implementation is privacy-preserving and local-first.
- If centralized analytics is added later, retain this schema to keep KPI continuity.
