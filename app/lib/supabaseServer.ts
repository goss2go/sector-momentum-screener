import { createServerClient } from "@supabase/ssr";
import { cookies } from "next/headers";

// Server-side client, still anon-key + RLS -- reads/writes are scoped to
// whoever's session cookie is attached to the request. This is NOT the
// service-role client; that one only ever lives in the worker.
export function createClient() {
  const cookieStore = cookies();
  return createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return cookieStore.getAll();
        },
        setAll(cookiesToSet) {
          cookiesToSet.forEach(({ name, value, options }) =>
            cookieStore.set(name, value, options)
          );
        },
      },
    }
  );
}
