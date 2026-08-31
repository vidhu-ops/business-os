import type { Metadata } from "next";
import Link from "next/link";
import { MarketingShell } from "@/components/marketing/MarketingShell";
import {
  CORE_BUSINESS_KEYWORDS,
  SEO_TOPICS,
  breadcrumbJsonLd,
  graphJsonLd,
  organizationJsonLd,
  websiteJsonLd,
} from "@/lib/seo";
import { SITE_URL } from "@/lib/site";

export const metadata: Metadata = {
  title: "Business Topics | Market Research, Consultation & Growth",
  description:
    "Explore IIDATECH guides on market research for founders, business consultation, new business growth, startup business plans, MSME tools, and company growth audits.",
  keywords: [...CORE_BUSINESS_KEYWORDS],
  alternates: { canonical: `${SITE_URL}/topics` },
  robots: { index: true, follow: true },
  openGraph: {
    title: "IIDATECH business topics for founders and MSMEs",
    description: "Guides that connect business research, planning, consultation, and growth execution.",
    url: `${SITE_URL}/topics`,
  },
};

const jsonLd = graphJsonLd([
  organizationJsonLd(),
  websiteJsonLd(),
  breadcrumbJsonLd([
    { name: "Home", path: "/" },
    { name: "Business topics", path: "/topics" },
  ]),
]);

export default function TopicsIndexPage() {
  return (
    <MarketingShell>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }} />
      <section className="mkt-wrap mkt-hero mkt-service-page-hero">
        <p className="mkt-eyebrow">SEO & founder guides</p>
        <h1 className="mkt-hero-title mkt-hero-title-plain">Business topics that lead to IIDATECH</h1>
        <p className="mkt-lead">
          Looking for market research, business consultation, new business growth, or a startup business plan? These
          guides explain how IIDATECH helps founders and B2B teams — then take you into the product.
        </p>
      </section>
      <section className="mkt-wrap mkt-section">
        <div className="mkt-about-grid">
          {SEO_TOPICS.map((topic) => (
            <article key={topic.slug} className="mkt-about-card">
              <h2 className="mkt-feature-title">
                <Link href={`/topics/${topic.slug}`}>{topic.title}</Link>
              </h2>
              <p className="mkt-feature-body">{topic.description}</p>
              <Link href={`/topics/${topic.slug}`} className="iid-btn iid-btn-ghost" style={{ marginTop: "0.75rem" }}>
                Read guide →
              </Link>
            </article>
          ))}
        </div>
      </section>
    </MarketingShell>
  );
}
