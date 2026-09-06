# Manual smoke test — Parts 1-3

This sandbox has no network access, so none of this has been run end-to-end
by me. Run these yourself after `pip install -r requirements.txt` (see main
README once Part 3 lands, or just: create venv, install, set up Postgres,
copy `.env.example` to `.env`, run `alembic upgrade head`).

## 1. Start the server
```
cd backend
uvicorn app.main:app --reload
```
Open http://localhost:8000/docs — Swagger UI should list all routes below.
If it fails to start, the traceback will point at the exact import/config
problem — that's expected to be the first thing you debug, not a sign the
code is fake.

## 2. Seed demo data
```
python -m app.seed
```
Expect console output ending in the three demo credential lines. Takes a
few seconds because it runs the AI pipeline once per demo complaint.

## 3. Register + login
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"citizen@smartcivicai.gov.in","password":"Demo@1234"}'
```
Expect a 200 with `access_token`, `refresh_token`, and a `user` object with
`role: "CITIZEN"`. Save the access token for the next steps:
```bash
export TOKEN="paste-access-token-here"
```

## 4. List modules (public, no auth needed)
```bash
curl http://localhost:8000/api/v1/modules
```
Expect all 4 modules with their categories nested.

## 5. Submit a complaint (multipart form, no image)
```bash
curl -X POST http://localhost:8000/api/v1/complaints \
  -H "Authorization: Bearer $TOKEN" \
  -F "module=TRAFFIC" \
  -F "description=There is a large pothole on Main Road causing accidents." \
  -F "original_language=en" \
  -F "latitude=17.385" -F "longitude=78.4867"
```
Expect a 201 with a `complaint_number` like `TRF-2026-000061`, a `priority`
(should come back HIGH or MEDIUM given the pothole/accident wording), and
`status` of either `PENDING` or `REQUIRES_ADMIN_REVIEW`.

## 6. List your own complaints
```bash
curl http://localhost:8000/api/v1/complaints -H "Authorization: Bearer $TOKEN"
```
Expect the complaint from step 5 plus nothing from other citizens (role
scoping — citizens only see their own).

## 7. Login as admin and see everything
```bash
curl -X POST http://localhost:8000/api/v1/auth/login -H "Content-Type: application/json" \
  -d '{"email":"admin@smartcivicai.gov.in","password":"Demo@1234"}'
```
Use that token to hit `GET /api/v1/complaints` — should now return ~61
complaints (60 seeded + your test one) across all modules/statuses.

## 8. Check the dashboard endpoints (admin token from step 7)
```bash
curl http://localhost:8000/api/v1/analytics/overview -H "Authorization: Bearer $ADMIN_TOKEN"
curl "http://localhost:8000/api/v1/analytics/over-time?granularity=month" -H "Authorization: Bearer $ADMIN_TOKEN"
curl http://localhost:8000/api/v1/analytics/hotspots -H "Authorization: Bearer $ADMIN_TOKEN"
curl http://localhost:8000/api/v1/analytics/predicted-volume -H "Authorization: Bearer $ADMIN_TOKEN"
```
Expect: `overview.total` around 61, `over-time` showing counts spread
across the last ~4 months (seed data is backdated), `hotspots` returning
several grid cells around Hyderabad, and `predicted-volume` returning 7
future dates with `is_demo_data: true`.

## 9. Test the real LLM pipeline (optional)
By default the app runs in demo mode with zero extra dependencies. To try
the actual LangGraph + Claude path:
```bash
pip install -r requirements-ai.txt
```
Then in `backend/.env`:
```
AI_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
```
Restart uvicorn, submit a new complaint (step 5), then check its AI
analysis — either via the admin AI Monitoring stats
(`GET /api/v1/analytics/ai-classification-stats`) or by inspecting the
`ai_analysis` table row for that complaint directly in Postgres:
```sql
SELECT provider, raw_error, overall_confidence FROM ai_analysis
ORDER BY created_at DESC LIMIT 1;
```
`provider = 'anthropic'` and `raw_error IS NULL` means the real LLM path
ran successfully. `provider = 'demo'` with a non-null `raw_error` tells you
exactly why it fell back (missing key, package not installed, or the
actual API error) — see `docs/BUILD_STATUS.md` Part 8 for the full list of
fallback cases.

## 10. Test the real predictive ML and YOLOv8 (optional)
Requires `pip install -r requirements-ai.txt`. In `backend/.env`:
```
PREDICTION_PROVIDER=xgboost
CV_PROVIDER=yolo
```
Restart uvicorn, then trigger training explicitly (don't skip this — the
first `predicted-volume` call will also auto-train if no model exists yet,
but this way you see the metrics directly):
```bash
curl -X POST "http://localhost:8000/api/v1/analytics/train-prediction-model" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```
Expect JSON with `mae`/`r2` and `training_rows` — with only ~60 seed
complaints across 4 months you'll see a small `training_rows` count and
metrics that reflect a genuinely thin dataset (this is expected and
labeled as such, see `docs/BUILD_STATUS.md` Part 9).

Then fetch a forecast and confirm which model actually ran:
```bash
curl "http://localhost:8000/api/v1/analytics/predicted-volume" -H "Authorization: Bearer $ADMIN_TOKEN"
```
`model_name` should read `"xgboost"` (or `"sklearn_gbr"` if xgboost isn't
installed) rather than `"demo_linear_trend"`.

For YOLOv8, upload a complaint with a photo, then check the image's CV
result directly in Postgres:
```sql
SELECT provider, status, detected_objects FROM cv_analysis ORDER BY created_at DESC LIMIT 1;
```
`status='ANALYZED_MODEL'` means your custom-trained weights ran (see
`models/yolo/README.md` for how to get one). `status='ANALYZED_DEMO'` with
`provider='yolo'` and labels prefixed `coco:` means it fell back to the
generic pretrained model — real detections, just not civic-issue-specific.

## If something breaks
Most likely causes, in order:
1. A Python 3.14 wheel isn't published yet for one of the pinned versions
   in requirements.txt — relax the pin (`pip install fastapi` with no
   version) and re-pin to whatever resolves once it works.
2. `DATABASE_URL` in `.env` doesn't match your local Postgres
   user/password/db name.
3. Forgot `alembic upgrade head` before `python -m app.seed`.
4. `analytics/over-time` uses Postgres' `date_trunc` — if you're not on
   Postgres (you should be, per spec) this will fail with a function-not-
   found error.

Report back exactly which command failed and the traceback and I'll fix
the actual code — don't spend time guessing.
