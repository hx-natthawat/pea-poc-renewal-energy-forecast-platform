"use client";

import { ArrowDown, ArrowUp, ChevronDown, ChevronRight, Clock, Globe, User } from "lucide-react";
import { useState } from "react";
import type { AuditLogEntry } from "@/types/audit";

interface AuditLogTableProps {
  logs: AuditLogEntry[];
  isLoading?: boolean;
}

type SortField = "time" | "user_id" | "action" | "resource_type" | "response_status";
type SortDirection = "asc" | "desc";

const getStatusColor = (status: number | null): string => {
  if (!status) return "text-gray-500 bg-gray-50";
  if (status >= 200 && status < 300) return "text-green-700 bg-green-50";
  if (status >= 400 && status < 500) return "text-amber-700 bg-amber-50";
  if (status >= 500) return "text-red-700 bg-red-50";
  return "text-gray-700 bg-gray-50";
};

const getMethodColor = (method: string | null): string => {
  if (!method) return "text-gray-600";
  switch (method.toUpperCase()) {
    case "GET":
      return "text-blue-600";
    case "POST":
      return "text-green-600";
    case "PUT":
    case "PATCH":
      return "text-amber-600";
    case "DELETE":
      return "text-red-600";
    default:
      return "text-gray-600";
  }
};

export default function AuditLogTable({ logs, isLoading = false }: AuditLogTableProps) {
  const [expandedRows, setExpandedRows] = useState<Set<number>>(new Set());
  const [sortField, setSortField] = useState<SortField>("time");
  const [sortDirection, setSortDirection] = useState<SortDirection>("desc");

  const toggleRow = (id: number) => {
    const newExpanded = new Set(expandedRows);
    if (newExpanded.has(id)) {
      newExpanded.delete(id);
    } else {
      newExpanded.add(id);
    }
    setExpandedRows(newExpanded);
  };

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === "asc" ? "desc" : "asc");
    } else {
      setSortField(field);
      setSortDirection("desc");
    }
  };

  const sortedLogs = [...logs].sort((a, b) => {
    let aValue: string | number | null = a[sortField];
    let bValue: string | number | null = b[sortField];

    if (aValue === null) return 1;
    if (bValue === null) return -1;

    if (typeof aValue === "string") aValue = aValue.toLowerCase();
    if (typeof bValue === "string") bValue = bValue.toLowerCase();

    if (aValue < bValue) return sortDirection === "asc" ? -1 : 1;
    if (aValue > bValue) return sortDirection === "asc" ? 1 : -1;
    return 0;
  });

  const SortIcon = ({ field }: { field: SortField }) => {
    if (sortField !== field) return null;
    return sortDirection === "asc" ? (
      <ArrowUp className="w-3 h-3 inline ml-1" />
    ) : (
      <ArrowDown className="w-3 h-3 inline ml-1" />
    );
  };

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        <div className="animate-pulse p-4">
          <div className="h-8 bg-gray-200 rounded mb-4" />
          <div className="space-y-3">
            <div key="skeleton-1" className="h-16 bg-gray-100 rounded" />
            <div key="skeleton-2" className="h-16 bg-gray-100 rounded" />
            <div key="skeleton-3" className="h-16 bg-gray-100 rounded" />
            <div key="skeleton-4" className="h-16 bg-gray-100 rounded" />
            <div key="skeleton-5" className="h-16 bg-gray-100 rounded" />
          </div>
        </div>
      </div>
    );
  }

  if (logs.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-md p-8 text-center">
        <Clock className="w-12 h-12 text-gray-300 mx-auto mb-3" />
        <p className="text-gray-500">No audit logs found</p>
        <p className="text-xs text-gray-400 mt-1">Try adjusting your filters</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden">
      {/* Desktop Table */}
      <div className="hidden lg:block overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="w-8 px-3 py-3" />
              <th
                className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                onClick={() => handleSort("time")}
              >
                Time <SortIcon field="time" />
              </th>
              <th
                className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                onClick={() => handleSort("user_id")}
              >
                User <SortIcon field="user_id" />
              </th>
              <th
                className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                onClick={() => handleSort("action")}
              >
                Action <SortIcon field="action" />
              </th>
              <th
                className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                onClick={() => handleSort("resource_type")}
              >
                Resource <SortIcon field="resource_type" />
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                Method
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                Path
              </th>
              <th
                className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                onClick={() => handleSort("response_status")}
              >
                Status <SortIcon field="response_status" />
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {sortedLogs.map((log) => (
              <>
                <tr
                  key={log.id}
                  className="hover:bg-gray-50 cursor-pointer transition-colors"
                  onClick={() => toggleRow(log.id)}
                >
                  <td className="px-3 py-3 text-center">
                    {expandedRows.has(log.id) ? (
                      <ChevronDown className="w-4 h-4 text-gray-500" />
                    ) : (
                      <ChevronRight className="w-4 h-4 text-gray-500" />
                    )}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-xs text-gray-600">
                    {new Date(log.time).toLocaleString("en-GB", {
                      year: "numeric",
                      month: "2-digit",
                      day: "2-digit",
                      hour: "2-digit",
                      minute: "2-digit",
                      second: "2-digit",
                    })}
                  </td>
                  <td className="px-4 py-3 text-sm">
                    <div className="font-medium text-gray-900">{log.user_id || "Anonymous"}</div>
                    {log.user_email && (
                      <div className="text-xs text-gray-500">{log.user_email}</div>
                    )}
                  </td>
                  <td className="px-4 py-3 text-sm">
                    <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs font-medium">
                      {log.action}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-900">
                    {log.resource_type || "-"}
                    {log.resource_id && (
                      <div className="text-xs text-gray-500">ID: {log.resource_id}</div>
                    )}
                  </td>
                  <td className="px-4 py-3 text-xs">
                    <span className={`font-semibold ${getMethodColor(log.request_method)}`}>
                      {log.request_method || "-"}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-xs text-gray-600 max-w-xs truncate">
                    {log.request_path || "-"}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap">
                    <span
                      className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(log.response_status)}`}
                    >
                      {log.response_status || "-"}
                    </span>
                  </td>
                </tr>
                {expandedRows.has(log.id) && (
                  <tr className="bg-gray-50">
                    <td colSpan={8} className="px-4 py-4">
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <h4 className="font-semibold text-gray-700 mb-2">Request Details</h4>
                          <dl className="space-y-1">
                            <div className="flex items-center text-xs">
                              <dt className="text-gray-500 w-24">IP Address:</dt>
                              <dd className="text-gray-900 flex items-center">
                                <Globe className="w-3 h-3 mr-1" />
                                {log.user_ip || "N/A"}
                              </dd>
                            </div>
                            <div className="flex items-center text-xs">
                              <dt className="text-gray-500 w-24">Session:</dt>
                              <dd className="text-gray-900 font-mono text-[10px]">
                                {log.session_id || "N/A"}
                              </dd>
                            </div>
                            <div className="flex items-start text-xs">
                              <dt className="text-gray-500 w-24">User Agent:</dt>
                              <dd className="text-gray-900 text-[10px] break-all">
                                {log.user_agent || "N/A"}
                              </dd>
                            </div>
                          </dl>
                        </div>
                        <div>
                          <h4 className="font-semibold text-gray-700 mb-2">Request Body</h4>
                          {log.request_body ? (
                            <pre className="text-xs bg-gray-100 p-2 rounded overflow-x-auto max-h-32">
                              {JSON.stringify(log.request_body, null, 2)}
                            </pre>
                          ) : (
                            <p className="text-xs text-gray-400 italic">No request body</p>
                          )}
                        </div>
                      </div>
                    </td>
                  </tr>
                )}
              </>
            ))}
          </tbody>
        </table>
      </div>

      {/* Mobile Card View */}
      <div className="lg:hidden divide-y divide-gray-200">
        {sortedLogs.map((log) => (
          <div key={log.id} className="p-4">
            <button
              type="button"
              className="flex items-start justify-between cursor-pointer w-full text-left"
              onClick={() => toggleRow(log.id)}
            >
              <div className="flex-1 min-w-0">
                <div className="flex items-center space-x-2 mb-2">
                  <span className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded text-xs font-medium">
                    {log.action}
                  </span>
                  <span
                    className={`px-2 py-0.5 rounded text-xs font-medium ${getStatusColor(log.response_status)}`}
                  >
                    {log.response_status || "-"}
                  </span>
                </div>
                <div className="text-sm font-medium text-gray-900 mb-1">
                  <User className="w-3 h-3 inline mr-1" />
                  {log.user_id || "Anonymous"}
                </div>
                <div className="text-xs text-gray-500 flex items-center">
                  <Clock className="w-3 h-3 mr-1" />
                  {new Date(log.time).toLocaleString()}
                </div>
                {log.request_path && (
                  <div className="text-xs text-gray-600 mt-1 truncate">
                    <span className={`font-semibold ${getMethodColor(log.request_method)}`}>
                      {log.request_method}
                    </span>{" "}
                    {log.request_path}
                  </div>
                )}
              </div>
              <div className="ml-2">
                {expandedRows.has(log.id) ? (
                  <ChevronDown className="w-5 h-5 text-gray-500" />
                ) : (
                  <ChevronRight className="w-5 h-5 text-gray-500" />
                )}
              </div>
            </button>

            {expandedRows.has(log.id) && (
              <div className="mt-3 pt-3 border-t border-gray-200 space-y-2 text-xs">
                <div>
                  <span className="text-gray-500">Resource:</span>{" "}
                  <span className="text-gray-900">
                    {log.resource_type || "N/A"}
                    {log.resource_id && ` (${log.resource_id})`}
                  </span>
                </div>
                <div>
                  <span className="text-gray-500">IP:</span>{" "}
                  <span className="text-gray-900">{log.user_ip || "N/A"}</span>
                </div>
                {log.user_email && (
                  <div>
                    <span className="text-gray-500">Email:</span>{" "}
                    <span className="text-gray-900">{log.user_email}</span>
                  </div>
                )}
                {log.request_body && (
                  <div>
                    <span className="text-gray-500">Request Body:</span>
                    <pre className="text-[10px] bg-gray-100 p-2 rounded mt-1 overflow-x-auto">
                      {JSON.stringify(log.request_body, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
