import { SITE_WHATSAPP } from "@/lib/site";
import type { MarketingPhotoId } from "./marketingImages";

const WHATSAPP_INTRO_MESSAGE =
  "Hi IIDATECH — I'd like to skip the self-serve flow and chat about what fits my business.";

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
  photoId: MarketingPhotoId;
  accent: string;
  cardVideo: string;
  founder: { title: string; body: string; inApp: string; output: string };
  company: { title: string; body: string; inApp: string; output: string };
  videoId?: string;
  videoSrc?: string;
}> = [
  {
    id: "research",
    label: "Market Research",
    short: "Research",
    photoId: "market-research",
    accent: "#0B5FFF",
    cardVideo: "/marketing/videos/tool-research.mp4",
    videoSrc: "/marketing/videos/research.mp4",
    founder: {
      title: "Market research for founders",
      body: "Validate your idea with sourced competitor maps, TAM/SAM/SOM, buyer pain, and pricing evidence — before you spend on ads or inventory.",
      inApp: "Open Market Research → pick your project → click Generate report. You get a multi-section report with citations you can share with co-founders or investors.",
      output: "A sourced market report with competitors, buyers, and sizing — ready to share.",
    },
    company: {
      title: "Market intelligence for growing companies",
      body: "Keep category, competitor, and pricing intelligence current for leadership, sales, and board updates — without hiring a full research bench.",
      inApp: "Create or open a company project → run Standard/Professional research → export the report for GTM and BD teams.",
      output: "Fresh category intelligence your sales and leadership teams can use.",
    },
  },
  {
    id: "plan",
    label: "Business Planning",
    short: "Plan",
    photoId: "presentation",
    accent: "#0D9488",
    cardVideo: "/marketing/videos/tool-plan.mp4",
    videoSrc: "/marketing/videos/plan.mp4",
    founder: {
      title: "Structured business plans for funding conversations",
      body: "Turn research into ICP, GTM, unit economics, and a structured plan you can use for funding, lending, and investor discussions.",
      inApp: "Open Plan → click Build Agentic Business Plan. The plan stays linked to the same project as your research.",
      output: "A structured business plan linked to your research — ready for your next funding conversation.",
    },
    company: {
      title: "Growth and operating plans for B2B teams",
      body: "Produce growth plans, expansion theses, and operating roadmaps that sales, ops, and finance can execute against.",
      inApp: "Use an existing-company project → generate a Growth/Investor plan → hand tasks to Employee OS.",
      output: "A growth or operating plan your teams can execute against.",
    },
  },
  {
    id: "execute",
    label: "Employee OS",
    short: "Execute",
    photoId: "collaboration",
    accent: "#EA580C",
    cardVideo: "/marketing/videos/tool-execute.mp4",
    videoSrc: "/marketing/videos/execute.mp4",
    founder: {
      title: "AI employees that execute your plan",
      body: "Taylor (COO) plus specialists turn the plan into tasks — research follow-ups, leads, decks, and outreach — with approvals before anything external sends.",
      inApp: "Open Employee OS → Build checklist from plan → Run next / Run full office day → Approve tasks in Tasks & Approvals.",
      output: "Approved tasks, drafts, and outreach — without hiring a full ops team.",
    },
    company: {
      title: "Virtual ops capacity for B2B companies",
      body: "Staff recurring research, CRM enrichment, outreach drafts, and department workflows without expanding headcount overnight.",
      inApp: "Configure department scope → hire agents → run office actions and approve outbound from the war room.",
      output: "Recurring research, CRM, and outreach capacity under your approval.",
    },
  },
  {
    id: "automate",
    label: "Automation",
    short: "Automate",
    photoId: "analytics",
    accent: "#0284C7",
    cardVideo: "/marketing/videos/tool-automate.mp4",
    videoSrc: "/marketing/videos/automate.mp4",
    founder: {
      title: "Automations that close the loop",
      body: "Build workflows across CRM, inbox, and reporting so research and outreach do not die in spreadsheets.",
      inApp: "Open Automation → build a workflow → run steps with credits → connect tools under Integrations.",
      output: "Workflows that keep CRM and follow-ups moving without spreadsheets.",
    },
    company: {
      title: "Department automation for B2B stacks",
      body: "Standardize lead routing, reporting packs, and follow-ups across HubSpot, Gmail, and your internal tools.",
      inApp: "Use Automation builders with team templates → run steps → monitor outcomes in the project workspace.",
      output: "Standardized lead routing and reporting across your tools.",
    },
  },
  {
    id: "mentor",
    label: "Mentor",
    short: "Mentor",
    photoId: "strategy-meeting",
    accent: "#059669",
    cardVideo: "/marketing/videos/tool-mentor.mp4",
    videoSrc: "/marketing/videos/mentor.mp4",
    founder: {
      title: "A mentor that knows your project",
      body: "Ask what to do next, get grounded advice from your research and plan, and hand work to Taylor when you are ready to execute.",
      inApp: "Open Mentor → chat about your idea or blockers → say run next or build checklist to trigger Employee OS.",
      output: "Clear next steps grounded in your project — not generic advice.",
    },
    company: {
      title: "Operator guidance for company projects",
      body: "Leadership and managers get context-aware coaching tied to company memory, goals, and live workspace artifacts.",
      inApp: "Open Mentor with your company project selected → ask for priorities → hand execution to Taylor.",
      output: "Operator coaching tied to your company's live workspace.",
    },
  },
  {
    id: "gauge",
    label: "GAUGE Company Audit",
    short: "Gauge",
    photoId: "msme-business",
    accent: "#E11D48",
    cardVideo: "/marketing/videos/tool-gauge.mp4",
    videoSrc: "/marketing/videos/gauge.mp4",
    founder: {
      title: "Score your idea before you scale",
      body: "Run a GAUGE company audit on traction, market fit, operations, and readiness — so you know what to fix before fundraising or hiring.",
      inApp: "Open GAUGE / Company Audit → answer the questionnaire → review scored dimensions and recommended next actions.",
      output: "A scored audit showing what to fix before you scale or raise.",
    },
    company: {
      title: "Company health audits for B2B operators",
      body: "Benchmark growth, ops, GTM, and financial readiness with a structured GAUGE audit your leadership team can act on.",
      inApp: "Start a free company audit → complete GAUGE inputs → share the scored report with leadership and Mentor.",
      output: "A leadership-ready health report across growth, ops, and GTM.",
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
    pipe: [
      { label: "Research", href: "/services/research" },
      { label: "Plan", href: "/services/plan" },
      { label: "Execute", href: "/services/execute" },
      { label: "Automate", href: "/services/automate" },
    ],
    primaryCta: { href: "/login?mode=register", label: "Start free" },
    secondaryCta: { href: "/app/research?project=demo_readonly", label: "See demo", demo: true },
    whoForTitle: "Built for founders and early-stage startups",
    whoForBody:
      "Solo founders, co-founder teams, and pre-seed to Series A startups who need investor-grade research, a real business plan, and AI employees that execute — without consulting fees.",
    headline: "The business OS for founders building from idea to execution.",
    trustLine: "Free credits · No credit card · 5-minute setup",
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
    pipe: [
      { label: "Audit", href: "/services/gauge" },
      { label: "Research", href: "/services/research" },
      { label: "Plan", href: "/services/plan" },
      { label: "Operate", href: "/services/execute" },
    ],
    primaryCta: { href: "/login?intent=audit&mode=register", label: "Start free" },
    secondaryCta: { href: "/app/research?project=demo_readonly", label: "See demo", demo: true },
    whoForTitle: "Built for established B2B companies and MSME operators",
    whoForBody:
      "Growth, GTM, and ops teams that need continuous market intelligence, operating plans, outbound support, and approved automation — without standing up a large strategy bench.",
    headline: "The business OS for B2B companies that need research, plans, and ops capacity.",
    trustLine: "Free credits · No credit card · 5-minute setup",
    aboutTitle: "About IIDATECH for B2B companies",
    aboutBody:
      "Use IIDATECH as your business operating layer: GAUGE health audits, competitor and pricing intelligence, growth plans, Mentor for operators, and Employee OS agents that work under human approval.",
  },
} as const;


/** Prefer lighter footage for major plates; darker clips are avoided on home. */
export const SECTION_VIDEOS = {
  steps: "/marketing/videos/section-steps.mp4",
  services: "/marketing/videos/section-services.mp4",
  about: "/marketing/videos/section-about.mp4",
  /** Prefer a light plate behind Process */
  process: "/marketing/videos/section-steps.mp4",
  why: "/marketing/videos/section-why.mp4",
  pricing: "/marketing/videos/section-pricing.mp4",
  integrations: "/marketing/videos/section-services.mp4",
} as const;

/** Hero copy + background video per Individual / Company toggle. */
export const HERO_WIX = {
  brand: "IIDA",
  founder: {
    eyebrow: "Validating a business idea",
    headline: "Turn your idea into a real business",
    pipe: [
      { label: "RESEARCH", href: "/services/research" },
      { label: "PLAN", href: "/services/plan" },
      { label: "EXECUTE", href: "/services/execute" },
      { label: "AUTOMATE", href: "/services/automate" },
    ],
    subline:
      "IIDATECH researches your market, builds your business strategy, and turns it into an execution plan — with AI employees to help you act.",
    trustLine: "30 free credits · No credit card · ~6 research runs or mix of tools",
    videoSrc: "/marketing/videos/hero-individual.mp4",
    cta: { href: "/login?mode=register", label: "Analyze my business" },
  },
  company: {
    eyebrow: "Growing an existing business",
    headline: "Grow what you already run",
    pipe: [
      { label: "AUDIT", href: "/services/gauge" },
      { label: "RESEARCH", href: "/services/research" },
      { label: "PLAN", href: "/services/plan" },
      { label: "OPERATE", href: "/services/execute" },
    ],
    subline: "",
    trustLine: "30 free credits · No credit card · Start with a free company audit",
    videoSrc: "/marketing/videos/hero-company.mp4",
    cta: { href: "/login?intent=audit&mode=register", label: "Analyze my business" },
  },
} as const;

export const HOME_STEPS = [
  {
    step: "01",
    title: "Research",
    body:
      "Know your market, customers, competitors, pricing, and opportunity before you spend money — with sourced evidence you can review and share.",
    photoId: "market-research" as const,
    frameSrc: "/marketing/frames/research.png",
    frameAlt: "IIDATECH market research report with citations",
  },
  {
    step: "02",
    title: "Business Plan",
    body:
      "Structured plans for funding, lending, and investor discussions — built from your research, not a blank template.",
    photoId: "presentation" as const,
    frameSrc: "/marketing/frames/plan.png",
    frameAlt: "IIDATECH business plan output",
  },
  {
    step: "03",
    title: "Execution Plan",
    body:
      "A step-by-step roadmap with hiring, vendors, and actions your team — or Taylor — can run with your approval.",
    photoId: "collaboration" as const,
    frameSrc: "/marketing/frames/execute.png",
    frameAlt: "IIDATECH Employee OS task board",
  },
];

export const PROCESS_STEPS = [
  {
    step: "01",
    title: "Register",
    body:
      "Register your name and email with us and get 30 free credits to try out anything you like on our platform.",
  },
  {
    step: "02",
    title: "Generate",
    body:
      "Input your idea and the fields required (4 fields max) for the tool you want to use from the 6 tools we have, and press generate.",
  },
  {
    step: "03",
    title: "Get results",
    body:
      "Your result will be generated within a minute — whatever you need, right at your fingertips.",
  },
] as const;

export const WHY_US = [
  { title: "Instant", body: "Structured reports in minutes — not weeks of consulting back-and-forth." },
  {
    title: "Your data, your account",
    body: "Project data stays in your workspace for the features you use. We do not use your business data to train public AI models.",
  },
  { title: "Time saver", body: "Focus on growth — let IIDATECH handle research structure and first drafts." },
  { title: "Evidence-first", body: "See sources, findings, and what they mean — not just a wall of AI text." },
  { title: "Focused", body: "Answers tied to your idea, market, and stage — not generic startup advice." },
  { title: "Affordable", body: "Start free with credits. Scale when the outputs earn their keep." },
] as const;

export type VisitorGoalId = "validate" | "market" | "launch" | "grow" | "expand" | "execute" | "whatsapp";

export const VISITOR_GOALS: Array<{
  id: VisitorGoalId;
  emoji: string;
  title: string;
  question: string;
  href: string;
  cta: string;
  external?: boolean;
}> = [
  {
    id: "validate",
    emoji: "💡",
    title: "Validate a business idea",
    question: "Should I pursue this opportunity?",
    href: "/app/research",
    cta: "Start with research",
  },
  {
    id: "market",
    emoji: "📊",
    title: "Understand my market",
    question: "Who competes, who buys, and what can I charge?",
    href: "/app/research",
    cta: "See market research",
  },
  {
    id: "launch",
    emoji: "🚀",
    title: "Launch a business",
    question: "I need a plan and first steps to go live.",
    href: "/app/plan",
    cta: "Build my plan",
  },
  {
    id: "grow",
    emoji: "📈",
    title: "Grow an existing business",
    question: "Where are my growth opportunities?",
    href: "/app/audit",
    cta: "Run a GAUGE audit",
  },
  {
    id: "expand",
    emoji: "🌎",
    title: "Enter a new market",
    question: "Is this market attractive and how do we enter?",
    href: "/app/research",
    cta: "Research a market",
  },
  {
    id: "execute",
    emoji: "🤖",
    title: "Get execution help",
    question: "I need tasks done — research, outreach, follow-ups.",
    href: "/app/team",
    cta: "Meet Taylor",
  },
  {
    id: "whatsapp",
    emoji: "💬",
    title: "Want to skip the hassle and text us?",
    question: "Message us on WhatsApp — we'll talk through your goal and what IIDATECH can do.",
    href: `${SITE_WHATSAPP}?text=${encodeURIComponent(WHATSAPP_INTRO_MESSAGE)}`,
    cta: "Chat on WhatsApp",
    external: true,
  },
];

export const DEMO_CASE_STUDY = {
  title: "See what IIDATECH produces — before you sign up",
  idea: "Premium healthy snack brand in Pune",
  inputs: [
    { label: "Idea", value: "Healthy snacks for working professionals" },
    { label: "Location", value: "Pune, India" },
    { label: "Customer", value: "Office workers, gyms, premium retail" },
    { label: "Budget", value: "₹10 lakh to start" },
  ],
  outputs: [
    { label: "Market opportunity", value: "Sized with segment focus" },
    { label: "Competition", value: "Key players and positioning gaps" },
    { label: "Customers", value: "Segments with highest willingness to pay" },
    { label: "Pricing", value: "Range grounded in local comparables" },
    { label: "GTM", value: "First 90-day launch moves" },
    { label: "Business plan", value: "Submission-ready sections linked to the same project" },
    { label: "Mentor", value: "Next-step guidance grounded in your research and plan" },
    { label: "Employee OS", value: "Taylor + specialists — tasks, drafts, and approvals" },
    { label: "Automation", value: "Optional workflows across CRM, inbox, and reporting" },
    { label: "Dashboard", value: "Your command center — credits, projects, and every tool in one place" },
  ],
  dashboardNote:
    "The live demo opens your dashboard first. From there you can explore sample research, business plan, Mentor, Employee OS, and GAUGE — without signing up.",
  demoHref: "/app/dashboard?project=demo_readonly",
} as const;

export const PRODUCT_STORY = [
  { step: "Input", body: '"I want to launch a premium skincare brand in India."' },
  { step: "IIDATECH", body: "Market · Competition · Customers · Pricing · Risks · GTM · Financials" },
  { step: "Your plan", body: "Structured business plan linked to the same project" },
  { step: "Your roadmap", body: "Execution checklist with owners and approvals" },
  { step: "AI employees", body: "Taylor can start distributor research, drafts, and follow-ups" },
] as const;

export const CHATGPT_COMPARE = {
  chatgpt: [
    "One-off answers in a chat thread",
    "No persistent project context",
    "You structure the output yourself",
    "No execution or approvals workflow",
  ],
  iidatech: [
    "Structured research → plan → execution workflow",
    "Sourced reports with citations in a project vault",
    "Business-specific sections — not generic essays",
    "Taylor + integrations when you are ready to act",
  ],
} as const;

export const TAYLOR_EXAMPLE = {
  goal: "Find 100 potential distributors in Maharashtra for my healthy snack brand.",
  steps: [
    "Taylor researches the category and builds a qualified company list.",
    "You review segments, pricing fit, and outreach angles.",
    "Taylor drafts emails and CRM entries — nothing sends without your approval.",
    "Approved outreach goes out; follow-ups land back in your workspace.",
  ],
} as const;

export const EVIDENCE_EXAMPLE = {
  finding: "Premium healthy-snack retail in Pune is growing fastest in office-adjacent micro-markets.",
  source: "Industry reports + competitor pricing scan",
  updated: "2026",
  implication: "Lead with corporate pantry pilots and gym partnerships before broad retail listings.",
} as const;

export const PRODUCT_UI_SHOTS = [
  { src: "/marketing/frames/research.png", alt: "Market research report", caption: "Research report with sections and citations" },
  { src: "/marketing/frames/plan.png", alt: "Business plan workspace", caption: "Business plan tied to your project" },
  { src: "/marketing/frames/execute.png", alt: "Employee OS office", caption: "Taylor and specialists in Employee OS" },
  { src: "/marketing/frames/mentor.png", alt: "Mentor chat", caption: "Mentor grounded in your project" },
  { src: "/marketing/frames/gauge.png", alt: "GAUGE company audit", caption: "GAUGE audit scores and gaps" },
] as const;

export const CASE_STUDIES = [
  {
    title: "Founder validating a D2C idea",
    before: "Unsure whether the niche was big enough to quit a day job.",
    after: "Sized the segment, mapped 8 competitors, and prioritized one beachhead channel.",
    note: "Early operator example — names published when customers approve.",
  },
  {
    title: "MSME entering a new city",
    before: "Expansion felt like guesswork on pricing and partners.",
    after: "Local pricing band, partner shortlist, and a 90-day rollout checklist.",
    note: "Representative workflow — not a paid case study yet.",
  },
  {
    title: "B2B team refreshing category intel",
    before: "Sales used outdated competitor slides.",
    after: "Shared research vault + quarterly refresh cadence in IIDATECH.",
    note: "Illustrates company-mode usage.",
  },
] as const;

/** Static credit guide — mirrors backend pricing_catalog defaults. */
export const CREDIT_GUIDE = [
  { action: "Quick market research", credits: 5 },
  { action: "Business plan generation", credits: 5 },
  { action: "Mentor conversation turn", credits: 1 },
  { action: "Employee OS task", credits: 1 },
] as const;

export const BY_THE_NUMBERS = [
  { value: "6", label: "Core tools in one workspace" },
  { value: "20+", label: "Industries covered in research" },
  { value: "30", label: "Free signup credits to start" },
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
  {
    name: "Pathak Automation Services",
    src: "/partners/pathak.png",
    srcOnDark: "/partners/pathak.png",
  },
  {
    name: "Loop",
    src: "/partners/loop.png",
    srcOnDark: "/partners/loop.png",
  },
  {
    name: "Tyoharwale",
    src: "/partners/tyoharwale.png",
    // Color mark stays readable on dark tiles; monochrome white asset is incomplete.
    srcOnDark: "/partners/tyoharwale.png",
  },
  {
    name: "JP Infralease",
    src: "/partners/jp-infralease.png",
    srcOnDark: "/partners/white/jp-infralease.png",
  },
  {
    name: "Elements Boutique",
    // Root SVG is light-on-transparent; white/ folder is dark text for light surfaces.
    src: "/partners/white/elements-boutique.svg",
    srcOnDark: "/partners/elements-boutique.svg",
  },
];

/** Product integrations shown on the marketing homepage (OAuth + LLM / research keys). */
export const INTEGRATION_LOGOS = [
  { name: "Gmail", src: "/integrations/gmail.svg", group: "apps" },
  { name: "Google", src: "/integrations/google.svg", group: "apps" },
  { name: "Google Drive", src: "/integrations/google-drive.svg", group: "apps" },
  { name: "Google Calendar", src: "/integrations/google-calendar.svg", group: "apps" },
  { name: "LinkedIn", src: "/integrations/linkedin.svg", group: "apps" },
  { name: "HubSpot", src: "/integrations/hubspot.svg", group: "apps" },
  { name: "Canva", src: "/integrations/canva.svg", group: "apps" },
  { name: "Notion", src: "/integrations/notion.svg", group: "apps" },
  { name: "Slack", src: "/integrations/slack.svg", group: "apps" },
  { name: "Perplexity", src: "/integrations/perplexity.svg", group: "models" },
  { name: "OpenAI", src: "/integrations/openai.svg", group: "models" },
  { name: "Claude", src: "/integrations/anthropic.svg", group: "models" },
  { name: "Gemini", src: "/integrations/gemini.svg", group: "models" },
  { name: "DeepSeek", src: "/integrations/deepseek.svg", group: "models" },
  { name: "Groq", src: "/integrations/groq.svg", group: "models" },
] as const;

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
