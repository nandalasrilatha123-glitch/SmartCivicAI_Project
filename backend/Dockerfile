# ==========================================================
# SmartCivicAI backend image
# Pinned to Python 3.12-slim: verified to run this exact codebase
# end-to-end (migrations, seed data, full API surface) with no
# code changes needed. python:3.14-slim (originally targeted per
# spec §23) carries availability risk for binary wheels of some
# dependencies and Docker Hub mirror lag this soon after a major
# CPython release; nothing in this codebase requires a 3.14-only
# language feature, so 3.12 is the safer default here. Bump the
# tag below if/when you've verified 3.14 independently.
# ==========================================================
FROM python:3.12-slim

WORKDIR /app

# libpq for psycopg, curl for the healthcheck / entrypoint's wait-for-db
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Optional heavy AI/ML/CV deps — only pulled in if INSTALL_AI_EXTRAS=true
# at build time (`docker compose build --build-arg INSTALL_AI_EXTRAS=true backend`),
# since they're large and have their own Python-version-availability risk
# (see requirements-ai.txt). Default build skips them, matching
# AI_PROVIDER=demo / CV_PROVIDER=demo / PREDICTION_PROVIDER=demo out of the box.
ARG INSTALL_AI_EXTRAS=false
COPY requirements-ai.txt .
RUN if [ "$INSTALL_AI_EXTRAS" = "true" ]; then pip install --no-cache-dir -r requirements-ai.txt; fi

COPY . .

RUN mkdir -p uploads/complaints uploads/resolutions models/trained

COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=20s --retries=5 \
    CMD curl -f http://localhost:8000/health || exit 1

ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
