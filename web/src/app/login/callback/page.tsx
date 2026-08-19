"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { setToken } from "@/lib/api";

function GoogleCallbackInner() {
  const router = useRouter();
  const params = useSearchParams();
  const [error, setError] = useState("");

  useEffect(() => {
    const token = params.get("token");
    const next = params.get("next") || "/app/dashboard";
    if (!token) {
      setError("Missing sign-in token from Google.");
      return;
    }
    setToken(token);
    const dest = next.startsWith("/app") ? next : "/app/dashboard";
    router.replace(dest);
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