# Magribi

Separate **Next.js/TypeScript frontend** and **Django/DRF backend**, backed by PostgreSQL. The approved brick/cream/gold design is retained. The existing `magribi-concepts/` is an untouched, separately hosted static design demo; it is not the new backend.

## Implemented

- Anonymous customer cards, cryptographically random private links, dynamic scannable QR codes, cross-device access using the same link, saved server-side history.
- Staff login using Django sessions, CSRF protection, manager/cashier roles, branch-scoped cashier history, employee creation/deactivation.
- Purchases (1–100 paid cups), seven-paid-cups reward threshold, carry-over and multiple rewards, one-at-a-time redemption.
- Atomic card updates using PostgreSQL row locks and persisted request UUIDs for idempotency. No client-side balance authority.
- Manager dashboard, branch creation, aggregate counters, paginated operations and reasoned full reversals. Neither cashiers nor managers can delete or edit the original ledger entry; PostgreSQL triggers reject UPDATE/DELETE.
- Real camera QR scanning (HTTPS/localhost and camera permission required), with manual card-link entry fallback.
- No customer registration, SMS, payment collection or automatic WhatsApp sending.

## Layout

- `apps/web`: frontend only, including a narrow same-origin API proxy. All authorization and business rules live in Django.
- `apps/api/config`: environment and Django routing.
- `apps/api/core/models.py`: staff, branch, card, immutable operation ledger.
- `apps/api/core/services.py`: transactional loyalty rules.
- `apps/api/core/api/`: REST adapters split into auth, cards, staff and management modules.
- `apps/api/tests`: PostgreSQL business, API/security and concurrency tests.
- `docs/api.md` and `docs/openapi.yaml`: API contracts. `docs/deployment.md`: separate-service deployment.

The operational core is a modular monolith. Inventory, shifts and orders are future modules, not fabricated screens or database tables.

## Run everything with Docker

Requires Docker Engine/Compose running.

```sh
python3 scripts/setup-local.py
docker compose up --build -d
docker compose exec api python manage.py bootstrap_manager --username owner
```

Choose a strong password in the interactive prompt. There is no shared/default manager password and no public staff sign-up.

Open `http://localhost:3000`, `/cashier` and `/manager`. The `migrate` service applies migrations once before API startup. PostgreSQL is persisted in `postgres_data`; do not remove the volume to update the app. These defaults are for local development (`DJANGO_DEBUG=1`); use the production settings in `docs/deployment.md` for an internet deployment.

If a local port is occupied, set `POSTGRES_PORT` or `WEB_PORT` in `.env`. Match `DATABASE_URL` to the database's host port when running Python outside Docker; container-to-container database connections always use port 5432. If changing the web port, also update `CSRF_TRUSTED_ORIGINS`.

## Local development without frontend/backend containers

```sh
python3 scripts/setup-local.py
python3 -m venv .venv
.venv/bin/pip install -r apps/api/requirements.lock
npm ci
docker compose up -d db
```

Load `.env` in the backend shell:

```sh
set -a
source .env
set +a
.venv/bin/python apps/api/manage.py migrate
.venv/bin/python apps/api/manage.py bootstrap_manager --username owner
bash scripts/dev-api.sh
```

In a second terminal run `npm run dev`. The frontend defaults to the API at `http://127.0.0.1:8000`. `API_INTERNAL_URL` is read server-side at runtime and never shipped to the browser. No CORS configuration is needed with the same-origin proxy.

## Checks

With the environment loaded and PostgreSQL running:

```sh
.venv/bin/python apps/api/manage.py check
.venv/bin/python apps/api/manage.py makemigrations --check --dry-run
.venv/bin/python apps/api/manage.py test tests --noinput
npm run typecheck
npm run build
```

The database user needs permission to create the separate test database. Concurrency tests require PostgreSQL; SQLite cannot validate row-lock behavior. A test-only temporary PostgreSQL instance was used during implementation, separate from the presentation website.

## Customer card access

A browser creates a 256-bit random token and stores it locally; Django persists only its SHA-256 hash. `/api/cards/` is idempotent for the same token. The private link carries the token in a URL fragment, so it is not sent in the URL to the web server. The API receives it via the Authorization header. A QR contains this same private link.

The link is the card's key, not proof of a named customer's identity. Anyone with it can view the card and present it for redemption. Cashiers still must sign in to change the balance. Clearing browser storage and losing the saved link means the card cannot be recovered without a later recovery/account feature. No cross-device recovery by phone number is implied.

## Status

This standalone app is prepared for your own deployment. The original `chatgpt.site` presentation remains unchanged. Configure a real production database, HTTPS domain, secret key and first manager before sharing this version with the café. No cloud services have been purchased or created by this implementation.

Verification evidence and remaining deployment/device checks: [docs/verification.md](docs/verification.md).
