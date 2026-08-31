import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { SeoTopicPage } from "@/components/marketing/SeoTopicPage";
import {
  SEO_TOPICS,
  breadcrumbJsonLd,
  faqJsonLd,
  getSeoTopic,
  graphJsonLd,
  organizationJsonLd,
  websiteJsonLd,
} from "@/lib/seo";
import { SITE_URL } from "@/lib/site";

type Props = { params: Promise<{ slug: string }> };

export function generateStaticParams() {
  return SEO_TOPICS.map((topic) => ({ slug: topic.slug }));
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  const topic = getSeoTopic(slug);
  if (!topic) return { title: "Business topic | IIDATECH" };
  return {
    title: `${topic.title} | IIDATECH`,
    description: topic.description,
    keywords: topic.keywords,
    alternates: { canonical: `${SITE_URL}/topics/${topic.slug}` },
    robots: { index: true, follow: true },
    openGraph: {
      title: `${topic.title} | IIDATECH`,
      description: topic.description,
      url: `${SITE_URL}/topics/${topic.slug}`,
      type: "article",
    },
    twitter: {
      card: "summary_large_image",
      title: `${topic.title} | IIDATECH`,
      description: topic.description,
    },
  };
}

export default async function Page({ params }: Props) {
  const { slug } = await params;
  const topic = getSeoTopic(slug);
  if (!topic) notFound();

  const jsonLd = graphJsonLd([
    organizationJsonLd(),
    websiteJsonLd(),
    breadcrumbJsonLd([
      { name: "Home", path: "/" },
      { name: "Business topics", path: "/topics" },
      { name: topic.title, path: `/topics/${topic.slug}` },
    ]),
    faqJsonLd(topic.faqs),
    {
      "@type": "Article",
      headline: topic.h1,
      description: topic.description,
      author: { "@id": `${SITE_URL}/#organization` },
      publisher: { "@id": `${SITE_URL}/#organization` },
      mainEntityOfPage: `${SITE_URL}/topics/${topic.slug}`,
      keywords: topic.keywords.join(", "),
    },
  ]);

  return (
    <>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }} />
      <SeoTopicPage topic={topic} />
    </>
  );
}
