# RAZVITON public-information release

This release preserves the existing FastAPI/public HTML design. It is an informational website, not a token sale, financial service or independently verified live dashboard.

## Data policy

- Conflicting allocation drafts are withheld, not replaced with invented percentages.
- Operational and audience claims without dated evidence are withheld or labelled UNVERIFIED.
- Token metadata retains the original declared name, symbol, mint, network and decimals with an explicit UNVERIFIED notice. No on-chain transaction or contract change is performed.
- Team identities, official contacts, whitepaper links, certifications, listings and financial figures are not invented.
- Root HTML mirrors public/; FastAPI serves public/ only.

## Deployment safeguards

- Render start command uses 0.0.0.0 and PORT; /health checks DB access.
- RAZVITON_COOKIE_SECURE=1 on HTTPS production.
- RAZVITON_REGISTRATION_ENABLED=0 in the blueprint; default on Render also fails closed if unset.
- Existing login/logout remain available. No existing user records are deleted or migrated.
- Before reopening registrations, the operator must configure verified durable storage via RAZVITON_DATA_DIR, test backup/restore and supply privacy/contact/retention information. An environment path alone does not provision durable storage.
- No new paid resources are requested or provisioned.
- Existing replicas still need a shared rate limiter before scaling beyond one process.

## Local checks

Install backend/requirements.txt in an isolated environment. For QA also install requests, and Playwright for the browser suite. Point RAZVITON_DATA_DIR to a new temporary directory, RAZVITON_COOKIE_SECURE=0, RAZVITON_REGISTRATION_ENABLED=1; start uvicorn with --app-dir backend on localhost.

Run test_release.py from backend; run test_auth_local.py and audit_browser.cjs with RAZVITON_TEST_BASE pointing at that isolated local server. Run audit_smoke.py --base URL last, because its rate-limit stress test deliberately exhausts a window. Tests must never use real user data. PLAYWRIGHT_MODULE selects the installed Playwright package.

Production availability must be checked with actual HTTP responses after Git push; an HTTP 200 from an older revision is not evidence that this release deployed.
