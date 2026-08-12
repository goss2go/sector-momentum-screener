import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabaseServer";

// GET /api/scans/:runId -- run summary + sector rankings (RLS ensures
// this 404s rather than leaks data if the run isn't the caller's own).
export async function GET(
  _req: Request,
  { params }: { params: { runId: string } }
) {
  const supabase = createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) {
    return NextResponse.json({ error: "unauthorized" }, { status: 401 });
  }

  const { data: run, error: runError } = await supabase
    .from("scan_runs")
    .select("*")
    .eq("id", params.runId)
    .single();

  if (runError || !run) {
    return NextResponse.json({ error: "not found" }, { status: 404 });
  }

  const { data: sectors, error: sectorError } = await supabase
    .from("sector_scores")
    .select("*")
    .eq("run_id", params.runId)
    .order("rank", { ascending: true, nullsFirst: false });

  if (sectorError) {
    return NextResponse.json({ error: sectorError.message }, { status: 500 });
  }

  return NextResponse.json({ run, sectors });
}
