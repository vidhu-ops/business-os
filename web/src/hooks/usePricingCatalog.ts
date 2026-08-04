"use client";

import { api } from "@/lib/api";
import { useEffect, useState } from "react";

export type PricingCatalog = Awaited<ReturnType<typeof api.pricingCatalog>>;

let cache: PricingCatalog | null = null;
let inflight: Promise<PricingCatalog> | null = null;

export function usePricingCatalog() {
  const [catalog, setCatalog] = useState<PricingCatalog | null>(cache);
  const [loading, setLoading] = useState(!cache);

  useEffect(() => {
    if (cache) {
      setCatalog(cache);
      setLoading(false);
      return;
    }
    if (!inflight) {
      inflight = api.pricingCatalog().then((data) => {
        cache = data;
        return data;
      });
    }
    inflight
      .then((data) => setCatalog(data))
      .catch(() => setCatalog(null))
      .finally(() => setLoading(false));
  }, []);

  return { catalog, loading };
}

export function researchCreditsForSection(catalog: PricingCatalog | null, sectionCount: number): number {
  const tier = catalog?.research_tiers?.find((t) => Number(t.section_count) === sectionCount);
  if (tier && typeof tier.credits === "number") return tier.credits;
  const fallback: Record<number, number> = { 3: 5, 8: 8, 16: 15, 25: 20 };
  return fallback[sectionCount] ?? 5;
}

export function formatCreditHint(
  catalog: PricingCatalog | null,
  action: string,
  opts?: { sectionCount?: number; unlimited?: boolean },
): string {
  if (opts?.unlimited) return "Included on your plan (unlimited).";
  if (action === "research" && opts?.sectionCount) {
    const credits = researchCreditsForSection(catalog, opts.sectionCount);
    return `This run uses ${credits} credits.`;
  }
  const costs = catalog?.credit_actions as Record<string, { credits?: number }> | undefined;
  const credits = costs?.[action]?.credits;
  if (credits) return `Uses ${credits} credits per run.`;
  return "Uses credits from your balance.";
}