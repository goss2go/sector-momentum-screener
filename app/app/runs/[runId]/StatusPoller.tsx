"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

// Server Components only fetch once when the page loads -- nothing
// re-checks on its own. This polls router.refresh() every few seconds
// while status is "running", which re-runs the page's server-side data
// fetch and re-renders with fresh props. Once the parent passes a new
// status (complete/failed), this component re-renders with that new
// prop and the effect's guard clause stops the interval on its own --
// no manual "stop polling" call needed.
export default function StatusPoller({ status }: { status: string }) {
  const router = useRouter();

  useEffect(() => {
    if (status !== "running") return;
    const interval = setInterval(() => {
      router.refresh();
    }, 4000);
    return () => clearInterval(interval);
  }, [status, router]);

  return null;
}
