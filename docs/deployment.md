# Deployment: separate web, API and database

The web and API are independently deployable services in one repository. The public entry point is the Next.js service; `/api/*` forwards to Django over private networking. PostgreSQL must not have a public internet endpoint for normal operation.

## Railway (or equivalent Docker hosting)

Create three services: **web**, **api**, **PostgreSQL**. Use repository root as the build context for both apps, selecting `apps/web/Dockerfile` and `apps/api/Dockerfile` respectively. Both images and the full local Compose startup have been verified, with 30 backend tests passing inside Docker against PostgreSQL 17.11. Public HTTPS and production configuration still require deployment verification.

For Railway, set the API service's custom config path to `/apps/api/railway.json` and the web service's to `/apps/web/railway.json`. Keep both root directories at the repository root. The configs select the Dockerfiles, scope watched files and enable readiness checks. The API config also runs migrations before each release. `.railwayignore` excludes local secrets, credentials, caches and the previous presentation from CLI uploads.

Deploy PostgreSQL first, then the API, then the web service. Wire API `DATABASE_URL` to `${{Postgres.DATABASE_URL}}` (matching the actual database service name) and web `API_INTERNAL_URL` to `http://${{api.RAILWAY_PRIVATE_DOMAIN}}:8000`. Set API `PORT=8000` and web `PORT=3000`. Generate only a web public domain. Include the API private hostname and Railway's `healthcheck.railway.app` hostname in `DJANGO_ALLOWED_HOSTS`, and the final HTTPS web origin in `CSRF_TRUSTED_ORIGINS`. Generate a new production Django secret; never reuse the local `.env`.

API environment:

```text
DATABASE_URL=<reference to the PostgreSQL service's private connection URL>
DJANGO_SECRET_KEY=<at least 50 cryptographically random characters>
DJANGO_DEBUG=0
DJANGO_ALLOWED_HOSTS=<api private hostname>,<public web hostname>
CSRF_TRUSTED_ORIGINS=https://<public web hostname>
WEB_CONCURRENCY=2
```

Use different secrets from local development. Do not put them in Docker build args, frontend `NEXT_PUBLIC_*` variables, source control or screenshots. Keep the API endpoint private. If the database provider requires TLS set `DB_SSLMODE=require` (or `verify-full` with an appropriate CA).

Web environment:

```text
API_INTERNAL_URL=http://<api private hostname>:8000
PORT=3000
```

Set the API service's `PORT=8000` when using this internal URL, or match the port assigned by your host. `API_INTERNAL_URL` is runtime configuration; the same frontend image can be promoted between environments.

API pre-deploy command (once per release, not on every worker start):

```sh
python manage.py migrate --noinput
```

Readiness path on each app: `/api/health/`. It returns 200 only when Django can query PostgreSQL. The frontend forwards this to the API, so allow startup time for both services.

Bootstrap the first owner from a trusted API console:

```sh
python manage.py bootstrap_manager --username owner
```

The command asks for a password and refuses to run if a manager already exists. If a noninteractive job is required, supply `BOOTSTRAP_PASSWORD` only as a one-time secret for that job and remove it afterward. Log in via `/manager`, add a branch/cashier, then test the workflow with a new customer card.

Daily maintenance: run `python manage.py clearsessions` and `python manage.py cleanup_login_failures`. Enable database backups, keep an offsite copy and test restoring it. A persistent volume alone is not a backup.

## Before sending the café its URL

1. Set production environment and HTTPS; check secure session cookies and login.
2. Create the manager, branch and cashier with unique passwords.
3. Open a new client card, copy its private link, and open that link on a second device. Confirm the same card/balance.
4. Scan/paste its QR link as cashier, add seven paid cups, redeem one reward, and confirm the cashier cannot redeem it twice.
5. As manager, reverse the redemption with a reason. The original record remains and the gift becomes available again.
6. Verify a cashier cannot access manager endpoints. Test DB restore and review error logs.

There is no automatic email/SMS delivery, account/password recovery or card-token recovery yet. If a staff member loses a password, an authorized operator resets it from a protected API console with Django's `changepassword <username>`. Add a self-service recovery flow before a broader rollout if needed.

## Concurrency and growth

Every purchase/redemption/reversal acquires a row lock on its card in an atomic transaction. Different cards can proceed concurrently. Request keys are globally unique; reusing a key for another actor/payload is rejected. Workers do not store authoritative balances in memory, so API replicas can share one PostgreSQL database.

Start with bounded DB connections and measure p95 request time, lock wait and error rate before increasing worker/replica counts. Configure edge rate limits for anonymous card creation before a broad public campaign. Application login throttling is database-backed; behind the Next proxy the IP limit is shared unless a trusted ingress-IP arrangement is explicitly configured. Username limits remain per-account. Do not blindly trust arbitrary `X-Forwarded-For` values.

## Legacy presentation

`magribi-concepts/` remains a standalone static prototype hosted on Sites. It is not automatically synchronized with this application's database. The new real app must be deployed using the services above. No production customer records were imported from the old browser-local demo.
