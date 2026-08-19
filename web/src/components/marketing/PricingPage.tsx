"use client";

import Link from "next/link";
import { Check } from "lucide-react";
import { HumanScene, VideoShowcase } from "./illustrations";
import { WorkspaceEntryLink } from "@/components/WorkspaceEntryLink";
import { usePricingCatalog } from "@/hooks/usePricingCatalog";

const WHATSAPP = "https://wa.me/919545403431";
const TEL = "tel:+919545403431";
const PHONE_LABEL = "+91 95454 03431";

type PlanCard = {
  name: string;
  blurb: string;
  perks: string[];
  featured?: boolean;
  badge?: string;
};

const TOOL_PLANS: PlanCard[] = [
  {
    name: "Free",
    blurb: "Validate an idea with real research output — free credits while paid plans are finalizing.",
    badge: "Available now",
    featured: true,
    perks: [
      "Free signup credits to explore the product",
      "Market research + business plan intake",
      "Demo workspace and Mentor guidance",
      "Community support",
    ],
  },
  {
    name: "Starter",
    blurb: "Solo founders and early-stage startups — core IIDATECH tools when paid billing opens.",
    perks: [
      "Unlimited research & plan runs in app",
      "Employee OS with AI agents",
      "OAuth integrations (Gmail, LinkedIn, HubSpot)",
      "Branded PDF exports",
      "Priority email support",
    ],
  },
  {
    name: "Growth",
    blurb: "Scaling teams — advanced research, AI employee modules, and automation builders.",
    perks: [
      "Everything in Starter",
      "Advanced research modules",
      "AI employee & automation builders",
      "Dedicated onboarding",
      "Priority support",
    ],
  },
  {
    name: "Business",
    blurb: "Growing businesses — full suite, automation templates, workflows, and priority support.",
    perks: [
      "Full platform access",
      "Automation templates & workflows",
      "Team-ready workspace features",
      "Priority support",
      "Custom onboarding",
    ],
  },
];

const SERVICE_PACKAGES: PlanCard[] = [
  {
    name: "Startup Package",
    blurb: "Early-stage businesses launching with AI-powered foundations.",
    featured: true,
    badge: "Talk to us",
    perks: [
      "Quick Research",
      "Startup Business Plan",
      "1 AI Employee (single role)",
      "1 Automation workflow",
      "IIDATECH team delivery & QA",
    ],
  },
  {
    name: "Scale Package",
    blurb: "Growing businesses scaling operations end-to-end with research, plan, AI team, and automation.",
    perks: [
      "Standard Research",
      "Growth Business Plan",
      "Department AI pack",
      "Department automation",
      "Business ecosystem setup",
      "Dedicated delivery manager",
    ],
  },
];

const FAQ = [
  {
    q: "When will paid plans open?",
    a: "Paid pricing is coming soon. Until then, enjoy the demo and free signup credits. Call or WhatsApp us to talk about your stage and we will place you on the right plan.",
  },
  {
    q: "Can I still use the product today?",
    a: "Yes. Sign up free, run the demo, and spend your free credits on research, plans, Mentor, and Employee OS exploration.",
  },
  {
    q: "How do I get a custom quote?",
    a: `Call or WhatsApp ${PHONE_LABEL}. Tell us whether you need self-serve tools or a done-for-you package.`,
  },
  {
    q: "Do I need my own API keys?",
    a: "Not for the free/demo experience. Bring-your-own keys is supported for advanced Employee OS setups.",
  },
];

function ContactCtas({ primary = false }: { primary?: boolean }) {
  return (
    <div className="mkt-price-cta-row flex flex-wrap gap-2">
      <a href={WHATSAPP} target="_blank" rel="noreferrer" className={`iid-btn ${primary ? "iid-btn-primary" : "iid-btn-ghost"} mkt-price-cta`}>
        WhatsApp {PHONE_LABEL}
      </a>
      <a href={TEL} className="iid-btn iid-btn-ghost mkt-price-cta">
        Call now
      </a>
    </div>
  );
}

function ComingSoonPrice() {
  return (
    <p className="mkt-price">
      <span className="mkt-price-coming">Price coming soon</span>
      <small>Enjoy demo & free credits till then</small>
    </p>
  );
}

export function PricingPage() {
  const { catalog } = usePricingCatalog();
  const signupCredits = catalog?.signup_credits ?? 30;

  const toolPlans: PlanCard[] = catalog?.plans?.length
    ? [
        TOOL_PLANS[0],
        ...catalog.plans
          .filter((p) => String(p.id).toLowerCase() !== "free" && String(p.display_name || "").toLowerCase() !== "free")
          .map((p) => ({
            name: String(p.display_name || p.id),
            blurb: String(
              TOOL_PLANS.find((t) => t.name === p.display_name)?.blurb ||
                (p.perks as string[])?.[0] ||
                "",
            ),
            perks: (p.perks as string[]) || [],
            featured: p.id === "growth" || p.id === "starter",
            badge: "Coming soon",
          })),
      ]
    : TOOL_PLANS;

  const servicePackages = catalog?.service_packages?.length
    ? catalog.service_packages.map((pkg) => ({
        name: String(pkg.name),
        blurb: String(pkg.user_type || "").replace(/_/g, " "),
        featured: pkg.id === "startup_package",
        badge: "Talk to us",
        perks: (pkg.includes as string[]) || [],
      }))
    : SERVICE_PACKAGES;

  return (
    <>
      <section className="mkt-wrap mkt-page-hero">
        <p className="mkt-eyebrow">Pricing</p>
        <h1 className="mkt-page-title">Pricing coming soon.</h1>
        <p className="mkt-lead mkt-page-lead">
          Paid plans and packages are being finalized. Until then, enjoy the demo and free credits — or talk to us for a quote.
        </p>
        <div className="mt-6 flex flex-wrap gap-3">
          <a href={WHATSAPP} target="_blank" rel="noreferrer" className="iid-btn iid-btn-primary">
            WhatsApp {PHONE_LABEL}
          </a>
          <a href={TEL} className="iid-btn iid-btn-ghost">
            Call {PHONE_LABEL}
          </a>
          <Link href="/login?mode=register" className="iid-btn iid-btn-ghost">
            Start free
          </Link>
          <WorkspaceEntryLink className="iid-btn iid-btn-ghost">See demo</WorkspaceEntryLink>
        </div>
      </section>

      <section className="mkt-wrap mkt-section-tight">
        <div className="mkt-credit-summary">
          <div className="mkt-credit-stat">
            <strong>{signupCredits}</strong>
            <span>free signup credits</span>
          </div>
          <div className="mkt-credit-stat">
            <strong>Demo</strong>
            <span>full product tour anytime</span>
          </div>
          <div className="mkt-credit-stat">
            <strong>Talk</strong>
            <span>call / WhatsApp for pricing</span>
          </div>
        </div>
      </section>

      <section className="mkt-wrap mkt-section-tight">
        <div className="mkt-section-head">
          <span className="mkt-label">Tool subscriptions</span>
          <h2 className="mkt-h2">Self-serve platform access</h2>
          <p className="mkt-sub">Plan names and inclusions stay — paid prices arrive soon. Use free credits and the demo meanwhile.</p>
        </div>
        <div className="mkt-pricing-grid mkt-pricing-grid-4">
          {toolPlans.map((plan) => (
            <article key={plan.name} className={`mkt-price-card ${plan.featured ? "is-featured" : ""}`}>
              {plan.badge ? <span className="mkt-price-badge">{plan.badge}</span> : null}
              <h3 className="mkt-feature-title">{plan.name}</h3>
              {plan.name === "Free" ? (
                <p className="mkt-price">
                  <span className="mkt-price-currency">&#8377;</span>0
                  <small>to begin</small>
                </p>
              ) : (
                <ComingSoonPrice />
              )}
              <p className="mkt-feature-body">{plan.blurb}</p>
              <ul className="mkt-price-list">
                {plan.perks.map((perk) => (
                  <li key={perk}>
                    <Check className="h-4 w-4 shrink-0" aria-hidden />
                    <span>{perk}</span>
                  </li>
                ))}
              </ul>
              {plan.name === "Free" ? (
                <Link href="/login?mode=register" className="iid-btn iid-btn-primary mkt-price-cta">
                  Start free
                </Link>
              ) : (
                <ContactCtas primary={Boolean(plan.featured)} />
              )}
            </article>
          ))}
        </div>
        <p className="mkt-pricing-note">
          <strong>Enterprise</strong> — custom scope, integrations, and SLA.{" "}
          <a href={WHATSAPP} target="_blank" rel="noreferrer">
            WhatsApp us
          </a>{" "}
          or call <a href={TEL}>{PHONE_LABEL}</a>.
        </p>
      </section>

      <section className="mkt-wrap mkt-section">
        <div className="mkt-section-head">
          <span className="mkt-label">Complete packages</span>
          <h2 className="mkt-h2">Done-for-you bundles</h2>
          <p className="mkt-sub">Service delivery by the IIDATECH team. Prices coming soon — talk to us for a quote.</p>
        </div>
        <div className="mkt-package-grid">
          {servicePackages.map((pkg) => (
            <article key={pkg.name} className={`mkt-price-card mkt-package-card ${pkg.featured ? "is-featured" : ""}`}>
              {pkg.badge ? <span className="mkt-price-badge">{pkg.badge}</span> : null}
              <h3 className="mkt-feature-title">{pkg.name}</h3>
              <ComingSoonPrice />
              <p className="mkt-feature-body">{pkg.blurb}</p>
              <ul className="mkt-price-list">
                {pkg.perks.map((perk) => (
                  <li key={perk}>
                    <Check className="h-4 w-4 shrink-0" aria-hidden />
                    <span>{perk}</span>
                  </li>
                ))}
              </ul>
              <ContactCtas primary={Boolean(pkg.featured)} />
            </article>
          ))}
        </div>
      </section>

      <section className="mkt-wrap mkt-section-tight">
        <div className="mkt-section-head">
          <span className="mkt-label">Credits & à la carte</span>
          <h2 className="mkt-h2">Usage pricing coming soon</h2>
          <p className="mkt-sub">
            Credit packs and individual research / plan / employee / automation rates will publish with paid billing. Until then, use free credits and the demo — or WhatsApp {PHONE_LABEL} for a custom quote.
          </p>
        </div>
        <div className="mkt-price-card" style={{ maxWidth: "40rem" }}>
          <ComingSoonPrice />
          <p className="mkt-feature-body mt-3">
            We will publish transparent credit burn rates and pack prices here. Prefer talking it through? Call or WhatsApp the number below.
          </p>
          <ContactCtas primary />
        </div>
      </section>

      <section className="mkt-wrap mkt-section">
        <div className="mkt-split">
          <HumanScene variant="founder" />
          <div className="mkt-split-copy">
            <span className="mkt-label">What you get</span>
            <h2 className="mkt-h2">Every plan includes the full OS.</h2>
            <p className="mkt-sub">
              Research, planning, Mentor, and Employee OS live in one workspace. Start free with credits, tour the demo, then talk to us when you are ready to subscribe.
            </p>
            <div className="flex flex-wrap gap-2">
              <Link href="/how-it-works" className="iid-btn iid-btn-primary">
                See how it works
              </Link>
              <a href={WHATSAPP} target="_blank" rel="noreferrer" className="iid-btn iid-btn-ghost">
                WhatsApp sales
              </a>
            </div>
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
          Call / WhatsApp: <a href={TEL}>{PHONE_LABEL}</a> ·{" "}
          <a href={WHATSAPP} target="_blank" rel="noreferrer">
            Open WhatsApp
          </a>
        </p>
      </section>
    </>
  );
}