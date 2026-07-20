# LinkForge

Enterprise URL shortener with multi-tenant workspaces, click analytics, QR codes, webhooks, API keys, team collaboration, and an event-driven architecture.

**Live**: [url-shortner-peay.vercel.app](https://url-shortner-peay.vercel.app)

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | Next.js 16, React 19, TypeScript, Tailwind CSS 4, shadcn/ui |
| **Backend** | Python 3.13, FastAPI, SQLAlchemy 2, Alembic |
| **Databases** | PostgreSQL 16 (Neon), MongoDB 7 (Atlas), Redis 7 (Upstash) |
| **Event Bus** | Apache Kafka + Karapace Schema Registry (Aiven) |
| **Auth** | JWT (access/refresh tokens), OAuth 2.0 (Google, GitHub), Argon2 hashing |
| **Observability** | OpenTelemetry → New Relic (traces + metrics) |
| **CI/CD** | GitHub Actions (8 jobs), Trivy security scan, GHCR |
| **Deployment** | Render (backend), Vercel (frontend) |

---

## Features

### Core
- **URL Shortening** — Custom aliases, auto-generated short codes (Base62)
- **QR Codes** — Per-URL QR generation, bulk QR ZIP download
- **Password Protection** — Gate access with a password
- **One-Time URLs** — Self-destruct after first visit
- **A/B Testing** — Device-specific redirects (iOS / Android / default)
- **URL Expiration** — Auto-disable links at a set date/time
- **Bulk Operations** — CSV import, bulk update/disable/delete, CSV/JSON export

### Analytics
- Click count, unique visitors, device/browser/OS breakdown
- Geographic data (country, city), UTM campaign breakdown, referrer breakdown
- Daily timeseries (up to 90 days)
- Aggregated rollups updated every 60s by dedicated worker

### Teams & Collaboration
- **Workspaces** — Multi-tenant isolation with CRUD
- **Roles** — Admin / Editor / Viewer with RBAC enforcement
- **Invites** — Email-based workspace invitations
- **Folders** — Organize URLs within workspaces
- **Tags** — Categorize URLs across folders

### Developer Tools
- **API Keys** — Create, revoke, rotate with per-key quota tracking (Redis daily limits)
- **Webhooks** — Subscribe to `url.clicked` events with HMAC-SHA256 signed delivery
- **Webhook Receiver** — Ingest webhooks from external services, view event history
- **Bulk API** — Programmatic CSV import/export and batch operations

### Admin
- Superadmin panel — List users/workspaces/URLs, toggle superadmin, platform-wide stats
- **Audit Logs** — Track all mutations by workspace, resource, or actor

### Security
- Argon2 password hashing
- JWT access + refresh token pair with Redis blacklisting
- Rate limiting — Token-bucket (IP-level + user-level, tiered by plan)
- RBAC middleware — Write-permission enforcement

---

## Architecture

```
                     ┌──────────────┐
                     │   Frontend   │
                     │  (Vercel)    │
                     └──────┬───────┘
                            │ HTTPS
                     ┌──────▼───────┐
                     │   Backend    │
                     │  (Render)    │
                     └──┬───────┬───┘
                        │       │
              ┌─────────▼──┐ ┌──▼──────────┐
              │ PostgreSQL │ │   MongoDB    │
              │  (Neon)    │ │  (Atlas)     │
              └────────────┘ └─────────────┘
                        │
              ┌─────────▼──┐ ┌──────────────┐
              │   Redis    │ │    Kafka     │
              │ (Upstash)  │ │   (Aiven)    │
              └────────────┘ └──────┬───────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
             ┌──────▼──────┐ ┌──────▼──────┐ ┌──────▼──────┐
             │  Analytics  │ │  Webhook    │ │  Metadata   │
             │   Worker    │ │  Consumer   │ │   Worker    │
             └─────────────┘ └─────────────┘ └─────────────┘
             ┌──────▼──────┐ ┌──────▼──────┐ ┌──────▼──────┐
             │Aggregation  │ │   Expiry    │ │   Cleanup   │
             │   Worker    │ │   Worker    │ │   Worker    │
             └─────────────┘ └─────────────┘ └─────────────┘
             ┌──────▼──────┐ ┌──────▼──────┐
             │Webhook Retry│ │  DLQ Replay │
             │   Worker    │ │   Worker    │
             └─────────────┘ └─────────────┘
```

- **Event-driven**: Click events and URL mutations are published to Kafka (Avro-serialized) and consumed by 8 dedicated workers.
- **Multi-database**: PostgreSQL for relational data, MongoDB for click event analytics, Redis for caching/rate limiting/idempotency/quotas.
- **Resilient**: DLQ (Dead Letter Queue) for failed events, exponential backoff reconnection, scheduled workers for expiry/cleanup/aggregation.
- **Workers run embedded** in the web process by default, or standalone with `STANDALONE_WORKERS=1`.

---

## API Overview

All routes under `/api/v1/`:

| Resource | Key Endpoints |
|---|---|
| **Auth** | `POST /auth/register`, `/auth/login`, `/auth/refresh`, `/auth/oauth/{provider}` |
| **URLs** | `GET/POST /urls`, `GET/PUT/DELETE /urls/{id}`, `GET /urls/{id}/qr` |
| **Analytics** | `GET /analytics/{short_code}/summary`, `/timeseries`, `/devices`, `/utm`, `/referrers` |
| **Workspaces** | `GET/POST /workspaces`, `POST /workspaces/{id}/invites`, `GET /workspaces/{id}/members` |
| **Webhooks** | `POST/GET /webhooks/workspace/{ws_id}`, `POST /webhook-receiver` |
| **API Keys** | `POST/GET /api-keys`, `DELETE /api-keys/{id}`, `POST /api-keys/{id}/rotate` |
| **Bulk** | `POST /urls/bulk/create`, `GET /urls/bulk/export`, `GET /urls/bulk/qr` |
| **Admin** | `GET /admin/users`, `GET /admin/stats`, `PATCH /admin/users/{id}/toggle-superadmin` |
| **Other** | `GET/POST /folders`, `GET/POST /tags`, `GET/POST /favorites`, `GET /audit-logs/...`, `POST /billing/upgrade` |

Redirect: `GET /{short_code}` — 302 redirect with support for password protection, A/B testing, device-specific URLs.

---

## Local Development

### Prerequisites
- Python 3.13+, Node.js 22+, Docker (for data stores)

### 1. Start data stores
```bash
docker compose up -d postgres mongodb redis
```

### 2. Backend
```bash
cd backend
uv venv && source .venv/bin/activate  # Windows: .venv\Scripts\Activate.ps1
uv sync
cp .env.example .env                   # configure credentials
alembic upgrade head
uv run uvicorn src.main:app --reload --port 8000
```

### 3. Frontend
```bash
cd frontend
npm ci
npm run dev                             # http://localhost:3000
```

### 4. Workers (optional, in separate terminals)
```bash
cd backend
uv run python run_worker_analytics.py
uv run python run_worker_metadata.py
# ... etc (8 workers total)
```

### Seed a superadmin
```bash
curl -X POST http://localhost:8000/api/v1/admin/seed -H "Authorization: Bearer <token>"
```

---

## Deployment

### Backend — Render
Single web service with 8 inline workers. Build: `pip install uv && uv sync --no-dev`. Start: `uv run uvicorn src.main:app --host 0.0.0.0 --port $PORT`.

### Frontend — Vercel
Auto-deploys from `main` branch. `NEXT_PUBLIC_API_URL` and `BACKEND_URL` point to Render. Server-side rewrites proxy `/r/:code` and `/api/v1/*`.

### Environment Variables
Key variables for `.env` (see `.env.example` for full list):

```
DATABASE_URL=postgresql+asyncpg://...
MONGODB_URL=mongodb://...
REDIS_URL=redis://...
KAFKA_BOOTSTRAP_SERVERS=...
KAFKA_SASL_USERNAME=...
KAFKA_SASL_PASSWORD=...
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GITHUB_CLIENT_ID=...
GITHUB_CLIENT_SECRET=...
OTEL_EXPORTER_OTLP_ENDPOINT=...
OTEL_EXPORTER_OTLP_HEADERS=api-key=...
```

---

## Workers

| Worker | Trigger | Purpose |
|---|---|---|
| **Analytics** | Kafka (`url-clicked`) | Parse user-agent, store click events in MongoDB, update PostgreSQL analytics |
| **Metadata** | Kafka (`url-created`) | Scrape title/description/OG image from destination URL |
| **Webhook Click** | Kafka (`url-clicked`) | Deliver click events to workspace webhooks with HMAC signature |
| **Webhook Retry** | Schedule (60s) | Retry failed webhook deliveries (exponential backoff, max 5 retries) |
| **Aggregation** | Schedule (60s) | Compute click counts and unique IPs per URL via MongoDB aggregation pipeline |
| **Expiry** | Schedule (30s) | Disable expired URLs, evict from Redis cache |
| **Cleanup** | Schedule (45s) | Purge soft-deleted URLs and associated data from all stores |
| **DLQ Replay** | Kafka (DLQ topics) | Replay failed messages back to original topics |

---

## Testing

```bash
# Backend
cd backend && uv run pytest                    # unit + integration
cd backend && uv run pytest -m "not slow"      # quick tests only

# Frontend
cd frontend && npm test                        # Vitest unit tests
cd frontend && npm run test:e2e                # Playwright e2e tests
cd frontend && npm run test:coverage           # with coverage report
```

CI runs 8 jobs: pre-commit, backend lint + unit + integration, frontend lint + test + build, Docker build + Trivy scan.

---

## License

MIT
