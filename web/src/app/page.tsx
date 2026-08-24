import type { Metadata } from "next";
import { LandingPage } from "@/components/marketing/LandingPage";

export const metadata: Metadata = {
  title: "IIDATECH | Business OS for Founders & B2B Companies — Research, Plan, Execute, Automate",
  description:
    "IIDATECH is the business ecosystem for startup founders and established B2B companies: AI market research, business plan generation, Mentor, Employee OS execution, and workflow automation in one workspace.",
  keywords: [
    "IIDATECH",
    "business OS for founders",
    "AI market research",
    "business plan generator",
    "Employee OS",
    "B2B business automation",
    "MSME market research India",
    "startup business plan software",
    "company audit GAUGE",
  ],
  alternates: { canonical: "https://iidatech.biz/" },
  openGraph: {
    title: "IIDATECH — Business ecosystem for founders and B2B companies",
    description:
      "Research, plan, execute, and automate on one platform. Free demo and signup credits while paid pricing finalizes.",
    url: "https://iidatech.biz/",
    siteName: "IIDATECH",
    type: "website",
    locale: "en_IN",
  },
  twitter: {
    card: "summary_large_image",
    title: "IIDATECH | Founder & B2B business OS",
    description: "AI market research, business plans, Mentor, Employee OS, and automation — one workspace.",
  },
  robots: { index: true, follow: true },
};

const jsonLd = {
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "Organization",
      name: "IIDATECH",
      url: "https://iidatech.biz/",
      email: "vidhugupta1996@gmail.com",
      telephone: "+919545403431",
      description:
        "Business ecosystem platform for founders and B2B companies — market research, business planning, mentorship, Employee OS, and automation.",
    },
    {
      "@type": "SoftwareApplication",
      name: "IIDATECH Business Ecosystem",
      applicationCategory: "BusinessApplication",
      operatingSystem: "Web",
      url: "https://iidatech.biz/",
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
      url: "https://iidatech.biz/",
      potentialAction: {
        "@type": "SearchAction",
        target: "https://iidatech.biz/how-it-works",
        "query-input": "required name=search_term_string",
      },
    },
    {
      "@type": "FAQPage",
      mainEntity: [
        {
          "@type": "Question",
          name: "What is IIDATECH for founders?",
          acceptedAnswer: {
            "@type": "Answer",
            text: "IIDATECH is an all-in-one business OS for startup founders: AI market research, business plan generation, Mentor coaching, Employee OS execution, and automation in one workspace.",
          },
        },
        {
          "@type": "Question",
          name: "How do established B2B companies use IIDATECH?",
          acceptedAnswer: {
            "@type": "Answer",
            text: "Established companies use IIDATECH for GAUGE audits, continuous market intelligence, growth planning, approved Employee OS capacity, and department automation without a large strategy bench.",
          },
        },
        {
          "@type": "Question",
          name: "Does IIDATECH include business research, planning, and automation?",
          acceptedAnswer: {
            "@type": "Answer",
            text: "Yes. Market Research produces sourced reports; Plan builds ICP/GTM financial structure; Automation and Employee OS execute workflows with human approvals.",
          },
        },
      ],
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
