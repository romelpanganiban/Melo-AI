# Production Deployment Checklist

Melo-AI is local-first and should not be exposed to the public internet until the
following settings and infrastructure controls are in place.

## Required Environment

Create the production environment outside the repository. Do not commit it and do
not copy local development secrets into deployment configuration.

```env
API_RELOAD=false
AUTH_COOKIE_SECURE=true
ENABLE_HSTS=true
ENABLE_CORS=true
CORS_ORIGINS=https://your-domain.example
MELO_AUTH_SECRET=<long-random-secret>
DATABASE_URL=<production-database-url>
QDRANT_URL=<private-qdrant-url>
QDRANT_API_KEY=<private-qdrant-key>
ENABLE_WORKSPACE_TOOLS=false
AGENT_ALLOWED_CAPABILITIES=file:read,code:analyze,document:search
```

Use a secret manager or deployment secret store for `MELO_AUTH_SECRET`,
`DATABASE_URL`, `QDRANT_API_KEY`, and any provider credentials. Never print these
values in logs or diagnostics.

## Network and Proxy

- Terminate TLS at a trusted reverse proxy.
- Forward requests only from the configured frontend origin.
- Configure proxy timeouts for streaming chat responses.
- Forward `X-Forwarded-Proto` and client information only from trusted proxies.
- Keep the backend and Qdrant network-private when possible.
- Do not expose the Qdrant admin/API port publicly.

## Application Safety

- Keep `ENABLE_WORKSPACE_TOOLS=false` until every workspace has an isolated root.
- Keep agent capabilities read-only unless mutation approvals are intentionally
  configured and monitored.
- Use PostgreSQL as the production source of truth rather than SQLite.
- Run database migrations as a controlled deployment step.
- Configure backups and test restoration before storing important documents.
- Review reconciliation reports after migrations or database restoration.

## Validation Gates

Run these checks before release:

```text
python -m pytest -q
python -m pip_audit -r backend/requirements.txt --progress-spinner off
bandit -r backend -q -f txt -x backend/tests,backend/.venv,backend/test_full_flow.py,backend/verify_workspace_fs.py
```

The GitHub Actions security workflow must pass before merging. After deployment,
verify health, authentication, secure cookies, CORS behavior, streaming chat, and
workspace isolation from a non-production client.

## Dormant Docker Compose Deployment

The repository includes a production-shaped Compose stack under `deploy/`. It is
not active until you start it. To prepare a host:

```bash
cd deploy
cp production.env.example production.env
# Replace every placeholder in production.env.
docker compose -f docker-compose.production.yml config
docker compose -f docker-compose.production.yml up -d --build
```

Set `PUBLIC_DOMAIN` to a DNS name that points to the host. Caddy obtains and
renews the TLS certificate automatically when ports 80 and 443 are reachable.
The frontend uses `/api` for backend requests, and Caddy routes that prefix to
the private backend service. PostgreSQL and Qdrant are internal Compose services
with persistent named volumes and are not published to the host.

To stop the stack without deleting persistent data:

```bash
docker compose -f docker-compose.production.yml down
```

Do not run `docker compose down -v` unless you intentionally want to delete the
database and vector volumes.