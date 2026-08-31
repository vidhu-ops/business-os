import Link from "next/link";
import { MarketingShell } from "@/components/marketing/MarketingShell";
import { WorkspaceEntryLink } from "@/components/WorkspaceEntryLink";
import type { SeoTopic } from "@/lib/seo";
import { SEO_TOPICS } from "@/lib/seo";

export function SeoTopicPage({ topic }: { topic: SeoTopic }) {
  const related = SEO_TOPICS.filter((t) => t.slug !== topic.slug).slice(0, 4);

  return (
    <MarketingShell>
      <section className="mkt-wrap mkt-hero mkt-service-page-hero">
        <p className="mkt-eyebrow">IIDATECH business guide</p>
        <h1 className="mkt-hero-title mkt-hero-title-plain">{topic.h1}</h1>
        <p className="mkt-lead">{topic.intro}</p>
        <div className="mkt-hero-cta">
          <Link href={topic.primaryCta.href} className="iid-btn iid-btn-primary">
            {topic.primaryCta.label}
          </Link>
          <Link href="/login?mode=register" className="iid-btn iid-btn-ghost">
            Start free
          </Link>
          <WorkspaceEntryLink className="iid-btn iid-btn-ghost">See demo</WorkspaceEntryLink>
        </div>
      </section>

      <section className="mkt-wrap mkt-section">
        <div className="mkt-about-grid">
          {topic.sections.map((section) => (
            <article key={section.heading} className="mkt-about-card">
              <h2 className="mkt-feature-title">{section.heading}</h2>
              <p className="mkt-feature-body">{section.body}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="mkt-wrap mkt-section">
        <div className="mkt-section-head">
          <span className="mkt-label">FAQ</span>
          <h2 className="mkt-h2">Common questions about {topic.title.toLowerCase()}</h2>
        </div>
        <div className="mkt-about-grid">
          {topic.faqs.map((faq) => (
            <article key={faq.q} className="mkt-about-card">
              <h3 className="mkt-feature-title">{faq.q}</h3>
              <p className="mkt-feature-body">{faq.a}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="mkt-wrap mkt-section">
        <div className="mkt-section-head">
          <span className="mkt-label">Related business topics</span>
          <h2 className="mkt-h2">Keep exploring how founders use IIDATECH</h2>
        </div>
        <div className="mkt-footer-keywords" style={{ marginTop: 0 }}>
          {related.map((item) => (
            <Link key={item.slug} href={`/topics/${item.slug}`}>
              {item.title}
            </Link>
          ))}
          <Link href="/topics">All business topics</Link>
          <Link href="/services/research">Market research</Link>
          <Link href="/services/plan">Business plan</Link>
          <Link href="/services/mentor">Business consultation</Link>
        </div>
        <div className="mkt-hero-cta" style={{ marginTop: "1.5rem" }}>
          <Link href="/login?mode=register" className="iid-btn iid-btn-primary">
            Start free on IIDATECH
          </Link>
          <Link href="/pricing" className="iid-btn iid-btn-ghost">
            Pricing
          </Link>
        </div>
      </section>
    </MarketingShell>
  );
}
