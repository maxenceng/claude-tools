# Frontend verbs. Node version is pinned in .nvmrc — run `nvm use` first.

.DEFAULT_GOAL := check
.PHONY: install dev build typecheck test dup openapi-client check clean

install: ## Install dependencies exactly as locked
	npm ci

dev: ## Start the dev server, proxying /api to the backend on :8080
	npm run dev

build: ## Typecheck and produce a production bundle
	npm run build

typecheck: ## Typecheck without emitting
	npm run typecheck

test: ## Run tests
	npm run test

dup: ## Report copy-pasted code
	npm run dup

openapi-client: ## Regenerate the typed client from docs/openapi.json
	npm run openapi-client

check: typecheck test ## What CI runs for the frontend

clean:
	rm -rf dist node_modules/.vite
