"use client";

import Link from "next/link";
import { Check } from "lucide-react";
import { WorkspaceEntryLink } from "@/components/WorkspaceEntryLink";
import { usePricingCatalog } from "@/hooks/usePricingCatalog";
import { SITE_PHONE, SITE_PHONE_TEL, SITE_WHATSAPP } from "@/lib/site";

const FAQ = [
  {
    q: "When will paid plans open?",
    a: "Paid pricing is coming soon. Until then, enjoy the demo and free signup credits. WhatsApp or email us to talk about your stage.",
  },
  {
    q: "Can I still use the product today?",
    a: "Yes. Start free, run the demo, and spend free credits on research, plans, Mentor, and Employee OS exploration.",
  },
  {
    q: "Do I need my own API keys?",
    a: "No for free and demo use — IIDATECH credits cover core research, plan, Mentor, and Employee OS exploration. Bring-your-own LLM keys and OAuth (Gmail, LinkedIn, HubSpot) are optional for advanced live outreach and custom model routing.",
  },
  {
    q: "How is my data handled?",
    a: "Account and workspace data power your projects only. We do not sell personal data. See the Privacy Policy for retention, deletion, and security practices.",
  },
  {
    q: "What happens to my data if I cancel?",
    a: "You can stop anytime. On cancellation or a deletion request we delete or anonymize personal data within a reasonable period unless law requires longer retention. Email hello@iidatech.com to request deletion.",
  },
  {
    q: "What powers the outputs?",
    a: "IIDATECH combines structured product workflows with large language models and sourced research pipelines. Optional BYO keys let advanced users choose their own model providers.",
  },
  {
    q: "How do I get a custom quote?",
    a: `Call or WhatsApp ${SITE_PHONE}. Tell us whether you need self-serve tools or a done-for-you package.`,
  },
];

export function PricingPage() {
  const { catalog } = usePricingCatalog();
  const signupCredits = catalog?.signup_credits ?? 30;

  return (
    <>
      <section className="mkt-wrap mkt-page-hero">
        <p className="mkt-eyebrow">Pricing</p>
        <h1 className="mkt-page-title">Simple pricing. Start free.</h1>
        <p className="mkt-lead mkt-page-lead">
          Free credits are live now. Paid and Enterprise options are talk-to-us while we finalize numbers. Currency shown in
          INR for India-first billing; other regions available on request.
        </p>
        <div className="mt-6 flex flex-wrap gap-3">
          <Link href="/login?mode=register" className="iid-btn iid-btn-primary">
            Start free
          </Link>
          <WorkspaceEntryLink className="iid-btn iid-btn-ghost">See demo</WorkspaceEntryLink>
        </div>
      </section>

      <section className="mkt-wrap mkt-section">
        <div className="mkt-pricing-grid mkt-pricing-grid-3">
          <article className="mkt-price-card is-featured">
            <span className="mkt-price-badge">Available now</span>
            <h2 className="mkt-feature-title">Free</h2>
            <p className="mkt-price">
              <span className="mkt-price-currency">&#8377;</span>0<small>to begin</small>
            </p>
            <p className="mkt-feature-body">
              Explore Research, Plan, Mentor, and Employee OS with {signupCredits} signup credits and a live demo workspace.
            </p>
            <ul className="mkt-price-list">
              {[
                "Research, Plan, Mentor, Employee OS access",
                "Demo workspace",
                "No credit card required",
                "Optional integrations later",
              ].map((perk) => (
                <li key={perk}>
                  <Check className="h-4 w-4 shrink-0" aria-hidden />
                  <span>{perk}</span>
                </li>
              ))}
            </ul>
            <Link href="/login?mode=register" className="iid-btn iid-btn-primary mkt-price-cta">
              Start free
            </Link>
          </article>

          <article className="mkt-price-card">
            <span className="mkt-price-badge">Talk to us</span>
            <h2 className="mkt-feature-title">Paid plans</h2>
            <p className="mkt-price">
              <span className="mkt-price-coming">Starting from — talk to us</span>
              <small>Indicative INR pricing while final numbers publish</small>
            </p>
            <p className="mkt-feature-body">
              Every paid plan includes Research, Plan, Mentor, and Employee OS access. Higher tiers add integrations,
              automation builders, higher limits, and support levels.
            </p>
            <ul className="mkt-price-list">
              {[
                "Core OS tools included",
                "OAuth integrations & automation builders",
                "Higher credit / usage limits",
                "Priority support options",
              ].map((perk) => (
                <li key={perk}>
                  <Check className="h-4 w-4 shrink-0" aria-hidden />
                  <span>{perk}</span>
                </li>
              ))}
            </ul>
            <a href={SITE_WHATSAPP} target="_blank" rel="noreferrer" className="iid-btn iid-btn-primary mkt-price-cta">
              WhatsApp for quote
            </a>
          </article>

          <article className="mkt-price-card">
            <span className="mkt-price-badge">Enterprise</span>
            <h2 className="mkt-feature-title">Enterprise</h2>
            <p className="mkt-price">
              <span className="mkt-price-coming">Custom</span>
              <small>Scope, SLA, and integrations</small>
            </p>
            <p className="mkt-feature-body">
              For teams that need custom workflows, security review, and dedicated delivery. Talk to us for a scoped proposal.
            </p>
            <ul className="mkt-price-list">
              {["Custom scope & SLA", "Security review support", "Dedicated onboarding", "Invoice billing"].map((perk) => (
                <li key={perk}>
                  <Check className="h-4 w-4 shrink-0" aria-hidden />
                  <span>{perk}</span>
                </li>
              ))}
            </ul>
            <a href={SITE_PHONE_TEL} className="iid-btn iid-btn-ghost mkt-price-cta">
              Call {SITE_PHONE}
            </a>
          </article>
        </div>
        <p className="mkt-pricing-note">
          Pricing is shown with India (INR) as the default. If you need USD or another region, WhatsApp us and we will quote accordingly.
        </p>
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
          Call / WhatsApp: <a href={SITE_PHONE_TEL}>{SITE_PHONE}</a> ·{" "}
          <a href={SITE_WHATSAPP} target="_blank" rel="noreferrer">
            Open WhatsApp
          </a>
        </p>
      </section>
    </>
  );
}
