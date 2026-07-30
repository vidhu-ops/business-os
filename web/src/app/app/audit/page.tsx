"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { ExistingCompanyPlanForward } from "@/components/ExistingCompanyPlanForward";
import { api, type User } from "@/lib/api";

export default function AuditPage() {
  const searchParams = useSearchParams();
  const projectId = searchParams.get("project") || "demo_readonly";
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    api.me().then(setUser).catch(() => setUser(null));
  }, []);

  const demoMode = Boolean(user?.is_demo);

  return (
  <div className="space-y-6">
    <div>
      <h1 className="text-2xl font-semibold text-slate-900">Company audit (GAUGE)</h1>
      <p className="mt-1 text-sm text-slate-600">
        {demoMode
          ? "Sample completed audit — read-only. Sign up to run a free audit on your company."
          : "Run a free company audit once, then build a 90-day plan from the results."}
      </p>
    </div>
    <ExistingCompanyPlanForward workspaceId={projectId} demoMode={demoMode} />
  </div>
  );
}