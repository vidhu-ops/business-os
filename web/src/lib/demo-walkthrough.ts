import { DEMO_CASE_STUDY } from "@/components/marketing/audienceContent";

export const DEMO_WALKTHROUGH_KEY = "iida-demo-walkthrough-done";
export const DEMO_WALKTHROUGH_STEP_KEY = "iida-demo-walkthrough-step";

/** Opens demo workspace and restarts the floating guided tour (see `guided=1` handler). */
export const GUIDED_DEMO_HREF = "/app/research?project=demo_readonly&guided=1";

export type DemoWalkthroughStep = {
  id: string;
  title: string;
  body: string;
  route: string;
  highlight?: string;
  primaryLabel: string;
};

export const DEMO_WALKTHROUGH_STEPS: DemoWalkthroughStep[] = [
  {
    id: "welcome",
    title: "Let's walk through a real business",
    body: `Demo idea: ${DEMO_CASE_STUDY.idea}. You will see what IIDATECH produced for this input — market sizing, competition, pricing, GTM, and execution — before you sign up.`,
    route: "/app/research?project=demo_readonly",
    primaryLabel: "Start with research",
  },
  {
    id: "research",
    title: "Step 1 — Market research",
    body: "This is a finished report with sections and citations — not a chat paste. Scroll through competitors, buyers, pricing, and opportunity. In your account, you enter 4 fields and generate this in minutes.",
    route: "/app/research?project=demo_readonly",
    highlight: '[data-demo-tour="research-report"]',
    primaryLabel: "Next: business plan",
  },
  {
    id: "plan",
    title: "Step 2 — Business plan",
    body: "The plan stays linked to the same project as your research. Use it for funding, lending, or investor discussions — then hand sections to Employee OS as tasks.",
    route: "/app/plan?project=demo_readonly",
    highlight: '[data-demo-tour="plan-output"]',
    primaryLabel: "Next: execution",
  },
  {
    id: "execute",
    title: "Step 3 — Employee OS",
    body: "Taylor (COO) and specialists turn the plan into tasks — research follow-ups, lists, drafts, and outreach. In demo mode you browse the office; with an account you approve before anything sends.",
    route: "/app/team?project=demo_readonly",
    highlight: '[data-demo-tour="employee-office"]',
    primaryLabel: "Finish tour",
  },
  {
    id: "finish",
    title: "Ready to run your own idea?",
    body: "Create a free account for 30 credits — generate research and a plan for your business, then let Taylor help execute with your approval.",
    route: "/app/research?project=demo_readonly",
    primaryLabel: "Create free account",
  },
];

export function isWalkthroughDone(): boolean {
  if (typeof window === "undefined") return true;
  return localStorage.getItem(DEMO_WALKTHROUGH_KEY) === "1";
}

export function markWalkthroughDone() {
  if (typeof window === "undefined") return;
  localStorage.setItem(DEMO_WALKTHROUGH_KEY, "1");
}

export function resetWalkthrough() {
  if (typeof window === "undefined") return;
  localStorage.removeItem(DEMO_WALKTHROUGH_KEY);
  localStorage.removeItem(DEMO_WALKTHROUGH_STEP_KEY);
}

export function getWalkthroughStepIndex(): number {
  if (typeof window === "undefined") return 0;
  const raw = localStorage.getItem(DEMO_WALKTHROUGH_STEP_KEY);
  const n = raw ? Number.parseInt(raw, 10) : 0;
  return Number.isFinite(n) ? Math.min(Math.max(n, 0), DEMO_WALKTHROUGH_STEPS.length - 1) : 0;
}

export function saveWalkthroughStepIndex(index: number) {
  if (typeof window === "undefined") return;
  localStorage.setItem(DEMO_WALKTHROUGH_STEP_KEY, String(index));
}
