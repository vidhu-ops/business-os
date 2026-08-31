import type { Metadata } from "next";
import { MarketingShell } from "@/components/marketing/MarketingShell";
import { HowItWorksPage } from "@/components/marketing/HowItWorksPage";
import { SITE_URL } from "@/lib/site";

export const metadata: Metadata = {
  title: "How IIDATECH Works | Research, Plan, Execute",
  description:
    "See how founders use IIDATECH for market research, business planning, business consultation, and Employee OS execution — step by step.",
  keywords: [
    "how IIDATECH works",
    "founder market research workflow",
    "business planning steps",
    "business consultation platform",
    "new business growth process",
  ],
  alternates: { canonical: `${SITE_URL}/how-it-works` },
  robots: { index: true, follow: true },
  openGraph: {
    title: "How IIDATECH works for founders and B2B teams",
    description:
      "Research → plan → execute. Market research, business planning, consultation, and growth ops in one OS.",
    url: `${SITE_URL}/how-it-works`,
  },
};

export default function Page() {
  return (
    <MarketingShell>
      <HowItWorksPage />
    </MarketingShell>
  );
}
