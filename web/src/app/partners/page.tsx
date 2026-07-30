import { MarketingShell } from "@/components/marketing/MarketingShell";
import { BecomePartnerPage } from "@/components/marketing/BecomePartnerPage";

export const metadata = {
  title: "Become a Partner | IIDATECH",
  description: "Join the IIDATECH partner network — list your services and get discovered by founders and MSMEs.",
};

export default function Page() {
  return (
    <MarketingShell>
      <BecomePartnerPage />
    </MarketingShell>
  );
}
