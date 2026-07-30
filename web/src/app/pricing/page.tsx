import { MarketingShell } from "@/components/marketing/MarketingShell";
import { PricingPage } from "@/components/marketing/PricingPage";

export const metadata = {
  title: "Pricing | IIDATECH",
  description: "Simple plans for founders, MSMEs, and teams — research, plans, and Employee OS in one workspace.",
};

export default function Page() {
  return (
    <MarketingShell>
      <PricingPage />
    </MarketingShell>
  );
}
