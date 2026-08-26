import type { Metadata } from "next";
import { LandingPage } from "@/components/marketing/LandingPage";
import { SITE_EMAIL, SITE_URL } from "@/lib/site";

export const metadata: Metadata = {
  title: "IIDATECH | Business OS for Founders & B2B",
  description:
    "IIDATECH helps founders and established B2B companies research markets, build plans, run Employee OS, and automate workflows in one workspace.",
  alternates: { canonical: `${SITE_URL}/` },
  openGraph: {
    title: "IIDATECH — Business OS for founders and B2B companies",
    description: "Research, plan, execute, and automate on one platform. Free credits. No card required.",
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
        "Business OS for founders and B2B companies — market research, planning, mentorship, Employee OS, and automation.",
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
        "AI market research reports",
        "Business plan generation",
        "Mentor guidance",
        "Employee OS AI workforce",
        "Workflow automation",
        "Company GAUGE audit",
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
