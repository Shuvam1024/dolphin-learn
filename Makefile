.PHONY: web-lint web-type web-test api-lint api-type api-test smoke a11y perf check content

WEB := npm --prefix apps/web
API := services/api

web-lint:
	$(WEB) run lint

web-type:
	cd apps/web && npx tsc --noEmit

web-test:
	$(WEB) test

api-lint:
	cd $(API) && .venv/bin/ruff check app tests

api-type:
	cd $(API) && .venv/bin/mypy app

api-test:
	cd $(API) && .venv/bin/pytest

smoke:
	cd apps/web && npx playwright test

a11y:
	cd apps/web && npx playwright test e2e/a11y.spec.ts --reporter=line

perf:
	cd $(API) && DOLPHIN_PERF=1 .venv/bin/pytest tests/perf -s
	cd apps/web && npx playwright test -c playwright.perf.config.ts --reporter=line

check: api-lint api-type api-test web-lint web-type web-test smoke a11y
	@echo "check complete (run make perf separately for latency budgets)"

content:
	cd $(API) && .venv/bin/python -m app.content.validate
