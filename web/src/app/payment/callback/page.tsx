import { MarketingShell } from "@/components/marketing/MarketingShell";
import { PaymentCallbackPage } from "@/components/marketing/PaymentCallbackPage";

export const metadata = {
  title: "Payment status | IIDATECH",
  description: "Confirm your IIDATECH subscription payment.",
};

export default function Page() {
  return (
    <MarketingShell>
      <PaymentCallbackPage />
    </MarketingShell>
  );
}