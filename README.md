# Spend Wise — Expense Tracking & Financial Wellness API

Python REST API for expense tracking, budgets, income, notifications, and smart insights (financial health score, categorization, subscription detection).

## Stack

- **Python** 3.11+
- **MySQL** 8.0 (connection pool via `mysql-connector-python`)
- **JWT** auth (`PyJWT`) with **bcrypt** password hashing (legacy SHA-256 hashes migrate on login)
- **Redis** optional cache for smart endpoints
- **stdlib `http.server`** (no Flask/FastAPI)
- **Docker Compose** with MySQL, Redis, nginx

## Layout

```
Spend_Wise/
├── app.py                 # HTTP server, routing, /health, /metrics
├── controller/            # Request handlers
├── database/              # Connection pool + SQL query modules
│   └── migration.sql      # Schema + seed data
├── model/                 # Domain objects
├── utils/                 # Auth, cache, categorizer, financial health, …
├── config/                # Settings + logging
├── nginx/                 # Reverse proxy config
├── tests/                 # Unit + integration tests
├── requirements/base.txt
├── Dockerfile
└── docker-compose.yml
```

## Quick start (local)

1. Copy env and edit secrets:

```bash
cp .env.example .env
```

2. Create/activate a venv and install deps:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements/base.txt
```

3. Start MySQL and apply schema:

```bash
mysql -u root -p < database/migration.sql
```

4. (Optional) Start Redis for caching:

```bash
redis-server
# or: docker run -p 6379:6379 redis:7-alpine
```

5. Run the API:

```bash
python app.py
```

Server listens on `SERVER_HOST`:`SERVER_PORT` (defaults: `localhost:8000`).

### Dev admin user

After migration, a seed admin exists:

- Username: `admin`
- Password: `admin123`

Change this immediately outside local development.

## Docker

```bash
docker-compose up --build
```

Services:

| Service | Ports |
|---------|-------|
| app | 8000 |
| mysql | 3306 |
| redis | 6379 |
| nginx | 80 (proxies to app) |

Production-style (nginx only exposed):

```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

App binds `0.0.0.0:8000` in the container. Health check: `GET /health`.

## API overview

### Public

- `POST /auth/register` — register
- `POST /auth/login` — returns JWT
- `GET /health` — `{ status, database }`
- `GET /metrics` — Prometheus text (if `prometheus-client` installed)

### Authenticated (`Authorization: Bearer <token>`)

| Area | Endpoints |
|------|-----------|
| Users | `GET/POST /users`, `GET/PUT/DELETE /users/{id}` |
| Expenses | CRUD `/expenses` (scoped to current user) |
| Budgets | CRUD `/budgets`, `GET /budgets/{id}/spending` |
| Incomes | CRUD `/incomes`, `GET /incomes/summary` |
| Notifications | CRUD + mark read |
| Smart | `GET /financial-health`, `/smart-categorize`, `/spending-patterns`, `POST /learn-categorization` |
| Subscriptions | `GET /subscriptions`, `/subscription-alternatives`, `/subscription-changes` |

CORS preflight (`OPTIONS`) is supported.

## Configuration

See [`.env.example`](.env.example):

| Variable | Purpose |
|----------|---------|
| `DB_*` | MySQL connection |
| `JWT_SECRET_KEY` | Token signing |
| `SERVER_HOST` / `SERVER_PORT` | Bind address |
| `REDIS_URL` | Cache (default `redis://localhost:6379/0`) |
| `CACHE_ENABLED` | `true`/`false` — if Redis is down, requests continue without cache |
| `ENVIRONMENT` | `development` / `production` / `testing` |

## Caching

When Redis is available:

| Key | TTL | Invalidated on |
|-----|-----|----------------|
| `fh:{user_id}` | 300s | expense/budget/income writes |
| `sp:{user_id}:{days}` | 600s | same |
| `sub:{user_id}:{days}` | 600s | same |

## Testing

```bash
source .venv/bin/activate
PYTHONPATH=. pytest
```

Coverage gate is configured in `pyproject.toml` / `.coveragerc` (controllers + core utils, 80%+).

## Security notes

- Passwords are stored with **bcrypt**; old SHA-256 hashes are re-hashed on successful login
- JWT required for all non-public routes (enforced in `app.py`)
- Resource queries are scoped by `user_id` from the token
- Do not commit real secrets; use `.env` (gitignored)

## Project origin

Original design notes live in [`Design and step.txt`](Design%20and%20step.txt) (early expense-tracker brief). The current codebase is the fixed-in-place layout described above.

## License

MIT (see project metadata in `pyproject.toml`).
