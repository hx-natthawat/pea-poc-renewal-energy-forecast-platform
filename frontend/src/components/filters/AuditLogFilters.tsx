"use client";

import { Calendar, Filter, RotateCcw, Search } from "lucide-react";
import { useState } from "react";
import type { AuditAction, AuditLogFilter, AuditResourceType } from "@/types/audit";

interface AuditLogFiltersProps {
  onFilterChange: (filters: AuditLogFilter) => void;
  onClear: () => void;
}

const ACTION_TYPES: AuditAction[] = [
  "read",
  "create",
  "update",
  "delete",
  "login",
  "logout",
  "export",
  "import",
  "configure",
];

const RESOURCE_TYPES: AuditResourceType[] = [
  "forecast",
  "voltage",
  "alert",
  "model",
  "user",
  "settings",
  "data",
  "report",
];

const REQUEST_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE"];

export default function AuditLogFilters({ onFilterChange, onClear }: AuditLogFiltersProps) {
  const [filters, setFilters] = useState<AuditLogFilter>({});
  const [isExpanded, setIsExpanded] = useState(false);

  const handleChange = (key: keyof AuditLogFilter, value: string | number | undefined) => {
    const newFilters = {
      ...filters,
      [key]: value || undefined,
    };
    setFilters(newFilters);
    onFilterChange(newFilters);
  };

  const handleClear = () => {
    setFilters({});
    onClear();
  };

  const activeFilterCount = Object.values(filters).filter(
    (v) => v !== undefined && v !== ""
  ).length;

  return (
    <div className="bg-white rounded-lg shadow-md p-3 sm:p-4 border-l-4 border-[#74045F]">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center">
          <Filter className="w-4 h-4 sm:w-5 sm:h-5 text-[#74045F] mr-2" />
          <h3 className="text-sm sm:text-lg font-semibold text-gray-800">Filters</h3>
          {activeFilterCount > 0 && (
            <span className="ml-2 bg-[#74045F] text-white text-xs px-2 py-0.5 rounded-full">
              {activeFilterCount}
            </span>
          )}
        </div>
        <div className="flex items-center space-x-2">
          <button
            type="button"
            onClick={handleClear}
            className="flex items-center text-xs sm:text-sm text-gray-600 hover:text-gray-800 px-2 sm:px-3 py-1 hover:bg-gray-100 rounded transition-colors"
          >
            <RotateCcw className="w-3 h-3 sm:w-4 sm:h-4 mr-1" />
            <span className="hidden sm:inline">Clear</span>
          </button>
          <button
            type="button"
            onClick={() => setIsExpanded(!isExpanded)}
            className="sm:hidden text-xs text-[#74045F] font-medium"
          >
            {isExpanded ? "Hide" : "Show"}
          </button>
        </div>
      </div>

      {/* Filter Grid - Always visible on desktop, toggleable on mobile */}
      <div className={`${isExpanded ? "block" : "hidden"} sm:block`}>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
          {/* Date Range */}
          <label className="block">
            <span className="block text-xs font-medium text-gray-700 mb-1">
              <Calendar className="w-3 h-3 inline mr-1" />
              Start Date
            </span>
            <input
              type="datetime-local"
              value={filters.start_date || ""}
              onChange={(e) => handleChange("start_date", e.target.value)}
              className="w-full px-2 py-1.5 text-xs sm:text-sm border border-gray-300 rounded focus:ring-2 focus:ring-[#74045F] focus:border-transparent"
            />
          </label>

          <label className="block">
            <span className="block text-xs font-medium text-gray-700 mb-1">
              <Calendar className="w-3 h-3 inline mr-1" />
              End Date
            </span>
            <input
              type="datetime-local"
              value={filters.end_date || ""}
              onChange={(e) => handleChange("end_date", e.target.value)}
              className="w-full px-2 py-1.5 text-xs sm:text-sm border border-gray-300 rounded focus:ring-2 focus:ring-[#74045F] focus:border-transparent"
            />
          </label>

          {/* User ID */}
          <label className="block">
            <span className="block text-xs font-medium text-gray-700 mb-1">
              <Search className="w-3 h-3 inline mr-1" />
              User ID / Email
            </span>
            <input
              type="text"
              value={filters.user_id || ""}
              onChange={(e) => handleChange("user_id", e.target.value)}
              placeholder="Search user..."
              className="w-full px-2 py-1.5 text-xs sm:text-sm border border-gray-300 rounded focus:ring-2 focus:ring-[#74045F] focus:border-transparent"
            />
          </label>

          {/* Action Type */}
          <label className="block">
            <span className="block text-xs font-medium text-gray-700 mb-1">Action Type</span>
            <select
              value={filters.action || ""}
              onChange={(e) => handleChange("action", e.target.value)}
              className="w-full px-2 py-1.5 text-xs sm:text-sm border border-gray-300 rounded focus:ring-2 focus:ring-[#74045F] focus:border-transparent"
            >
              <option value="">All Actions</option>
              {ACTION_TYPES.map((action) => (
                <option key={action} value={action}>
                  {action.charAt(0).toUpperCase() + action.slice(1)}
                </option>
              ))}
            </select>
          </label>

          {/* Resource Type */}
          <label className="block">
            <span className="block text-xs font-medium text-gray-700 mb-1">Resource Type</span>
            <select
              value={filters.resource_type || ""}
              onChange={(e) => handleChange("resource_type", e.target.value)}
              className="w-full px-2 py-1.5 text-xs sm:text-sm border border-gray-300 rounded focus:ring-2 focus:ring-[#74045F] focus:border-transparent"
            >
              <option value="">All Resources</option>
              {RESOURCE_TYPES.map((resource) => (
                <option key={resource} value={resource}>
                  {resource.charAt(0).toUpperCase() + resource.slice(1)}
                </option>
              ))}
            </select>
          </label>

          {/* Request Method */}
          <label className="block">
            <span className="block text-xs font-medium text-gray-700 mb-1">HTTP Method</span>
            <select
              value={filters.request_method || ""}
              onChange={(e) => handleChange("request_method", e.target.value)}
              className="w-full px-2 py-1.5 text-xs sm:text-sm border border-gray-300 rounded focus:ring-2 focus:ring-[#74045F] focus:border-transparent"
            >
              <option value="">All Methods</option>
              {REQUEST_METHODS.map((method) => (
                <option key={method} value={method}>
                  {method}
                </option>
              ))}
            </select>
          </label>

          {/* Response Status */}
          <label className="block">
            <span className="block text-xs font-medium text-gray-700 mb-1">Status Code</span>
            <select
              value={filters.response_status || ""}
              onChange={(e) =>
                handleChange("response_status", e.target.value ? Number(e.target.value) : undefined)
              }
              className="w-full px-2 py-1.5 text-xs sm:text-sm border border-gray-300 rounded focus:ring-2 focus:ring-[#74045F] focus:border-transparent"
            >
              <option value="">All Status</option>
              <option value="200">200 OK</option>
              <option value="201">201 Created</option>
              <option value="400">400 Bad Request</option>
              <option value="401">401 Unauthorized</option>
              <option value="403">403 Forbidden</option>
              <option value="404">404 Not Found</option>
              <option value="500">500 Server Error</option>
            </select>
          </label>
        </div>
      </div>

      {/* Quick Filters */}
      <div className="mt-3 pt-3 border-t border-gray-100">
        <p className="text-xs text-gray-500 mb-2">Quick Filters:</p>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => {
              const now = new Date();
              const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
                .toISOString()
                .slice(0, 16);
              handleChange("start_date", today);
            }}
            className="text-xs px-2 py-1 bg-gray-100 hover:bg-gray-200 rounded transition-colors"
          >
            Today
          </button>
          <button
            type="button"
            onClick={() => {
              const now = new Date();
              const yesterday = new Date(now.getTime() - 24 * 60 * 60 * 1000)
                .toISOString()
                .slice(0, 16);
              handleChange("start_date", yesterday);
            }}
            className="text-xs px-2 py-1 bg-gray-100 hover:bg-gray-200 rounded transition-colors"
          >
            Last 24h
          </button>
          <button
            type="button"
            onClick={() => {
              const now = new Date();
              const lastWeek = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000)
                .toISOString()
                .slice(0, 16);
              handleChange("start_date", lastWeek);
            }}
            className="text-xs px-2 py-1 bg-gray-100 hover:bg-gray-200 rounded transition-colors"
          >
            Last 7d
          </button>
          <button
            type="button"
            onClick={() => handleChange("action", "login")}
            className="text-xs px-2 py-1 bg-blue-100 hover:bg-blue-200 text-blue-700 rounded transition-colors"
          >
            Logins
          </button>
          <button
            type="button"
            onClick={() => handleChange("action", "delete")}
            className="text-xs px-2 py-1 bg-red-100 hover:bg-red-200 text-red-700 rounded transition-colors"
          >
            Deletes
          </button>
        </div>
      </div>
    </div>
  );
}
