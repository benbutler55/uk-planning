# Wave D UX + Data Presentation Backlog

## Goal

Implement a user-guided, evidence-traceable interface that makes complex planning data easier to understand, compare, and act on for policy teams, LPAs, and public users.

## Backlog format

- `R-ID`: unique recommendation identifier
- `Owner`: primary delivery owner (support roles can be added in sprint planning)
- `Effort`: `S` (<=1 week), `M` (1-3 weeks), `L` (3+ weeks)
- `Dependencies`: technical/data prerequisites
- `Acceptance criteria`: testable definition of done

## Ranked implementation backlog

| R-ID | Recommendation | Owner | Effort | Dependencies | Acceptance criteria |
|---|---|---|---|---|---|
| R-D01 | Add task-first entry routes on `index.html` (`Understand national issues`, `Compare authorities`, `Track recommendation delivery`) with direct deep links | Product + frontend | S | Existing IA nav map in `scripts/build_site.py` | Homepage shows all 3 routes above fold; each route lands on correct page/section; links pass `check_links.py` |
| R-D02 | Add universal page intro pattern (`Start here`, `How to interpret`, `Next actions`) to all data-heavy pages | Product + content design | M | Existing `render_table_guide()` and page wrappers | `benchmark`, `contradictions`, `recommendations`, `reports`, `coverage`, detail pages all include the 3-block guidance pattern |
| R-D03 | Add global `Guided` vs `Expert` mode toggle (persisted per user) to adjust guidance density | Frontend | M | Shared state/localStorage pattern already used for filters | Toggle appears globally; mode persists across pages; `Guided` shows helper blocks and `Expert` hides non-essential helper text |
| R-D04 | Implement consistent metric context block (Definition / Why it matters / Source + confidence) for every headline metric | Data product + methodology | M | Existing metric tooltip and provenance helper functions | All benchmark/report headline metrics render the 3-part context block; no metric without source/confidence label |
| R-D05 | Add baseline comparison chips on metric rows/cards (`vs England`, `vs cohort`, `vs peer group`) | Data engineering + frontend | M | Benchmark and peer-group calculations | For in-scope metrics, chips render numeric delta and direction; chips degrade gracefully when comparator unavailable |
| R-D06 | Standardize trust language globally (`Official`, `Estimated`, `Confidence`) and add compact provenance legend in layout shell | Methodology + frontend | S | Existing provenance/confidence badge helpers | Every data page displays the same terms; legend appears in global shell/footer; no legacy wording variants remain |
| R-D07 | Add per-page data trust panel (`last refreshed`, `source tier`, `known caveats`) | Data lead + frontend | M | `compute_data_health()` outputs + metadata availability | Trust panel visible on benchmark/reports/coverage/detail pages; refreshed date and caveat text present and non-empty |
| R-D08 | Add filter presets and explicit active-filter summary chips on major tables | Frontend | M | Existing filter scripts and shared filter state | Presets available on contradictions/recommendations/benchmark; active filters shown as chips; clear-all action works |
| R-D09 | Improve dense-table usability: sticky first column (desktop), explicit mobile row-tap hint, per-column sort state text | Frontend | M | Existing mobile drawer implementation | Desktop sticky first column active on benchmark/reports/contradictions; mobile hint visible; sort state announced in UI |
| R-D10 | Add faceted search for `site/search.html` (type, pathway, authority, confidence, status) and prioritize ID exact matches | Search + frontend | L | Existing `search-index.json` generation and categories | Search supports facet filtering; exact ID query ranks matching detail page first; facets update result counts |
| R-D11 | Add related-content module on detail pages (`users also viewed`, `connected records`) | Product + frontend | M | Connected links already generated on detail pages | Every contradiction/recommendation detail page shows a related-content block with at least 3 contextual links |
| R-D12 | Add shareable state links (`Copy this view`) for filtered list pages and detail-page anchor sections | Frontend | S | URL/hash state + clipboard API fallback | Button copies a valid URL preserving current filters/anchor; opening copied link restores state |
| R-D13 | Accessibility hardening: keyboard order, ARIA labels for controls, skip links (`filters`, `table`, `evidence`) | Accessibility + frontend | M | Existing accessibility script and templates | Keyboard-only navigation completes core tasks; skip links present on data-heavy pages; no critical accessibility script failures |
| R-D14 | Add text alternatives for charts and sparkline summaries in-page and in downloadable tables | Data viz + frontend | M | Sparkline rendering + report exports | Each chart/sparkline has adjacent text summary; equivalent values available in table/export for non-visual interpretation |
| R-D15 | Add plain-language guidance mode for non-specialist/public users (jargon explanations and short interpretations) | Content design + policy analyst | M | Existing audience pages and glossary terms | Plain-language panel visible on relevant pages; top jargon terms explained contextually; user can toggle visibility |
| R-D16 | Establish UX instrumentation KPIs (`time-to-first-insight`, detail-page click-through, filter use success, repeat use) | Product analytics | M | Lightweight event schema and analytics endpoint/log sink | KPI spec documented; events emitted on key interactions; monthly KPI report artifact generated |

## Delivery sequence (recommended)

### Sprint group A: Wayfinding and guidance foundation (R-D01 to R-D04)

Focus on making first-time navigation obvious and interpretation safe.

### Sprint group B: Data interpretation and trust (R-D05 to R-D08)

Focus on context, comparators, provenance consistency, and filter clarity.

### Sprint group C: Discovery and interaction efficiency (R-D09 to R-D12)

Focus on dense-table interaction speed, search quality, and shareable state.

### Sprint group D: Accessibility, inclusion, and measurement (R-D13 to R-D16)

Focus on inclusive use, chart alternatives, plain language, and measurable outcomes.

## Definition of done for Wave D

Wave D is complete when:

1. Every critical data page follows the same guidance and trust structure.
2. Users can navigate from overview to evidence detail with explicit wayfinding cues at each step.
3. Filtered views and detail anchors can be shared and reopened without losing context.
4. Accessibility checks pass with no critical blockers on key journeys.
5. KPI instrumentation is active and reporting on usage quality, not just traffic volume.
