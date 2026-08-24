import type { Metadata } from "next";
import { notFound } from "next/navigation";
import {
  SERVICE_DETAILS,
  getServiceBySlug,
} from "@/components/marketing/audienceContent";
import { ServiceDetailPage } from "@/components/marketing/ServiceDetailPage";

type Props = { params: Promise<{ slug: string }> };

export function generateStaticParams() {
  return SERVICE_DETAILS.map((s) => ({ slug: s.slug }));
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  const service = getServiceBySlug(slug);
  if (!service) return { title: "Service | IIDATECH" };
  return {
    title: `${service.label} | IIDATECH`,
    description: service.summary,
  };
}

export default async function Page({ params }: Props) {
  const { slug } = await params;
  const service = getServiceBySlug(slug);
  if (!service) notFound();
  return <ServiceDetailPage service={service} />;
}
