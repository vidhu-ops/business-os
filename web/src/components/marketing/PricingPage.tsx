"use client";

import Link from "next/link";
import { Check } from "lucide-react";
import { HumanScene, VideoShowcase } from "./illustrations";
import { WorkspaceEntryLink } from "@/components/WorkspaceEntryLink";
import { usePricingCatalog } from "@/hooks/usePricingCatalog";

type PlanCard = {
  name: string;
  price: string;
  period?: string;
  blurb: string;
  perks: string[];
  featured?: boolean;
  badge?: string;
  cta: { label: string; href: string; primary?: boolean; demo?: boolean };
};

/** Tool-only subscriptions from IIDATECH pricing deck (self-serve in app). */
const TOOL_PLANS: PlanCard[] = [
  {
    name: "Free",
    price: "0",
    period: "to begin",
    blurb: "Validate an idea with real research output before you subscribe.",
    perks: [
      "30 credits on signup (~₹6,000 tool value)",
      "Market research + business plan intake",
      "Reference hub and demo workspace",
      "Community support",
    ],
    cta: { label: "Start free", href: "/login?mode=register" },
  },
  {
    name: "Starter",
    price: "4,999",
    period: "/ month",
    blurb: "Solo founders and early-stage startups — core IIDATECH tools and standard support.",
    featured: true,
    badge: "Self-serve",
    perks: [
      "Unlimited research & plan runs in app",
      "Employee OS with 6 AI agents",
      "OAuth integrations (Gmail, LinkedIn, HubSpot)",
      "Branded PDF exports",
      "Priority email support",
    ],
    cta: { label: "Subscribe", href: "/checkout?plan=growth", primary: true },
  },
  {
    name: "Growth",
    price: "8,999",
    period: "/ month",
    blurb: "Scaling teams — advanced research, AI employee modules, automation builders, and onboarding.",
    perks: [
      "Everything in Starter",
      "Advanced research modules",
      "AI employee & automation builders",
      "Dedicated onboarding",
      "Priority support",
    ],
    cta: { label: "Talk to sales", href: "/#contact" },
  },
  {
    name: "Business",
    price: "12,999",
    period: "/ month",
    blurb: "Growing businesses — full suite, automation templates, workflows, and priority support.",
    perks: [
      "Full platform access",
      "Automation templates & workflows",
      "Team-ready workspace features",
      "Priority support",
      "Custom onboarding",
    ],
    cta: { label: "Talk to sales", href: "/#contact" },
  },
];

/** Done-for-you service packages (pricing deck). */
const SERVICE_PACKAGES: PlanCard[] = [
  {
    name: "Startup Package",
    price: "24,999",
    blurb: "Early-stage businesses launching with AI-powered foundations.",
    featured: true,
    badge: "Bundle save",
    perks: [
      "Quick Research (3–5 sections)",
      "Startup Business Plan",
      "1 AI Employee (single role)",
      "1 Automation workflow",
      "IIDATECH team delivery & QA",
    ],
    cta: { label: "Request package", href: "/#contact", primary: true },
  },
  {
    name: "Scale Package",
    price: "74,999",
    blurb: "Growing businesses scaling operations end-to-end with research, plan, AI team, and automation.",
    perks: [
      "Standard Research (6–10 sections)",
      "Growth Business Plan",
      "Department AI pack (5 employees)",
      "Department automation (up to 5 workflows)",
      "Business ecosystem setup",
      "Dedicated delivery manager",
    ],
    cta: { label: "Request package", href: "/#contact" },
  },
];

/** Credit burn rates in the app (see backend credit_service). */
const CREDIT_ACTIONS = [
  { action: "Market research report", credits: 5, toolFrom: 999, toolTo: 4500 },
  { action: "Business plan generation", credits: 5, toolFrom: 1999, toolTo: 4999 },
  { action: "Employee OS — one department (1 week)", credits: 10, toolFrom: 2000, toolTo: null },
  { action: "Employee OS — full office (1 week)", credits: 50, toolFrom: 25000, toolTo: null },
  { action: "Automation workflow build", credits: 8, toolFrom: 3500, toolTo: null },
  { action: "Automation step run", credits: 8, toolFrom: 3500, toolTo: null },
];

const A_LA_CARTE = [
  { category: "Research", items: [
    { name: "Quick (3–5 sections)", tool: 999, service: 2000 },
    { name: "Standard (6–10 sections)", tool: 1999, service: 3500 },
    { name: "Professional (10–15 sections)", tool: 3500, service: 5000 },
    { name: "Enterprise (20+ sections)", tool: 4500, service: 6000 },
  ]},
  { category: "Business plans", items: [
    { name: "Startup plan", tool: null, service: 1999 },
    { name: "Growth plan", tool: null, service: 2999 },
    { name: "Investor plan", tool: 4999, service: 4999 },
    { name: "Enterprise strategic", tool: null, service: 6999 },
  ]},
  { category: "AI employees", items: [
    { name: "Single employee", tool: 2000, service: 3000 },
    { name: "Department pack (5)", tool: 8000, service: 12000 },
    { name: "Complete workforce (20–30)", tool: 25000, service: 32000 },
  ]},
  { category: "Automations", items: [
    { name: "Single workflow", tool: 3500, service: 4500 },
    { name: "Department suite", tool: 18000, service: 22000 },
    { name: "Company-wide", tool: 50000, service: 70000 },
  ]},
];

const FAQ = [
  {
    q: "How much is one credit worth?",
    a: "Credits map to IIDATECH tool list prices. A 5-credit research run aligns with Quick Research at ₹999 (~₹200/credit). Deeper tiers run ₹400–₹900/credit. Your 30 signup credits are worth roughly ₹6,000 at the Quick Research rate.",
  },
  {
    q: "Tool vs service pricing?",
    a: "Tool prices are self-serve in the IIDATECH workspace. Service prices include expert delivery, QA, and consulting. Complete packages bundle both at a discount.",
  },
  {
    q: "Can I use outputs for bank or visa applications?",
    a: "Yes. Enable application mode in the plan workspace to shape outputs for MSME loans, visas, and investor submissions.",
  },
  {
    q: "Do I need my own API keys?",
    a: "No on paid tool plans — we host AI and search. Bring-your-own keys is supported for advanced Employee OS setups.",
  },
];

function formatInr(amount: number) {
  return new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(amount);
}

function creditRange(toolFrom: number, toolTo: number | null, credits: number) {
  const low = Math.round(toolFrom / credits);
  const high = toolTo ? Math.round(toolTo / credits) : null;
  return high ? `${formatInr(low)}–${formatInr(high)}` : `from ${formatInr(low)}`;
}

function PlanCta({ cta }: { cta: PlanCard["cta"] }) {
  const className = `iid-btn mkt-price-cta ${cta.primary ? "iid-btn-primary" : "iid-btn-ghost"}`;
  if (cta.demo) {
    return <WorkspaceEntryLink className={className}>{cta.label}</WorkspaceEntryLink>;
  }
  return (
    <Link href={cta.href} className={className}>
      {cta.label}
    </Link>
  );
}

function PriceAmount({ price }: { price: string }) {
  if (price === "Custom") return <>Custom</>;
  if (price === "0") {
    return (
      <>
        <span className="mkt-price-currency">&#8377;</span>0
      </>
    );
  }
  return (
    <>
      <span className="mkt-price-currency">&#8377;</span>
      {price}
    </>
  );
}

export function PricingPage() {
  const { catalog } = usePricingCatalog();
  const signupCredits = catalog?.signup_credits ?? 30;
  const baselineInr = catalog?.credit_baseline_inr ?? 200;
  const toolPlans = catalog?.plans?.length
    ? catalog.plans.map((p) => ({
        name: String(p.display_name || p.id),
        price: p.price_label === "Free" ? "0" : String(p.price_label || "").replace(/[^\d,]/g, "") || "Custom",
        period: String(p.period || (p.price_label === "Free" ? "to begin" : "")),
        blurb: String((p.perks as string[])?.[0] || ""),
        perks: (p.perks as string[]) || [],
        featured: p.id === "growth",
        badge: p.billable ? "Self-serve" : p.id === "starter" ? undefined : undefined,
        cta: p.billable
          ? { label: "Subscribe", href: `/checkout?plan=${p.id}`, primary: true }
          : p.id === "starter"
            ? { label: "Start free", href: "/login?mode=register" }
            : { label: "Talk to sales", href: "/#contact" },
      }))
    : TOOL_PLANS;
  const servicePackages = catalog?.service_packages?.length
    ? catalog.service_packages.map((pkg) => ({
        name: String(pkg.name),
        price: String(pkg.price_label || "").replace(/[^\d,]/g, ""),
        blurb: String(pkg.user_type || "").replace(/_/g, " "),
        featured: pkg.id === "startup_package",
        badge: pkg.id === "startup_package" ? "Bundle save" : undefined,
        perks: (pkg.includes as string[]) || [],
        cta: { label: "Request package", href: "/#contact", primary: pkg.id === "startup_package" },
      }))
    : SERVICE_PACKAGES;
  const creditActions = catalog?.research_tiers?.length
    ? [
        ...catalog.research_tiers.map((t) => ({
          action: `${t.label} (${t.sections_label || t.section_count + " sections"})`,
          credits: Number(t.credits),
          toolFrom: Number(t.tool_inr),
          toolTo: Number(t.service_inr) > Number(t.tool_inr) ? Number(t.tool_inr) : null,
        })),
        { action: "Business plan generation", credits: 5, toolFrom: 1999, toolTo: 4999 },
        { action: "Employee OS — one department (1 week)", credits: 10, toolFrom: 2000, toolTo: null },
        { action: "Employee OS — full office (1 week)", credits: 50, toolFrom: 25000, toolTo: null },
        { action: "Automation workflow build", credits: 8, toolFrom: 3500, toolTo: null },
        { action: "Automation step run", credits: 8, toolFrom: 3500, toolTo: null },
      ]
    : CREDIT_ACTIONS;
  const aLaCarte = catalog?.a_la_carte?.length ? catalog.a_la_carte : A_LA_CARTE;
  const creditPacks = (catalog?.credit_packs || []) as Array<{
    id: string;
    credits: number;
    price_label: string;
    blurb?: string;
    per_credit_inr?: number;
  }>;

  return (
    <>
      <section className="mkt-wrap mkt-page-hero">
        <p className="mkt-eyebrow">Pricing</p>
        <h1 className="mkt-page-title">Transparent pricing for every stage.</h1>
        <p className="mkt-lead mkt-page-lead">
          Self-serve tool subscriptions, done-for-you service packages, and credit-based usage — aligned with the IIDATECH pricing overview.
        </p>
      </section>

      <section className="mkt-wrap mkt-section-tight">
        <div className="mkt-section-head">
          <span className="mkt-label">Tool subscriptions</span>
          <h2 className="mkt-h2">Self-serve platform access</h2>
          <p className="mkt-sub">Monthly tool-only plans. Starter (₹4,999/mo) is available for instant checkout in the app.</p>
        </div>
        <div className="mkt-pricing-grid mkt-pricing-grid-4">
          {toolPlans.map((plan) => (
            <article key={plan.name} className={`mkt-price-card ${plan.featured ? "is-featured" : ""}`}>
              {plan.badge ? <span className="mkt-price-badge">{plan.badge}</span> : null}
              <h3 className="mkt-feature-title">{plan.name}</h3>
              <p className="mkt-price">
                <PriceAmount price={plan.price} />
                {plan.period ? <small>{plan.period}</small> : null}
              </p>
              <p className="mkt-feature-body">{plan.blurb}</p>
              <ul className="mkt-price-list">
                {plan.perks.map((perk) => (
                  <li key={perk}>
                    <Check className="h-4 w-4 shrink-0" aria-hidden />
                    <span>{perk}</span>
                  </li>
                ))}
              </ul>
              <PlanCta cta={plan.cta} />
            </article>
          ))}
        </div>
        <p className="mkt-pricing-note">
          <strong>Enterprise</strong> — custom pricing with dedicated account manager, integrations, and SLA-backed support.{" "}
          <Link href="/#contact">Contact sales</Link>.
        </p>
      </section>

      <section className="mkt-wrap mkt-section">
        <div className="mkt-section-head">
          <span className="mkt-label">Complete packages</span>
          <h2 className="mkt-h2">Done-for-you bundles</h2>
          <p className="mkt-sub">Service delivery by the IIDATECH team — significant savings vs buying each item separately.</p>
        </div>
        <div className="mkt-package-grid">
          {servicePackages.map((pkg) => (
            <article key={pkg.name} className={`mkt-price-card mkt-package-card ${pkg.featured ? "is-featured" : ""}`}>
              {pkg.badge ? <span className="mkt-price-badge">{pkg.badge}</span> : null}
              <h3 className="mkt-feature-title">{pkg.name}</h3>
              <p className="mkt-price">
                <PriceAmount price={pkg.price} />
                <small> service</small>
              </p>
              <p className="mkt-feature-body">{pkg.blurb}</p>
              <ul className="mkt-price-list">
                {pkg.perks.map((perk) => (
                  <li key={perk}>
                    <Check className="h-4 w-4 shrink-0" aria-hidden />
                    <span>{perk}</span>
                  </li>
                ))}
              </ul>
              <PlanCta cta={pkg.cta} />
            </article>
          ))}
        </div>
      </section>

      <section className="mkt-wrap mkt-section-tight">
        <div className="mkt-section-head">
          <span className="mkt-label">User stages</span>
          <h2 className="mkt-h2">Who each tier is for</h2>
          <p className="mkt-sub">Credits for exploration, subscriptions for volume, service packages for done-for-you delivery.</p>
        </div>
        <div className="mkt-stage-grid">
          {(catalog?.user_stages || []).map((stage) => (
            <article key={stage.id} className="mkt-faq-card">
              <h3>{stage.label}</h3>
              <p>{stage.description}</p>
            </article>
          ))}
        </div>
      </section>

      {creditPacks.length > 0 ? (
        <section className="mkt-wrap mkt-section-tight">
          <div className="mkt-section-head">
            <span className="mkt-label">Credit packs</span>
            <h2 className="mkt-h2">Buy credits when you need more</h2>
            <p className="mkt-sub">Packs priced at ~₹{baselineInr}/credit (Quick Research baseline).</p>
          </div>
          <div className="mkt-pricing-grid mkt-pricing-grid-3">
            {creditPacks.map((pack) => (
              <article key={String(pack.id)} className="mkt-price-card">
                <h3 className="mkt-feature-title">{pack.credits} credits</h3>
                <p className="mkt-price">
                  <span className="mkt-price-currency">&#8377;</span>
                  {String(pack.price_label || "").replace(/[^\d,]/g, "")}
                </p>
                <p className="mkt-feature-body">{String(pack.blurb || "")}</p>
                <p className="text-xs text-[var(--iid-muted)]">~₹{String(pack.per_credit_inr ?? "")}/credit</p>
                <Link href={`/login?next=${encodeURIComponent(`/checkout?pack=${pack.id}`)}`} className="iid-btn iid-btn-primary mkt-price-cta">
                  Buy credits
                </Link>
              </article>
            ))}
          </div>
        </section>
      ) : null}

      <section className="mkt-wrap mkt-section">
        <div className="mkt-section-head">
          <span className="mkt-label">Credits</span>
          <h2 className="mkt-h2">What each credit is worth</h2>
          <p className="mkt-sub">
            In the app, actions consume credits. We derive credit value from IIDATECH tool list prices ÷ credits used.
            Baseline: <strong>~₹200/credit</strong> (Quick Research ₹999 ÷ 5 credits). Deeper work runs ₹400–₹900/credit.
          </p>
        </div>
        <div className="mkt-credit-summary">
          <div className="mkt-credit-stat">
            <strong>{signupCredits}</strong>
            <span>free signup credits</span>
          </div>
          <div className="mkt-credit-stat">
            <strong>~₹{(signupCredits * baselineInr).toLocaleString("en-IN")}</strong>
            <span>nominal tool value at Quick Research rate</span>
          </div>
          <div className="mkt-credit-stat">
            <strong>6</strong>
            <span>full research runs at 5 credits each</span>
          </div>
        </div>
        <div className="mkt-table-wrap">
          <table className="mkt-catalog-table">
            <thead>
              <tr>
                <th>Action in app</th>
                <th>Credits</th>
                <th>Tool list price</th>
                <th>Implied ₹/credit</th>
              </tr>
            </thead>
            <tbody>
              {creditActions.map((row) => (
                <tr key={row.action}>
                  <td>{row.action}</td>
                  <td>{row.credits}</td>
                  <td>
                    {row.toolTo
                      ? `${formatInr(row.toolFrom)} – ${formatInr(row.toolTo)}`
                      : `from ${formatInr(row.toolFrom)}`}
                  </td>
                  <td>{creditRange(row.toolFrom, row.toolTo, row.credits)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="mkt-wrap mkt-section">
        <div className="mkt-section-head">
          <span className="mkt-label">À la carte</span>
          <h2 className="mkt-h2">Individual service & tool prices</h2>
          <p className="mkt-sub">All research tiers include the 33-topic deep-dive framework. Service prices include expert delivery.</p>
        </div>
        <div className="mkt-catalog-grid">
          {(aLaCarte as typeof A_LA_CARTE).map((group) => (
            <div key={group.category} className="mkt-catalog-group">
              <h3 className="mkt-feature-title">{group.category}</h3>
              <div className="mkt-table-wrap">
                <table className="mkt-catalog-table mkt-catalog-table-compact">
                  <thead>
                    <tr>
                      <th>Item</th>
                      <th>Tool</th>
                      <th>Service</th>
                    </tr>
                  </thead>
                  <tbody>
                    {group.items.map((item) => (
                      <tr key={item.name}>
                        <td>{item.name}</td>
                        <td>{item.tool != null ? formatInr(item.tool) : "—"}</td>
                        <td>{item.service != null ? formatInr(item.service) : "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="mkt-wrap mkt-section">
        <div className="mkt-split">
          <HumanScene variant="founder" />
          <div className="mkt-split-copy">
            <span className="mkt-label">What you get</span>
            <h2 className="mkt-h2">Every plan includes the full OS.</h2>
            <p className="mkt-sub">
              Research, planning, reference tools, and execution live in one workspace. Start free with credits, subscribe for unlimited self-serve, or book a done-for-you package.
            </p>
            <Link href="/how-it-works" className="iid-btn iid-btn-primary">
              See how it works
            </Link>
          </div>
        </div>
      </section>

      <section className="mkt-wrap mkt-section">
        <VideoShowcase
          title="Watch a 2-minute walkthrough"
          subtitle="From signup to your first sourced market report."
          videoId="LXb3EKWsInQ"
        />
      </section>

      <section className="mkt-wrap mkt-section mkt-section-last">
        <div className="mkt-section-head">
          <span className="mkt-label">FAQ</span>
          <h2 className="mkt-h2">Common questions</h2>
        </div>
        <div className="mkt-faq-grid mkt-faq-grid-2">
          {FAQ.map((item) => (
            <article key={item.q} className="mkt-faq-card">
              <h3>{item.q}</h3>
              <p>{item.a}</p>
            </article>
          ))}
        </div>
        <p className="mkt-pricing-contact">
          Sales: <a href="tel:+919545403431">+91 95454 03431</a> · <a href="mailto:sales@iidatech.com">sales@iidatech.com</a>
        </p>
      </section>
    </>
  );
}