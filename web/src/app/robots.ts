import type { MetadataRoute } from "next";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: "*",
      allow: "/",
      disallow: ["/app/", "/api/", "/checkout", "/payment/"],
    },
    sitemap: "https://iidatech.biz/sitemap.xml",
    host: "https://iidatech.biz",
  };
}
