# Sector Rotation Income Scanner

Login-gated app that runs the sector-rotation bull put screener on
demand: ranks all 11 sector ETFs by technical momentum, drills into the
top 3 sectors' top-ranked symbols, and surfaces qualifying bull put
credit spreads as trade cards. Every run is kept as an immutable
historical snapshot.

Full product spec / architecture rationale: see `sector-scanner-app-spec.md`
(the doc this repo implements).

## Structure

```
app/          Next.js frontend + API routes (deploys to Vercel)
worker/       Python scan service -- FastAPI (deploys to Railway/Fly/Render)
supabase/     Postgres schema + RLS policies (migrations)
```

This uses **Option B** from the architecture doc: the scan runs in a
separate long-running Python service, not as a Vercel serverless
function, since a full scan (11 sector ETFs + ~200 candidate stocks +
live option chains on ~30 symbols) takes a few minutes.

## Setup

### 1. Supabase
1. Create a project at supabase.com.
2. Run `supabase/migrations/0001_init.sql` against it (SQL editor, or
   `supabase db push` if using the CLI).
3. Note the project URL, anon key, and service role key (Project
   Settings -> API).
4. Enable email auth (Authentication -> Providers) -- magic link is
   what the included login page uses.

### 2. Worker (Railway / Fly / Render -- anywhere that runs a
   long-lived container)
1. Deploy `worker/` as a Docker service (the included `Dockerfile`
   works as-is on any of those platforms).
2. Set env vars from `worker/.env.example`: `SUPABASE_URL`,
   `SUPABASE_SERVICE_ROLE_KEY`, `WORKER_API_KEY` (generate with
   `openssl rand -hex 32`).
3. Confirm `GET /health` returns `{"status": "ok"}` once deployed.

### 3. App (Vercel)
1. Import this repo into Vercel, set the root directory to `app/`.
2. Set env vars from `app/.env.example`: `NEXT_PUBLIC_SUPABASE_URL`,
   `NEXT_PUBLIC_SUPABASE_ANON_KEY`, `WORKER_URL` (the worker's deployed
   URL), `WORKER_API_KEY` (same value as the worker's).
3. Deploy. Vercel's GitHub integration auto-deploys on push to `main`
   and creates preview deploys per PR.

## Local development

```bash
# worker
cd worker
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in real values
uvicorn app.main:app --reload

# app (separate terminal)
cd app
npm install
cp .env.example .env.local   # fill in real values, WORKER_URL=http://localhost:8000
npm run dev
```

## Status

MVP scaffold: auth, run history, sector -> symbol -> trade-card
drill-down, rerun action, worker wired to Supabase. Not yet built:
UI-editable thresholds, outcome tracking (mark a trade taken/skipped
and settle it), scheduled runs. See the spec doc's "Phase 2" section.
