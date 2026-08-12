import Link from "next/link";
import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabaseServer";
import RunScanButton from "./RunScanButton";

export default async function DashboardPage() {
  const supabase = createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) redirect("/login");

  const { data: runs } = await supabase
    .from("scan_runs")
    .select("id, started_at, completed_at, status")
    .order("started_at", { ascending: false });

  return (
    <main>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-semibold">Scan History</h1>
        <RunScanButton />
      </div>

      <div className="border border-neutral-800 rounded-lg divide-y divide-neutral-800">
        {(!runs || runs.length === 0) && (
          <p className="p-4 text-neutral-400">No runs yet -- click "Run New Scan" to start.</p>
        )}
        {runs?.map((run) => (
          <Link
            key={run.id}
            href={`/runs/${run.id}`}
            className="flex items-center justify-between p-4 hover:bg-neutral-900"
          >
            <span>{new Date(run.started_at).toLocaleString()}</span>
            <StatusBadge status={run.status} />
          </Link>
        ))}
      </div>
    </main>
  );
}

function StatusBadge({ status }: { status: string }) {
  const color =
    status === "complete"
      ? "bg-emerald-900 text-emerald-300"
      : status === "failed"
      ? "bg-red-900 text-red-300"
      : "bg-amber-900 text-amber-300";
  return <span className={`text-xs px-2 py-1 rounded ${color}`}>{status}</span>;
}
