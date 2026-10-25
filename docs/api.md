# Magribi REST API v1

Manager-only generated OpenAPI is available at `/api/schema/` and its viewer at `/api/docs/`. Native Django CSRF/login/readiness endpoints are described below.

All paths below start with `/api`. JSON responses use `Cache-Control: no-store`. Dates are UTC ISO-8601; the UI displays Asia/Almaty.

## Authentication

Guest cards use `Authorization: Bearer <43-character card token>`. A card token grants read-only card/history access. Write operations require an authenticated staff session.

Staff: first GET `/auth/csrf/` to get `{csrfToken}` and the CSRF cookie, then POST `/auth/login/` with `{username,password}` and `X-CSRFToken`. Django sets an HttpOnly session cookie. Fetch a fresh CSRF token after login and include it in POST/PATCH requests. `/auth/me/` returns the current employee. POST `/auth/logout/` invalidates the session. There is no sign-up endpoint.

The web proxy forwards cookies, bearer header and CSRF header to the private Django service; staff credentials never live in localStorage.

## Endpoints

| Method | Path | Permission | Input / output |
|---|---|---|---|
| GET | `/health/` | Any | database readiness |
| GET | `/auth/csrf/` | Any | CSRF token + cookie |
| POST | `/auth/login/` | Any + CSRF | username/password → staff |
| GET | `/auth/me/` | Staff | current staff |
| POST | `/auth/logout/` | Staff + CSRF | logout |
| POST | `/cards/` | Any | `{token}` → new empty card or existing same-token card |
| GET | `/cards/current/` | Card bearer | card balance |
| GET | `/cards/history/?page=1` | Card bearer | own history without employee identity/reversal reason |
| POST | `/staff/lookup/` | Staff | `{token}` → card |
| POST | `/staff/purchase/` | Staff | `{card_id,quantity,request_key}` |
| POST | `/staff/redeem/` | Staff | `{card_id,quantity:1,request_key}` |
| GET | `/staff/operations/?page=1` | Staff | cashier's branch or all branches for manager |
| GET | `/manager/summary/` | Manager | cards, net paid cups, net redeemed gifts, operations, active cashiers |
| GET/POST | `/manager/staff/` | Manager | list / create employee |
| PATCH | `/manager/staff/{id}/` | Manager | `{is_active}`; cannot disable self/last manager |
| GET/POST | `/manager/branches/` | Manager | list / create `{name,address}` |
| POST | `/manager/operations/{id}/reverse/` | Manager | `{reason,request_key}`; full reversal |

Staff input: `{username,name,password,role,branch_id}`. Username is case-insensitive, password must pass Django validation and be at least 10 characters. No password is returned. Branch must be active. A cashier can transact a customer card at their assigned branch; each operation records that branch.

## Response shapes

Card: `{id,stamps,rewards,paid_units,redeemed_units}`. `stamps = paid_units % 7`, `rewards = floor(paid_units / 7) - redeemed_units`.

Mutation: `{ok:true,operation,card}` (reversal returns the new operation; refresh the card separately).

History: `{items: Operation[],page,has_more}`, 25 records per page. Operation fields: `id,kind,quantity,paid_delta,redeemed_delta,branch,created_at,reverses,reversed`. Staff responses additionally contain `card_id,actor,reason`.

Failures: `{detail: string}` or field validation errors. 400 invalid input, 401 missing guest token, 403 staff permission/CSRF failure, 404 unknown card/record, 409 business conflict or idempotency mismatch, 429 login throttled.

## Rules

- Seven paid cups unlock one gift; multiple gifts accumulate, leftovers carry over.
- A redemption consumes one gift and awards no new paid stamps.
- `request_key` must be a UUID generated once when the employee opens confirmation. Reuse it for network retries. The server rejects reuse with a different payload, card or actor.
- Reversals require a 5–500 character reason and only restore/remove the original operation's exact deltas. An operation may be reversed once. A reversal itself cannot be reversed.
- If reducing paid cups would invalidate an already redeemed gift, first reverse the relevant redemption. Negative available rewards are never allowed.
- Database triggers reject updates/deletion of ledger records. Corrections are appended as new reversal operations.
