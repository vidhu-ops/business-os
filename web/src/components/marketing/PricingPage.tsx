import Link from "next/link";
import { Check } from "lucide-react";
import { HumanScene, VideoShowcase } from "./illustrations";
import { WorkspaceEntryLink } from "@/components/WorkspaceEntryLink";

const PLANS = [
  {
    name: "Starter",
    price: "0",
    currency: "INR",
    period: "to begin",
    blurb: "For founders validating an idea with real research output.",
    cta: "Start free",
    featured: false,
    perks: [
      "30 free credits on signup",
      "1 market research report",
      "Business plan intake + export",
      "Reference hub (Plan It Out and Business Plan)",
      "Community support",
    ],
  },
  {
    name: "Growth",
    price: "4,999",
    currency: "INR",
    period: "/ month",
    blurb: "For MSMEs and small teams shipping weekly decisions.",
    cta: "Start Growth",
    featured: true,
    perks: [
      "Unlimited research runs",
      "Agentic business plans + GAUGE for existing cos.",
      "Employee OS with 6 AI agents",
      "OAuth integrations (Gmail, LinkedIn, HubSpot)",
      "Priority email support",
      "Branded PDF exports",
    ],
  },
  {
    name: "Scale",
    price: "Custom",
    currency: "",
    period: "",
    blurb: "For agencies, accelerators, and portfolio operators.",
    cta: "Talk to us",
    featured: false,
    perks: [
      "Multi-workspace and team seats",
      "Done-for-you research sprints",
      "Custom automations and workflows",
      "Dedicated onboarding",
      "SLA and phone support",
      "White-label deliverables",
    ],
  },
];

const FAQ = [
  {
    q: "What is a credit?",
    a: "One credit covers a focused research generation pass. Growth removes per-run limits so your team can iterate freely.",
  },
  {
    q: "Can I use this for bank or visa applications?",
    a: "Yes. Enable application mode in the plan workspace to shape outputs for MSME loans, visas, and investor submissions.",
  },
  {
    q: "Do I need my own API keys?",
    a: "No on Growth. We host AI and search. Bring-your-own keys is supported for advanced Employee OS setups.",
  },
];

export function PricingPage() {
  return (
    <>
      <section className="mkt-wrap mkt-page-hero">
        <p className="mkt-eyebrow">Pricing</p>
        <h1 className="mkt-page-title">Plans that grow with your business.</h1>
        <p className="mkt-lead mkt-page-lead">
          Start free with real deliverables. Upgrade when you need Employee OS, integrations, and unlimited research.
        </p>
      </section>

      <section className="mkt-wrap mkt-section-tight">
        <div className="mkt-pricing-grid">
          {PLANS.map((plan) => (
            <article key={plan.name} className={`mkt-price-card ${plan.featured ? "is-featured" : ""}`}>
              {plan.featured ? <span className="mkt-price-badge">Most popular</span> : null}
              <h2 className="mkt-feature-title">{plan.name}</h2>
              <p className="mkt-price">
                {plan.price === "Custom" ? (
                  plan.price
                ) : (
                  <>
                    {plan.currency === "INR" ? <span className="mkt-price-currency">&#8377;</span> : null}
                    {plan.price}
                  </>
                )}
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
              {plan.name === "Scale" ? (
                <Link href="/#contact" className="iid-btn iid-btn-ghost mkt-price-cta">
                  {plan.cta}
                </Link>
              ) : (
                <WorkspaceEntryLink
                  className={`iid-btn mkt-price-cta ${plan.featured ? "iid-btn-primary" : "iid-btn-ghost"}`}
                >
                  {plan.cta}
                </WorkspaceEntryLink>
              )}
            </article>
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
              Research, planning, reference tools, and execution live in one workspace. You only pay for volume and team features as you scale.
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
        <div className="mkt-faq-grid">
          {FAQ.map((item) => (
            <article key={item.q} className="mkt-faq-card">
              <h3>{item.q}</h3>
              <p>{item.a}</p>
            </article>
          ))}
        </div>
      </section>
    </>
  );
}
