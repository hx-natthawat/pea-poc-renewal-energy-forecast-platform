/**
 * API configuration utilities for PEA RE Forecast Platform.
 *
 * ARCHITECTURE:
 * - Always use `/backend` as the API base path (unified approach)
 * - Infrastructure handles routing:
 *   - Local development: Next.js rewrites `/backend/*` → `http://localhost:8000/*`
 *   - Production (Kong): Kong routes `/backend/*` → backend service
 * - This eliminates environment-specific URL detection issues
 */

import type { AuditLogFilter, AuditLogResponse, AuditLogStatsResponse } from "@/types/audit";

/**
 * Get the base API URL.
 *
 * Strategy: Always use `/backend` relative path.
 * - Local dev: Next.js rewrites handle proxying to localhost:8000
 * - Production: Kong gateway routes to backend service
 *
 * This unified approach avoids:
 * - CORS issues (same-origin requests)
 * - Environment detection bugs
 * - Path-based routing inconsistencies
 */
export function getApiBaseUrl(): string {
  // Server-side rendering needs direct URL for internal calls
  if (typeof window === "undefined") {
    // In SSR context, use environment variable or default to docker service name
    return process.env.NEXT_PUBLIC_API_URL || "http://backend:8000";
  }

  // Client-side: Always use /backend relative path
  // Infrastructure (Next.js rewrites or Kong) handles the routing
  return "/backend";
}

/**
 * Get the WebSocket base URL.
 *
 * Strategy: Use same unified approach as API.
 * - Local dev: Direct connection to backend (WebSocket can't be rewritten)
 * - Production: Use /backend path through Kong
 */
export function getWebSocketBaseUrl(): string {
  // Server-side fallback
  if (typeof window === "undefined") {
    return process.env.NEXT_PUBLIC_WS_URL || "ws://backend:8000/api/v1/ws";
  }

  // Check for explicit WebSocket URL override
  if (process.env.NEXT_PUBLIC_WS_URL) {
    return process.env.NEXT_PUBLIC_WS_URL;
  }

  const hostname = window.location.hostname;
  const port = window.location.port;
  const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";

  // Local development: connect directly to backend
  // WebSocket connections can't be rewritten by Next.js
  const isLocalhost = hostname === "localhost" || hostname === "127.0.0.1";
  if (isLocalhost && (port === "3000" || port === "3001")) {
    return "ws://localhost:8000/api/v1/ws";
  }

  // Production/Kong: use relative path through gateway
  return `${wsProtocol}//${window.location.host}/backend/api/v1/ws`;
}

/**
 * Audit Log API Client
 * TOR 7.1.6 Requirement: Security and Audit Trail
 */

/**
 * Fetch audit logs with optional filters and pagination
 */
export async function getAuditLogs(
  filters?: AuditLogFilter,
  page = 1,
  limit = 50
): Promise<AuditLogResponse> {
  const params = new URLSearchParams({
    page: page.toString(),
    limit: limit.toString(),
  });

  if (filters?.start_date) params.append("start_date", filters.start_date);
  if (filters?.end_date) params.append("end_date", filters.end_date);
  if (filters?.user_id) params.append("user_id", filters.user_id);
  if (filters?.action) params.append("action", filters.action);
  if (filters?.resource_type) params.append("resource_type", filters.resource_type);
  if (filters?.request_method) params.append("request_method", filters.request_method);
  if (filters?.response_status)
    params.append("response_status", filters.response_status.toString());

  const response = await fetch(`${getApiBaseUrl()}/api/v1/audit/logs?${params.toString()}`);

  if (!response.ok) {
    throw new Error(`Failed to fetch audit logs: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Fetch audit log statistics
 */
export async function getAuditStats(
  startDate?: string,
  endDate?: string
): Promise<AuditLogStatsResponse> {
  const params = new URLSearchParams();

  if (startDate) params.append("start_date", startDate);
  if (endDate) params.append("end_date", endDate);

  const response = await fetch(`${getApiBaseUrl()}/api/v1/audit/stats?${params.toString()}`);

  if (!response.ok) {
    throw new Error(`Failed to fetch audit stats: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Export audit logs to CSV or JSON
 */
export async function exportAuditLogs(
  filters?: AuditLogFilter,
  format: "csv" | "json" = "csv"
): Promise<Blob> {
  const params = new URLSearchParams({
    format,
  });

  if (filters?.start_date) params.append("start_date", filters.start_date);
  if (filters?.end_date) params.append("end_date", filters.end_date);
  if (filters?.user_id) params.append("user_id", filters.user_id);
  if (filters?.action) params.append("action", filters.action);
  if (filters?.resource_type) params.append("resource_type", filters.resource_type);
  if (filters?.request_method) params.append("request_method", filters.request_method);
  if (filters?.response_status)
    params.append("response_status", filters.response_status.toString());

  const response = await fetch(`${getApiBaseUrl()}/api/v1/audit/export?${params.toString()}`, {
    method: "POST",
  });

  if (!response.ok) {
    throw new Error(`Failed to export audit logs: ${response.statusText}`);
  }

  return response.blob();
}
