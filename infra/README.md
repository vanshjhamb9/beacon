# Infrastructure

Docker Compose defines the local production-like runtime:

- `api`: FastAPI service that runs Alembic migrations before starting Uvicorn.
- `worker`: Celery worker for asynchronous jobs.
- `postgres`: PostgreSQL 16 with a persistent local volume.
- `redis`: Redis 7 with append-only persistence.

Configuration is read from `.env`. Keep production secrets outside source control and inject them through the deployment platform.
