"use client";

import {
  AlertCircle,
  BarChart3,
  ChevronLeft,
  ChevronRight,
  Download,
  RefreshCw,
  Shield,
  Users,
} from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { exportAuditLogs, getAuditLogs, getAuditStats } from "@/lib/api";
import type { AuditLogEntry, AuditLogFilter, AuditLogStats } from "@/types/audit";
import AuditLogFilters from "../filters/AuditLogFilters";
import AuditLogTable from "../tables/AuditLogTable";

// Helper to safely format numbers
const formatNumber = (value: number | undefined | null): string => {
  return (value ?? 0).toLocaleString();
};

export default function AuditLogViewer() {
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [stats, setStats] = useState<AuditLogStats | null>(null);
  const [filters, setFilters] = useState<AuditLogFilter>({});
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalEntries, setTotalEntries] = useState(0);
  const [limit] = useState(50);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isExporting, setIsExporting] = useState(false);

  const loadLogs = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await getAuditLogs(filters, page, limit);

      if (response.status === "success") {
        setLogs(response.data.logs);
        setTotalPages(response.data.pages);
        setTotalEntries(response.data.total);
      }
    } catch (err) {
      console.error("Error fetching audit logs:", err);
      setError("Failed to load audit logs. Please try again.");
    } finally {
      setIsLoading(false);
    }
  }, [filters, page, limit]);

  const loadStats = useCallback(async () => {
    try {
      const response = await getAuditStats(filters.start_date, filters.end_date);

      if (response.status === "success") {
        setStats(response.data.stats);
      }
    } catch (err) {
      console.error("Error fetching audit stats:", err);
    }
  }, [filters.start_date, filters.end_date]);

  useEffect(() => {
    loadLogs();
    loadStats();
  }, [loadLogs, loadStats]);

  const handleFilterChange = (newFilters: AuditLogFilter) => {
    setFilters(newFilters);
    setPage(1); // Reset to first page when filters change
  };

  const handleClearFilters = () => {
    setFilters({});
    setPage(1);
  };

  const handleExport = async (format: "csv" | "json") => {
    setIsExporting(true);
    try {
      const blob = await exportAuditLogs(filters, format);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `audit_logs_${new Date().toISOString().split("T")[0]}.${format}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Error exporting audit logs:", err);
      setError("Failed to export audit logs. Please try again.");
    } finally {
      setIsExporting(false);
    }
  };

  const handleRefresh = () => {
    loadLogs();
    loadStats();
  };

  return (
    <div className="space-y-4 sm:space-y-6">
      {/* Statistics Cards */}
      {stats && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
          <div className="bg-white rounded-lg shadow p-3 sm:p-4 border-l-4 border-blue-500">
            <div className="flex items-center justify-between">
              <div className="min-w-0 flex-1">
                <p className="text-xs sm:text-sm text-gray-500">Total Requests</p>
                <p className="text-lg sm:text-2xl font-bold text-gray-800">
                  {formatNumber(stats.total_requests)}
                </p>
              </div>
              <BarChart3 className="w-8 h-8 sm:w-10 sm:h-10 text-blue-500 opacity-80" />
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-3 sm:p-4 border-l-4 border-purple-500">
            <div className="flex items-center justify-between">
              <div className="min-w-0 flex-1">
                <p className="text-xs sm:text-sm text-gray-500">Unique Users</p>
                <p className="text-lg sm:text-2xl font-bold text-gray-800">
                  {formatNumber(stats.unique_users)}
                </p>
              </div>
              <Users className="w-8 h-8 sm:w-10 sm:h-10 text-purple-500 opacity-80" />
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-3 sm:p-4 border-l-4 border-green-500">
            <div className="flex items-center justify-between">
              <div className="min-w-0 flex-1">
                <p className="text-xs sm:text-sm text-gray-500">Success Rate</p>
                <p className="text-lg sm:text-2xl font-bold text-gray-800">
                  {stats.total_requests > 0
                    ? `${((1 - stats.error_rate) * 100).toFixed(1)}%`
                    : "N/A"}
                </p>
              </div>
              <Shield className="w-8 h-8 sm:w-10 sm:h-10 text-green-500 opacity-80" />
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-3 sm:p-4 border-l-4 border-amber-500">
            <div className="flex items-center justify-between">
              <div className="min-w-0 flex-1">
                <p className="text-xs sm:text-sm text-gray-500">Top Resource</p>
                <p className="text-sm sm:text-lg font-bold text-gray-800 truncate">
                  {Object.entries(stats.resources_breakdown || {}).sort(
                    (a, b) => b[1] - a[1]
                  )[0]?.[0] || "N/A"}
                </p>
                <p className="text-xs text-gray-500">
                  {formatNumber(
                    Object.entries(stats.resources_breakdown || {}).sort(
                      (a, b) => b[1] - a[1]
                    )[0]?.[1]
                  )}{" "}
                  accesses
                </p>
              </div>
              <AlertCircle className="w-8 h-8 sm:w-10 sm:h-10 text-amber-500 opacity-80" />
            </div>
          </div>
        </div>
      )}

      {/* Error Banner */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
          <div className="flex items-center">
            <AlertCircle className="w-5 h-5 mr-2" />
            <span className="font-medium">{error}</span>
          </div>
        </div>
      )}

      {/* Filters */}
      <AuditLogFilters onFilterChange={handleFilterChange} onClear={handleClearFilters} />

      {/* Export Controls */}
      <div className="bg-white rounded-lg shadow-md p-3 sm:p-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm sm:text-base font-semibold text-gray-800">Export Logs</h3>
            <p className="text-xs sm:text-sm text-gray-500">
              Download audit logs in CSV or JSON format
            </p>
          </div>
          <div className="flex space-x-2">
            <button
              type="button"
              onClick={handleRefresh}
              disabled={isLoading}
              className="flex items-center px-3 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 text-xs sm:text-sm font-medium rounded transition-colors disabled:opacity-50"
              title="Refresh"
            >
              <RefreshCw className={`w-3 h-3 sm:w-4 sm:h-4 ${isLoading ? "animate-spin" : ""}`} />
            </button>
            <button
              type="button"
              onClick={() => handleExport("csv")}
              disabled={isExporting}
              className="flex items-center px-3 py-2 bg-[#74045F] hover:bg-[#5A0349] text-white text-xs sm:text-sm font-medium rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Download className="w-3 h-3 sm:w-4 sm:h-4 mr-1" />
              CSV
            </button>
            <button
              type="button"
              onClick={() => handleExport("json")}
              disabled={isExporting}
              className="flex items-center px-3 py-2 bg-gray-600 hover:bg-gray-700 text-white text-xs sm:text-sm font-medium rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Download className="w-3 h-3 sm:w-4 sm:h-4 mr-1" />
              JSON
            </button>
          </div>
        </div>
      </div>

      {/* Audit Log Table */}
      <AuditLogTable logs={logs} isLoading={isLoading} />

      {/* Pagination */}
      {!isLoading && totalPages > 1 && (
        <div className="bg-white rounded-lg shadow-md p-3 sm:p-4">
          <div className="flex items-center justify-between">
            <div className="text-xs sm:text-sm text-gray-600">
              Showing {(page - 1) * limit + 1} to {Math.min(page * limit, totalEntries)} of{" "}
              {totalEntries.toLocaleString()} entries
            </div>
            <div className="flex items-center space-x-2">
              <button
                type="button"
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="flex items-center px-2 sm:px-3 py-1.5 sm:py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 text-xs sm:text-sm font-medium rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <ChevronLeft className="w-3 h-3 sm:w-4 sm:h-4 mr-1" />
                <span className="hidden sm:inline">Previous</span>
              </button>
              <div className="flex items-center space-x-1">
                {[...Array(Math.min(5, totalPages))].map((_, i) => {
                  let pageNum: number;
                  if (totalPages <= 5) {
                    pageNum = i + 1;
                  } else if (page <= 3) {
                    pageNum = i + 1;
                  } else if (page >= totalPages - 2) {
                    pageNum = totalPages - 4 + i;
                  } else {
                    pageNum = page - 2 + i;
                  }

                  return (
                    <button
                      key={pageNum}
                      type="button"
                      onClick={() => setPage(pageNum)}
                      className={`px-2 sm:px-3 py-1 text-xs sm:text-sm font-medium rounded transition-colors ${
                        page === pageNum
                          ? "bg-[#74045F] text-white"
                          : "bg-gray-100 hover:bg-gray-200 text-gray-700"
                      }`}
                    >
                      {pageNum}
                    </button>
                  );
                })}
              </div>
              <button
                type="button"
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="flex items-center px-2 sm:px-3 py-1.5 sm:py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 text-xs sm:text-sm font-medium rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <span className="hidden sm:inline">Next</span>
                <ChevronRight className="w-3 h-3 sm:w-4 sm:h-4 ml-1" />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Footer Note */}
      <div className="bg-gray-50 rounded-lg p-3 sm:p-4 text-xs sm:text-sm text-gray-600">
        <p>
          <Shield className="w-3 h-3 sm:w-4 sm:h-4 inline mr-1" />
          <strong>TOR 7.1.6 Compliance:</strong> Audit logs are retained for 5 years and include
          access logs, attack detection, and full audit trail per PEA security standards.
        </p>
      </div>
    </div>
  );
}
