import type { NextConfig } from "next";

const apiBase = (process.env.API_URL || process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8001").replace(/\/$/, "");

// Dev-friendly proxy: Turbopack was not mounting app/api/v1/[...path] reliably.
// Production Docker build still uses the route handler; rewrites also work in prod.
const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/v1/:path*",
        destination: `${apiBase}/api/v1/:path*`,
      },
    ];
  },
};

export default nextConfig;