"""
FastAPI worker service (Option B from the architecture doc).

Deployed separately from the Vercel app (Railway/Fly/Render -- anywhere
that allows a process to run for a few minutes uninstructed). The
Next.js app's /api/scans route calls POST /scan here with a shared
secret; this service does the actual multi-minute yfinance/options work
and writes results straight to Supabase using the service role key.
The Next.js app never talks to yfinance directly.
"""

import os
import traceback
from datetime import datetime, timezone

from fastapi import FastAPI, Header, HTTPException, BackgroundTasks
from pydantic import BaseModel

from . import config as cfg
from . import scan
from .supabase_client import get_client

app = FastAPI(title="sector-scanner-worker")

WORKER_API_KEY = os.environ.get("WORKER_API_KEY")


class ScanRequest(BaseModel):
    user_id: str


def _check_auth(authorization: str | None):
    if not WORKER_API_KEY:
        raise HTTPException(500, "WORKER_API_KEY not configured on the worker")
    if authorization != f"Bearer {WORKER_API_KEY}":
        raise HTTPException(401, "unauthorized")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/scan")
def trigger_scan(
    req: ScanRequest,
    background_tasks: BackgroundTasks,
    authorization: str | None = Header(default=None),
):
    _check_auth(authorization)

    sb = get_client()
    run = sb.table("scan_runs").insert({
        "user_id": req.user_id,
        "status": "running",
        "config_snapshot": cfg.config_snapshot(),
    }).execute()
    run_id = run.data[0]["id"]

    background_tasks.add_task(_execute_scan, run_id)

    return {"run_id": run_id, "status": "running"}


def _execute_scan(run_id: str):
    sb = get_client()

    def progress(msg: str):
        # Lightweight progress signal -- written into error_message's
        # sibling isn't ideal long-term, but for MVP this gives the
        # frontend something better than a flat "running" if you want to
        # poll it. Consider a dedicated status_detail column if this
        # gets used for more than a spinner label.
        try:
            sb.table("scan_runs").update({"status": "running"}).eq("id", run_id).execute()
        except Exception:
            pass

    try:
        sector_rows, symbol_rows, trade_rows, r = scan.run_full_scan(progress_cb=progress)

        if sector_rows:
            sb.table("sector_scores").insert([
                {"run_id": run_id, **row} for row in sector_rows
            ]).execute()

        if symbol_rows:
            sb.table("symbol_scores").insert([
                {"run_id": run_id, **row} for row in symbol_rows
            ]).execute()

        if trade_rows:
            sb.table("trade_candidates").insert([
                {"run_id": run_id, **row} for row in trade_rows
            ]).execute()

        sb.table("scan_runs").update({
            "status": "complete",
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "risk_free_rate": r,
        }).eq("id", run_id).execute()

    except Exception as e:
        sb.table("scan_runs").update({
            "status": "failed",
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "error_message": f"{e}\n{traceback.format_exc()[-2000:]}",
        }).eq("id", run_id).execute()
