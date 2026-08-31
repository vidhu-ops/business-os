import type { Metadata } from "next";
import { MarketingShell } from "@/components/marketing/MarketingShell";
import { BecomePartnerPage } from "@/components/marketing/BecomePartnerPage";
import { SITE_URL } from "@/lib/site";

export const metadata: Metadata = {
  title: "Become an IIDATECH Partner | Founders & MSME Network",
  description:
    "Join the IIDATECH partner network. Help founders and MSMEs with market research, business consultation, and new business growth services.",
  keywords: [
    "IIDATECH partners",
    "business consultation partners",
    "founder service providers",
    "MSME growth partners",
  ],
  alternates: { canonical: `${SITE_URL}/partners` },
  robots: { index: true, follow: true },
  openGraph: {
    title: "Partner with IIDATECH",
    description: "Get discovered by founders and MSMEs looking for research, planning, and growth support.",
    url: `${SITE_URL}/partners`,
  },
};

export default function Page() {
  return (
    <MarketingShell>
      <BecomePartnerPage />
    </MarketingShell>
  );
}
