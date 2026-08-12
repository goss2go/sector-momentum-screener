import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabaseServer";

// GET /api/scans -- list the current user's past runs, newest first.
export async function GET() {
  const supabase = createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) {
    return NextResponse.json({ error: "unauthorized" }, { status: 401 });
  }

  const { data, error } = await supabase
    .from("scan_runs")
    .select("id, started_at, completed_at, status, error_message")
    .order("started_at", { ascending: false });

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
  return NextResponse.json({ runs: data });
}

// POST /api/scans -- trigger a new scan. This only proxies to the
// worker with the shared secret attached server-side; the browser never
// sees WORKER_API_KEY or WORKER_URL.
export async function POST() {
  const supabase = createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) {
    return NextResponse.json({ error: "unauthorized" }, { status: 401 });
  }

  const workerUrl = process.env.WORKER_URL;
  const workerKey = process.env.WORKER_API_KEY;
  if (!workerUrl || !workerKey) {
    return NextResponse.json(
      { error: "worker not configured (WORKER_URL / WORKER_API_KEY missing)" },
      { status: 500 }
    );
  }

  const res = await fetch(`${workerUrl}/scan`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${workerKey}`,
    },
    body: JSON.stringify({ user_id: user.id }),
  });

  if (!res.ok) {
    const text = await res.text();
    return NextResponse.json(
      { error: `worker error: ${text}` },
      { status: 502 }
    );
  }

  const body = await res.json();
  return NextResponse.json(body);
}
