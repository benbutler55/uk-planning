# UI Blueprint (Phase 7)

## Objective

Provide reusable layout and copy components so every page follows the same summary-to-detail pattern.

## Navigation model

- Top-level sections: Overview, System Analysis, Authority Insights, Recommendations, Data & Methods, For Audiences
- Section sub-navigation visible on every page
- Breadcrumbs on non-home pages
- Header utility link to search

## Reusable page components

These components are implemented in `scripts/build_site.py`:

- `render_page_purpose(purpose)`
  - Renders four fields:
    - What this page shows
    - Who this is for
    - How to use it
    - Data source and freshness

- `render_table_guide(title, bullets)`
  - Renders plain-language "How to read this table" explainers
  - Used before major analytical tables

- `render_next_steps(steps)`
  - Renders consistent navigation actions at end of page
  - Encourages drill-down flow

- `default_breadcrumbs(active)`
  - Builds breadcrumb trails from section configuration

- `default_purpose(active)`
  - Provides page-specific default guide copy for core pages

## Page shell contract

`page(title, subhead, active, body, context=None, purpose=None, breadcrumbs=None, next_steps=None)`

- `active`: page key used for section and sub-navigation highlighting
- `purpose`: optional override for page guide copy
- `breadcrumbs`: optional override for custom trails (for example LPA profile pages)
- `next_steps`: list of `(href, label)` tuples for directional links

## Table guidance policy

- Add table guide blocks to all major data tables
- Explain:
  - row meaning
  - key metrics and derived columns
  - caveats (official vs estimated)
  - filtering/sorting intent

## Accessibility and readability

- Keyboard-visible focus states
- Search input labels remain present for screen readers
- Sticky table headers on large tables
- Mobile-first fallback for layout blocks and header utility links

## Future extension

- Add task-specific section landing pages if content grows
- Add row-level expandable detail for complex tables
- Add glossary chips for specialist terms (s106, NSIP, tilted balance)
