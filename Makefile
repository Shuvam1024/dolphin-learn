.PHONY: web-lint web-type web-test api-lint api-type api-test smoke a11y perf check content ai-eval release-suite release-api

WEB := npm --prefix apps/web
API := services/api
API_PYTHON := $(API)/.venv/bin/python

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

ai-eval:
	cd $(API) && AI_EVAL_RECORD=1 .venv/bin/python -m tests.ai_eval.run

smoke:
	cd apps/web && npx playwright test

a11y:
	cd apps/web && npx playwright test e2e/a11y.spec.ts --reporter=line

perf:
	cd $(API) && DOLPHIN_PERF=1 .venv/bin/pytest tests/perf -s
	cd apps/web && npx playwright test -c playwright.perf.config.ts --reporter=line

release-api:
	@pid=$$(ss -tlnp 2>/dev/null | rg ':8000' | rg -o 'pid=[0-9]+' | head -1 | cut -d= -f2); \
	  if [ -n "$$pid" ]; then kill $$pid 2>/dev/null || true; sleep 0.4; fi
	cd $(API) && AI_PROVIDER="$(AI_PROVIDER)" AI_GATEWAY_ENABLED="$(AI_GATEWAY_ENABLED)" DOLPHIN_E2E_FAST_CLOCK=1 \
	  .venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 &
	@for i in 1 2 3 4 5 6 7 8 9 10; do curl -sf http://127.0.0.1:8000/health >/dev/null && exit 0; sleep 0.5; done; exit 1

release-suite:
	$(MAKE) release-api AI_PROVIDER= AI_GATEWAY_ENABLED=
	cd apps/web && AI_PROVIDER= npx playwright test -c playwright.release.config.ts --reporter=line
	$(MAKE) release-api AI_PROVIDER=fake AI_GATEWAY_ENABLED=true
	cd apps/web && AI_PROVIDER=fake AI_GATEWAY_ENABLED=true npx playwright test -c playwright.release.config.ts --reporter=line

check: api-lint api-type api-test web-lint web-type web-test smoke a11y
	@echo "check complete (run make perf separately for latency budgets)"

content:
	cd $(API) && .venv/bin/python -m app.content.validate
