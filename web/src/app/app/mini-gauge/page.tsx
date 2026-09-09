"use client";

import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { MiniGaugePanel } from "@/components/MiniGaugePanel";
import { api, type User } from "@/lib/api";

function MiniGaugeContent() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      try {
        const me = await api.me();
        if (!cancelled) setUser(me);
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : "Could not load session");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const demoMode = Boolean(user?.is_demo);

  return (
    <div className="space-y-6">
      <div>
        <p className="text-xs uppercase tracking-[0.22em] muted mb-2">GAUGE</p>
        <h1 className="font-display text-3xl font-bold">Mini Gauge</h1>
        <p className="mt-2 muted max-w-2xl">
          {demoMode
            ? "Demo accounts are read-only. Sign up to run a free Mini Gauge on your company."
            : "Fast scored snapshot from company basics + public URLs. Use Company Audit for the full GAUGE."}{" "}
          <Link href="/app/audit" className="underline underline-offset-2">
            Open full audit
          </Link>
        </p>
      </div>
      {loading && <p className="muted text-sm">Preparing Mini Gauge…</p>}
      {error && (
        <section className="iid-card border border-red-500/40">
          <p className="text-sm text-red-400">{error}</p>
        </section>
      )}
      {!loading && !error && <MiniGaugePanel demoMode={demoMode} />}
    </div>
  );
}

export default function MiniGaugePage() {
  return (
    <Suspense fallback={<p className="muted">Loading Mini Gauge…</p>}>
      <MiniGaugeContent />
    </Suspense>
  );
}