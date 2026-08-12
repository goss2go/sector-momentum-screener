import { createBrowserClient } from "@supabase/ssr";

// Uses the anon key + RLS -- safe for the browser. Every query a user
// makes is automatically scoped to their own scan_runs via the policies
// in supabase/migrations/0001_init.sql.
export function createClient() {
  return createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  );
}
