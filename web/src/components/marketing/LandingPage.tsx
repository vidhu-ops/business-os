"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { ContactForm } from "./ContactForm";
import { GlowOrb, HumanScene, MarketingPhoto } from "./illustrations";
import { IconClock, IconGlobe, IconMail, IconPhone, IconPin, IconSearch, IconUser } from "./icons";
import { IndustryBanner } from "./IndustryBanner";
import { MarketingShell } from "./MarketingShell";
import { WorkspaceEntryLink } from "@/components/WorkspaceEntryLink";
import { SITE_EMAIL, SITE_PHONE, SITE_PHONE_TEL, SITE_WHATSAPP } from "@/lib/site";
import {
  AUDIENCE,
  BY_THE_NUMBERS,
  CLIENT_LOGOS,
  HOME_STEPS,
  PROBLEM,
  SOLUTION,
  TOOLS,
  type Audience,
  type ToolId,
} from "./audienceContent";

const PRODUCT_SHOTS = [
  {
    src: "/marketing/frames/research.png",
    alt: "IIDATECH market research report screen",
    caption: "Market research report",
  },
  {
    src: "/marketing/frames/plan.png",
    alt: "IIDATECH business plan output screen",
    caption: "Business plan output",
  },
  {
    src: "/marketing/frames/execute.png",
    alt: "IIDATECH Employee OS task board",
    caption: "Employee OS task board",
  },
] as const;

export function LandingPage() {
  const [audience, setAudience] = useState<Audience>("founder");
  const [service, setService] = useState<ToolId>("research");
  const copy = AUDIENCE[audience];
  const problem = PROBLEM[audience];
  const solution = SOLUTION[audience];
  const activeService = useMemo(() => TOOLS.find((t) => t.id === service) || TOOLS[0], [service]);
  const serviceCopy = activeService[audience];

  return (
    <MarketingShell>
      <GlowOrb className="mkt-glow-hero" />

      <section className="mkt-wrap mkt-hero" aria-labelledby="hero-heading">
        <div className="mkt-hero-grid">
          <div className="mkt-hero-intro">
            <div className="mkt-audience-toggle" role="group" aria-label="Choose how to read IIDATECH">
              <button
                type="button"
                className={`mkt-audience-btn${audience === "founder" ? " is-active" : ""}`}
                aria-pressed={audience === "founder"}
                onClick={() => setAudience("founder")}
              >
                Read as founder
              </button>
              <button
                type="button"
                className={`mkt-audience-btn${audience === "company" ? " is-active" : ""}`}
                aria-pressed={audience === "company"}
                onClick={() => setAudience("company")}
              >
                Read as established company
              </button>
            </div>

            <p className="mkt-eyebrow">IIDATECH business ecosystem</p>
            <h1 id="hero-heading" className="mkt-hero-title mkt-hero-title-plain">
              {copy.headline}
            </h1>
          </div>

          <div className="mkt-hero-aside">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src="/marketing/frames/research.png"
              alt="IIDATECH market research product screen"
              className="mkt-hero-photo mkt-product-shot"
            />
            <p className="mkt-hero-aside-caption">
              {audience === "founder"
                ? "Validate, plan, and execute from one founder workspace."
                : "Audit, research, and operate from one company workspace."}
            </p>
          </div>

          <div className="mkt-hero-copy">
            <div className="mkt-pipe" aria-hidden>
              {copy.pipe.flatMap((step, i) =>
                i === 0
                  ? [<span key={step}>{step}</span>]
                  : [<i key={`${step}-arrow`}>→</i>, <span key={step}>{step}</span>],
              )}
            </div>

            <p className="mkt-lead">{copy.lead}</p>

            <div className="mkt-hero-cta">
              <Link href={copy.primaryCta.href} className="iid-btn iid-btn-primary">
                Start free — no card required
              </Link>
              <WorkspaceEntryLink href={copy.secondaryCta.href} className="iid-btn iid-btn-ghost">
                See a live demo
              </WorkspaceEntryLink>
            </div>
            <p className="mkt-lead mkt-hero-note">{copy.trustLine}</p>
          </div>
        </div>
      </section>

      <IndustryBanner />

      <section id="about" className="mkt-wrap mkt-section" aria-labelledby="about-heading">
        <div className="mkt-section-head">
          <span className="mkt-label">Who it is for</span>
          <h2 id="about-heading" className="mkt-h2">
            {copy.whoForTitle}
          </h2>
          <p className="mkt-sub">{copy.whoForBody}</p>
        </div>

        <div className="mkt-product-shots" aria-label="Product screenshots">
          {PRODUCT_SHOTS.map((shot) => (
            <figure key={shot.src} className="mkt-product-shot-card">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={shot.src} alt={shot.alt} loading="lazy" />
              <figcaption>{shot.caption}</figcaption>
            </figure>
          ))}
        </div>
      </section>

      <section id="how" className="mkt-wrap mkt-section">
        <div className="mkt-section-head">
          <span className="mkt-label">How it works</span>
          <h2 className="mkt-h2">Research. Plan. Execute.</h2>
          <p className="mkt-sub">Three moves inside one project vault — depth lives on the walkthrough page.</p>
        </div>
        <div className="mkt-process mkt-process-3">
          {HOME_STEPS.map((s) => (
            <div key={s.step} className="mkt-process-step">
              <p className="mkt-step-big">{s.step}</p>
              <h3>{s.title}</h3>
              <p>{s.body}</p>
            </div>
          ))}
        </div>
        <Link href="/how-it-works" className="iid-btn iid-btn-ghost mkt-section-cta-inline">
          See the full walkthrough →
        </Link>
      </section>

      <section id="services" className="mkt-wrap mkt-section">
        <div className="mkt-section-head">
          <span className="mkt-label">Services</span>
          <h2 className="mkt-h2">Six services on the platform</h2>
          <p className="mkt-sub">
            Switch audience above to see founder vs company framing. Each service has a full page with steps and FAQ.
          </p>
        </div>
        <div className="mkt-service-tabs" role="tablist" aria-label="IIDATECH services">
          {TOOLS.map((t) => (
            <button
              key={t.id}
              type="button"
              role="tab"
              aria-selected={service === t.id}
              className={`mkt-service-tab${service === t.id ? " is-active" : ""}`}
              onClick={() => setService(t.id)}
            >
              {t.label}
            </button>
          ))}
        </div>
        <article className="mkt-service-detail" aria-live="polite">
          <div className="mkt-service-detail-copy">
            <span className="mkt-tag">{activeService.short.toUpperCase()}</span>
            <h3 className="mkt-feature-title">{serviceCopy.title}</h3>
            <p className="mkt-feature-body">{serviceCopy.body}</p>
            <p className="mkt-wheel-inapp">
              <strong>In the app:</strong> {serviceCopy.inApp}
            </p>
            <div className="flex flex-wrap gap-2 mt-4">
              <Link href={`/services/${activeService.id}`} className="iid-btn iid-btn-primary">
                Read more
              </Link>
              <Link href="/login?mode=register" className="iid-btn iid-btn-ghost">
                Start free
              </Link>
              <WorkspaceEntryLink className="iid-btn iid-btn-ghost">See demo</WorkspaceEntryLink>
            </div>
          </div>
          <div className="mkt-service-detail-media">
            {activeService.videoSrc ? (
              <div className="mkt-wheel-video">
                <video key={activeService.videoSrc} controls playsInline preload="metadata">
                  <source src={activeService.videoSrc} type="video/mp4" />
                </video>
              </div>
            ) : (
              <MarketingPhoto id="analytics" />
            )}
          </div>
        </article>
      </section>

      <section id="proof" className="mkt-wrap mkt-section">
        <div className="mkt-section-head">
          <span className="mkt-label">By the numbers</span>
          <h2 className="mkt-h2">Proof without unverifiable quotes</h2>
          <p className="mkt-sub">We will publish named testimonials when we have permission to link them. Until then, here is what the product ships today.</p>
        </div>
        <div className="mkt-stats-grid">
          {BY_THE_NUMBERS.map((stat) => (
            <article key={stat.label} className="mkt-stat-card">
              <strong>{stat.value}</strong>
              <span>{stat.label}</span>
            </article>
          ))}
        </div>
      </section>

      <section id="clients" className="mkt-wrap mkt-section">
        <div className="mkt-section-head">
          <span className="mkt-label">Early operator partners</span>
          <h2 className="mkt-h2">Service providers shipping alongside IIDATECH</h2>
          <p className="mkt-sub">
            These logos are early operator and service-provider partners — not an enterprise customer logo wall. They
            collaborate with founders and MSMEs in the IIDATECH ecosystem.
          </p>
        </div>
        <div className="mkt-client-logos">
          {CLIENT_LOGOS.map((logo) => (
            <div key={logo.name} className="mkt-client-logo">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={logo.src} alt={`${logo.name} logo`} loading="lazy" />
              <span className="sr-only">{logo.name}</span>
            </div>
          ))}
        </div>
        <Link href="/partners" className="iid-btn iid-btn-ghost mkt-section-cta-inline">
          Become a partner →
        </Link>
      </section>

      <section id="why" className="mkt-wrap mkt-section">
        <div className="mkt-split mkt-split-problem">
          <div className="mkt-split-copy">
            <span className="mkt-label">The problem</span>
            <h2 className="mkt-h2">{problem.title}</h2>
            <p className="mkt-sub">{problem.sub}</p>
          </div>
          <HumanScene
            variant="founder"
            photoId="msme-business"
            cardA={{ label: "MSMEs worldwide (approx.)", value: "~78M" }}
            cardB={{ label: "India-first focus today", value: "Local" }}
          />
        </div>
        <div className="mkt-pain-row">
          <div className="mkt-pain-tile">
            <span className="mkt-icon-ring">
              <IconSearch />
            </span>
            <strong>No research bench</strong>
            <p>Founders and MSMEs rarely have in-house analysts.</p>
          </div>
          <div className="mkt-pain-tile">
            <span className="mkt-icon-ring">
              <IconClock />
            </span>
            <strong>Slow consulting</strong>
            <p>Weeks of back-and-forth before you can act.</p>
          </div>
          <div className="mkt-pain-tile">
            <span className="mkt-icon-ring">
              <IconUser />
            </span>
            <strong>Teams stretched thin</strong>
            <p>Research, planning, and outreach compete for the same hours.</p>
          </div>
          <div className="mkt-pain-tile">
            <span className="mkt-icon-ring">
              <IconGlobe />
            </span>
            <strong>Local context missing</strong>
            <p>Global tools miss regulation, pricing, and buyer reality.</p>
          </div>
        </div>
      </section>

      <section id="features" className="mkt-wrap mkt-section">
        <div className="mkt-section-head">
          <span className="mkt-label">The solution</span>
          <h2 className="mkt-h2">{solution.title}</h2>
          <p className="mkt-sub">{solution.body}</p>
        </div>
      </section>

      <section id="pricing" className="mkt-wrap mkt-section">
        <div className="mkt-cta-banner">
          <span className="mkt-label">Pricing</span>
          <h2 className="mkt-h2">Start free. Paid plans when you are ready.</h2>
          <p className="mkt-sub">
            Free credits and a live demo are available now. See the full pricing structure — Free, talk-to-us paid, and
            Enterprise — on the pricing page.
          </p>
          <div className="mkt-hero-cta mkt-cta-banner-actions">
            <Link href="/pricing" className="iid-btn iid-btn-primary">
              View pricing
            </Link>
            <Link href="/login?mode=register" className="mkt-text-link">
              Start free
            </Link>
          </div>
        </div>
      </section>

      <section id="contact" className="mkt-wrap mkt-section">
        <div className="mkt-section-head">
          <span className="mkt-label">Contact</span>
          <h2 className="mkt-h2">Talk to the IIDATECH team</h2>
        </div>
        <div className="mkt-contact-grid">
          <div className="mkt-contact-visual">
            <MarketingPhoto id="founder-team" />
            <div className="mkt-contact-stack">
              <div className="mkt-contact-card">
                <span className="mkt-icon-ring sm">
                  <IconMail />
                </span>
                <div>
                  <strong>Email</strong>
                  <a href={`mailto:${SITE_EMAIL}`}>{SITE_EMAIL}</a>
                </div>
              </div>
              <div className="mkt-contact-card">
                <span className="mkt-icon-ring sm">
                  <IconPhone />
                </span>
                <div>
                  <strong>Call / WhatsApp</strong>
                  <a href={SITE_PHONE_TEL}>{SITE_PHONE}</a> ·{" "}
                  <a href={SITE_WHATSAPP} target="_blank" rel="noreferrer">
                    WhatsApp
                  </a>
                </div>
              </div>
              <div className="mkt-contact-card">
                <span className="mkt-icon-ring sm">
                  <IconPin />
                </span>
                <div>
                  <strong>Focus</strong>
                  <span>India-first today, serving founders and B2B teams globally</span>
                </div>
              </div>
            </div>
          </div>
          <ContactForm />
        </div>
      </section>

      <section className="mkt-wrap mkt-section mkt-section-last">
        <div className="mkt-cta-banner">
          <span className="mkt-label">Ready?</span>
          <h2 className="mkt-h2">
            {audience === "founder" ? "Start free as a founder." : "Start free as a B2B operator."}
          </h2>
          <p className="mkt-sub">{copy.trustLine}</p>
          <div className="mkt-hero-cta mkt-cta-banner-actions">
            <Link href={copy.primaryCta.href} className="iid-btn iid-btn-primary">
              Start free
            </Link>
            <WorkspaceEntryLink href={copy.secondaryCta.href} className="mkt-text-link">
              See demo
            </WorkspaceEntryLink>
          </div>
        </div>
      </section>
    </MarketingShell>
  );
}
