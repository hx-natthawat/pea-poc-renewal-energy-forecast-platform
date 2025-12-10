import type { NextConfig } from "next";

// Use basePath only when behind Kong (production/staging)
// Dev: NEXT_PUBLIC_USE_KONG=false or unset → no basePath
// Prod: NEXT_PUBLIC_USE_KONG=true → basePath="/console"
const useKong = process.env.NEXT_PUBLIC_USE_KONG === "true";

const nextConfig: NextConfig = {
  output: "standalone",
  // Base path for Kong gateway routing (/console/* → frontend)
  // Only enabled when NEXT_PUBLIC_USE_KONG=true
  ...(useKong && { basePath: "/console" }),
  // Turbopack is now stable in Next.js 15
  // Enable via: next dev --turbopack
};

export default nextConfig;
