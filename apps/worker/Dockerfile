FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/apps/api:/app/apps/worker:/app/packages:/app

WORKDIR /app

COPY pyproject.toml ./
COPY apps ./apps
COPY packages ./packages

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir "."

CMD ["celery", "-A", "worker.celery_app.celery_app", "worker", "--beat", "--loglevel=INFO"]
