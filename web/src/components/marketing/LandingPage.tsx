"use client";

import Link from "next/link";
import { Check } from "lucide-react";
import { useEffect, useRef, useState, type CSSProperties } from "react";
import { ContactForm } from "./ContactForm";
import { WixBrandSections } from "./WixBrandSections";
import { WixDetailCards } from "./WixDetailCards";
import { HumanScene, MarketingPhoto } from "./illustrations";
import { IconClock, IconGlobe, IconMail, IconPhone, IconPin, IconSearch, IconUser } from "./icons";
import { IndustryBanner } from "./IndustryBanner";
import { LogoMarquee } from "./LogoMarquee";
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
  SECTION_VIDEOS,
  SOLUTION,
  TOOLS,
  WHY_US,
  type Audience
} from "./audienceContent";

function SectionVideo({ src }: { src: string }) {
  const ref = useRef<HTMLVideoElement | null>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const io = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            if (!el.src) {
              el.src = src;
              el.load();
            }
            void el.play().catch(() => {
              /* muted autoplay usually works once in view */
            });
          } else {
            el.pause();
          }
        }
      },
      { rootMargin: "200px 0px", threshold: 0.05 }
    );
    io.observe(el);
    return () => io.disconnect();
  }, [src]);

  return (
    <div className="mkt-section-video" aria-hidden="true">
      <video
        ref={ref}
        className="mkt-section-video-el"
        muted
        loop
        playsInline
        preload="none"
        data-src={src}
      />
      <div className="mkt-section-video-scrim" />
    </div>
  );
}

export function LandingPage() {
  const [audience, setAudience] = useState<Audience>("founder");
  const heroVideoRef = useRef<HTMLVideoElement | null>(null);
  const copy = AUDIENCE[audience];
  const problem = PROBLEM[audience];
  const solution = SOLUTION[audience];
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
        className={`mkt-hero mkt-hero-wix mkt-hero-wix--${audience}`}
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
            preload="metadata"
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
          <div className="mkt-hero-wix-pipe" role="navigation" aria-label="Core product links">
            {hero.pipe.map((item) => (
              <Link key={item.href + item.label} href={item.href} className="mkt-hero-pipe-btn">
                {item.label}
              </Link>
            ))}
          </div>
          <div className="mkt-hero-cta mkt-hero-wix-cta">
            <Link href={hero.cta.href} className="iid-btn iid-btn-primary mkt-hero-wix-btn">
              {hero.cta.label}
            </Link>
          </div>
          <p className="mkt-hero-wix-subline">{hero.subline}</p>
        </div>
      </section>

      <section id="how" className="mkt-band mkt-band-full mkt-band-steps">
        <div className="mkt-wrap mkt-section mkt-section-steps mkt-band-content">
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
        <div className="mkt-section-cta-row">
          <Link href="/how-it-works" className="iid-btn iid-btn-primary mkt-steps-walkthrough">
            See walkthrough
          </Link>
        </div>
        </div>
      </section>

      <section id="services" className="mkt-band mkt-band-full mkt-band-services mkt-band-has-video">
        <SectionVideo src={SECTION_VIDEOS.services} />
        <div className="mkt-wrap mkt-section mkt-band-content">
          <div className="mkt-section-head mkt-section-head-center">
            <span className="mkt-label">Our services</span>
            <h2 className="mkt-h2">Six tools. One platform.</h2>
            <p className="mkt-sub">
              {audience === "founder"
                ? "Bold, focused tools for founders — research through execution in one workspace."
                : "Bold, focused tools for B2B teams — audit, research, plan, and operate in one workspace."}
            </p>
          </div>
          <div className="mkt-tool-grid">
            {TOOLS.map((tool) => {
              const toolCopy = tool[audience];
              const peopleSrc = `/marketing/people/${tool.id === "execute" ? "execute" : tool.id}.jpg`;
              return (
                <article
                  key={tool.id}
                  className="mkt-tool-card"
                  style={{ ["--tool-accent"]: tool.accent } as CSSProperties}
                >
                  <div className="mkt-tool-card-media">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      className="mkt-tool-card-photo"
                      src={peopleSrc}
                      alt=""
                      loading="lazy"
                    />
                    <span className="mkt-tool-card-tag">{tool.short}</span>
                  </div>
                  <div className="mkt-tool-card-body">
                    <h3 className="mkt-tool-card-title">{toolCopy.title}</h3>
                    <p className="mkt-tool-card-desc">{toolCopy.body}</p>
                    <p className="mkt-tool-card-output">{toolCopy.output}</p>
                    <div className="mkt-tool-card-actions">
                      <Link href={"/services/" + tool.id} className="iid-btn iid-btn-ghost mkt-tool-card-btn">
                        Read more
                      </Link>
                      <WorkspaceEntryLink
                        href={
                          tool.id === "execute"
                            ? "/app/team"
                            : tool.id === "gauge"
                              ? "/app/audit"
                              : tool.id === "automate"
                                ? "/app/automation"
                                : "/app/" + tool.id
                        }
                        className="iid-btn iid-btn-primary mkt-tool-card-btn"
                      >
                        Check it out
                      </WorkspaceEntryLink>
                    </div>
                  </div>
                </article>
              );
            })}
          </div>
        </div>
      </section>

      <section id="about" className="mkt-band mkt-band-full mkt-band-about" aria-labelledby="about-heading">
        <div className="mkt-wrap mkt-section mkt-section-about-human mkt-band-content">
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
              <div className="mkt-about-actions">
                <Link href="/about?audience=founder" className="iid-btn iid-btn-primary">
                  Read more
                </Link>
                <Link href="/topics" className="iid-btn iid-btn-ghost">
                  Browse topics
                </Link>
              </div>
            </div>
            <div className="mkt-about-people" aria-label="People building with IIDATECH">
              <figure className="mkt-about-people-hero">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src="/marketing/people/about-1.jpg" alt="Founders collaborating on a business plan" loading="lazy" />
              </figure>
              <figure className="mkt-about-people-side">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src="/marketing/people/about-2.jpg" alt="Founder working on a laptop" loading="lazy" />
              </figure>
              <figure className="mkt-about-people-side">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src="/marketing/people/about-3.jpg" alt="Team collaborating around a laptop" loading="lazy" />
              </figure>
            </div>
          </div>
        </div>
      </section>

      <section id="process" className="mkt-band mkt-band-full mkt-band-process mkt-band-has-video mkt-band-has-video-light">
        <SectionVideo src={SECTION_VIDEOS.process} />
        <div className="mkt-wrap mkt-section mkt-section-process mkt-band-content">
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
        </div>
      </section>

      <WixDetailCards />

      <section id="why-us" className="mkt-band mkt-band-full mkt-band-why">
        <div className="mkt-wrap mkt-section mkt-band-content">
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
          <h2 className="mkt-h2">Partners</h2>
        </div>
        <div className="mkt-wrap mkt-partner-spotlight" aria-label="Featured partners">
          {CLIENT_LOGOS.slice(0, 3).map((logo) => (
            <div key={logo.name} className="mkt-partner-spotlight-item">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                className="mkt-partner-logo-light"
                src={logo.src}
                alt={`${logo.name} logo`}
                loading="lazy"
              />
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                className="mkt-partner-logo-dark"
                src={logo.srcOnDark}
                alt=""
                aria-hidden="true"
                loading="lazy"
              />
            </div>
          ))}
        </div>
        <div className="mkt-wrap">
          <Link href="/partners" className="iid-btn iid-btn-ghost mkt-section-cta-inline">
            See all partners →
          </Link>
        </div>
      </section>

      <section
        id="integrations"
        className="mkt-band mkt-band-full mkt-band-integrations mkt-band-has-video mkt-band-has-video-light"
        aria-labelledby="integrations-heading"
      >
        <SectionVideo src={SECTION_VIDEOS.integrations} />
        <div className="mkt-wrap mkt-section mkt-band-content">
          <div className="mkt-section-head mkt-section-head-center">
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
        </div>
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
          <MarketingPhoto id="analytics" className="mkt-features-visual" rounded="lg" />
        </div>
      </section>

      <section id="pricing" className="mkt-band mkt-band-full mkt-band-pricing">
        <div className="mkt-wrap mkt-section mkt-band-content">
          <div className="mkt-section-head mkt-section-head-center">
            <span className="mkt-label">Pricing</span>
            <h2 className="mkt-h2">Start free. Grow when you are ready.</h2>
            <p className="mkt-sub">
              30 free credits to try research, plans, Mentor, and Employee OS. Paid and Enterprise options are a quick conversation away.
            </p>
          </div>
          <div className="mkt-pricing-grid mkt-pricing-grid-3">
            <article className="mkt-price-card is-featured">
              <span className="mkt-price-badge">Available now</span>
              <h3 className="mkt-feature-title">Free</h3>
              <p className="mkt-price">
                <span className="mkt-price-currency">&#8377;</span>0<small>to begin</small>
              </p>
              <p className="mkt-feature-body">Explore Research, Plan, Mentor, and Employee OS with 30 signup credits.</p>
              <ul className="mkt-price-list">
                {["Research, Plan, Mentor, Employee OS", "Demo workspace", "No credit card required"].map((perk) => (
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
              <h3 className="mkt-feature-title">Paid plans</h3>
              <p className="mkt-price">
                <span className="mkt-price-coming">Starting from — talk to us</span>
              </p>
              <p className="mkt-feature-body">Higher limits, integrations, automation builders, and support for growing teams.</p>
              <ul className="mkt-price-list">
                {["Core OS tools included", "OAuth integrations", "Higher usage limits"].map((perk) => (
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
              <h3 className="mkt-feature-title">Enterprise</h3>
              <p className="mkt-price">
                <span className="mkt-price-coming">Custom</span>
              </p>
              <p className="mkt-feature-body">Custom workflows, security review, dedicated onboarding, and invoice billing.</p>
              <ul className="mkt-price-list">
                {["Custom scope & SLA", "Security review", "Dedicated onboarding"].map((perk) => (
                  <li key={perk}>
                    <Check className="h-4 w-4 shrink-0" aria-hidden />
                    <span>{perk}</span>
                  </li>
                ))}
              </ul>
              <a href={SITE_PHONE_TEL} className="iid-btn iid-btn-primary mkt-price-cta">
                Call {SITE_PHONE}
              </a>
            </article>
          </div>
          <div className="mkt-pricing-home-actions">
            <Link href="/pricing" className="iid-btn iid-btn-primary mkt-price-cta">
              Full pricing details →
            </Link>
          </div>
        </div>
      </section>

      <WixBrandSections />

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
