import type { Metadata } from "next";
import { MarketingShell } from "@/components/marketing/MarketingShell";
import { PricingPage } from "@/components/marketing/PricingPage";
import { SITE_URL } from "@/lib/site";

export const metadata: Metadata = {
  title: "Pricing | Start Free Market Research & Business OS",
  description:
    "Start free with IIDATECH for market research, business planning, business consultation, and new business growth. Talk to us for paid and Enterprise plans.",
  keywords: [
    "IIDATECH pricing",
    "free market research for founders",
    "business consultation pricing",
    "startup business plan software",
  ],
  alternates: { canonical: `${SITE_URL}/pricing` },
  robots: { index: true, follow: true },
};

export default function Page() {
  return (
    <MarketingShell>
      <PricingPage />
    </MarketingShell>
  );
}
