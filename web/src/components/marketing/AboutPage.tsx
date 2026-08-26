"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { MarketingShell } from "./MarketingShell";
import { WorkspaceEntryLink } from "@/components/WorkspaceEntryLink";
import { ABOUT_BY_AUDIENCE, ABOUT_SHARED } from "./aboutContent";
import type { Audience } from "./audienceContent";

export function AboutPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const initial = searchParams.get("audience") === "company" ? "company" : "founder";
  const [audience, setAudience] = useState<Audience>(initial);
  const copy = useMemo(() => ABOUT_BY_AUDIENCE[audience], [audience]);

  useEffect(() => {
    const next = searchParams.get("audience") === "company" ? "company" : "founder";
    setAudience(next);
  }, [searchParams]);

  function selectAudience(next: Audience) {
    setAudience(next);
    router.replace(next === "company" ? "/about?audience=company" : "/about?audience=founder", { scroll: false });
  }

  return (
    <MarketingShell>
      <section className="mkt-wrap mkt-page-hero">
        <div className="mkt-audience-toggle" role="group" aria-label="Choose About audience">
          <button
            type="button"
            className={`mkt-audience-btn${audience === "founder" ? " is-active" : ""}`}
            aria-pressed={audience === "founder"}
            onClick={() => selectAudience("founder")}
          >
            About for founders
          </button>
          <button
            type="button"
            className={`mkt-audience-btn${audience === "company" ? " is-active" : ""}`}
            aria-pressed={audience === "company"}
            onClick={() => selectAudience("company")}
          >
            About for B2B companies
          </button>
        </div>
        <p className="mkt-eyebrow">About IIDATECH</p>
        <h1 className="mkt-page-title">{copy.heroTitle}</h1>
        <p className="mkt-lead mkt-page-lead">{copy.heroLead}</p>
        <p className="mkt-sub" style={{ marginTop: "1rem", maxWidth: "44rem" }}>
          {ABOUT_SHARED.oneLiner}
        </p>
        <div className="mkt-hero-cta" style={{ marginTop: "1.5rem" }}>
          <Link href={copy.ctaHref} className="iid-btn iid-btn-primary">
            {copy.ctaLabel}
          </Link>
          <WorkspaceEntryLink className="iid-btn iid-btn-ghost">See demo</WorkspaceEntryLink>
        </div>
      </section>

      <section className="mkt-wrap mkt-section">
        <div className="mkt-section-head">
          <span className="mkt-label">The platform</span>
          <h2 className="mkt-h2">What lives inside the IIDATECH business OS</h2>
        </div>
        <div className="mkt-grid-3 mkt-features-grid">
          {ABOUT_SHARED.pillars.map((p) => (
            <article key={p.title} className="mkt-feature-card">
              <h3 className="mkt-feature-title">{p.title}</h3>
              <p className="mkt-feature-body">{p.body}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="mkt-wrap mkt-section" id="what-is">
        <div className="mkt-section-head">
          <span className="mkt-label">Definition</span>
          <h2 className="mkt-h2">{copy.whatIs.title}</h2>
          <p className="mkt-sub">{copy.whatIs.body}</p>
        </div>
        <ul className="mkt-service-list">
          {copy.whatIs.bullets.map((b) => (
            <li key={b}>{b}</li>
          ))}
        </ul>
      </section>

      <section className="mkt-wrap mkt-section" id="results">
        <div className="mkt-section-head">
          <span className="mkt-label">Results</span>
          <h2 className="mkt-h2">{copy.results.title}</h2>
        </div>
        <div className="mkt-grid-3 mkt-features-grid">
          {copy.results.items.map((item) => (
            <article key={item.title} className="mkt-feature-card">
              <h3 className="mkt-feature-title">{item.title}</h3>
              <p className="mkt-feature-body">{item.body}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="mkt-wrap mkt-section" id="problem">
        <div className="mkt-section-head">
          <span className="mkt-label">Problem</span>
          <h2 className="mkt-h2">{copy.problem.title}</h2>
          <p className="mkt-sub">{copy.problem.body}</p>
        </div>
        <ul className="mkt-service-list">
          {copy.problem.points.map((p) => (
            <li key={p}>{p}</li>
          ))}
        </ul>
      </section>

      <section className="mkt-wrap mkt-section" id="why-us">
        <div className="mkt-section-head">
          <span className="mkt-label">Why us</span>
          <h2 className="mkt-h2">{copy.whyUs.title}</h2>
        </div>
        <div className="mkt-about-grid">
          {copy.whyUs.points.map((p) => (
            <article key={p.title} className="mkt-about-card">
              <h3 className="mkt-feature-title">{p.title}</h3>
              <p className="mkt-feature-body">{p.body}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="mkt-wrap mkt-section" id="who">
        <div className="mkt-section-head">
          <span className="mkt-label">Audience</span>
          <h2 className="mkt-h2">{copy.whoFor.title}</h2>
          <p className="mkt-sub">{copy.whoFor.body}</p>
        </div>
        <div className="mkt-about-grid">
          <article className="mkt-about-card">
            <h3 className="mkt-feature-title">A strong fit if you are</h3>
            <ul className="mkt-service-list">
              {copy.whoFor.fits.map((f) => (
                <li key={f}>{f}</li>
              ))}
            </ul>
          </article>
          <article className="mkt-about-card">
            <h3 className="mkt-feature-title">Probably not if you want</h3>
            <ul className="mkt-service-list">
              {copy.whoFor.notFor.map((f) => (
                <li key={f}>{f}</li>
              ))}
            </ul>
          </article>
        </div>
      </section>

      <section className="mkt-wrap mkt-section" id="how">
        <div className="mkt-section-head">
          <span className="mkt-label">How it helps</span>
          <h2 className="mkt-h2">{copy.howItHelps.title}</h2>
        </div>
        <div className="mkt-process">
          {copy.howItHelps.steps.map((s, i) => (
            <div key={s.title} className="mkt-process-step">
              <p className="mkt-step-big">{String(i + 1).padStart(2, "0")}</p>
              <h3>{s.title}</h3>
              <p>{s.body}</p>
            </div>
          ))}
        </div>
        <Link href="/how-it-works" className="iid-btn iid-btn-ghost mkt-section-cta-inline">
          See the full walkthrough →
        </Link>
      </section>

      <section className="mkt-wrap mkt-section" id="faq">
        <div className="mkt-section-head">
          <span className="mkt-label">FAQ</span>
          <h2 className="mkt-h2">Common questions about IIDATECH</h2>
        </div>
        <div className="mkt-faq-grid mkt-faq-grid-2">
          {copy.faqs.map((faq) => (
            <article key={faq.q} className="mkt-faq-card">
              <h3>{faq.q}</h3>
              <p>{faq.a}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="mkt-wrap mkt-section mkt-section-last">
        <div className="mkt-cta-banner">
          <span className="mkt-label">Next step</span>
          <h2 className="mkt-h2">Ready to see IIDATECH on your idea or company?</h2>
          <p className="mkt-sub">Free credits · No credit card · 5-minute setup</p>
          <div className="mkt-hero-cta mkt-cta-banner-actions">
            <Link href={copy.ctaHref} className="iid-btn iid-btn-primary">
              {copy.ctaLabel}
            </Link>
            <WorkspaceEntryLink className="mkt-text-link">See demo</WorkspaceEntryLink>
          </div>
        </div>
      </section>
    </MarketingShell>
  );
}
