import type { Metadata } from "next";
import { LandingPage } from "@/components/marketing/LandingPage";
import {
  CORE_BUSINESS_KEYWORDS,
  SEO_TOPICS,
  faqJsonLd,
  graphJsonLd,
  organizationJsonLd,
  softwareJsonLd,
  websiteJsonLd,
} from "@/lib/seo";
import { SITE_URL } from "@/lib/site";

export const metadata: Metadata = {
  title: "IIDATECH | Market Research, Business Planning & Growth OS",
  description:
    "Market research for founders, business planning, business consultation, and new business growth — plus Employee OS and automation. Start free on IIDATECH.",
  keywords: [...CORE_BUSINESS_KEYWORDS],
  alternates: { canonical: `${SITE_URL}/` },
  openGraph: {
    title: "IIDATECH — Market research & business growth OS for founders",
    description:
      "Research markets, plan new businesses, get consultation guidance, and execute growth in one workspace. Free credits. No card required.",
    url: `${SITE_URL}/`,
    siteName: "IIDATECH",
    type: "website",
    locale: "en_IN",
    images: [{ url: "/marketing/frames/research.png", width: 1200, height: 630, alt: "IIDATECH product" }],
  },
  twitter: {
    card: "summary_large_image",
    title: "IIDATECH | Founder & B2B business OS",
    description: "AI market research, business plans, Mentor, Employee OS, and automation — one workspace.",
    images: ["/marketing/frames/research.png"],
  },
  robots: { index: true, follow: true },
};

const homeFaqs = [
  {
    q: "What is IIDATECH?",
    a: "IIDATECH is a business OS for founders and B2B companies covering market research, business planning, business consultation, Employee OS execution, and automation.",
  },
  {
    q: "Can founders get market research without an analyst team?",
    a: "Yes. IIDATECH generates structured market research reports for founders and MSMEs, then connects them to planning and execution in the same workspace.",
  },
  {
    q: "Does IIDATECH offer business consultation?",
    a: "Mentor provides business consultation grounded in your project memory, research, plan, and GAUGE audit — with next actions you can approve.",
  },
  {
    q: "Is there a free way to try IIDATECH?",
    a: "Yes. Start free with credits, or open the live demo workspace to browse sample research, plans, and Employee OS.",
  },
];

const jsonLd = graphJsonLd([
  organizationJsonLd(),
  websiteJsonLd(),
  softwareJsonLd(),
  faqJsonLd(homeFaqs),
  {
    "@type": "ItemList",
    name: "IIDATECH business topics",
    itemListElement: SEO_TOPICS.map((topic, index) => ({
      "@type": "ListItem",
      position: index + 1,
      name: topic.title,
      url: `${SITE_URL}/topics/${topic.slug}`,
    })),
  },
]);

export default function Home() {
  return (
    <>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }} />
      <LandingPage />
    </>
  );
}
