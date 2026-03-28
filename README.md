# Roby Data Portal
 
**Roby Data Portal** is a self-hosted Django 4.2 platform that consolidates multiple business tools under a single authentication layer. It ships with six production-ready modules out of the box — inventory management, task tracking, event planning, data schema analysis, creative project tooling, and a manufacturing/production system — each isolated as its own Django app but sharing a common user model, permissions framework, and collaboration layer.
 
## Key Technical Characteristics
 
- **Auth & access control**: Session-based auth with email verification, per-user app access grants, and a middleware-enforced login gate across all routes
- **Sharing system**: Generic content sharing via Django's ContentType framework, with configurable permission levels (View / Comment / Edit / Admin), expiration, password protection, and access logging
- **Multi-database**: Primary PostgreSQL instance for portal data; a dedicated secondary PostgreSQL instance for the manufacturing module, with a custom DB router enforcing the boundary
- **Storage**: DigitalOcean Spaces (S3-compatible) for media files via `django-storages`
- **REST API**: DRF-based endpoints with per-user rate limiting (daily and monthly caps) and database-backed response caching
- **Frontend**: Server-rendered Django templates with a Vue 3 + D3 layer for interactive visualizations, built via Webpack
- **Deployment**: Gunicorn + WhiteNoise, targeting Heroku/DigitalOcean App Platform; Python 3.11
 
New modules can be added as standard Django apps and registered in the portal's app registry — the nav, access control, and sharing system pick them up automatically.
 
## Bundled Modules
 
| Module | Django App | Description |
|---|---|---|
| Inventory | `inventory` | Warehouse structure (rack/shelf/bin), stock tracking, dispositions |
| Todo | `todo` | Kanban-style task and project management |
| Events | `events` | Event planning with agenda, RSVP, and suggestion box |
| SchemaScope | `schemascope` | Upload and analyze CSV/Excel schemas; detect PKs and relationships |
| Storycraft | `storycraft` | Creative writing tool; characters, plots, scenes, relationships |
| SmolKraft | `smolkraft` | Manufacturing module; BOM, BOO, production orders, inventory (separate DB) |
 
## Stack
 
| Layer | Technology |
|---|---|
| Framework | Django 4.2 |
| Database | PostgreSQL (psycopg2) |
| API | Django REST Framework 3.15 |
| Frontend | Vue 3, D3 7, Webpack |
| File Storage | DigitalOcean Spaces (S3) via django-storages |
| Auth | Django session auth + custom middleware |
| Static Files | WhiteNoise |
| Web Server | Gunicorn |
| Runtime | Python 3.11 |