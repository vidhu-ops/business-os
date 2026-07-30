"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { ExistingCompanyPlanForward } from "@/components/ExistingCompanyPlanForward";
import { api, type User } from "@/lib/api";

function AuditContent() {
  const searchParams = useSearchParams();
  const [user, setUser] = useState<User | null>(null);
  const [workspaceId, setWorkspaceId] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      setError("");
      try {
        const me = await api.me();
        if (cancelled) return;
        setUser(me);
        if (me.is_demo) {
          setWorkspaceId(searchParams.get("project") || "demo_readonly");
        } else {
          const fromUrl = searchParams.get("project");
          if (fromUrl && fromUrl !== "demo_readonly") {
            setWorkspaceId(fromUrl);
          } else {
            const data = await api.ensureAuditWorkspace();
            setWorkspaceId(String(data.workspace_id || ""));
          }
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Could not start audit workspace");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [searchParams]);

  const demoMode = Boolean(user?.is_demo);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-3xl font-bold">Company audit (GAUGE)</h1>
        <p className="mt-2 muted">
          {demoMode
            ? "Sample completed audit — read-only. Sign up to run a free audit on your company."
            : "Run your free company audit — no project setup required. Complete the steps below, then run GAUGE."}
        </p>
      </div>

      {loading && <p className="muted text-sm">Preparing your audit workspace…</p>}
      {error && (
        <section className="iid-card border border-red-500/40">
          <p className="text-sm text-red-400">{error}</p>
        </section>
      )}
      {!loading && workspaceId && (
        <ExistingCompanyPlanForward workspaceId={workspaceId} demoMode={demoMode} />
      )}
    </div>
  );
}

export default function AuditPage() {
  return (
    <Suspense fallback={<p className="muted">Loading audit…</p>}>
      <AuditContent />
    </Suspense>
  );
}