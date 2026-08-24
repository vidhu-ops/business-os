import type { MarketingPhotoId } from "./marketingImages";

export type Audience = "founder" | "company";

export type ToolId =
  | "research"
  | "plan"
  | "execute"
  | "automate"
  | "mentor"
  | "gauge";

export const TOOLS: Array<{
  id: ToolId;
  label: string;
  short: string;
  founder: { title: string; body: string; inApp: string };
  company: { title: string; body: string; inApp: string };
  videoId?: string;
  videoSrc?: string;
}> = [
  {
    id: "research",
    label: "Market Research",
    short: "Research",

    videoSrc: "/marketing/videos/research.mp4",
    founder: {
      title: "Market research for founders",
      body: "Validate your idea with sourced competitor maps, TAM/SAM/SOM, buyer pain, and pricing evidence — before you spend on ads or inventory.",
      inApp: "Open Market Research → pick your project → click Generate report. You get a multi-section report with citations you can share with co-founders or investors.",
    },
    company: {
      title: "Market intelligence for growing companies",
      body: "Keep category, competitor, and pricing intelligence current for leadership, sales, and board updates — without hiring a full research bench.",
      inApp: "Create or open a company project → run Standard/Professional research → export the report for GTM and BD teams.",
    },
  },
  {
    id: "plan",
    label: "Business Planning",
    short: "Plan",

    videoSrc: "/marketing/videos/plan.mp4",
    founder: {
      title: "Bank- and investor-ready business plans",
      body: "Turn research into ICP, GTM, unit economics, and a structured plan you can submit for funding, loans, or co-founder alignment.",
      inApp: "Open Plan → click Build Agentic Business Plan. The plan stays linked to the same project as your research.",
    },
    company: {
      title: "Growth and operating plans for B2B teams",
      body: "Produce growth plans, expansion theses, and operating roadmaps that sales, ops, and finance can execute against.",
      inApp: "Use an existing-company project → generate a Growth/Investor plan → hand tasks to Employee OS.",
    },
  },
  {
    id: "execute",
    label: "Employee OS",
    short: "Execute",

    videoSrc: "/marketing/videos/execute.mp4",
    founder: {
      title: "AI employees that execute your plan",
      body: "Taylor (COO) plus specialists turn the plan into tasks — research follow-ups, leads, decks, and outreach — with approvals before anything external sends.",
      inApp: "Open Employee OS → Build checklist from plan → Run next / Run full office day → Approve tasks in Tasks & Approvals.",
    },
    company: {
      title: "Virtual ops capacity for B2B companies",
      body: "Staff recurring research, CRM enrichment, outreach drafts, and department workflows without expanding headcount overnight.",
      inApp: "Configure department scope → hire agents → run office actions and approve outbound from the war room.",
    },
  },
  {
    id: "automate",
    label: "Automation",
    short: "Automate",

    videoSrc: "/marketing/videos/automate.mp4",
    founder: {
      title: "Automations that close the loop",
      body: "Build workflows across CRM, inbox, and reporting so research and outreach do not die in spreadsheets.",
      inApp: "Open Automation → build a workflow → run steps with credits → connect tools under Integrations.",
    },
    company: {
      title: "Department automation for B2B stacks",
      body: "Standardize lead routing, reporting packs, and follow-ups across HubSpot, Gmail, and your internal tools.",
      inApp: "Use Automation builders with team templates → run steps → monitor outcomes in the project workspace.",
    },
  },
  {
    id: "mentor",
    label: "Mentor",
    short: "Mentor",

    videoSrc: "/marketing/videos/mentor.mp4",
    founder: {
      title: "A mentor that knows your project",
      body: "Ask what to do next, get grounded advice from your research and plan, and hand work to Taylor when you are ready to execute.",
      inApp: "Open Mentor → chat about your idea or blockers → say run next or build checklist to trigger Employee OS.",
    },
    company: {
      title: "Operator guidance for company projects",
      body: "Leadership and managers get context-aware coaching tied to company memory, goals, and live workspace artifacts.",
      inApp: "Open Mentor with your company project selected → ask for priorities → hand execution to Taylor.",
    },
  },
  {
    id: "gauge",
    label: "GAUGE Company Audit",
    short: "Gauge",

    videoSrc: "/marketing/videos/gauge.mp4",
    founder: {
      title: "Score your idea before you scale",
      body: "Run a GAUGE company audit on traction, market fit, operations, and readiness — so you know what to fix before fundraising or hiring.",
      inApp: "Open GAUGE / Company Audit → answer the questionnaire → review scored dimensions and recommended next actions.",
    },
    company: {
      title: "Company health audits for B2B operators",
      body: "Benchmark growth, ops, GTM, and financial readiness with a structured GAUGE audit your leadership team can act on.",
      inApp: "Start a free company audit → complete GAUGE inputs → share the scored report with leadership and Mentor.",
    },
  },
];

export const AUDIENCE = {
  founder: {
    label: "Founder",
    ariaLabel: "Read IIDATECH as a founder",
    h1Lead: "The business OS for",
    h1Accent: ["FOUNDERS", "BUILDING"],
    lead:
      "IIDATECH is the all-in-one business ecosystem for startup founders: AI market research, business plan generation, Mentor guidance, Employee OS execution, and automation — so you can validate, plan, and ship without a full team.",
    pipe: ["RESEARCH", "PLAN", "EXECUTE", "AUTOMATE"],
    primaryCta: { href: "/login?mode=register", label: "Start free as a founder" },
    secondaryCta: { href: "/app/research?project=demo_readonly", label: "See founder demo", demo: true },
    whoForTitle: "Built for founders and early-stage startups",
    whoForBody:
      "Solo founders, co-founder teams, and pre-seed to Series A startups who need investor-grade research, a real business plan, and AI employees that execute — without consulting fees.",
    aboutTitle: "About IIDATECH for founders",
    aboutBody:
      "IIDATECH combines market intelligence, business planning, mentorship, and an AI workforce in one workspace. Founders go from idea → sourced report → bank-ready plan → executed tasks with approvals.",
  },
  company: {
    label: "Established company",
    ariaLabel: "Read IIDATECH as an established B2B company",
    h1Lead: "The business OS for",
    h1Accent: ["B2B", "COMPANIES"],
    lead:
      "IIDATECH helps established B2B companies run market research, growth planning, CRM-ready execution, and workflow automation on one platform — with GAUGE company audits and Employee OS capacity your teams can approve and scale.",
    pipe: ["AUDIT", "RESEARCH", "PLAN", "OPERATE"],
    primaryCta: { href: "/login?intent=audit&mode=register", label: "Run free company audit" },
    secondaryCta: { href: "/app/research?project=demo_readonly", label: "See company demo", demo: true },
    whoForTitle: "Built for MSMEs and B2B growth teams",
    whoForBody:
      "Established companies, MSME operators, and B2B teams that need continuous market intelligence, operating plans, outbound support, and automation — without standing up a large strategy or ops org.",
    aboutTitle: "About IIDATECH for B2B companies",
    aboutBody:
      "Use IIDATECH as your business operating layer: GAUGE health audits, competitor and pricing intelligence, growth plans, Mentor for operators, and Employee OS agents that work under human approval.",
  },
} as const;

export const HOW_IT_WORKS = [
  { step: "01", title: "Create a project", body: "Click Create project. Choose new idea (founder) or existing company (B2B) and capture your market." },
  { step: "02", title: "Generate research", body: "Open Market Research and click Generate report for sourced market intelligence." },
  { step: "03", title: "Build the plan", body: "Open Plan and click Build Agentic Business Plan tied to the same project." },
  { step: "04", title: "Ask Mentor", body: "Use Mentor for next steps grounded in your research, plan, and company memory." },
  { step: "05", title: "Run Employee OS", body: "Build checklist from plan, run tasks, and approve external actions before send." },
  { step: "06", title: "Automate & ship", body: "Connect integrations, run automations, and export reports, plans, and decks." },
];

export const PROBLEM = {
  founder: {
    title: "Founders still decide with guesswork.",
    sub: "Most early teams lack analysts, strategy partners, and operators — so validation, planning, and outreach stall.",
  },
  company: {
    title: "B2B teams still buy time they cannot spare.",
    sub: "Consulting is slow and expensive; global tools miss local buyers, regulation, and pricing — while ops stays manual.",
  },
};

export const SOLUTION = {
  founder: {
    title: "One founder OS: research, plan, execute, automate.",
    body: "IIDATECH replaces fragmented docs and agencies with a single workspace that produces sourced research, a real plan, and AI employees that execute with your approval.",
  },
  company: {
    title: "One company OS: audit, intelligence, ops capacity.",
    body: "IIDATECH gives established B2B companies continuous market intelligence, growth planning, and approved automation — so leadership ships decisions faster than consulting cycles.",
  },
};

export const CLIENT_LOGOS = [
  { name: "Pathak Automation Services", src: "/partners/white/pathak.png" },
  { name: "Loop", src: "/partners/loop.png" },
  { name: "Tyoharwale", src: "/partners/white/tyoharwale.png" },
  { name: "JP Infralease", src: "/partners/white/jp-infralease.png" },
  { name: "IIDATECH platform", src: "/marketing/platform-wheel.png" },
];

export type ServiceDetail = {
  id: ToolId;
  slug: string;
  label: string;
  short: string;
  photoId: MarketingPhotoId;
  videoSrc?: string;
  summary: string;
  outcomes: string[];
  whoFor: string[];
  steps: string[];
  faqs: Array<{ q: string; a: string }>;
};

export const SERVICE_DETAILS: ServiceDetail[] = [
  {
    id: "research",
    slug: "research",
    label: "Market Research",
    short: "Research",
    photoId: "market-research",
    videoSrc: "/marketing/videos/research.mp4",
    summary:
      "IIDATECH Market Research turns a niche into a sourced intelligence report — competitors, TAM/SAM/SOM, buyer pain, pricing, and citations you can share with co-founders, investors, or your GTM team.",
    outcomes: [
      "Multi-section report with citations",
      "Competitor and pricing maps",
      "TAM / SAM / SOM framing for your market",
      "Markdown export for decks and memos",
    ],
    whoFor: [
      "Founders validating an idea before spend",
      "B2B teams refreshing category intelligence",
      "Operators preparing investor or board packs",
    ],
    steps: [
      "Create or open a project for your idea or company.",
      "Open Market Research and set topic, industry, and market.",
      "Choose depth and click Generate report.",
      "Review sections, export Markdown, or feed the report into Plan.",
    ],
    faqs: [
      {
        q: "How is this different from generic ChatGPT research?",
        a: "IIDATECH structures the report for founders and B2B operators, ties it to a project vault, and keeps outputs ready for planning and Employee OS — not a one-off chat paste.",
      },
      {
        q: "Can I reuse research across plan and Mentor?",
        a: "Yes. Keep the same project selected so Plan, Mentor, and Employee OS can ground on the latest research artifact.",
      },
    ],
  },
  {
    id: "plan",
    slug: "plan",
    label: "Business Planning",
    short: "Plan",
    photoId: "presentation",
    videoSrc: "/marketing/videos/plan.mp4",
    summary:
      "Business Planning turns research into ICP, GTM, unit economics, and a structured plan you can use for funding, loans, co-founder alignment, or B2B growth roadmaps.",
    outcomes: [
      "Investor- or bank-ready plan structure",
      "ICP and GTM sections linked to research",
      "Financial framing for decisions",
      "Handoff into Employee OS checklists",
    ],
    whoFor: [
      "Founders raising or applying for credit",
      "Established companies building growth plans",
      "Teams that need one shared operating narrative",
    ],
    steps: [
      "Open Plan with the same project as your research.",
      "Choose new-company or existing-company / growth mode.",
      "Use research as input where available.",
      "Click Build Agentic Business Plan and review Plan Output.",
    ],
    faqs: [
      {
        q: "Does the plan stay connected to research?",
        a: "Yes — keep one project selected so research, plan, and execution stay in the same vault.",
      },
      {
        q: "Can Employee OS use the plan?",
        a: "Yes. Build checklist from plan in Employee OS to turn sections into runnable tasks.",
      },
    ],
  },
  {
    id: "execute",
    slug: "execute",
    label: "Employee OS",
    short: "Execute",
    photoId: "collaboration",
    videoSrc: "/marketing/videos/execute.mp4",
    summary:
      "Employee OS is your AI workforce — Taylor (COO) plus specialists that turn plans into tasks, drafts, research follow-ups, and outreach with human approval before anything external sends.",
    outcomes: [
      "Checklist built from your plan",
      "Office-day runs with specialist agents",
      "Approvals before outbound actions",
      "CRM / inbox / deliverable outputs",
    ],
    whoFor: [
      "Founders without a full ops team",
      "B2B companies needing virtual capacity",
      "Managers who want approved automation, not black-box sends",
    ],
    steps: [
      "Open Employee OS and select your project.",
      "Configure Full office, Department, or Employee mode.",
      "Build checklist from plan, then Run next or Run full office day.",
      "Approve tasks in Tasks & Approvals before external send.",
    ],
    faqs: [
      {
        q: "Will agents send emails without me?",
        a: "External actions are designed to sit behind approvals so you stay in control of outreach.",
      },
      {
        q: "How do credits work?",
        a: "Real Employee OS work units consume credits. Demo mode lets you explore without spend.",
      },
    ],
  },
  {
    id: "automate",
    slug: "automate",
    label: "Automation",
    short: "Automate",
    photoId: "analytics",
    videoSrc: "/marketing/videos/automate.mp4",
    summary:
      "Automation closes the loop across CRM, inbox, and reporting so research and outreach do not die in spreadsheets — with credit-metered workflow steps and integrations.",
    outcomes: [
      "Reusable workflows across tools",
      "Lead routing and follow-up packs",
      "Reporting automation for operators",
      "Integration hooks under your project",
    ],
    whoFor: [
      "Founders tired of manual CRM hygiene",
      "B2B teams standardizing department follow-ups",
      "Ops leads connecting HubSpot, Gmail, and reports",
    ],
    steps: [
      "Open Automation and pick a workflow template or blank flow.",
      "Connect tools under Integrations where needed.",
      "Build steps, then run with credits.",
      "Monitor outcomes from the project workspace.",
    ],
    faqs: [
      {
        q: "Do I need paid plans for automation?",
        a: "You can explore with demo and free credits. Paid pricing is finalizing — WhatsApp the team for stage-specific quotes.",
      },
      {
        q: "What can I connect?",
        a: "Use Integrations for LLM keys and optional Gmail / LinkedIn / HubSpot-style connections as enabled in your workspace.",
      },
    ],
  },
  {
    id: "mentor",
    slug: "mentor",
    label: "Mentor",
    short: "Mentor",
    photoId: "strategy-meeting",
    videoSrc: "/marketing/videos/mentor.mp4",
    summary:
      "Mentor is context-aware coaching grounded in your project — research, plan, and company memory — so next steps are specific, not generic advice.",
    outcomes: [
      "Advice tied to your live artifacts",
      "Prioritized next actions",
      "Handoff prompts into Employee OS",
      "Operator coaching for company projects",
    ],
    whoFor: [
      "Founders stuck on what to do next",
      "Managers coaching teams from shared project context",
      "Operators who want grounded, not generic, advice",
    ],
    steps: [
      "Open Mentor with your project selected.",
      "Ask about blockers, priorities, or GTM choices.",
      "Use guidance to refine the plan or research.",
      "Hand work to Taylor / Employee OS when ready to execute.",
    ],
    faqs: [
      {
        q: "Does Mentor know my research?",
        a: "When the same project is selected, Mentor can ground on workspace context instead of starting from zero.",
      },
      {
        q: "Can Mentor trigger execution?",
        a: "You can ask for next steps and hand work into Employee OS flows like run next or build checklist.",
      },
    ],
  },
  {
    id: "gauge",
    slug: "gauge",
    label: "GAUGE Company Audit",
    short: "Gauge",
    photoId: "msme-business",
    videoSrc: "/marketing/videos/gauge.mp4",
    summary:
      "GAUGE is a structured company / idea audit across traction, market fit, operations, and readiness — scored so founders and B2B operators know what to fix before scaling or fundraising.",
    outcomes: [
      "Scored dimensions you can act on",
      "Readiness gaps before hire or raise",
      "Shared report for leadership",
      "Natural handoff into Mentor and Plan",
    ],
    whoFor: [
      "Founders stress-testing an idea",
      "Established companies running a free health audit",
      "Leadership teams aligning on priorities",
    ],
    steps: [
      "Open GAUGE / Company Audit (or start via free company audit signup).",
      "Complete the questionnaire for your stage.",
      "Review scored dimensions and recommended actions.",
      "Share with Mentor or fold gaps into Plan and Employee OS.",
    ],
    faqs: [
      {
        q: "Is the company audit free?",
        a: "You can start a free company audit path from signup. Demo and free credits help you explore while paid pricing finalizes.",
      },
      {
        q: "What happens after the score?",
        a: "Use Mentor for prioritization, Plan for the operating narrative, and Employee OS to execute the fixes.",
      },
    ],
  },
];

export function getServiceBySlug(slug: string): ServiceDetail | undefined {
  return SERVICE_DETAILS.find((s) => s.slug === slug);
}
