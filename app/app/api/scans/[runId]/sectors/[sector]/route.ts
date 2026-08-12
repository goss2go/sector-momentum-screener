import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabaseServer";

export async function GET(
  _req: Request,
  { params }: { params: { runId: string; sector: string } }
) {
  const supabase = createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) {
    return NextResponse.json({ error: "unauthorized" }, { status: 401 });
  }

  const { data, error } = await supabase
    .from("symbol_scores")
    .select("*")
    .eq("run_id", params.runId)
    .eq("sector", decodeURIComponent(params.sector))
    .order("rank", { ascending: true });

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
  return NextResponse.json({ symbols: data });
}
