import { SITE_EMAIL, SITE_PHONE, SITE_URL } from "@/lib/site";

/** Core business-intent phrases we want associated with IIDATECH. */
export const CORE_BUSINESS_KEYWORDS = [
  "IIDATECH",
  "business OS",
  "market research for founders",
  "business research",
  "founder market research",
  "new business growth",
  "business consultation",
  "business planning",
  "startup business plan",
  "AI business plan",
  "business growth platform",
  "MSME market research",
  "MSME growth",
  "startup research tools",
  "company growth audit",
  "B2B market research",
  "founder tools India",
  "business automation for startups",
  "Employee OS",
  "GAUGE audit",
] as const;

export type SeoTopic = {
  slug: string;
  title: string;
  h1: string;
  description: string;
  keywords: string[];
  intro: string;
  sections: Array<{ heading: string; body: string }>;
  faqs: Array<{ q: string; a: string }>;
  primaryCta: { href: string; label: string };
  relatedService?: string;
};

export const SEO_TOPICS: SeoTopic[] = [
  {
    slug: "market-research-for-founders",
    title: "Market Research for Founders",
    h1: "Market research for founders — without an analyst team",
    description:
      "Run market research for founders on IIDATECH: niche sizing, competitors, pricing signals, and sourced reports so you can validate before you build.",
    keywords: [
      "market research for founders",
      "founder market research",
      "startup market research",
      "business research",
      "MSME market research",
    ],
    intro:
      "Founders need market research that is fast, sourced, and decision-ready — not a 6-week agency deck. IIDATECH turns your niche into a structured research report you can act on inside the same workspace.",
    sections: [
      {
        heading: "What founder market research should answer",
        body: "Who buys, how big the opportunity is, who already competes, what buyers pay, and which risks matter before you hire or spend. IIDATECH structures these into clear sections with source context.",
      },
      {
        heading: "From research to plan and execution",
        body: "Unlike standalone research tools, IIDATECH keeps the report attached to your project so you can build a business plan, get business consultation from Mentor, and execute with Employee OS.",
      },
      {
        heading: "Built for India-first and global niches",
        body: "Start with India markets or expand — set country, industry, and cities so business research stays relevant to your go-to-market.",
      },
    ],
    faqs: [
      {
        q: "Is this market research for startups or only large companies?",
        a: "IIDATECH is built for founders, startups, and MSMEs first — while still useful for B2B teams that need continuous market research.",
      },
      {
        q: "Can I try market research before paying?",
        a: "Yes. Start free, open the live demo workspace, and explore a sample completed market research report.",
      },
    ],
    primaryCta: { href: "/services/research", label: "Explore market research" },
    relatedService: "research",
  },
  {
    slug: "business-consultation",
    title: "Business Consultation for Founders",
    h1: "Business consultation grounded in your project — not generic advice",
    description:
      "Get business consultation on IIDATECH Mentor: step-by-step guidance using your market research, business plan, GAUGE audit, and organizational memory.",
    keywords: [
      "business consultation",
      "founder consultation",
      "startup business advice",
      "AI business consultation",
      "business mentor for founders",
    ],
    intro:
      "Most business consultation is expensive and disconnected from your files. IIDATECH Mentor coaches from your live project context — research, plan, goals, and next actions.",
    sections: [
      {
        heading: "Consultation that knows your business",
        body: "Mentor reads organizational memory, research readiness, and plan status so recommendations match what you are actually building.",
      },
      {
        heading: "From advice to approved action",
        body: "Pair consultation with Employee OS so suggested outreach, research follow-ups, and ops tasks can be drafted and approved — not stuck in chat.",
      },
      {
        heading: "When to use business consultation on IIDATECH",
        body: "Use it when you need sequencing: what to finish this week, which GTM move to prioritize, or how to turn research into a growth plan.",
      },
    ],
    faqs: [
      {
        q: "Is Mentor a replacement for a human consultant?",
        a: "It is an always-on business consultation layer for founders. Many teams still use specialists for fundraising or legal — IIDATECH handles day-to-day operating guidance.",
      },
      {
        q: "Does consultation work for existing companies?",
        a: "Yes. Established B2B companies can combine GAUGE audits with Mentor for growth-focused consultation.",
      },
    ],
    primaryCta: { href: "/services/mentor", label: "Explore Mentor consultation" },
    relatedService: "mentor",
  },
  {
    slug: "new-business-growth",
    title: "New Business Growth Platform",
    h1: "New business growth: research, plan, and execute in one OS",
    description:
      "Accelerate new business growth with IIDATECH — market research, business planning, consultation, Employee OS, and automation for founders and MSMEs.",
    keywords: [
      "new business growth",
      "business growth platform",
      "startup growth tools",
      "MSME growth",
      "founder growth OS",
    ],
    intro:
      "New business growth stalls when research lives in docs, plans live in slides, and execution lives nowhere. IIDATECH is one business OS so growth work stays connected.",
    sections: [
      {
        heading: "Validate before you scale spend",
        body: "Use market research and GAUGE audits to find the real constraint — demand, pricing, retention, or ops — before you buy ads.",
      },
      {
        heading: "Plan that becomes operating work",
        body: "Business planning on IIDATECH is not a PDF graveyard. Move from plan sections into Employee OS tasks and automation workflows.",
      },
      {
        heading: "Growth for founders and B2B teams",
        body: "Whether you are launching a new business or expanding an existing company, keep intelligence, consultation, and execution in one vault.",
      },
    ],
    faqs: [
      {
        q: "Can IIDATECH help with new business ideas?",
        a: "Yes. Start with a niche, generate market research, then convert findings into a business plan and growth sequence.",
      },
      {
        q: "Is this only for tech startups?",
        a: "No. IIDATECH supports SaaS, services, retail, healthcare, logistics, and other founder niches.",
      },
    ],
    primaryCta: { href: "/how-it-works", label: "See the growth workflow" },
  },
  {
    slug: "startup-business-plan",
    title: "Startup Business Plan Software",
    h1: "Startup business plan software built from your research",
    description:
      "Build a startup business plan on IIDATECH from market research and company context — investor-ready structure without starting from a blank page.",
    keywords: [
      "startup business plan",
      "business planning software",
      "AI business plan",
      "business plan for founders",
      "new business planning",
    ],
    intro:
      "Blank templates waste weeks. IIDATECH generates business planning drafts from your market research, then lets you refine and execute.",
    sections: [
      {
        heading: "Plans that inherit research",
        body: "Connect your report so market, competition, and pricing context flow into the business plan instead of being rewritten from memory.",
      },
      {
        heading: "New company and existing company paths",
        body: "Founders building something new and operators improving an existing company both get structured planning — including GAUGE-forward plans.",
      },
      {
        heading: "After the plan: execution",
        body: "Hand off into Employee OS and automation so the business plan becomes weekly work, not shelfware.",
      },
    ],
    faqs: [
      {
        q: "Is the business plan investor-ready?",
        a: "IIDATECH produces structured, readable plans you can refine for investors, partners, or internal operators.",
      },
      {
        q: "Do I need research first?",
        a: "Research improves plan quality, but you can also start from uploads and notes inside the Business Plan workspace.",
      },
    ],
    primaryCta: { href: "/services/plan", label: "Explore business planning" },
    relatedService: "plan",
  },
  {
    slug: "business-research",
    title: "Business Research Platform",
    h1: "Business research that stays attached to your company workspace",
    description:
      "Do business research on IIDATECH: competitors, demand, pricing, and market structure — then continue into planning, consultation, and growth execution.",
    keywords: [
      "business research",
      "business research platform",
      "market and business research",
      "competitor research for startups",
      "B2B business research",
    ],
    intro:
      "Business research should reduce uncertainty, not create more documents. IIDATECH keeps research inside the same business OS you use to plan and operate.",
    sections: [
      {
        heading: "Research for decisions, not decoration",
        body: "Get sectioned reports you can download, share, and reuse for planning and consultation.",
      },
      {
        heading: "Continuous intelligence for B2B teams",
        body: "Established companies use IIDATECH for recurring business research and GAUGE health checks without spinning up a new consulting engagement each quarter.",
      },
      {
        heading: "Connected to automation",
        body: "Once research clarifies the ICP, automation and Employee OS can help draft outreach and operating loops.",
      },
    ],
    faqs: [
      {
        q: "How is this different from ChatGPT for business research?",
        a: "IIDATECH is a project vault with research, planning, consultation, and execution tools — not a one-off chat thread.",
      },
      {
        q: "Can teams collaborate on research?",
        a: "Projects live in the workspace with related plans, Mentor context, and Employee OS activity.",
      },
    ],
    primaryCta: { href: "/services/research", label: "Start with business research" },
    relatedService: "research",
  },
  {
    slug: "msme-business-growth",
    title: "MSME Business Growth Tools",
    h1: "MSME business growth tools for operators who wear every hat",
    description:
      "IIDATECH helps MSMEs with market research, business consultation, planning, and automation — practical business growth tools without a large analyst team.",
    keywords: [
      "MSME business growth",
      "MSME tools",
      "small business growth platform",
      "MSME market research",
      "business tools for MSMEs",
    ],
    intro:
      "MSMEs need business growth tools that fit real operating constraints: limited time, limited team, and a need for clear next steps.",
    sections: [
      {
        heading: "Research and audit without a big team",
        body: "Run market research or a GAUGE company audit to see what to fix before spending more on growth.",
      },
      {
        heading: "Consultation that sequences the week",
        body: "Mentor helps MSME founders prioritize: memory, GTM, retention, or ops — using the project they already opened.",
      },
      {
        heading: "Automation for repetitive work",
        body: "Connect apps and run workflows so growth tasks do not die in spreadsheets.",
      },
    ],
    faqs: [
      {
        q: "Is IIDATECH only for tech MSMEs?",
        a: "No. Services, retail, clinics, logistics, and software MSMEs can all run research and growth planning.",
      },
      {
        q: "Can I start free?",
        a: "Yes. Create an account with free credits or browse the demo workspace first.",
      },
    ],
    primaryCta: { href: "/pricing", label: "See free and paid options" },
  },
  {
    slug: "ai-business-planning",
    title: "AI Business Planning",
    h1: "AI business planning for founders who need speed and structure",
    description:
      "Use AI business planning on IIDATECH to draft plans from research, refine them, and connect planning to consultation and Employee OS execution.",
    keywords: [
      "AI business planning",
      "AI business plan",
      "AI business plan generator",
      "AI planning for startups",
      "business plan AI India",
    ],
    intro:
      "AI business planning is useful only when outputs stay editable, sourced from your context, and linked to execution. That is the IIDATECH design.",
    sections: [
      {
        heading: "Context-aware drafts",
        body: "Plans draw from market research and company inputs instead of generic filler paragraphs.",
      },
      {
        heading: "Human approval stays in the loop",
        body: "Founders edit the plan and approve Employee OS actions — AI accelerates, it does not auto-spend your reputation.",
      },
      {
        heading: "India-ready workflow",
        body: "Set India or other markets, industries, and cities so AI business planning stays local to your GTM.",
      },
    ],
    faqs: [
      {
        q: "Will the AI invent fake market numbers?",
        a: "IIDATECH emphasizes structured research and transparent report sections. Always review claims before investor use.",
      },
      {
        q: "Can I export the plan?",
        a: "Yes — readable plan views and downloads are part of the planning workflow.",
      },
    ],
    primaryCta: { href: "/services/plan", label: "Try AI business planning" },
    relatedService: "plan",
  },
  {
    slug: "company-growth-audit",
    title: "Company Growth Audit (GAUGE)",
    h1: "Company growth audit with GAUGE — score what to fix next",
    description:
      "Run a company growth audit on IIDATECH GAUGE: score financials, customers, and GTM readiness, then turn gaps into a forward business plan.",
    keywords: [
      "company growth audit",
      "business growth audit",
      "GAUGE audit",
      "company health score",
      "B2B growth assessment",
    ],
    intro:
      "A company growth audit should tell you what to fix before you scale spend. GAUGE scores the business and points to the next operating moves.",
    sections: [
      {
        heading: "Clear scores, clear priorities",
        body: "See category scores and focus items — churn tracking, CAC by channel, runway, and more — written for operators.",
      },
      {
        heading: "From audit to forward plan",
        body: "Existing companies can continue into a GAUGE forward plan instead of restarting strategy from scratch.",
      },
      {
        heading: "Pair with consultation",
        body: "Mentor uses audit context so business consultation stays tied to the real gaps in the company.",
      },
    ],
    faqs: [
      {
        q: "Who should run a GAUGE audit?",
        a: "Founders of existing companies and B2B operators who need a structured growth readiness check.",
      },
      {
        q: "Is there a sample audit?",
        a: "Yes. Open the demo workspace and browse a sample completed GAUGE audit.",
      },
    ],
    primaryCta: { href: "/services/gauge", label: "Explore GAUGE audit" },
    relatedService: "gauge",
  },
];

export function getSeoTopic(slug: string): SeoTopic | undefined {
  return SEO_TOPICS.find((t) => t.slug === slug);
}

export function organizationJsonLd() {
  return {
    "@type": "Organization",
    "@id": `${SITE_URL}/#organization`,
    name: "IIDATECH",
    url: SITE_URL,
    email: SITE_EMAIL,
    telephone: SITE_PHONE.replace(/\s/g, ""),
    description:
      "Business OS for founders and B2B companies — market research, business planning, business consultation, new business growth, Employee OS, and automation.",
    areaServed: ["IN", "US", "GB", "AE", "SG"],
    knowsAbout: [...CORE_BUSINESS_KEYWORDS],
    contactPoint: [
      {
        "@type": "ContactPoint",
        contactType: "customer support",
        email: SITE_EMAIL,
        telephone: "+919545403431",
        availableLanguage: ["English", "Hindi"],
      },
    ],
  };
}

export function websiteJsonLd() {
  return {
    "@type": "WebSite",
    "@id": `${SITE_URL}/#website`,
    name: "IIDATECH",
    url: SITE_URL,
    publisher: { "@id": `${SITE_URL}/#organization` },
    inLanguage: "en",
  };
}

export function softwareJsonLd() {
  return {
    "@type": "SoftwareApplication",
    "@id": `${SITE_URL}/#software`,
    name: "IIDATECH Business Ecosystem",
    applicationCategory: "BusinessApplication",
    operatingSystem: "Web",
    url: SITE_URL,
    offers: {
      "@type": "Offer",
      price: "0",
      priceCurrency: "INR",
      description: "Free signup with demo access and credits.",
    },
    featureList: [
      "Market research for founders",
      "Business planning and AI business plans",
      "Business consultation with Mentor",
      "New business growth workflows",
      "Employee OS AI workforce",
      "Business automation",
      "GAUGE company growth audit",
    ],
    keywords: CORE_BUSINESS_KEYWORDS.join(", "),
  };
}

export function faqJsonLd(faqs: Array<{ q: string; a: string }>) {
  return {
    "@type": "FAQPage",
    mainEntity: faqs.map((faq) => ({
      "@type": "Question",
      name: faq.q,
      acceptedAnswer: { "@type": "Answer", text: faq.a },
    })),
  };
}

export function breadcrumbJsonLd(items: Array<{ name: string; path: string }>) {
  return {
    "@type": "BreadcrumbList",
    itemListElement: items.map((item, index) => ({
      "@type": "ListItem",
      position: index + 1,
      name: item.name,
      item: `${SITE_URL}${item.path}`,
    })),
  };
}

export function graphJsonLd(nodes: object[]) {
  return {
    "@context": "https://schema.org",
    "@graph": nodes,
  };
}
