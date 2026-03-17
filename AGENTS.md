# Agent Operating Rules

This file governs the behaviour of any AI agent (including Claude, OpenCode, Copilot, or similar) working in this repository.

## Mandatory rules

1. **README currency** — After any substantive change to project structure, datasets, scripts, or site pages, update `README.md` to reflect the current state of the repository before finishing the task.

2. **Commit hygiene** — All changes must be committed to git before declaring work complete. A dirty working tree is not an acceptable end state unless the user explicitly says otherwise.

3. **Push to remote** — At the end of every work cycle, push committed changes to `origin/main` (or the current tracking branch). Confirm the push succeeded.

4. **No silent drift** — If generated files in `site/` are regenerated, they must be included in the commit. Do not leave generated output out of sync with source data.

5. **Validation before commit** — Run `python3 scripts/validate_data.py`, `python3 scripts/build_site.py`, and `python3 scripts/check_links.py` before committing. Fix any hard errors. Log any warnings.

6. **Schema compliance** — Any new or modified CSV must conform to the schema defined in `data/schemas/datasets.json`. Update the schema first if adding new fields or datasets.

7. **Evidence traceability** — Every recommendation must reference at least one official dataset row in `data/evidence/recommendation_evidence_links.csv`. Do not add recommendations without evidence linkage.

8. **Verification state** — New data records should be added with `verification_state: draft`. Only mark as `verified` or `legal-reviewed` after explicit user confirmation.

## Workflow sequence

```
validate_data.py -> build_site.py -> check_links.py -> git add -> git commit -> git push
```

## Branch policy

- Default branch: `main`
- All work happens on `main` unless the user requests a feature branch.
- Never force-push to `main`.
