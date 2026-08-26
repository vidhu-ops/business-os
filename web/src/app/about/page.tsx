import type { Metadata } from "next";
import { Suspense } from "react";
import { AboutPage } from "@/components/marketing/AboutPage";
import { ABOUT_SEO_FAQS, ABOUT_SHARED } from "@/components/marketing/aboutContent";
import { SITE_URL } from "@/lib/site";

export const metadata: Metadata = {
  title: "About IIDATECH | Business OS for Founders & B2B",
  description:
    "Learn what IIDATECH is, what results it delivers, what problems it solves, and why founders and B2B companies use one business OS for research, planning, mentorship, and execution.",
  keywords: [
    "about IIDATECH",
    "what is IIDATECH",
    "business OS for founders",
    "B2B market research platform",
    "GAUGE company audit",
    "Employee OS",
    "AI business plan software",
  ],
  alternates: { canonical: `${SITE_URL}/about` },
  openGraph: {
    title: "About IIDATECH — Business OS for founders and B2B companies",
    description: ABOUT_SHARED.oneLiner,
    url: `${SITE_URL}/about`,
    type: "website",
  },
};

const jsonLd = {
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "AboutPage",
      name: "About IIDATECH",
      url: `${SITE_URL}/about`,
      description: ABOUT_SHARED.oneLiner,
      isPartOf: { "@type": "WebSite", name: "IIDATECH", url: SITE_URL },
    },
    {
      "@type": "Organization",
      name: "IIDATECH",
      url: SITE_URL,
      description: ABOUT_SHARED.oneLiner,
    },
    {
      "@type": "FAQPage",
      mainEntity: ABOUT_SEO_FAQS.map((faq) => ({
        "@type": "Question",
        name: faq.q,
        acceptedAnswer: { "@type": "Answer", text: faq.a },
      })),
    },
  ],
};

export default function Page() {
  return (
    <>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }} />
      <Suspense fallback={<main className="mkt-page mkt-wrap mkt-section">Loading about…</main>}>
        <AboutPage />
      </Suspense>
    </>
  );
}
