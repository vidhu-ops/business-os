import { MarketingShell } from "@/components/marketing/MarketingShell";
import { HowItWorksPage } from "@/components/marketing/HowItWorksPage";

export const metadata = {
  title: "How it works | IIDATECH",
  description: "Click-by-click workflow: create a project, generate research, build a plan, and run Employee OS with six AI agents.",
};

export default function Page() {
  return (
    <MarketingShell>
      <HowItWorksPage />
    </MarketingShell>
  );
}
