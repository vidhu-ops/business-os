"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { ContactForm } from "./ContactForm";
import {
  AgentBadge,
  DocPreview,
  GlowOrb,
  HumanScene,
  MarketingPhoto,
  PhotoStrip,
} from "./illustrations";
import { IconClock, IconGlobe, IconMail, IconPhone, IconPin, IconSearch, IconUser } from "./icons";
import { IndustryBanner } from "./IndustryBanner";
import { MarketingShell } from "./MarketingShell";
import { WorkspaceEntryLink } from "@/components/WorkspaceEntryLink";
import {
  AUDIENCE,
  CLIENT_LOGOS,
  HOW_IT_WORKS,
  PROBLEM,
  SOLUTION,
  TOOLS,
  type Audience,
  type ToolId,
} from "./audienceContent";

const REVIEWS = [
  {
    quote: "We replaced a two-lakh consulting sprint with a 40-page market report in one afternoon.",
    name: "Arjun K.",
    role: "SaaS Founder, Bengaluru",
    initials: "AK",
    tone: "blue",
  },
  {
    quote: "Finally something built for MSMEs like ours. Our bank loan deck was ready the same day.",
    name: "Priya S.",
    role: "MSME Owner, Pune",
    initials: "PS",
    tone: "violet",
  },
  {
    quote: "The AI workforce handled research and outreach while we focused on product.",
    name: "Rahul M.",
    role: "D2C Founder, Mumbai",
    initials: "RM",
    tone: "emerald",
  },
];

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

      {/* 1. Hero — audience toggle */}
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
            <h1 id="hero-heading" className="mkt-hero-title">
              <span className="mkt-hero-os">{copy.h1Lead}</span>
              <span className="mkt-hero-accent">
                {copy.h1Accent.map((word) => (
                  <span key={word} className="mkt-hero-accent-word">
                    {word}
                  </span>
                ))}
              </span>
            </h1>
          </div>

          <div className="mkt-hero-aside">
            <MarketingPhoto id="workspace" className="mkt-hero-photo" />
            <p className="mkt-hero-aside-caption">
              {audience === "founder"
                ? "Founder workspace: research, plan, Mentor, and Employee OS in one place."
                : "Company workspace: GAUGE audit, market intelligence, plans, and approved automation."}
            </p>
          </div>

          <div className="mkt-hero-copy">
            <div className="mkt-pipe" aria-hidden>
              {copy.pipe.flatMap((step, i) =>
                i === 0
                  ? [<span key={step}>{step}</span>]
                  : [
                      <i key={`${step}-arrow`}>→</i>,
                      <span key={step}>{step}</span>,
                    ],
              )}
            </div>

            <p className="mkt-lead">{copy.lead}</p>

            <div className="mkt-hero-cta">
              <Link href={copy.primaryCta.href} className="iid-btn iid-btn-primary">
                {copy.primaryCta.label}
              </Link>
              {"demo" in copy.secondaryCta && copy.secondaryCta.demo ? (
                <WorkspaceEntryLink href={copy.secondaryCta.href} className="iid-btn iid-btn-ghost">
                  {copy.secondaryCta.label}
                </WorkspaceEntryLink>
              ) : (
                <Link href={copy.secondaryCta.href} className="iid-btn iid-btn-ghost">
                  {copy.secondaryCta.label}
                </Link>
              )}
            </div>
            <p className="mkt-lead mkt-hero-note">
              Free signup credits · demo workspace · WhatsApp{" "}
              <a href="https://wa.me/919545403431">+91 95454 03431</a> for pricing
            </p>
          </div>
        </div>
      </section>

      <IndustryBanner />

      <section className="mkt-wrap mkt-section-tight mkt-section-visual" aria-hidden={false}>
        <PhotoStrip ids={["presentation", "founder-team", "retail", "logistics"]} />
      </section>

      {/* About / how it works / who / services */}
      <section id="about" className="mkt-wrap mkt-section" aria-labelledby="about-heading">
        <div className="mkt-section-head">
          <span className="mkt-label">About IIDATECH</span>
          <h2 id="about-heading" className="mkt-h2">
            {copy.aboutTitle}
          </h2>
          <p className="mkt-sub">{copy.aboutBody}</p>
        </div>

        <PhotoStrip ids={["strategy-meeting", "market-research", "collaboration", "analytics"]} />

        <div className="mkt-about-grid">
          <article className="mkt-about-card">
            <h3 className="mkt-feature-title">Who it is for</h3>
            <p className="mkt-feature-body">
              <strong>{copy.whoForTitle}.</strong> {copy.whoForBody}
            </p>
          </article>
          <article className="mkt-about-card">
            <h3 className="mkt-feature-title">What business research, planning &amp; automation means</h3>
            <p className="mkt-feature-body">
              <strong>Business research</strong> is sourced market intelligence (competitors, TAM, buyers, pricing).{" "}
              <strong>Business planning</strong> turns that into ICP, GTM, and financial structure.{" "}
              <strong>Automation</strong> connects CRM, inbox, and recurring workflows so execution does not stay manual.
            </p>
          </article>
        </div>

        <div id="how" className="mkt-section-head mkt-section-head-tight">
          <span className="mkt-label">How it works</span>
          <h2 className="mkt-h2">Six steps inside the app</h2>
          <p className="mkt-sub">Button names match the product — so founders and B2B teams can follow without a manual.</p>
        </div>
        <div className="mkt-process">
          {HOW_IT_WORKS.map((s) => (
            <div key={s.step} className="mkt-process-step">
              <p className="mkt-step-big">{s.step}</p>
              <h3>{s.title}</h3>
              <p>{s.body}</p>
            </div>
          ))}
        </div>
        <Link href="/how-it-works" className="iid-btn iid-btn-ghost mkt-section-cta-inline">
          Full product walkthrough →
        </Link>

        <div id="services" className="mkt-section-head mkt-section-head-tight">
          <span className="mkt-label">Services</span>
          <h2 className="mkt-h2">Six services on the platform</h2>
          <p className="mkt-sub">Click a service to see the explanation, in-app workflow, and walkthrough video.</p>
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
              <strong>How it works in the app:</strong> {serviceCopy.inApp}
            </p>
            <div className="flex flex-wrap gap-2 mt-4">
              <Link href={`/services/${activeService.id}`} className="iid-btn iid-btn-primary">
                Read more
              </Link>
              <Link href="/login?mode=register" className="iid-btn iid-btn-ghost">
                Try this free
              </Link>
              <WorkspaceEntryLink className="iid-btn iid-btn-ghost">Open demo</WorkspaceEntryLink>
            </div>
          </div>
          <div className="mkt-service-detail-media">
            {activeService.videoSrc ? (
              <div className="mkt-wheel-video">
                <video key={activeService.videoSrc} controls playsInline preload="metadata">
                  <source src={activeService.videoSrc} type="video/mp4" />
                </video>
              </div>
            ) : activeService.videoId ? (
              <div className="mkt-wheel-video">
                <iframe
                  title={`${activeService.label} screen walkthrough`}
                  src={`https://www.youtube.com/embed/${activeService.videoId}?rel=0`}
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                  allowFullScreen
                />
              </div>
            ) : (
              <MarketingPhoto id="analytics" />
            )}
            <p className="mkt-service-video-note">
              Product walkthrough for {activeService.label} — recorded from the live IIDATECH workspace.
            </p>
          </div>
        </article>
      </section>

      {/* 4. Pricing */}
      <section id="pricing" className="mkt-wrap mkt-section" aria-labelledby="pricing-heading">
        <div className="mkt-section-head">
          <span className="mkt-label">Pricing</span>
          <h2 id="pricing-heading" className="mkt-h2">
            Pricing coming soon — demo &amp; free credits now
          </h2>
          <p className="mkt-sub">
            Paid plans for founders and B2B companies are being finalized. Until then, enjoy the demo and free signup credits.
            Call or WhatsApp <a href="tel:+919545403431">+91 95454 03431</a> to talk about your stage.
          </p>
        </div>
        <div className="mkt-pricing-teaser-grid">
          <article className="mkt-price-card is-featured">
            <span className="mkt-price-badge">Available now</span>
            <h3 className="mkt-feature-title">Free</h3>
            <p className="mkt-price">
              <span className="mkt-price-currency">&#8377;</span>0<small>to begin</small>
            </p>
            <p className="mkt-feature-body">Signup credits, demo workspace, research &amp; plan intake, Mentor exploration.</p>
            <Link href="/login?mode=register" className="iid-btn iid-btn-primary mkt-price-cta">
              Start free
            </Link>
          </article>
          <article className="mkt-price-card">
            <span className="mkt-price-badge">Coming soon</span>
            <h3 className="mkt-feature-title">Founder &amp; company plans</h3>
            <p className="mkt-price">
              <span className="mkt-price-coming">Price coming soon</span>
              <small>Enjoy demo &amp; free credits till then</small>
            </p>
            <p className="mkt-feature-body">Self-serve tools, Employee OS, automation, and done-for-you packages.</p>
            <div className="mkt-price-cta-row flex flex-wrap gap-2">
              <a href="https://wa.me/919545403431" target="_blank" rel="noreferrer" className="iid-btn iid-btn-primary mkt-price-cta">
                WhatsApp for quote
              </a>
              <Link href="/pricing" className="iid-btn iid-btn-ghost mkt-price-cta">
                Full pricing page
              </Link>
            </div>
          </article>
        </div>
      </section>

      {/* Reviews */}
      <section id="reviews" className="mkt-wrap mkt-section">
        <div className="mkt-section-head">
          <span className="mkt-label">Reviews</span>
          <h2 className="mkt-h2">What founders and operators say</h2>
        </div>
        <div className="mkt-split mkt-split-reviews">
          <MarketingPhoto id="mobile-founder" className="mkt-reviews-photo" />
          <div className="mkt-reviews-grid">
            {REVIEWS.map((r) => (
              <article key={r.name} className="mkt-review-card">
                <p className="mkt-stars">★★★★★</p>
                <p className="mkt-review-quote">&ldquo;{r.quote}&rdquo;</p>
                <div className="mkt-reviewer">
                  <AgentBadge initials={r.initials} tone={r.tone} />
                  <div>
                    <strong>{r.name}</strong>
                    <span>{r.role}</span>
                  </div>
                </div>
              </article>
            ))}
          </div>
        </div>
      </section>

      {/* Partners & service providers */}
      <section id="clients" className="mkt-wrap mkt-section" aria-labelledby="clients-heading">
        <div className="mkt-section-head">
          <span className="mkt-label">Partners &amp; service providers</span>
          <h2 id="clients-heading" className="mkt-h2">
            Partners and service providers we work with
          </h2>
          <p className="mkt-sub">
            Operators and specialists shipping alongside IIDATECH — automation, brand, commerce, and infrastructure partners.
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
      </section>

      {/* 5. Problem */}
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
            cardA={{ label: "MSMEs globally", value: "7.86 Cr" }}
            cardB={{ label: "Without research teams", value: "< 5%" }}
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

      {/* Solution */}
      <section id="features" className="mkt-wrap mkt-section">
        <div className="mkt-section-head">
          <span className="mkt-label">The solution</span>
          <h2 className="mkt-h2">{solution.title}</h2>
          <p className="mkt-sub">{solution.body}</p>
        </div>
        <PhotoStrip ids={["market-research", "analytics", "presentation", "collaboration"]} />
        <div className="mkt-grid-3 mkt-features-grid">
          {TOOLS.slice(0, 3).map((t) => (
            <article key={t.id} className="mkt-feature-card">
              <span className="mkt-tag">{t.short.toUpperCase()}</span>
              <h3 className="mkt-feature-title">{t[audience].title}</h3>
              <p className="mkt-feature-body">{t[audience].body}</p>
            </article>
          ))}
        </div>
        <div className="mkt-samples-grid" style={{ marginTop: "2rem" }}>
          <div className="mkt-sample-card">
            <DocPreview variant="report" />
            <div className="mkt-sample-body">
              <span className="mkt-tag">RESEARCH</span>
              <h3>Market report</h3>
              <p>Sourced competitor, TAM, and pricing intelligence.</p>
            </div>
          </div>
          <div className="mkt-sample-card">
            <DocPreview variant="plan" />
            <div className="mkt-sample-body">
              <span className="mkt-tag">PLAN</span>
              <h3>Business plan</h3>
              <p>ICP, GTM, and financial structure ready to share.</p>
            </div>
          </div>
          <div className="mkt-sample-card">
            <DocPreview variant="exec" />
            <div className="mkt-sample-body">
              <span className="mkt-tag">EXECUTE</span>
              <h3>Employee OS</h3>
              <p>Tasks, approvals, and automation from the same plan.</p>
            </div>
          </div>
        </div>
      </section>

      <section id="demo" className="mkt-wrap mkt-section-tight">
        <div className="mkt-section-head">
          <span className="mkt-label">Walkthrough</span>
          <h2 className="mkt-h2">
            {audience === "founder" ? "Watch how founders use IIDATECH" : "Watch how B2B teams use IIDATECH"}
          </h2>
          <p className="mkt-sub">
            Screen walkthrough of the live workspace — research intake through Mentor coaching.
          </p>
        </div>
        <div className="mkt-wheel-video mkt-demo-video">
          <video
            key={audience}
            controls
            playsInline
            preload="metadata"
            poster="/marketing/frames/research2.png"
          >
            <source
              src={audience === "founder" ? "/marketing/videos/research.mp4" : "/marketing/videos/mentor.mp4"}
              type="video/mp4"
            />
          </video>
        </div>
      </section>

      <section className="mkt-wrap mkt-section">
        <div className="mkt-cta-banner">
          <span className="mkt-label">Ready to ship?</span>
          <h2 className="mkt-h2">
            {audience === "founder" ? "Start free as a founder." : "Run a free company audit."}
          </h2>
          <p className="mkt-sub">No card required. Demo + free credits while paid pricing finalizes.</p>
          <div className="mkt-hero-cta mkt-cta-banner-actions">
            <Link href={copy.primaryCta.href} className="iid-btn iid-btn-primary">
              {copy.primaryCta.label}
            </Link>
            <Link href="/pricing" className="iid-btn iid-btn-ghost">
              Pricing coming soon
            </Link>
            <a href="https://wa.me/919545403431" target="_blank" rel="noreferrer" className="iid-btn iid-btn-ghost">
              WhatsApp +91 95454 03431
            </a>
          </div>
        </div>
      </section>

      <section id="contact" className="mkt-wrap mkt-section mkt-section-last">
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
                  <a href="mailto:vidhugupta1996@gmail.com">vidhugupta1996@gmail.com</a>
                </div>
              </div>
              <div className="mkt-contact-card">
                <span className="mkt-icon-ring sm">
                  <IconPhone />
                </span>
                <div>
                  <strong>Call / WhatsApp</strong>
                  <a href="tel:+919545403431">+91 95454 03431</a> ·{" "}
                  <a href="https://wa.me/919545403431" target="_blank" rel="noreferrer">
                    WhatsApp
                  </a>
                </div>
              </div>
              <div className="mkt-contact-card">
                <span className="mkt-icon-ring sm">
                  <IconPin />
                </span>
                <div>
                  <strong>Based in</strong>
                  <span>Serving founders and B2B companies globally</span>
                </div>
              </div>
            </div>
          </div>
          <ContactForm />
        </div>
      </section>
    </MarketingShell>
  );
}
