import type { NextConfig } from "next";

/**
 * PEA RE Forecast Platform - Next.js Configuration
 *
 * API ROUTING ARCHITECTURE:
 * ========================
 * Frontend always uses `/backend/*` for API calls. This is handled by:
 *
 * 1. LOCAL DEVELOPMENT (NEXT_PUBLIC_USE_KONG=false or unset):
 *    - Next.js rewrites proxy `/backend/*` → `http://localhost:8000/*`
 *    - No basePath, runs on http://localhost:3000
 *
 * 2. PRODUCTION (NEXT_PUBLIC_USE_KONG=true):
 *    - Kong gateway routes `/backend/*` → backend service
 *    - basePath="/console" for frontend routes
 *    - Runs behind Kong at http://host:8888/console
 *
 * This unified approach ensures:
 * - No CORS issues (same-origin requests)
 * - No environment detection bugs in browser code
 * - Consistent behavior across environments
 */

const useKong = process.env.NEXT_PUBLIC_USE_KONG === "true";

const nextConfig: NextConfig = {
  output: "standalone",

  // basePath: Only set when behind Kong gateway
  ...(useKong && { basePath: "/console" }),

  // Rewrites: Proxy /backend to actual backend in local development
  // In production, Kong handles this routing before requests reach Next.js
  async rewrites() {
    if (useKong) {
      // Production: Kong handles /backend routing
      return [];
    }

    // Local development: Proxy /backend to backend service
    const backendUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    return [
      {
        source: "/backend/:path*",
        destination: `${backendUrl}/:path*`,
      },
    ];
  },
};

export default nextConfig;
