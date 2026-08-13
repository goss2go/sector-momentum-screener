"use client";

import { useState } from "react";
import { createClient } from "@/lib/supabaseClient";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const supabase = createClient();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    const { error } = await supabase.auth.signInWithOtp({
      email,
      options: { emailRedirectTo: `${window.location.origin}/auth/callback` },
    });
    if (error) setError(error.message);
    else setSent(true);
  }

  return (
    <main className="max-w-sm mx-auto mt-24">
      <h1 className="text-xl font-semibold mb-4">Sign in</h1>
      {sent ? (
        <p className="text-neutral-300">Check your email for a magic link.</p>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-3">
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
            className="w-full bg-neutral-900 border border-neutral-800 rounded-md px-3 py-2"
          />
          <button
            type="submit"
            className="w-full bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-2 rounded-md font-medium"
          >
            Send magic link
          </button>
          {error && <p className="text-red-400 text-sm">{error}</p>}
        </form>
      )}
    </main>
  );
}
