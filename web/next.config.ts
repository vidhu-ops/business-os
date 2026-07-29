import type { NextConfig } from "next";

// API proxying is handled at runtime by web/src/app/api/v1/[...path]/route.ts
// so API_URL can stay http://127.0.0.1:8000 on Replit without a rebuild.
const nextConfig: NextConfig = {};

export default nextConfig;
