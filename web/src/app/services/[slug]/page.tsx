import type { Metadata } from "next";
import { notFound } from "next/navigation";
import {
  SERVICE_DETAILS,
  getServiceBySlug,
} from "@/components/marketing/audienceContent";
import { ServiceDetailPage } from "@/components/marketing/ServiceDetailPage";
import { SITE_URL } from "@/lib/site";

type Props = { params: Promise<{ slug: string }> };

export function generateStaticParams() {
  return SERVICE_DETAILS.map((s) => ({ slug: s.slug }));
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  const service = getServiceBySlug(slug);
  if (!service) return { title: "Service | IIDATECH" };
  const keywordMap: Record<string, string[]> = {
    research: ["market research for founders", "business research", "MSME market research", "AI market research"],
    plan: ["business planning", "startup business plan", "new business growth", "AI business plan"],
    mentor: ["business consultation", "founder mentoring", "startup advice"],
    execute: ["Employee OS", "AI workforce", "founder execution"],
    automate: ["business automation", "MSME automation", "workflow automation"],
    gauge: ["company growth audit", "business growth assessment", "B2B audit"],
  };
  return {
    title: `${service.label} | Market Research & Business Growth | IIDATECH`,
    description: `${service.summary} Built for founders and B2B teams who need market research, business planning, consultation, and growth execution.`,
    keywords: ["IIDATECH", service.label.toLowerCase(), ...(keywordMap[slug] || [])],
    alternates: { canonical: `${SITE_URL}/services/${slug}` },
    robots: { index: true, follow: true },
    openGraph: {
      title: `${service.label} | IIDATECH`,
      description: service.summary,
      url: `${SITE_URL}/services/${slug}`,
    },
  };
}

export default async function Page({ params }: Props) {
  const { slug } = await params;
  const service = getServiceBySlug(slug);
  if (!service) notFound();
  return <ServiceDetailPage service={service} />;
}
