import type { MetadataRoute } from "next";
import { SITE_URL } from "@/lib/site";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      {
        userAgent: "*",
        allow: ["/", "/topics", "/topics/", "/services/", "/about", "/pricing", "/how-it-works", "/partners", "/llms.txt"],
        disallow: ["/app/", "/api/", "/checkout", "/payment/", "/login/callback"],
      },
      {
        userAgent: "GPTBot",
        allow: ["/", "/topics", "/llms.txt", "/about", "/services/"],
        disallow: ["/app/", "/api/"],
      },
      {
        userAgent: "Google-Extended",
        allow: ["/", "/topics", "/llms.txt", "/about", "/services/"],
        disallow: ["/app/", "/api/"],
      },
    ],
    sitemap: `${SITE_URL}/sitemap.xml`,
    host: SITE_URL,
  };
}
