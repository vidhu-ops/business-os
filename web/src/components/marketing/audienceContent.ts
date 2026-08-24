export type Audience = "founder" | "company";

export type ToolId =
  | "research"
  | "plan"
  | "execute"
  | "automate"
  | "mentor"
  | "brand";

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
    id: "brand",
    label: "Brand & Deliverables",
    short: "Brand",

    videoSrc: "/marketing/videos/brand.mp4",
    founder: {
      title: "Founder-ready decks and one-pagers",
      body: "Package research and plans into pitch decks, memos, and branded exports you can send to investors and partners.",
      inApp: "From plan/research outputs → export PDF or open Reference tools to structure decks and one-pagers.",
    },
    company: {
      title: "Client and board-ready deliverables",
      body: "Produce consistent, branded packs for clients, partners, and internal reviews from the same source of truth.",
      inApp: "Export reports and plans → reuse Reference and deck flows for recurring stakeholder updates.",
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
  { name: "Partner brand", src: "/partners/white/loop.png" },
  { name: "Tyoharwale", src: "/partners/white/tyoharwale.png" },
];
