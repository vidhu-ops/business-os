import type { Metadata } from "next";
import { LandingPage } from "@/components/marketing/LandingPage";
import { SITE_EMAIL, SITE_URL } from "@/lib/site";

export const metadata: Metadata = {
  title: "IIDATECH | Market Research, Business Planning & Growth OS",
  description:
    "Market research for founders, business planning, business consultation, and new business growth — plus Employee OS and automation. Start free on IIDATECH.",
  keywords: [
    "market research for founders",
    "business research",
    "new business growth",
    "business consultation",
    "founder business OS",
    "startup business plan",
    "MSME market research",
    "AI business plan",
    "IIDATECH",
  ],
  alternates: { canonical: `${SITE_URL}/` },
  openGraph: {
    title: "IIDATECH — Market research & business growth OS for founders",
    description: "Research markets, plan new businesses, get consultation guidance, and execute growth in one workspace. Free credits. No card required.",
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

const jsonLd = {
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "Organization",
      name: "IIDATECH",
      url: `${SITE_URL}/`,
      email: SITE_EMAIL,
      telephone: "+919545403431",
      description:
        "Business OS for founders and B2B companies — market research, business planning, business consultation, new business growth, Employee OS, and automation.",
      knowsAbout: [
        "market research",
        "founder tools",
        "business consultation",
        "new business growth",
        "business planning",
        "MSME automation",
      ],
    },
    {
      "@type": "SoftwareApplication",
      name: "IIDATECH Business Ecosystem",
      applicationCategory: "BusinessApplication",
      operatingSystem: "Web",
      url: `${SITE_URL}/`,
      offers: {
        "@type": "Offer",
        price: "0",
        priceCurrency: "INR",
        description: "Free signup with demo access and credits; paid plans coming soon.",
      },
      featureList: [
        "AI market research reports for founders",
        "Business plan generation for new business growth",
        "Business consultation and mentor guidance",
        "Employee OS AI workforce",
        "Workflow automation",
        "Company GAUGE growth audit",
      ],
    },
    {
      "@type": "WebSite",
      name: "IIDATECH",
      url: `${SITE_URL}/`,
    },
  ],
};

export default function Home() {
  return (
    <>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }} />
      <LandingPage />
    </>
  );
}
