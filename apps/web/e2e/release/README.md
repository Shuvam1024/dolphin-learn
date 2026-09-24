# Golden release suite (S103)

Curated first-ship Playwright specs. Run twice — AI off and FakeProvider.

```bash
# from repo root (restarts API with the matching AI_* env between modes)
make release-suite
```

Or manually:

```bash
# AI off
cd services/api && AI_PROVIDER= DOLPHIN_E2E_FAST_CLOCK=1 .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
cd apps/web && AI_PROVIDER= npx playwright test -c playwright.release.config.ts --reporter=line

# Fake provider (restart API with AI_PROVIDER=fake AI_GATEWAY_ENABLED=true)
cd apps/web && AI_PROVIDER=fake AI_GATEWAY_ENABLED=true npx playwright test -c playwright.release.config.ts --reporter=line
```

Catalog: `e2e/release/catalog.spec.ts`. Flake list: empty at first ship.

CI job `release-suite` runs both modes on `main` / PRs.
