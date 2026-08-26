import type { Audience } from "./audienceContent";

export type AboutAudienceCopy = {
  label: string;
  heroTitle: string;
  heroLead: string;
  whatIs: { title: string; body: string; bullets: string[] };
  results: { title: string; items: Array<{ title: string; body: string }> };
  problem: { title: string; body: string; points: string[] };
  whyUs: { title: string; points: Array<{ title: string; body: string }> };
  whoFor: { title: string; body: string; fits: string[]; notFor: string[] };
  howItHelps: { title: string; steps: Array<{ title: string; body: string }> };
  faqs: Array<{ q: string; a: string }>;
  ctaLabel: string;
  ctaHref: string;
};

export const ABOUT_SHARED = {
  brandName: "IIDATECH",
  oneLiner:
    "IIDATECH is a business OS that helps founders and established B2B companies research markets, build plans, mentor decisions, execute with AI employees, and automate follow-through — in one workspace.",
  pillars: [
    { title: "Research", body: "Sourced market intelligence: competitors, buyers, sizing, and pricing evidence." },
    { title: "Plan", body: "ICP, GTM, and structured business or growth plans tied to the same project." },
    { title: "Mentor", body: "Context-aware guidance grounded in your research, plan, and company memory." },
    { title: "Execute", body: "Employee OS agents turn plans into tasks with human approvals before outbound." },
    { title: "Automate", body: "Optional workflows across CRM, inbox, and reporting so work does not stall in spreadsheets." },
    { title: "GAUGE", body: "A structured company-health audit across growth, ops, GTM, and readiness." },
  ],
};

export const ABOUT_BY_AUDIENCE: Record<Audience, AboutAudienceCopy> = {
  founder: {
    label: "Founders",
    heroTitle: "About IIDATECH for founders",
    heroLead:
      "IIDATECH is the business OS for startup founders who need investor-grade research, a real plan, and AI employees that execute — without hiring a full strategy team.",
    whatIs: {
      title: "What IIDATECH is",
      body:
        "IIDATECH is not a single chatbot or a generic document template. It is a connected workspace where your idea becomes research, a plan, mentorship, and approved execution inside one project vault.",
      bullets: [
        "AI market research reports with competitor, TAM/SAM/SOM, buyer, and pricing framing",
        "Business plan generation linked to the same project as your research",
        "Mentor coaching that knows your artifacts",
        "Employee OS (Taylor + specialists) for tasks, outreach drafts, and follow-ups",
        "Optional automation and integrations when you are ready to scale ops",
      ],
    },
    results: {
      title: "What results founders can expect",
      items: [
        {
          title: "Faster validation",
          body: "Move from a vague idea to a structured market view before you spend on ads, inventory, or hiring.",
        },
        {
          title: "Shareable research and plans",
          body: "Produce reports and plans you can send to co-founders, advisors, investors, or lenders.",
        },
        {
          title: "Execution without a full team",
          body: "Turn the plan into Employee OS tasks and keep human approval on anything external.",
        },
        {
          title: "Clear next steps",
          body: "Use Mentor to decide what to do next, then hand work to Taylor instead of starting from a blank chat.",
        },
      ],
    },
    problem: {
      title: "The problem IIDATECH solves for founders",
      body:
        "Most early teams lack analysts, strategy partners, and operators. Validation, planning, and outreach stall — or get outsourced into slow, expensive consulting cycles.",
      points: [
        "No in-house research bench",
        "Business plans rebuilt from scratch in docs and decks",
        "Advice that ignores your actual project context",
        "Outreach and follow-ups trapped in spreadsheets",
        "Hard to show progress to investors without a coherent narrative",
      ],
    },
    whyUs: {
      title: "Why founders choose IIDATECH",
      points: [
        {
          title: "One project vault",
          body: "Research, plan, Mentor, and Employee OS stay linked — so outputs compound instead of fragmenting.",
        },
        {
          title: "Built for action",
          body: "The product is designed around buttons and workflows founders actually click, not abstract dashboards.",
        },
        {
          title: "Human approvals",
          body: "External actions are meant to sit behind approvals so you stay in control of outreach.",
        },
        {
          title: "Start free",
          body: "Free credits and a live demo let you test the OS before you commit to paid capacity.",
        },
      ],
    },
    whoFor: {
      title: "Who IIDATECH is for",
      body: "Built for founders and early-stage startups who need speed and structure without consulting fees.",
      fits: [
        "Solo founders and co-founder teams",
        "Pre-seed to Series A startups",
        "Founders preparing investor, bank, or partner materials",
        "Builders who need research + plan + execution in one place",
      ],
      notFor: [
        "Teams that only want a one-off chat answer with no workspace",
        "Enterprises needing a custom procurement-only suite on day one (talk to us for Enterprise)",
      ],
    },
    howItHelps: {
      title: "How IIDATECH helps founders step by step",
      steps: [
        { title: "Create a project", body: "Capture your idea, industry, and market in one vault." },
        { title: "Generate research", body: "Run Market Research for a sourced intelligence report." },
        { title: "Build the plan", body: "Turn research into ICP, GTM, and a structured business plan." },
        { title: "Ask Mentor", body: "Get next-step advice grounded in your live artifacts." },
        { title: "Execute with Employee OS", body: "Build checklists, run tasks, and approve outbound work." },
      ],
    },
    faqs: [
      {
        q: "What is IIDATECH in simple terms?",
        a: "IIDATECH is a business operating system for founders: research, plan, mentor, execute, and automate in one workspace.",
      },
      {
        q: "Is IIDATECH only for tech startups?",
        a: "No. Founders across SaaS, services, D2C, healthcare, and other niches use it — research and planning adapt to your industry and market.",
      },
      {
        q: "Can IIDATECH replace a consulting firm?",
        a: "It replaces a lot of fragmented research and planning work for early teams. Complex legal, accounting, or regulated advice still needs specialists — IIDATECH helps you arrive prepared.",
      },
      {
        q: "Do I need my own API keys to start?",
        a: "No for free and demo exploration. Bring-your-own LLM keys and OAuth apps are optional for advanced routing and live outreach.",
      },
      {
        q: "How is IIDATECH different from ChatGPT?",
        a: "IIDATECH structures work into projects, reports, plans, approvals, and Employee OS tasks — so outputs stay connected and executable, not lost in a chat thread.",
      },
    ],
    ctaLabel: "Start free",
    ctaHref: "/login?mode=register",
  },
  company: {
    label: "B2B companies",
    heroTitle: "About IIDATECH for established B2B companies",
    heroLead:
      "IIDATECH is the business OS for MSMEs and B2B growth teams that need market intelligence, operating plans, GAUGE audits, and approved AI capacity — without standing up a large strategy bench.",
    whatIs: {
      title: "What IIDATECH is for B2B operators",
      body:
        "IIDATECH is an operating layer for established companies: continuous intelligence, growth planning, Mentor for managers, and Employee OS agents that work under human approval.",
      bullets: [
        "GAUGE company audits to score growth, ops, GTM, and readiness",
        "Market research for category, competitor, and pricing updates",
        "Growth and investor-style plans leadership can execute against",
        "Employee OS capacity for research follow-ups, CRM enrichment, and outreach drafts",
        "Optional automation across HubSpot, Gmail, and reporting packs",
      ],
    },
    results: {
      title: "What results B2B teams can expect",
      items: [
        {
          title: "Faster leadership decisions",
          body: "Keep competitor and pricing intelligence current without waiting on a consulting sprint.",
        },
        {
          title: "Shared operating narrative",
          body: "Align sales, ops, and finance around one plan and one project memory.",
        },
        {
          title: "Approved virtual capacity",
          body: "Use Employee OS for recurring work while keeping outbound under human approval.",
        },
        {
          title: "Clear company health signal",
          body: "Run a GAUGE audit to surface gaps before hiring, expansion, or fundraising.",
        },
      ],
    },
    problem: {
      title: "The problem IIDATECH solves for B2B companies",
      body:
        "Consulting is slow and expensive. Global tools miss local buyers, regulation, and pricing — while ops stays manual and teams stay stretched.",
      points: [
        "No dedicated research or RevOps bench",
        "Plans that go stale after the workshop",
        "CRM and inbox hygiene eating operator time",
        "Leadership updates rebuilt from scratch each quarter",
        "Automation risk without approval controls",
      ],
    },
    whyUs: {
      title: "Why B2B companies choose IIDATECH",
      points: [
        {
          title: "Built for operators",
          body: "Framed for MSMEs and B2B teams that need outcomes, not another unused SaaS seat.",
        },
        {
          title: "GAUGE + execution",
          body: "Audit readiness, then fold gaps into Plan, Mentor, and Employee OS instead of stopping at a score.",
        },
        {
          title: "Approval-first automation",
          body: "External actions are designed to wait for human approval when the product presents that step.",
        },
        {
          title: "India-first, globally useful",
          body: "Local market context matters for many customers, with a workspace that still serves cross-border teams.",
        },
      ],
    },
    whoFor: {
      title: "Who IIDATECH is for in B2B",
      body: "Built for established companies, MSME operators, and growth teams that need continuous intelligence and ops capacity.",
      fits: [
        "MSME and mid-market B2B operators",
        "GTM, BD, and ops managers",
        "Leadership teams preparing board or lender updates",
        "Companies that want AI capacity with approval controls",
      ],
      notFor: [
        "Buyers who only want unmanaged auto-send bots with no approvals",
        "One-off market scans with no ongoing operating use",
      ],
    },
    howItHelps: {
      title: "How IIDATECH helps B2B teams step by step",
      steps: [
        { title: "Start with GAUGE or a company project", body: "Score readiness or open an existing-company workspace." },
        { title: "Refresh market intelligence", body: "Run research for category, competitor, and pricing updates." },
        { title: "Build the growth plan", body: "Produce an operating narrative sales and ops can execute." },
        { title: "Coach with Mentor", body: "Prioritize with context from company memory and live artifacts." },
        { title: "Scale with Employee OS", body: "Staff recurring tasks and approve outbound before send." },
      ],
    },
    faqs: [
      {
        q: "What is a GAUGE audit?",
        a: "GAUGE is a structured company-health score across growth, operations, GTM, and readiness — so leadership knows what to fix before scaling.",
      },
      {
        q: "Can established companies use IIDATECH without being a startup?",
        a: "Yes. The established-company path is built for operating businesses that need intelligence, plans, and approved AI capacity.",
      },
      {
        q: "Does IIDATECH integrate with CRM and email?",
        a: "Optional OAuth and keys support tools like Gmail, LinkedIn, and HubSpot for advanced live outreach. Free and demo exploration work without BYO keys.",
      },
      {
        q: "Is IIDATECH useful for India MSMEs?",
        a: "Yes. Many workflows are India-first in pricing and market framing, while remaining useful for B2B teams operating across regions.",
      },
      {
        q: "How is this different from hiring consultants?",
        a: "IIDATECH gives continuous workspace capacity you can re-run, approve, and automate — instead of a one-time slide deck that goes stale.",
      },
    ],
    ctaLabel: "Start free",
    ctaHref: "/login?intent=audit&mode=register",
  },
};

export const ABOUT_SEO_FAQS = [
  ...ABOUT_BY_AUDIENCE.founder.faqs.slice(0, 3),
  ...ABOUT_BY_AUDIENCE.company.faqs.slice(0, 3),
];
