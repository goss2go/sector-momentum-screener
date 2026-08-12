"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function RunScanButton() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  async function handleClick() {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/scans", { method: "POST" });
      const body = await res.json();
      if (!res.ok) throw new Error(body.error || "scan failed to start");
      router.push(`/runs/${body.run_id}`);
      router.refresh();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <button
        onClick={handleClick}
        disabled={loading}
        className="bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white px-4 py-2 rounded-md font-medium"
      >
        {loading ? "Starting scan..." : "Run New Scan"}
      </button>
      {error && <p className="text-red-400 text-sm mt-2">{error}</p>}
    </div>
  );
}
