# Roby Data Portal — Architecture
 
> **Status**: Living document. First pass covers naming, structure, app responsibilities, known integration bugs, and request flow. Iterate from here.
 
---
 
## 1. The Naming Map (Read This First)
 
This codebase has one significant source of confusion: SmolKraft was originally a standalone Django project that was dropped into this repo as a subdirectory. That graft left behind a tangle of names that don't agree with each other. This section is the authoritative map.
 
### Name → Meaning
 
| Name | What it actually refers to |
|---|---|
| `roby_data_portal` | **Two things at once:** (1) the git repo root directory, and (2) the Django project config package (`roby_data_portal/settings.py`, `urls.py`, `wsgi.py`, etc.) |
| `portal` | The Django app handling user auth, registration, app access grants, and the homepage. Lives at `portal/`. Not the same as the project. |
| `smolkraft` | **Three things at once:** (1) the subdirectory `smolkraft/` containing the dropped-in project, (2) the database alias for SmolKraft's secondary PostgreSQL instance in `DATABASES`, and (3) the *incorrect* entry currently in `INSTALLED_APPS` |
| `sk_backend` | **Two things at once:** (1) the directory `smolkraft/sk_backend/`, which is the root of the original standalone SmolKraft Django project (contains `manage.py`), and (2) the Django project config package inside that — `smolkraft/sk_backend/sk_backend/` (contains `settings.py`, `urls.py`, `wsgi.py`) |
| `backend_api` | The actual Django **app** within SmolKraft. Lives at `smolkraft/sk_backend/backend_api/`. Contains models, views, serializers, the DB router, and migrations. |
| `sk_backend_api` | The value of `AppConfig.name` in `backend_api/apps.py`. **This is wrong** — it's a made-up string that does not match the app's Python module path and causes Django to fail to locate the app. |
 
### The Physical Nesting
 
```
roby_data_portal/               ← git repo root
├── roby_data_portal/           ← Django project config (settings, urls, wsgi)
├── portal/                     ← Django app: auth & user management
├── api/                        ← Django app: REST endpoints
├── inventory/                  ← Django app: warehouse management
├── todo/                       ← Django app: task tracking
├── events/                     ← Django app: event planning
├── storycraft/                 ← Django app: creative writing
├── schemascope/                ← Django app: schema analysis
├── shares/                     ← Django app: sharing & permissions
└── smolkraft/                  ← dropped-in SmolKraft project (not a Django app itself)
    └── sk_backend/             ← SmolKraft's Django project root (has manage.py)
        ├── manage.py
        ├── sk_backend/         ← SmolKraft's project config (settings, urls, wsgi)
        │   ├── settings.py
        │   ├── urls.py
        │   └── wsgi.py
        └── backend_api/        ← SmolKraft's actual Django app ← THIS is what Django needs to know about
            ├── apps.py
            ├── models.py
            ├── views.py
            ├── serializers.py
            ├── db_router.py
            └── migrations/
```
 
---
 
## 2. What Each App Does
 
### `portal`
The front door. Handles user registration, email verification, login/logout, and the homepage. Owns the `UserProfile` model (extends Django's `User` with company, job title, API limits, and email-verified flag). Also owns the `App` registry — a database table of available portal modules — and `UserAppAccess`, which tracks which users can see which apps. Every other app depends on this one indirectly through the shared `User` model.
 
### `api`
DRF-based REST endpoints, primarily serving the Storycraft Vue frontend. Also houses the Google Places search endpoint (with DB-backed caching) and the `@api_access_required` decorator, which enforces per-user daily/monthly rate limits and logs all API usage to `APIUsageLog`.
 
### `storycraft`
A creative writing tool. Users create `Story` objects, then populate them with `Character`, `Setting`, `Plot`, and `Scene` models. Characters can have typed relationships to each other (`CharacterRelationship`). Scenes can have per-character motivation records. The whole thing is visualizable as a network graph (served via the `api` app). Implements `ShareableInterface` so stories can be shared with other users.
 
### `inventory`
Hierarchical warehouse management: `Warehouse → Rack → Shelf → Bin → Item`. Tracks stock changes in two directions — `StockAddition` (items arriving) and `Disposition` (items leaving, with typed reasons: sold, waste, damaged, etc.). Dashboard surfaces low-stock warnings.
 
### `todo`
Kanban-style task management. `Project → Board → Task`. Tasks have a status field (`todo`, `in_progress`, `done`) and optional start/due dates. Simple and self-contained.
 
### `events`
Event planning with structured agendas. Each `Event` has `Space` objects (think: rooms or stages), and each `Space` has `AgendaItem` records with durations. One space per event is auto-created as a "suggestion box" — invitees can propose agenda items there. Has `EventInvitation` for RSVP tracking. Implements `ShareableInterface`.
 
### `schemascope`
Upload a CSV or Excel file; the app detects its schema and stores column definitions, row counts, and uniqueness ratios. Identifies primary key candidates. Tracks schema versions when a file is re-uploaded with structural changes. Can detect relationships between schemas based on column similarity.
 
### `shares`
The generic collaboration backbone used by `storycraft` and `events`. A `Share` record links any model instance (via Django's `ContentType` framework) to a recipient, with a permission level (View / Comment / Edit / Admin), optional password, and expiration. Access is logged. Apps opt in by implementing `ShareableInterface`. Two middleware classes (`LoginRequiredMiddleware`, `SharePermissionMiddleware`) enforce access rules globally.
 
### `smolkraft` / `backend_api`
Manufacturing and production tracking. Runs against a **separate PostgreSQL database**. Models cover the full production cycle: `Vendor`, `Material`, `BOMHeader`/`BOMLine` (Bill of Materials), `BOOHeader`/`Operation` (Bill of Operations), `ProductionOrder`, and `Inventory`. Cross-references to portal `User` records are stored as plain `IntegerField` (not FK) because the two databases cannot have relational constraints between them. A custom DB router (`SmolkraftRouter`) directs all reads/writes for this app to the secondary database.
 
---
 
## 3. Shared Systems
 
### Authentication & Access Control
- Registration creates `User` + `UserProfile` + sends a verification email with a 48-hour token.
- Login is blocked until email is verified.
- `LoginRequiredMiddleware` enforces authentication on every route except a short whitelist (login, register, guest page, email verify, and public share URLs).
- `UserAppAccess` records control which portal modules appear in a user's nav. Apps marked `is_default=True` are granted to all new users automatically via a `post_save` signal.
 
### Sharing System
Apps that implement `ShareableInterface` gain shareable URLs, permission checks, and appear in the "shared with me" feed. The `@owner_or_permission_required` decorator is the standard guard on any view that touches shareable content.
 
### REST API & Rate Limiting
The `@api_access_required(endpoint_name)` decorator wraps any API view to enforce `api_access_enabled`, `api_daily_limit`, and `api_monthly_limit` from the user's profile. All calls — successful or not — are written to `APIUsageLog`.
 
---
 
## 4. Database Layout
 
| Alias | Used for | Env vars |
|---|---|---|
| `default` | Everything except SmolKraft | `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_PORT` |
| `smolkraft` | All `backend_api` models | `SMOLKRAFT_DB_*` |
 
The router (`SmolkraftRouter`) inspects `model._meta.app_label`. Any model whose label matches the SmolKraft app is sent to the `smolkraft` DB; everything else goes to `default`. Cross-database foreign keys are intentionally avoided — portal user IDs are stored in SmolKraft models as plain integers.
 
---
 
## 5. Request Flow (Happy Path)
 
```
Browser → Gunicorn
  → CorsMiddleware
  → SecurityMiddleware
  → SessionMiddleware
  → AuthenticationMiddleware
  → LoginRequiredMiddleware      ← bounces unauthenticated requests to /login
  → SharePermissionMiddleware    ← validates share tokens on /shares/access/* routes
  → URL router (roby_data_portal/urls.py)
      → portal.urls              /
      → api.urls                 /api/
      → storycraft.urls          /storycraft/
      → inventory.urls           /inventory/
      → todo.urls                /todo/
      → events.urls              /events/
      → shares.urls              /shares/
      → schemascope.urls         /schemascope/
      → smolkraft sk_backend urls  /smolkraft/
  → View
  → Template or JSON response
```
 
---
 
## 6. Known Integration Bugs (SmolKraft Graft)
 
These are the specific errors preventing the app from starting after SmolKraft was embedded.
 
### Bug 1 — Missing `__init__.py` files (Python import chain broken)
 
`smolkraft/` and `smolkraft/sk_backend/` have no `__init__.py`. Python does not treat them as packages, so any dotted import path through them fails immediately.
 
**Fix**: create two empty files:
```
smolkraft/__init__.py
smolkraft/sk_backend/__init__.py
```
 
### Bug 2 — `INSTALLED_APPS` points at the wrong thing
 
```python
# settings.py line 84 — WRONG
'smolkraft'
```
 
`smolkraft` is a directory, not a Django app. Django looks for an `apps.py` or app config there and finds nothing.
 
**Fix**:
```python
# settings.py — CORRECT
'smolkraft.sk_backend.backend_api'
```
 
### Bug 3 — `DATABASE_ROUTERS` path is wrong
 
```python
# settings.py line 192 — WRONG
DATABASE_ROUTERS = ['backend_api.db_router.SmolkraftRouter']
```
 
`backend_api` is not a top-level package. This import will fail.
 
**Fix**:
```python
DATABASE_ROUTERS = ['smolkraft.sk_backend.backend_api.db_router.SmolkraftRouter']
```
 
### Bug 4 — `AppConfig.name` does not match the module path
 
```python
# smolkraft/sk_backend/backend_api/apps.py — WRONG
name = 'sk_backend_api'
```
 
Django requires `AppConfig.name` to be the full dotted Python import path to the app package. `sk_backend_api` is a fiction — no such module path exists.
 
**Fix**:
```python
name = 'smolkraft.sk_backend.backend_api'
```
 
### Bug 5 — `app_label` mismatch after fixing Bug 4
 
The DB router currently checks:
```python
APP_LABEL = 'sk_backend_api'   # db_router.py
```
 
Once `AppConfig.name` is corrected to `smolkraft.sk_backend.backend_api`, Django will derive the default `app_label` as `backend_api` (the last component). The router's check will silently stop matching, and all SmolKraft DB operations will fall through to `default`.
 
**Fix** — explicitly declare the label in `AppConfig` so it stays stable:
```python
# smolkraft/sk_backend/backend_api/apps.py
class BackendApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'smolkraft.sk_backend.backend_api'
    label = 'sk_backend_api'   # keeps existing migrations and router check valid
```
 
No changes needed to `db_router.py` if the label is preserved this way.
 
---
 
## 7. Environment Variables Required
 
```
# Django
SECRET_KEY
DEBUG
 
# Main database
DB_HOST
DB_NAME
DB_USER
DB_PASSWORD
DB_PORT
 
# SmolKraft database
SMOLKRAFT_DB_NAME
SMOLKRAFT_DB_USER
SMOLKRAFT_DB_PASSWORD
SMOLKRAFT_DB_HOST
SMOLKRAFT_DB_PORT
 
# DigitalOcean Spaces (media storage)
DO_SPACES_ACCESS_KEY
DO_SPACES_SECRET_KEY
DO_SPACES_BUCKET_NAME
DO_SPACES_ENDPOINT_URL
DO_SPACES_REGION
 
# Email
EMAIL_BACKEND
EMAIL_HOST
EMAIL_PORT
EMAIL_HOST_USER
EMAIL_HOST_PASSWORD
 
# External APIs
GOOGLE_MAPS_API_KEY
```
 
---
 
## 8. What's Not Covered Yet (Next Iterations)
 
- Per-app model diagrams / ERDs
- Frontend build process (Webpack / Vue component map)
- Deployment runbook (migrations, collectstatic, Heroku/DO config)
- SmolKraft API endpoint reference
- Adding a new module to the portal (step-by-step)
- Channels / WebSocket setup (currently commented out)