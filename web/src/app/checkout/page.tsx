import { MarketingShell } from "@/components/marketing/MarketingShell";
import { CheckoutPage } from "@/components/marketing/CheckoutPage";

export const metadata = {
  title: "Checkout | IIDATECH",
  description: "Upgrade to Growth with secure Freecharge payments.",
};

export default function Page() {
  return (
    <MarketingShell>
      <CheckoutPage />
    </MarketingShell>
  );
}