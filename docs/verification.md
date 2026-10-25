# Implementation verification — 2026-10-25

## Passed

- Django system check; migrations contain no ungenerated schema changes.
- 30 tests against an isolated PostgreSQL 14 database, including independent concurrent purchases, duplicate request UUIDs, concurrent redemption and cross-card idempotency collisions with rollback.
- Purchase thresholds/carry-over, multiple gifts, redemption without stamps, reasoned reversal, spent-gift reversal ordering, branch scope, disabled employees, manager-only writes, CSRF/login throttling and immutable ledger records.
- Card recovery with the same token from independent API clients. Card history is paginated and takes two SQL queries independent of page size.
- Next.js production build, TypeScript check, dependency consistency and Docker Compose configuration validation.
- Docker images built successfully for the Next.js frontend and Django API/migration service. The frontend builder preserves both root and workspace-local npm dependencies, including the QR scanner.
- Docker Compose startup: PostgreSQL 17.11 healthy, migrations completed, Gunicorn API healthy and frontend serving on localhost:3000. Frontend `/api/health/` returned HTTP 200 with `{"status":"ok"}` through the runtime proxy.
- All 30 backend tests passed again inside the API container against PostgreSQL 17.11, including concurrency and immutable-ledger checks. Tests used a separate automatically created/dropped database.
- Generated OpenAPI contract validation.
- Actual frontend standalone server + Gunicorn (two workers/two threads) + PostgreSQL integration. Both readiness endpoints return HTTP 200.
- Browser workflow: create an anonymous empty card; copy its private link; staff session login; create cashier; look up the card; add seven cups; redeem; reverse redemption with a reason; see the restored reward/history on the customer page.
- Browser role check: cashier login works and the manager page denies access. Logout/account switches remount the dashboard so previous employee state is cleared. Native confirmation dialog constrains focus.

## Not yet verified

- Physical-phone camera scanning: the camera integration is implemented, but device permissions/actual camera hardware were not exercised. Manual link entry was tested.
- Public HTTPS deployment, production secure-cookie flow, backups/restore and sustained load. These belong to the deployment verification checklist.

## Separation from the presentation

The previously published chatgpt.site design is unchanged. The real application is in apps/web and apps/api and has not been deployed to cloud hosting. QA accounts/data live only in the isolated local PostgreSQL instance; credentials are in ignored .local/qa-credentials.json, never in source or documentation.
