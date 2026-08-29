import type { NextConfig } from "next";
import path from "path";

// Must match FastAPI (see Dockerfile / render-combined-start.sh). Wrong default broke local auth.
const apiBase = (process.env.API_URL || process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000").replace(/\/$/, "");

// Dev-friendly proxy: Turbopack was not mounting app/api/v1/[...path] reliably.
// Production Docker build still uses the route handler; rewrites also work in prod.
const nextConfig: NextConfig = {
  // Keep Turbopack rooted at web/ so Next resolves packages correctly under src/app.
  turbopack: {
    root: path.resolve(__dirname),
  },
  async redirects() {
    return [
      { source: "/analystics", destination: "/app/analytics", permanent: false },
      { source: "/app/analystics", destination: "/app/analytics", permanent: false },
    ];
  },
  async rewrites() {
    return {
      afterFiles: [
        {
          source: "/api/v1/:path*",
          destination: `${apiBase}/api/v1/:path*`,
        },
      ],
      // If the dedicated page is missing from a stale image, still open CRM analytics.
      fallback: [
        { source: "/app/analytics", destination: "/app/crm" },
        { source: "/analytics", destination: "/app/crm" },
      ],
    };
  },
};

export default nextConfig;