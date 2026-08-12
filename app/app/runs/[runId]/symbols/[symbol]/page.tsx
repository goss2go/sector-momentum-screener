import Link from "next/link";
import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabaseServer";

export default async function SymbolDetailPage({
  params,
}: {
  params: { runId: string; symbol: string };
}) {
  const supabase = createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) redirect("/login");

  const symbol = decodeURIComponent(params.symbol);

  const { data: candidates } = await supabase
    .from("trade_candidates")
    .select("*")
    .eq("run_id", params.runId)
    .eq("symbol", symbol)
    .order("ror_pct", { ascending: false });

  return (
    <main>
      <Link href={`/runs/${params.runId}`} className="text-sm text-neutral-400 hover:text-neutral-200">
        &larr; Back to run
      </Link>
      <h1 className="text-2xl font-semibold mt-2 mb-6">{symbol} &mdash; Bull Put Candidates</h1>

      {(!candidates || candidates.length === 0) && (
        <p className="text-neutral-400">
          {symbol} made the top-10 list this run, but no spreads cleared the ROR/POP filter.
        </p>
      )}

      <div className="grid gap-4 sm:grid-cols-2">
        {candidates?.map((c) => (
          <div
            key={c.id}
            className="border border-neutral-800 rounded-lg p-4 relative"
          >
            {c.in_sweet_spot && (
              <span className="absolute top-3 right-3 text-xs bg-emerald-900 text-emerald-300 px-2 py-1 rounded">
                sweet spot
              </span>
            )}
            <p className="text-sm text-neutral-400 mb-2">
              Exp {c.expiration} &middot; {c.dte} DTE &middot; spot ${c.spot}
            </p>
            <p className="text-lg font-medium mb-3">
              Short ${c.short_strike} / Long ${c.long_strike} put
              <span className="text-neutral-400 text-sm"> &nbsp;(${c.width} wide)</span>
            </p>
            <dl className="grid grid-cols-2 gap-y-1 text-sm">
              <dt className="text-neutral-400">Credit</dt>
              <dd className="text-right">${c.credit}</dd>
              <dt className="text-neutral-400">Max loss</dt>
              <dd className="text-right">${c.max_loss}</dd>
              <dt className="text-neutral-400">ROR</dt>
              <dd className="text-right">{c.ror_pct}%</dd>
              <dt className="text-neutral-400">POP</dt>
              <dd className="text-right">{c.pop_pct}%</dd>
              <dt className="text-neutral-400">Short delta</dt>
              <dd className="text-right">{c.short_delta}</dd>
              <dt className="text-neutral-400">Short OI</dt>
              <dd className="text-right">{c.short_oi}</dd>
              <dt className="text-neutral-400">Short IV</dt>
              <dd className="text-right">{c.short_iv}%</dd>
            </dl>
          </div>
        ))}
      </div>
    </main>
  );
}
