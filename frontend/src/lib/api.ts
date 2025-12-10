/**
 * API configuration utilities for PEA RE Forecast Platform.
 * Handles dynamic URL resolution for both browser and server contexts.
 */

import type { AuditLogFilter, AuditLogResponse, AuditLogStatsResponse } from "@/types/audit";

/**
 * Get the base API URL based on the current environment.
 * Uses NEXT_PUBLIC_API_URL environment variable if set.
 * Falls back to same-origin API in production.
 */
export function getApiBaseUrl(): string {
  // Use environment variable if configured (works on both server and client)
  if (process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL;
  }

  // Server-side fallback
  if (typeof window === "undefined") {
    return "http://localhost:8000";
  }

  // Client-side: detect Kong gateway (port 8888) or direct access
  if (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1") {
    // If accessing via Kong (port 8888), use /backend prefix
    // Kong routes: /backend/* → backend:8000 (strips /backend)
    if (window.location.port === "8888") {
      return `${window.location.protocol}//${window.location.host}/backend`;
    }
    // Direct frontend access (port 3000) - use backend at port 8000
    return "http://localhost:8000";
  }

  // Production: use /backend prefix (Kong gateway)
  return `${window.location.protocol}//${window.location.host}/backend`;
}

/**
 * Get the WebSocket base URL based on the current environment.
 * Uses NEXT_PUBLIC_WS_URL environment variable if set.
 */
export function getWebSocketBaseUrl(): string {
  // Use environment variable if configured
  if (process.env.NEXT_PUBLIC_WS_URL) {
    return process.env.NEXT_PUBLIC_WS_URL;
  }

  // Server-side fallback
  if (typeof window === "undefined") {
    return "ws://localhost:8000/api/v1/ws";
  }

  // Client-side: derive from API URL or current location
  const apiUrl = getApiBaseUrl();
  const wsProtocol = apiUrl.startsWith("https") ? "wss:" : "ws:";
  const apiHost = apiUrl.replace(/^https?:\/\//, "");

  return `${wsProtocol}//${apiHost}/api/v1/ws`;
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
