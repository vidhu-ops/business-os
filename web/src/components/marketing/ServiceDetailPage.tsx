import Link from "next/link";
import { MarketingShell } from "@/components/marketing/MarketingShell";
import { MarketingPhoto, PhotoStrip } from "@/components/marketing/illustrations";
import { WorkspaceEntryLink } from "@/components/WorkspaceEntryLink";
import {
  SERVICE_DETAILS,
  type ServiceDetail,
} from "@/components/marketing/audienceContent";

export function ServiceDetailPage({ service }: { service: ServiceDetail }) {
  const others = SERVICE_DETAILS.filter((s) => s.id !== service.id);

  return (
    <MarketingShell>
      <section className="mkt-wrap mkt-hero mkt-service-page-hero">
        <div className="mkt-service-page-grid">
          <div className="mkt-service-page-copy">
            <p className="mkt-eyebrow">IIDATECH service</p>
            <h1 className="mkt-hero-title">
              <span className="mkt-hero-os">{service.label}</span>
              <span className="mkt-hero-accent">
                <span className="mkt-hero-accent-word">{service.short.toUpperCase()}</span>
              </span>
            </h1>
            <p className="mkt-lead">{service.summary}</p>
            <div className="mkt-hero-cta">
              <Link href="/login?mode=register" className="iid-btn iid-btn-primary">
                Start free
              </Link>
              <WorkspaceEntryLink className="iid-btn iid-btn-ghost">See demo</WorkspaceEntryLink>
            </div>
          </div>
          <div className="mkt-service-page-media">
            <MarketingPhoto id={service.photoId} className="mkt-hero-photo" />
            {service.videoSrc ? (
              <div className="mkt-wheel-video mkt-service-page-video">
                <video controls playsInline preload="metadata">
                  <source src={service.videoSrc} type="video/mp4" />
                </video>
              </div>
            ) : null}
          </div>
        </div>
      </section>

      <section className="mkt-wrap mkt-section">
        <div className="mkt-section-head">
          <span className="mkt-label">What you get</span>
          <h2 className="mkt-h2">Outcomes for founders and B2B teams</h2>
        </div>
        <div className="mkt-grid-3 mkt-features-grid">
          {service.outcomes.map((item) => (
            <article key={item} className="mkt-feature-card">
              <h3 className="mkt-feature-title">{item}</h3>
            </article>
          ))}
        </div>
      </section>

      <section className="mkt-wrap mkt-section">
        <div className="mkt-split mkt-split-problem">
          <div className="mkt-split-copy">
            <span className="mkt-label">Who it is for</span>
            <h2 className="mkt-h2">Built for real operating contexts</h2>
            <ul className="mkt-service-list">
              {service.whoFor.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>
          <MarketingPhoto id="founder-team" />
        </div>
      </section>

      <section className="mkt-wrap mkt-section">
        <div className="mkt-section-head">
          <span className="mkt-label">In the app</span>
          <h2 className="mkt-h2">How {service.short} works</h2>
        </div>
        <div className="mkt-process">
          {service.steps.map((step, i) => (
            <div key={step} className="mkt-process-step">
              <p className="mkt-step-big">{String(i + 1).padStart(2, "0")}</p>
              <h3>Step {i + 1}</h3>
              <p>{step}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="mkt-wrap mkt-section">
        <div className="mkt-section-head">
          <span className="mkt-label">FAQ</span>
          <h2 className="mkt-h2">Common questions</h2>
        </div>
        <div className="mkt-about-grid">
          {service.faqs.map((faq) => (
            <article key={faq.q} className="mkt-about-card">
              <h3 className="mkt-feature-title">{faq.q}</h3>
              <p className="mkt-feature-body">{faq.a}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="mkt-wrap mkt-section">
        <div className="mkt-section-head">
          <span className="mkt-label">More services</span>
          <h2 className="mkt-h2">Explore the rest of the platform</h2>
        </div>
        <PhotoStrip ids={others.slice(0, 4).map((s) => s.photoId)} />
        <div className="mkt-service-more-row">
          {others.map((s) => (
            <Link key={s.slug} href={`/services/${s.slug}`} className="iid-btn iid-btn-ghost">
              {s.label}
            </Link>
          ))}
        </div>
      </section>

      <section className="mkt-wrap mkt-section mkt-section-last">
        <div className="mkt-cta-banner">
          <span className="mkt-label">Ready?</span>
          <h2 className="mkt-h2">Start with {service.label}</h2>
          <p className="mkt-sub">Free signup credits · demo workspace · WhatsApp +91 95454 03431</p>
          <div className="mkt-hero-cta mkt-cta-banner-actions">
            <Link href="/login?mode=register" className="iid-btn iid-btn-primary">
              Start free
            </Link>
            <Link href="/how-it-works" className="iid-btn iid-btn-ghost">
              How it works
            </Link>
          </div>
        </div>
      </section>
    </MarketingShell>
  );
}
