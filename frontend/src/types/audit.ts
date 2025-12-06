/**
 * Audit Log Types for PEA RE Forecast Platform
 * TOR 7.1.6 Requirement: Security and Audit Trail
 */

export interface AuditLogEntry {
  id: number;
  time: string;
  user_id: string | null;
  user_email: string | null;
  user_ip: string | null;
  action: string;
  resource_type: string | null;
  resource_id: string | null;
  request_method: string | null;
  request_path: string | null;
  request_body: Record<string, unknown> | null;
  response_status: number | null;
  user_agent: string | null;
  session_id: string | null;
}

export interface AuditLogFilter {
  start_date?: string;
  end_date?: string;
  user_id?: string;
  action?: string;
  resource_type?: string;
  request_method?: string;
  response_status?: number;
}

export interface AuditLogStats {
  total_entries: number;
  unique_users: number;
  actions_breakdown: Record<string, number>;
  top_resources: Array<{
    resource_type: string;
    count: number;
  }>;
  status_breakdown: Record<string, number>;
  methods_breakdown: Record<string, number>;
}

export interface AuditLogResponse {
  status: string;
  data: {
    logs: AuditLogEntry[];
    total: number;
    page: number;
    limit: number;
    pages: number;
  };
}

export interface AuditLogStatsResponse {
  status: string;
  data: {
    stats: AuditLogStats;
  };
}

export interface AuditLogExportRequest {
  filters: AuditLogFilter;
  format: "csv" | "json";
}

export type AuditAction =
  | "read"
  | "create"
  | "update"
  | "delete"
  | "login"
  | "logout"
  | "export"
  | "import"
  | "configure";

export type AuditResourceType =
  | "forecast"
  | "voltage"
  | "alert"
  | "model"
  | "user"
  | "settings"
  | "data"
  | "report";
