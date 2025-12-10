/**
 * API configuration utilities for PEA RE Forecast Platform.
 * Handles dynamic URL resolution for both browser and server contexts.
 */

import type { AuditLogFilter, AuditLogResponse, AuditLogStatsResponse } from "@/types/audit";

/**
 * Get the base API URL based on the current environment.
 * Detects Kong gateway and uses relative URLs to avoid CORS issues.
 */
export function getApiBaseUrl(): string {
  // Server-side rendering: use direct backend URL
  if (typeof window === "undefined") {
    // SSR calls go directly to backend
    return process.env.NEXT_PUBLIC_API_URL || "http://backend:8000";
  }

  // Client-side: detect Kong gateway
  const port = window.location.port;
  const pathname = window.location.pathname || "";
  const hostname = window.location.hostname;

  // Kong gateway detection (most common case first)
  // Port 8888 = Kong gateway, use relative /backend path
  if (port === "8888") {
    return "/backend";
  }

  // Check if accessed via /console path (Kong basePath routing)
  if (pathname.startsWith("/console")) {
    return "/backend";
  }

  // Environment variable override (build-time)
  if (process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL;
  }

  // Direct localhost access on port 3000 - use backend at 8000
  const isLocalhost = hostname === "localhost" || hostname === "127.0.0.1";
  if (isLocalhost && (port === "3000" || port === "")) {
    return "http://localhost:8000";
  }

  // Default: use relative backend path (production)
  return "/backend";
}

/**
 * Get the WebSocket base URL based on the current environment.
 * Detects Kong gateway and uses appropriate WebSocket URL.
 */
export function getWebSocketBaseUrl(): string {
  // Server-side fallback
  if (typeof window === "undefined") {
    return process.env.NEXT_PUBLIC_WS_URL || "ws://backend:8000/api/v1/ws";
  }

  // Use environment variable if configured
  if (process.env.NEXT_PUBLIC_WS_URL) {
    return process.env.NEXT_PUBLIC_WS_URL;
  }

  const port = window.location.port;
  const pathname = window.location.pathname || "";
  const hostname = window.location.hostname;
  const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";

  // Kong gateway detection (port 8888)
  if (port === "8888") {
    return `${wsProtocol}//${window.location.host}/backend/api/v1/ws`;
  }

  // Check if accessed via /console path (Kong basePath routing)
  if (pathname.startsWith("/console")) {
    return `${wsProtocol}//${window.location.host}/backend/api/v1/ws`;
  }

  // Direct localhost access - connect to backend port 8000
  const isLocalhost = hostname === "localhost" || hostname === "127.0.0.1";
  if (isLocalhost && (port === "3000" || port === "")) {
    return `ws://${hostname}:8000/api/v1/ws`;
  }

  // Default: production with /backend prefix
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
