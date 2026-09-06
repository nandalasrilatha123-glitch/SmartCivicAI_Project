# Running SmartCivicAI with Docker Compose

This is the one-command path: Postgres, backend, and frontend all start
together, with the backend automatically running Alembic migrations before
it starts serving.

## Prerequisites
- Docker and Docker Compose installed
- Nothing else — you do NOT need Python, Node, or Postgres installed
  locally for this path.

## First run
```bash
cd SmartCivicAI
cp .env.example .env      # edit if you want real email/AI keys; safe to leave as-is for demo mode
docker compose up --build
```

Wait for the backend healthcheck to pass (you'll see
`smartcivicai-backend` become healthy in `docker compose ps`), then in a
**second terminal**, seed demo data once:
```bash
docker compose exec backend python -m app.seed
```
(You can instead set `SEED_ON_START=true` in `.env` before the *first*
`docker compose up`, but don't leave it on for subsequent restarts — see
the warning in `docker-entrypoint.sh`, it appends a fresh batch of demo
complaints every time it runs.)

## URLs
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- Swagger docs: http://localhost:8000/docs
- Postgres (if you want to connect directly, e.g. with a GUI client):
  `localhost:5432`, user `smartcivic_user`, password `smartcivic_pass`,
  database `smartcivicai` (all overridable in `docker-compose.yml`).

## Demo accounts
Same as the non-Docker path — see the main README or
`docs/testing-guide.md`. Password for all: `Demo@1234`.

## Enabling AI/ML/CV extras
By default the backend image installs only `requirements.txt` (core web
app, demo-mode AI/CV/predictions — matches `AI_PROVIDER=demo` etc.). To
bake in LangGraph/Anthropic/scikit-learn/XGBoost/ultralytics:
```bash
docker compose build --build-arg INSTALL_AI_EXTRAS=true backend
```
Then set the corresponding provider variables in `.env`
(`AI_PROVIDER=anthropic`, `ANTHROPIC_API_KEY=...`, `CV_PROVIDER=yolo`,
`PREDICTION_PROVIDER=xgboost`) and `docker compose up -d backend` to
restart just that service with the new image.

## Stopping / resetting
```bash
docker compose down            # stop containers, keep data
docker compose down -v         # stop containers AND delete the Postgres/
                                # uploads/trained-models volumes — full reset
```

## Troubleshooting
- **`python:3.14-slim` fails to pull**: see the note at the top of
  `backend/Dockerfile` — pin a specific patch tag or temporarily build
  against `python:3.12-slim` instead; nothing in the app code requires
  3.14-only syntax.
- **Backend keeps restarting**: `docker compose logs backend` — the
  entrypoint script waits for Postgres and then runs `alembic upgrade
  head` before starting uvicorn, so a crash loop is almost always either
  a migration error or a bad `DATABASE_URL`.
- **Frontend loads but API calls fail**: the frontend's API base URL is
  baked in at *build* time (Vite convention) from `VITE_API_BASE_URL` in
  `docker-compose.yml`'s `frontend.build.args` — it must be a URL your
  **browser** can reach (`http://localhost:8000/api/v1` with the default
  port mapping), not the Docker-internal service name `http://backend:8000`.
