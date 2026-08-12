import Link from "next/link";
import { redirect, notFound } from "next/navigation";
import { createClient } from "@/lib/supabaseServer";

export default async function SectorDetailPage({
  params,
}: {
  params: { runId: string; sector: string };
}) {
  const supabase = createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) redirect("/login");

  const sectorName = decodeURIComponent(params.sector);

  const { data: symbols } = await supabase
    .from("symbol_scores")
    .select("*")
    .eq("run_id", params.runId)
    .eq("sector", sectorName)
    .order("rank", { ascending: true });

  if (!symbols) notFound();

  return (
    <main>
      <Link href={`/runs/${params.runId}`} className="text-sm text-neutral-400 hover:text-neutral-200">
        &larr; Sector Rankings
      </Link>
      <h1 className="text-2xl font-semibold mt-2 mb-6">{sectorName} &mdash; Top Symbols</h1>

      <table className="w-full text-sm border border-neutral-800 rounded-lg overflow-hidden">
        <thead className="bg-neutral-900 text-neutral-400">
          <tr>
            <th className="text-left p-3">Rank</th>
            <th className="text-left p-3">Symbol</th>
            <th className="text-right p-3">Score</th>
            <th className="text-right p-3">RSI</th>
            <th className="text-right p-3">% off 52w high</th>
            <th className="text-center p-3">MACD rising</th>
            <th className="text-right p-3">3m rel. strength</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-neutral-800">
          {symbols.map((sym) => (
            <tr key={sym.id} className="hover:bg-neutral-900 cursor-pointer">
              <td className="p-3">
                <Link href={`/runs/${params.runId}/symbols/${sym.symbol}`} className="block">
                  {sym.rank}
                </Link>
              </td>
              <td className="p-3 font-medium">
                <Link href={`/runs/${params.runId}/symbols/${sym.symbol}`} className="block">
                  {sym.symbol}
                </Link>
              </td>
              <td className="p-3 text-right">{sym.score}</td>
              <td className="p-3 text-right">{sym.rsi}</td>
              <td className="p-3 text-right">{sym.pct_off_52w_high}</td>
              <td className="p-3 text-center">{sym.macd_rising ? "Yes" : "No"}</td>
              <td className="p-3 text-right">{sym.rel_strength_3m_pct}%</td>
            </tr>
          ))}
        </tbody>
      </table>
    </main>
  );
}
