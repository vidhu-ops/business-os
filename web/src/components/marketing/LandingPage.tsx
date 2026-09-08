"use client";

import Link from "next/link";
import { useEffect, useMemo, useRef, useState } from "react";
import { ContactForm } from "./ContactForm";
import { FrameIllustration, HumanScene, MarketingPhoto } from "./illustrations";
import { IconClock, IconGlobe, IconMail, IconPhone, IconPin, IconSearch, IconUser } from "./icons";
import { IndustryBanner } from "./IndustryBanner";
import { LogoMarquee } from "./LogoMarquee";
import { MARKETING_PHOTOS } from "./marketingImages";
import { MarketingShell } from "./MarketingShell";
import { WorkspaceEntryLink } from "@/components/WorkspaceEntryLink";
import { SITE_EMAIL, SITE_PHONE, SITE_PHONE_TEL, SITE_WHATSAPP } from "@/lib/site";
import {
  AUDIENCE,
  BY_THE_NUMBERS,
  CLIENT_LOGOS,
  HERO_WIX,
  HOME_STEPS,
  INTEGRATION_LOGOS,
  PROCESS_STEPS,
  PROBLEM,
  SOLUTION,
  TOOLS,
  WHY_US,
  type Audience,
  type ToolId,
} from "./audienceContent";

const PRODUCT_SHOTS = [
  {
    src: "/marketing/frames/research.png",
    alt: "IIDATECH demo market research report",
    caption: "Market research report",
  },
  {
    src: "/marketing/frames/plan.png",
    alt: "IIDATECH demo business plan workspace",
    caption: "Business plan output",
  },
  {
    src: "/marketing/frames/execute.png",
    alt: "IIDATECH demo Employee OS office",
    caption: "Execution workspace",
  },
] as const;

export function LandingPage() {
  const [audience, setAudience] = useState<Audience>("founder");
  const [service, setService] = useState<ToolId>("research");
  const heroVideoRef = useRef<HTMLVideoElement | null>(null);
  const copy = AUDIENCE[audience];
  const problem = PROBLEM[audience];
  const solution = SOLUTION[audience];
  const activeService = useMemo(() => TOOLS.find((t) => t.id === service) ?? TOOLS[0], [service]);
  const serviceCopy = activeService[audience];
  const servicePhoto = MARKETING_PHOTOS[activeService.photoId];
  const hero = HERO_WIX[audience];

  useEffect(() => {
    const el = heroVideoRef.current;
    if (!el) return;
    el.muted = true;
    const play = () => {
      void el.play().catch(() => {
        /* autoplay can be blocked; muted+playsInline usually succeeds */
      });
    };
    play();
    el.addEventListener("loadeddata", play);
    return () => el.removeEventListener("loadeddata", play);
  }, [hero.videoSrc]);

  return (
    <MarketingShell>
      <section
        className={`mkt-wrap mkt-hero mkt-hero-wix mkt-hero-wix--${audience}`}
        aria-labelledby="hero-heading"
      >
        <div className="mkt-hero-wix-media" aria-hidden="true">
          <video
            key={hero.videoSrc}
            ref={heroVideoRef}
            className="mkt-hero-wix-video"
            src={hero.videoSrc}
            autoPlay
            muted
            loop
            playsInline
            preload="auto"
          />
          <div className="mkt-hero-wix-scrim" />
        </div>
        <div className="mkt-hero-wix-glow" aria-hidden="true" />
        <div className="mkt-hero-wix-inner">
          <div className="mkt-hero-audience mkt-hero-audience-compact" role="group" aria-label="Choose how to read IIDATECH">
            <button
              type="button"
              className={`mkt-hero-audience-btn${audience === "founder" ? " is-active" : ""}`}
              aria-pressed={audience === "founder"}
              onClick={() => setAudience("founder")}
            >
              Individual
            </button>
            <button
              type="button"
              className={`mkt-hero-audience-btn${audience === "company" ? " is-active" : ""}`}
              aria-pressed={audience === "company"}
              onClick={() => setAudience("company")}
            >
              Company
            </button>
          </div>

          <p className="mkt-hero-wix-brand" aria-hidden="true">
            {HERO_WIX.brand}
          </p>
          <h1 id="hero-heading" className="mkt-hero-wix-headline">
            {hero.headline}
          </h1>
          <p className="mkt-hero-wix-pipe">{hero.pipe}</p>
          <div className="mkt-hero-cta mkt-hero-wix-cta">
            <Link href={hero.cta.href} className="iid-btn iid-btn-primary mkt-hero-wix-btn">
              {hero.cta.label}
            </Link>
          </div>
          <p className="mkt-hero-wix-subline">{hero.subline}</p>
        </div>
      </section>

      <section id="how" className="mkt-wrap mkt-section mkt-section-steps">
        <div className="mkt-section-head mkt-section-head-center">
          <span className="mkt-label">What you get</span>
          <h2 className="mkt-h2">Research. Plan. Execute.</h2>
        </div>
        <div className="mkt-step-cards">
          {HOME_STEPS.map((s) => (
            <article key={s.step} className="mkt-step-card">
              <MarketingPhoto id={s.photoId} className="mkt-step-card-photo" rounded="lg" />
              <h3 className="mkt-step-card-title">{s.title}</h3>
              <p className="mkt-step-card-body">{s.body}</p>
            </article>
          ))}
        </div>
      </section>

      <section id="services" className="mkt-wrap mkt-section">
        <div className="mkt-section-head mkt-section-head-center">
          <span className="mkt-label">Our services</span>
          <h2 className="mkt-h2">Six tools. One platform.</h2>
          <p className="mkt-sub">
            {audience === "founder"
              ? "Everything a founder needs to research, plan, and execute — without weeks of consulting."
              : "Research, planning, ops capacity, and automation for established B2B teams."}
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
              {t.short}
            </button>
          ))}
        </div>
        <article className="mkt-service-detail mkt-service-detail-human" aria-live="polite">
          <div className="mkt-service-detail-copy">
            <span className="mkt-tag">{activeService.short.toUpperCase()}</span>
            <h3 className="mkt-feature-title">{serviceCopy.title}</h3>
            <p className="mkt-feature-body">{serviceCopy.body}</p>
            <p className="mkt-service-output">
              <strong>You get:</strong> {serviceCopy.output}
            </p>
            <div className="flex flex-wrap gap-2 mt-4">
              <Link href={`/services/${activeService.id}`} className="iid-btn iid-btn-primary">
                Try it
              </Link>
              <WorkspaceEntryLink className="iid-btn iid-btn-ghost">See demo</WorkspaceEntryLink>
            </div>
          </div>
          <div className="mkt-service-detail-media">
            <figure className="mkt-service-detail-image">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                key={`${activeService.id}-${audience}`}
                src={servicePhoto.src}
                alt={servicePhoto.alt}
                loading="lazy"
              />
            </figure>
          </div>
        </article>
      </section>

      <section id="about" className="mkt-wrap mkt-section mkt-section-about-human" aria-labelledby="about-heading">
        <div className="mkt-about-human-grid">
          <div className="mkt-section-head">
            <span className="mkt-label">All about us</span>
            <h2 id="about-heading" className="mkt-h2">
              Investor-ready plans in minutes — not months.
            </h2>
            <p className="mkt-sub">
              We built IIDATECH for people who need professional business plans but do not have weeks to research
              markets, create financial models, or write 30-page documents.
            </p>
            <p className="mkt-sub" style={{ marginTop: "0.75rem" }}>
              {copy.aboutBody}
            </p>
            <ul className="mkt-about-list">
              <li>Research your industry and competitors</li>
              <li>Validate your idea with real market data</li>
              <li>Create detailed financial projections</li>
              <li>Build step-by-step execution roadmaps</li>
              <li>Generate professional documents for individuals and teams</li>
            </ul>
            <div className="flex flex-wrap gap-2" style={{ marginTop: "1.25rem" }}>
              <Link href="/about?audience=founder" className="iid-btn iid-btn-primary">
                Read more
              </Link>
              <Link href="/topics" className="iid-btn iid-btn-ghost">
                Browse topics
              </Link>
            </div>
          </div>
          <div className="mkt-product-shots mkt-product-shots-compact" aria-label="Product screenshots">
            {PRODUCT_SHOTS.map((shot) => (
              <figure key={shot.src} className="mkt-product-shot-card">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={shot.src} alt={shot.alt} loading="lazy" />
                <figcaption>{shot.caption}</figcaption>
              </figure>
            ))}
          </div>
        </div>
      </section>

      <section id="process" className="mkt-wrap mkt-section mkt-section-process">
        <div className="mkt-section-head mkt-section-head-center">
          <span className="mkt-label">Process</span>
          <h2 className="mkt-h2">It&apos;s as easy as 1, 2, 3</h2>
        </div>
        <div className="mkt-process mkt-process-3 mkt-process-human">
          {PROCESS_STEPS.map((s) => (
            <div key={s.step} className="mkt-process-step mkt-process-step-human">
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

      <section id="why-us" className="mkt-wrap mkt-section">
        <div className="mkt-section-head mkt-section-head-center">
          <span className="mkt-label">Why us</span>
          <h2 className="mkt-h2">For a seamless business experience</h2>
        </div>
        <div className="mkt-why-grid">
          {WHY_US.map((item) => (
            <article key={item.title} className="mkt-why-card">
              <h3>{item.title}</h3>
              <p>{item.body}</p>
            </article>
          ))}
        </div>
      </section>

      <IndustryBanner />

      <section id="proof" className="mkt-wrap mkt-section">
        <div className="mkt-section-head mkt-section-head-center">
          <span className="mkt-label">By the numbers</span>
          <h2 className="mkt-h2">Built for real operators</h2>
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

      <section id="clients" className="mkt-section mkt-clients-section">
        <div className="mkt-wrap mkt-section-head mkt-section-head-center">
          <span className="mkt-label">Partners</span>
          <h2 className="mkt-h2">Built by creators, for creators</h2>
        </div>
        <LogoMarquee
          items={CLIENT_LOGOS}
          ariaLabel="Early operator and client partners"
          itemClassName="mkt-logo-marquee-item-client"
        />
        <div className="mkt-wrap">
          <Link href="/partners" className="iid-btn iid-btn-ghost mkt-section-cta-inline">
            Become a partner →
          </Link>
        </div>
      </section>

      <section id="integrations" className="mkt-section mkt-integrations-section" aria-labelledby="integrations-heading">
        <div className="mkt-wrap mkt-section-head mkt-section-head-center">
          <span className="mkt-label">Integrations</span>
          <h2 id="integrations-heading" className="mkt-h2">
            All the tools you need in one platform
          </h2>
        </div>
        <LogoMarquee
          items={INTEGRATION_LOGOS}
          ariaLabel="IIDATECH product integrations"
          itemClassName="mkt-logo-marquee-item-integration"
        />
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
        <div className="mkt-features-split">
          <div className="mkt-section-head">
            <span className="mkt-label">The solution</span>
            <h2 className="mkt-h2">{solution.title}</h2>
            <p className="mkt-sub">{solution.body}</p>
          </div>
          <FrameIllustration
            src="/marketing/frames/automate.png"
            alt="IIDATECH automation workflows connecting CRM, inbox, and reporting"
            className="mkt-features-visual"
          />
        </div>
      </section>

      <section id="pricing" className="mkt-wrap mkt-section">
        <div className="mkt-cta-banner mkt-cta-banner-human">
          <span className="mkt-label">Pricing</span>
          <h2 className="mkt-h2">Start free. Grow when you are ready.</h2>
          <p className="mkt-sub">
            30 free credits to try research, plans, Mentor, and Employee OS. Paid and Enterprise options are a quick
            conversation away.
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
        <div className="mkt-section-head mkt-section-head-center">
          <span className="mkt-label">Let us find you</span>
          <h2 className="mkt-h2">Tell us about your idea</h2>
          <p className="mkt-sub">Fill in the form and we will personally contact you to discuss your premise.</p>
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
        <div className="mkt-cta-banner mkt-cta-banner-human">
          <span className="mkt-label">Ready?</span>
          <h2 className="mkt-h2">Changing the way the world does business.</h2>
          <p className="mkt-sub">{copy.trustLine}</p>
          <div className="mkt-hero-cta mkt-cta-banner-actions">
            <Link href={copy.primaryCta.href} className="iid-btn iid-btn-primary">
              {HERO_WIX[audience].cta.label}
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
