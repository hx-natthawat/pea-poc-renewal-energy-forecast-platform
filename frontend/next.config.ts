import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  // Turbopack is now stable in Next.js 15
  // Enable via: next dev --turbopack
};

export default nextConfig;
