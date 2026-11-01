"use client";

import Link from "next/link";
import { useEffect, useRef, useState, type CSSProperties } from "react";
import { ContactForm } from "./ContactForm";
import { CaseStudiesSection, HomePricingTeaser } from "./FirstVisitorSections";
import { MarketingPhoto } from "./illustrations";
import { IconMail, IconPhone, IconPin } from "./icons";
import { IndustryBanner } from "./IndustryBanner";
import { LogoMarquee } from "./LogoMarquee";
import { MarketingShell } from "./MarketingShell";
import { WorkspaceEntryLink } from "@/components/WorkspaceEntryLink";
import { usePricingCatalog } from "@/hooks/usePricingCatalog";
import { SITE_EMAIL, SITE_PHONE, SITE_PHONE_TEL, SITE_WHATSAPP } from "@/lib/site";
import { SectionVideo } from "./SectionVideo";
import {
  AUDIENCE,
  BY_THE_NUMBERS,
  CLIENT_LOGOS,
  HERO_WIX,
  HOME_ABOUT,
  INTEGRATION_LOGOS,
  PROCESS_STEPS,
  SECTION_VIDEOS,
  TOOLS,
  type Audience
} from "./audienceContent";

export function LandingPage() {
  const [audience, setAudience] = useState<Audience>("founder");
  const heroVideoRef = useRef<HTMLVideoElement | null>(null);
  const { catalog } = usePricingCatalog();
  const signupCredits = catalog?.signup_credits ?? 30;
  const copy = AUDIENCE[audience];
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

          <p className="mkt-hero-wix-eyebrow">{hero.eyebrow}</p>
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
          {hero.subline ? <p className="mkt-hero-wix-subline">{hero.subline}</p> : null}
          <p className="mkt-hero-wix-trust">{hero.trustLine}</p>
        </div>
      </section>

      <IndustryBanner />

      <section id="services" className="mkt-band mkt-band-full mkt-band-services">
        <div className="mkt-wrap mkt-section mkt-band-content">
          <div className="mkt-section-head mkt-section-head-center">
            <span className="mkt-label">Our services</span>
            <h2 className="mkt-h2">When you are ready — the tools behind each goal</h2>
            <p className="mkt-sub">
              {audience === "founder"
                ? "You do not need all six on day one. Start with research or a plan — the rest unlock as you grow."
                : "Start with a GAUGE audit or market refresh — then add ops capacity when leadership is ready."}
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
                    <p className="mkt-tool-card-output">{toolCopy.output}</p>
                    <Link
                      href={"/services/" + tool.id}
                      className="mkt-tool-card-link"
                    >
                      Read more
                    </Link>
                  </div>
                </article>
              );
            })}
          </div>
        </div>
      </section>

      <HomePricingTeaser signupCredits={signupCredits} />

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
          {CLIENT_LOGOS.map((logo) => (
            <div key={logo.name} className="mkt-partner-spotlight-item">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={logo.srcOnDark || logo.src}
                alt=""
                loading="lazy"
              />
              <span className="mkt-partner-spotlight-name">{logo.name}</span>
            </div>
          ))}
        </div>
        <div className="mkt-wrap mkt-section-cta-row">
          <Link href="/partners" className="iid-btn iid-btn-ghost">
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
            <span className="mkt-label">Connect your stack</span>
            <h2 id="integrations-heading" className="mkt-h2">
              Integrations vs AI models
            </h2>
            <p className="mkt-sub">
              Optional OAuth apps connect your workspace to tools you already use. Model logos show which AI providers can
              power research and agents — not separate product logins.
            </p>
          </div>
          <p className="mkt-integrations-group-label">Workspace integrations (OAuth)</p>
          <LogoMarquee
            items={INTEGRATION_LOGOS.filter((logo) => logo.group === "apps")}
            ariaLabel="IIDATECH workspace integrations"
            itemClassName="mkt-logo-marquee-item-integration"
          />
          <p className="mkt-integrations-group-label">AI models powering IIDATECH</p>
          <LogoMarquee
            items={INTEGRATION_LOGOS.filter((logo) => logo.group === "models")}
            ariaLabel="AI models available in IIDATECH"
            itemClassName="mkt-logo-marquee-item-integration"
          />
        </div>
      </section>

      <section id="about" className="mkt-band mkt-band-full mkt-band-about" aria-labelledby="about-heading">
        <div className="mkt-wrap mkt-section mkt-section-about-human mkt-band-content">
          <div className="mkt-about-human-grid">
            <div className="mkt-section-head">
              <span className="mkt-label">All about us</span>
              <h2 id="about-heading" className="mkt-h2">
                {HOME_ABOUT.headline}
              </h2>
              <p className="mkt-sub">{HOME_ABOUT.lead}</p>
              <p className="mkt-sub mkt-about-sub-tight">{HOME_ABOUT.toolAndService}</p>
              <p className="mkt-sub mkt-about-sub-tight">{HOME_ABOUT.integration[audience]}</p>

              <h3 className="mkt-about-subhead">{HOME_ABOUT.platformTitle}</h3>
              <ul className="mkt-about-pillars">
                {HOME_ABOUT.platform.map((item) => (
                  <li key={item.title}>
                    <strong>{item.title}</strong>
                    <span>{item.body}</span>
                  </li>
                ))}
              </ul>

              <h3 className="mkt-about-subhead">{HOME_ABOUT.resultsTitle}</h3>
              <ul className="mkt-about-results">
                {HOME_ABOUT.results.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>

              <div className="mkt-about-actions">
                <Link href={audience === "company" ? "/about?audience=company" : "/about?audience=founder"} className="iid-btn iid-btn-primary">
                  Read more
                </Link>
                <Link href="#results" className="iid-btn iid-btn-ghost">
                  See case studies
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
        <CaseStudiesSection intro={HOME_ABOUT.caseStudiesIntro} className="mkt-section-case-in-about" />
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
          <div className="mkt-section-cta-row">
            <Link href="/how-it-works" className="iid-btn iid-btn-primary">
              See the full walkthrough →
            </Link>
          </div>
        </div>
      </section>

      <section id="contact" className="mkt-wrap mkt-section mkt-contact-section">
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
