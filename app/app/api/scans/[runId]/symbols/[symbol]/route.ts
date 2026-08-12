import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabaseServer";

export async function GET(
  _req: Request,
  { params }: { params: { runId: string; symbol: string } }
) {
  const supabase = createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) {
    return NextResponse.json({ error: "unauthorized" }, { status: 401 });
  }

  const { data, error } = await supabase
    .from("trade_candidates")
    .select("*")
    .eq("run_id", params.runId)
    .eq("symbol", decodeURIComponent(params.symbol))
    .order("ror_pct", { ascending: false });

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
  return NextResponse.json({ candidates: data });
}
