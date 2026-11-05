# syntax=docker/dockerfile:1
FROM python:3.12-slim AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /build

COPY pyproject.toml ./
COPY src ./src
RUN --mount=type=secret,id=proxy_ca \
    if [ -f /run/secrets/proxy_ca ]; then export PIP_CERT=/run/secrets/proxy_ca; fi; \
    pip wheel --no-cache-dir --wheel-dir /wheels .

FROM builder AS test-builder
RUN --mount=type=secret,id=proxy_ca \
    if [ -f /run/secrets/proxy_ca ]; then export PIP_CERT=/run/secrets/proxy_ca; fi; \
    pip wheel --no-cache-dir --wheel-dir /wheels ".[dev]"

FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/home/app/.local/bin:$PATH

RUN useradd --create-home --uid 10001 app \
    && mkdir -p /app \
    && chown app:app /app
WORKDIR /app
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir --no-index --find-links=/wheels space-earth-dashboard \
    && rm -rf /wheels
COPY --chown=app:app alembic.ini ./
COPY --chown=app:app migrations ./migrations
COPY --chown=app:app frontend ./frontend

USER app
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health/live', timeout=2)"]
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers ${WEB_CONCURRENCY:-2}"]

FROM runtime AS test
USER root
COPY --from=test-builder /wheels /wheels
RUN pip install --no-cache-dir --no-index --find-links=/wheels "space-earth-dashboard[dev]" \
    && rm -rf /wheels
COPY --chown=app:app tests ./tests
COPY --chown=app:app pyproject.toml ./
USER app
CMD ["python", "-m", "pytest"]

FROM runtime AS production
