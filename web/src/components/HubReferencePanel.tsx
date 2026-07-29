"use client";

import { useRouter } from "next/navigation";
import { Toaster } from "@/hub-reference/components/ui/sonner";
import { PlanItOut } from "@/hub-reference/components/PlanItOut";
import { BusinessPlan } from "@/hub-reference/components/BusinessPlan";
import { ThemeProvider } from "@/hub-reference/contexts/ThemeContext";
import "@/hub-reference/styles/globals.css";

type HubReferencePanelProps = {
  mode: "plan-it-out" | "business-planning";
};

export function HubReferencePanel({ mode }: HubReferencePanelProps) {
  const router = useRouter();

  return (
    <ThemeProvider>
      <div className="hub-reference-root dark min-h-[720px] rounded-xl border border-[var(--iid-line)] overflow-hidden bg-[var(--background)] text-[var(--foreground)]">
        <Toaster />
        {mode === "plan-it-out" ? (
          <PlanItOut onSwitchToResearch={() => router.push("/app/research")} />
        ) : (
          <BusinessPlan />
        )}
      </div>
    </ThemeProvider>
  );
}
