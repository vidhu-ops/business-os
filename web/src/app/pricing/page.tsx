import type { Metadata } from "next";
import { MarketingShell } from "@/components/marketing/MarketingShell";
import { PricingPage } from "@/components/marketing/PricingPage";
import { SITE_URL } from "@/lib/site";

export const metadata: Metadata = {
  title: "Pricing",
  description: "Start free with IIDATECH. Talk to us for paid and Enterprise plans.",
  alternates: { canonical: `${SITE_URL}/pricing` },
};

export default function Page() {
  return (
    <MarketingShell>
      <PricingPage />
    </MarketingShell>
  );
}
