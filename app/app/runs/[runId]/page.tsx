import Link from "next/link";
import { redirect, notFound } from "next/navigation";
import { createClient } from "@/lib/supabaseServer";
import RunScanButton from "../../RunScanButton";
import StatusPoller from "./StatusPoller";

export default async function RunDetailPage({ params }: { params: { runId: string } }) {
  const supabase = createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) redirect("/login");

  const { data: run } = await supabase
    .from("scan_runs")
    .select("*")
    .eq("id", params.runId)
    .single();
  if (!run) notFound();

  const { data: sectors } = await supabase
    .from("sector_scores")
    .select("*")
    .eq("run_id", params.runId)
    .order("rank", { ascending: true, nullsFirst: false });

  return (
    <main>
      <div className="flex items-center justify-between mb-2">
        <Link href="/" className="text-sm text-neutral-400 hover:text-neutral-200">
          &larr; Scan History
        </Link>
        <RunScanButton />
      </div>
      <h1 className="text-2xl font-semibold mb-1">Sector Rankings</h1>
      <p className="text-neutral-400 text-sm mb-6">
        {new Date(run.started_at).toLocaleString()} &middot; {run.status}
      </p>

      {run.status === "running" && (
        <>
          <StatusPoller status={run.status} />
          <p className="text-amber-400 mb-4">Scan in progress -- this page will update automatically.</p>
        </>
      )}
      {run.status === "failed" && (
        <p className="text-red-400 mb-4">Scan failed: {run.error_message}</p>
      )}

      <table className="w-full text-sm border border-neutral-800 rounded-lg overflow-hidden">
        <thead className="bg-neutral-900 text-neutral-400">
          <tr>
            <th className="text-left p-3">Sector</th>
            <th className="text-left p-3">ETF</th>
            <th className="text-right p-3">Score</th>
            <th className="text-right p-3">RSI</th>
            <th className="text-right p-3">% off 52w high</th>
            <th className="text-center p-3">MACD rising</th>
            <th className="text-right p-3">3m rel. strength</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-neutral-800">
          {sectors?.map((s) => (
            <tr
              key={s.id}
              className={`${s.passed_gate ? "hover:bg-neutral-900 cursor-pointer" : "opacity-40"}`}
            >
              <td className="p-3">
                {s.passed_gate ? (
                  <Link href={`/runs/${params.runId}/sectors/${encodeURIComponent(s.sector)}`} className="block">
                    {s.is_top_3 && <span className="mr-2">&#9733;</span>}
                    {s.sector}
                  </Link>
                ) : (
                  <span>{s.sector} <span className="text-xs text-neutral-500">(gated out)</span></span>
                )}
              </td>
              <td className="p-3">{s.etf}</td>
              <td className="p-3 text-right">{s.score ?? "--"}</td>
              <td className="p-3 text-right">{s.rsi ?? "--"}</td>
              <td className="p-3 text-right">{s.pct_off_52w_high ?? "--"}</td>
              <td className="p-3 text-center">{s.macd_rising === null ? "--" : s.macd_rising ? "Yes" : "No"}</td>
              <td className="p-3 text-right">{s.rel_strength_3m_pct ?? "--"}%</td>
            </tr>
          ))}
        </tbody>
      </table>
    </main>
  );
}
