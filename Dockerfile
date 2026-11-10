# Multi-stage Dockerfile for Dozentenmanager
FROM python:3.12-slim AS builder

RUN pip install --no-cache-dir uv

WORKDIR /app

COPY pyproject.toml ./
COPY app/ ./app/
COPY cli/ ./cli/
COPY run.py config.py ./
COPY migrations/ ./migrations/

RUN uv venv /app/.venv --seed
ENV PATH="/app/.venv/bin:$PATH"
RUN uv pip install .

# Runtime stage
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH" \
    FLASK_APP=run.py

RUN useradd -m -u 1000 appuser && \
    mkdir -p /app /app/instance /app/uploads /app/logs && \
    chown -R appuser:appuser /app

WORKDIR /app

COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv
COPY --chown=appuser:appuser . .

USER appuser

RUN mkdir -p instance uploads logs migrations/versions

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/auth/login', timeout=5)" || exit 1

CMD ["dozentenmanager"]
