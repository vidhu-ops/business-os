import type { MetadataRoute } from "next";
import { SEO_TOPICS } from "@/lib/seo";
import { SITE_URL } from "@/lib/site";

export default function sitemap(): MetadataRoute.Sitemap {
  const base = SITE_URL;
  const now = new Date();
  const staticRoutes: MetadataRoute.Sitemap = [
    { url: `${base}/`, lastModified: now, changeFrequency: "weekly", priority: 1 },
    { url: `${base}/about`, lastModified: now, changeFrequency: "monthly", priority: 0.9 },
    { url: `${base}/pricing`, lastModified: now, changeFrequency: "weekly", priority: 0.9 },
    { url: `${base}/how-it-works`, lastModified: now, changeFrequency: "monthly", priority: 0.85 },
    { url: `${base}/topics`, lastModified: now, changeFrequency: "weekly", priority: 0.9 },
    { url: `${base}/services/research`, lastModified: now, changeFrequency: "weekly", priority: 0.85 },
    { url: `${base}/services/plan`, lastModified: now, changeFrequency: "weekly", priority: 0.85 },
    { url: `${base}/services/mentor`, lastModified: now, changeFrequency: "weekly", priority: 0.85 },
    { url: `${base}/services/execute`, lastModified: now, changeFrequency: "monthly", priority: 0.75 },
    { url: `${base}/services/automate`, lastModified: now, changeFrequency: "monthly", priority: 0.75 },
    { url: `${base}/services/gauge`, lastModified: now, changeFrequency: "weekly", priority: 0.8 },
    { url: `${base}/partners`, lastModified: now, changeFrequency: "monthly", priority: 0.65 },
    { url: `${base}/privacy`, lastModified: now, changeFrequency: "yearly", priority: 0.2 },
    { url: `${base}/terms`, lastModified: now, changeFrequency: "yearly", priority: 0.2 },
    { url: `${base}/login`, lastModified: now, changeFrequency: "monthly", priority: 0.4 },
  ];

  const topicRoutes: MetadataRoute.Sitemap = SEO_TOPICS.map((topic) => ({
    url: `${base}/topics/${topic.slug}`,
    lastModified: now,
    changeFrequency: "weekly" as const,
    priority: 0.88,
  }));

  return [...staticRoutes, ...topicRoutes];
}
