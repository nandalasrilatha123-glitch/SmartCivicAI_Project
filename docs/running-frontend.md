# Running the frontend

```
cd frontend
cp .env.example .env       # defaults to https://smartcivicai-backend.onrender.com/api/v1 — fine if backend runs on its default port
npm install
npm run dev
```

Open http://localhost:5173. Make sure the backend (Parts 1-3) is running
first at http://localhost:8000 — see `docs/testing-guide.md`.

## Quick manual check
1. Register a new account (or log in as `citizen@smartcivicai.gov.in` /
   `Demo@1234` if you ran the seed script).
2. Click "Report an issue", pick a module (e.g. Traffic), pick a category,
   write a description, optionally use your browser location, submit.
3. You should land on the complaint detail page showing a real AI-generated
   priority/summary and status — this comes from the actual demo AI
   pipeline in the backend, not a placeholder.
4. Go to Dashboard — your new complaint should be in the list.
5. Switch the language switcher (top right) to తెలుగు or हिन्दी — all UI
   labels should switch immediately (this is client-side, no reload).

If `npm install` fails on any package version, relax the pin in
`package.json` the same way as the backend — none of these are exotic
packages, so any reasonably recent version should work.
