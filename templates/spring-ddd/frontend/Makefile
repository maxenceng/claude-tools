# Frontend verbs. Node version is pinned in .nvmrc — run `nvm use` first.

.DEFAULT_GOAL := help
.PHONY: help install dev build typecheck lint test dup openapi-client check ci clean

help: ## Show available targets
	@grep -hE '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies exactly as locked
	npm ci

dev: ## Start the dev server, proxying /api to the backend on :8080
	npm run dev

build: ## Typecheck and produce a production bundle
	npm run build

typecheck: ## Typecheck without emitting
	npm run typecheck

lint: ## Fail on code that breaks the frontend's conventions
	npm run lint

test: ## Run tests
	npm run test

dup: ## Report copy-pasted code
	npm run dup

design-check: ## Fail on the UI anti-patterns impeccable detects without a model
	npm run design-check

openapi-client: ## Regenerate the typed client from docs/openapi.json
	npm run openapi-client

check: typecheck test ## The inner loop: typecheck and tests, no bundle

ci: typecheck lint test dup design-check build ## What CI runs for the frontend, cheapest first

clean: ## Remove build output
	rm -rf dist node_modules/.vite
