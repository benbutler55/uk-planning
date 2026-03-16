# UK Planning Analysis

This repository contains the research, analysis, and website assets for an England-first review of the UK planning system.

## Project Structure

- `IMPLEMENTATION_PLAN.md`: phased implementation plan.
- `content/`: markdown source content and templates.
- `data/`: structured research datasets (CSV/JSON).
- `site/`: static website files for localhost and GitHub Pages.
- `scripts/`: helper scripts.

## Run Locally

Build pages from datasets, then serve the static site:

```bash
python3 scripts/build_site.py
python3 -m http.server 4173 --directory site
```

Open the URL printed by the script (it will use `4173` or another free fallback port).

Or use:

```bash
./scripts/serve_local.sh
```

## Quality Checks

Run data and site integrity checks:

```bash
python3 scripts/validate_data.py
python3 scripts/build_site.py
python3 scripts/check_links.py
```

These checks also run in GitHub Actions (`.github/workflows/ci.yml`) and before GitHub Pages deployment (`.github/workflows/pages.yml`).
