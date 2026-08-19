"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { api, setToken } from "@/lib/api";

function GoogleCallbackInner() {
  const router = useRouter();
  const params = useSearchParams();
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    async function finish() {
      const token = params.get("token");
      const next = params.get("next") || "/app/dashboard";
      const dest = next.startsWith("/app") ? next : "/app/dashboard";
      try {
        if (token) {
          setToken(token);
        }
        // Confirm session (cookie and/or token). Do not clear token on transient errors.
        await api.me();
        if (!cancelled) router.replace(dest);
      } catch (err) {
        if (token) {
          // Token was set — still enter workspace; layout will revalidate.
          if (!cancelled) router.replace(dest);
          return;
        }
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Google sign-in failed.");
        }
      }
    }
    finish();
    return () => {
      cancelled = true;
    };
  }, [params, router]);

  if (error) {
    return (
      <main className="login-shell">
        <p className="p-8 text-sm text-red-400">{error}</p>
        <a className="iid-btn iid-btn-primary mx-8" href="/login">
          Back to sign in
        </a>
      </main>
    );
  }

  return (
    <main className="login-shell">
      <p className="muted p-8">Finishing Google sign-in…</p>
    </main>
  );
}

export default function GoogleCallbackPage() {
  return (
    <Suspense fallback={<main className="login-shell"><p className="muted p-8">Loading…</p></main>}>
      <GoogleCallbackInner />
    </Suspense>
  );
}