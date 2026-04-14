.PHONY: build validate test lint check serve clean assets links accessibility help

build: ## Build site from CSV data
	python3 scripts/build_site.py

validate: ## Run data validation
	python3 scripts/validate_data.py

test: ## Run pytest suite
	pytest scripts/tests/ -v

lint: ## Run ruff lint check
	ruff check scripts/

links: ## Check internal links
	python3 scripts/check_links.py

accessibility: ## Check accessibility basics
	python3 scripts/check_accessibility.py

check: validate build lint test links accessibility ## Run all checks
	@echo "All checks passed."

serve: build ## Start local dev server
	python3 -m http.server 4173 --directory site

clean: ## Remove generated artifacts
	rm -rf site/assets/dist
	rm -f metric-stability-report.json metric-stability-report.txt
	find . -type d -name __pycache__ -not -path './.venv/*' -exec rm -rf {} + 2>/dev/null || true

assets: ## Build minified assets
	bash scripts/build_assets.sh

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'
