# Phase 3 Implementation Plan (Post-v2.0)

## Objective

Phase 3 focuses on turning the analysis site into a decision-support tool for operational use by policy teams, LPAs, and external reviewers.

## Prioritized Changes

1. **LPA Comparison View**
   - Add side-by-side comparison of two LPAs.
   - Include major decision speed, growth context, constraints, issue density, and data quality tier.
   - Output page: `compare.html`.

2. **Data Quality Tiering**
   - Add explicit data quality classification per LPA (`A`, `B`, `C`) with rationale.
   - Surface this in comparison/map outputs to avoid overconfidence in weak evidence regions.

3. **Build Integrity Guardrails**
   - Ensure CI fails if generated files in `site/` are out of sync with source data.
   - Add `git diff --exit-code` checks after `build_site.py` in CI and Pages workflows.

4. **Workflow Governance Hardening**
   - Add `CODEOWNERS` for `.github/workflows/` so workflow changes are explicitly review-gated.

## Success Criteria

- A user can compare any two LPAs in one view.
- Every LPA has a visible data quality tier.
- CI prevents stale generated artifacts from being merged/deployed.
- Workflow files require designated reviewer approval.
