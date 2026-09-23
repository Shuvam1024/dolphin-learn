.PHONY: web-lint web-type web-test api-lint api-type api-test

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
