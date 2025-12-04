"use client";

import {
  AlertTriangle,
  Bell,
  Check,
  CheckCircle,
  Clock,
  Radio,
  RefreshCw,
  XCircle,
} from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { useAlertsWebSocket } from "@/hooks";
import { getApiBaseUrl } from "@/lib/api";

interface Alert {
  id: number;
  time: string;
  alert_type: string;
  severity: "critical" | "warning" | "info";
  target_id: string;
  message: string;
  current_value: number | null;
  threshold_value: number | null;
  acknowledged: boolean;
  resolved: boolean;
}

interface AlertStats {
  total: number;
  critical: number;
  warning: number;
  info: number;
  unacknowledged: number;
}

interface TimelineEntry {
  time: string;
  total: number;
  critical: number;
  warning: number;
  info: number;
  affected_prosumers: string[];
}

interface AlertDashboardProps {
  height?: number;
  enableRealtime?: boolean;
}

const SEVERITY_COLORS = {
  critical: "#DC2626",
  warning: "#F59E0B",
  info: "#3B82F6",
};

const SEVERITY_BG = {
  critical: "bg-red-50 border-red-200",
  warning: "bg-amber-50 border-amber-200",
  info: "bg-blue-50 border-blue-200",
};

const SEVERITY_TEXT = {
  critical: "text-red-700",
  warning: "text-amber-700",
  info: "text-blue-700",
};

export default function AlertDashboard({
  height = 250,
  enableRealtime = true,
}: AlertDashboardProps) {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [stats, setStats] = useState<AlertStats | null>(null);
  const [timeline, setTimeline] = useState<TimelineEntry[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [liveUpdateCount, setLiveUpdateCount] = useState(0);

  // WebSocket connection for real-time alert updates
  const { isConnected: wsConnected } = useAlertsWebSocket(
    enableRealtime
      ? (update) => {
          // Add new alert to the list
          const severity =
            update.severity === "critical" ||
            update.severity === "warning" ||
            update.severity === "info"
              ? update.severity
              : "warning";

          const newAlert: Alert = {
            id: Date.now(),
            time: new Date().toISOString(),
            alert_type: update.alert_type || "voltage",
            severity,
            target_id: update.target_id || "unknown",
            message: update.message || "Alert received",
            current_value: update.value || null,
            threshold_value: null,
            acknowledged: false,
            resolved: false,
          };

          setAlerts((prev) => [newAlert, ...prev].slice(0, 50));
          setLiveUpdateCount((prev) => prev + 1);

          // Update stats
          setStats((prev) =>
            prev
              ? {
                  ...prev,
                  total: prev.total + 1,
                  [newAlert.severity]: (prev[newAlert.severity as keyof AlertStats] as number) + 1,
                  unacknowledged: prev.unacknowledged + 1,
                }
              : null
          );
        }
      : undefined
  );

  const loadData = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const [alertsRes, statsRes, timelineRes] = await Promise.all([
        fetch(`${getApiBaseUrl()}/api/v1/alerts/?limit=20`),
        fetch(`${getApiBaseUrl()}/api/v1/alerts/stats?hours=24`),
        fetch(`${getApiBaseUrl()}/api/v1/alerts/timeline?hours=24&interval=1h`),
      ]);

      if (alertsRes.ok) {
        const alertsData = await alertsRes.json();
        if (alertsData.status === "success") {
          setAlerts(alertsData.data.alerts || []);
        }
      }

      if (statsRes.ok) {
        const statsData = await statsRes.json();
        if (statsData.status === "success") {
          setStats(statsData.data.stats || null);
        }
      }

      if (timelineRes.ok) {
        const timelineData = await timelineRes.json();
        if (timelineData.status === "success") {
          setTimeline(timelineData.data.timeline || []);
        }
      }
    } catch (err) {
      console.error("Error fetching alert data:", err);
      setError("Could not load alert data");
    } finally {
      setIsLoading(false);
    }
  }, []);

  const acknowledgeAlert = async (alertId: number) => {
    try {
      const response = await fetch(`${getApiBaseUrl()}/api/v1/alerts/${alertId}/acknowledge`, {
        method: "POST",
      });

      if (response.ok) {
        setAlerts((prev) => prev.map((a) => (a.id === alertId ? { ...a, acknowledged: true } : a)));
        setStats((prev) =>
          prev ? { ...prev, unacknowledged: Math.max(0, prev.unacknowledged - 1) } : null
        );
      }
    } catch (err) {
      console.error("Error acknowledging alert:", err);
    }
  };

  const resolveAlert = async (alertId: number) => {
    try {
      const response = await fetch(`${getApiBaseUrl()}/api/v1/alerts/${alertId}/resolve`, {
        method: "POST",
      });

      if (response.ok) {
        setAlerts((prev) => prev.filter((a) => a.id !== alertId));
        setStats((prev) =>
          prev
            ? {
                ...prev,
                total: Math.max(0, prev.total - 1),
                unacknowledged: Math.max(0, prev.unacknowledged - 1),
              }
            : null
        );
      }
    } catch (err) {
      console.error("Error resolving alert:", err);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 60000); // Refresh every minute
    return () => clearInterval(interval);
  }, [loadData]);

  // Format time for chart
  const formatTimelineData = timeline.map((entry) => ({
    ...entry,
    time: entry.time
      ? new Date(entry.time).toLocaleTimeString("en-US", {
          hour: "2-digit",
          minute: "2-digit",
        })
      : "",
  }));

  return (
    <div className="bg-white rounded-lg shadow-md p-3 sm:p-4 border-l-4 border-red-500">
      {/* Header */}
      <div className="flex items-center justify-between mb-3 sm:mb-4">
        <div className="flex items-center flex-wrap gap-1">
          <Bell className="w-4 h-4 sm:w-5 sm:h-5 text-red-500 mr-1 sm:mr-2" />
          <h3 className="text-sm sm:text-lg font-semibold text-gray-800">Alert Dashboard</h3>
          {enableRealtime && (
            <span
              className={`flex items-center text-[10px] sm:text-xs px-1.5 sm:px-2 py-0.5 rounded-full ${
                wsConnected ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-500"
              }`}
              title={
                wsConnected ? "Real-time updates active" : "Connecting to real-time updates..."
              }
            >
              <Radio
                className={`w-2.5 h-2.5 sm:w-3 sm:h-3 mr-0.5 sm:mr-1 ${wsConnected ? "animate-pulse" : ""}`}
              />
              {wsConnected ? "LIVE" : "..."}
            </span>
          )}
        </div>
        <button
          type="button"
          onClick={loadData}
          className="p-1.5 sm:p-2 hover:bg-gray-100 rounded-full transition-colors touch-manipulation"
          title="Refresh data"
        >
          <RefreshCw className={`w-4 h-4 text-gray-500 ${isLoading ? "animate-spin" : ""}`} />
        </button>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-4 gap-1.5 sm:gap-3 mb-3 sm:mb-4">
        <div className="bg-gray-50 rounded-lg p-2 sm:p-3 text-center">
          <p className="text-[10px] sm:text-xs text-gray-500 font-medium">Total</p>
          <p className="text-lg sm:text-2xl font-bold text-gray-800">{stats?.total || 0}</p>
        </div>
        <div className="bg-red-50 rounded-lg p-2 sm:p-3 text-center">
          <p className="text-[10px] sm:text-xs text-red-600 font-medium">Critical</p>
          <p className="text-lg sm:text-2xl font-bold text-red-600">{stats?.critical || 0}</p>
        </div>
        <div className="bg-amber-50 rounded-lg p-2 sm:p-3 text-center">
          <p className="text-[10px] sm:text-xs text-amber-600 font-medium">Warning</p>
          <p className="text-lg sm:text-2xl font-bold text-amber-600">{stats?.warning || 0}</p>
        </div>
        <div className="bg-blue-50 rounded-lg p-2 sm:p-3 text-center">
          <p className="text-[10px] sm:text-xs text-blue-600 font-medium truncate">Unack</p>
          <p className="text-lg sm:text-2xl font-bold text-blue-600">
            {stats?.unacknowledged || 0}
          </p>
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="bg-amber-50 text-amber-700 px-2 sm:px-3 py-1.5 sm:py-2 rounded mb-3 sm:mb-4 text-xs sm:text-sm">
          {error}
        </div>
      )}

      {/* Timeline Chart */}
      <div className="mb-3 sm:mb-4">
        <h4 className="text-xs sm:text-sm font-medium text-gray-600 mb-2">Alert Timeline (24h)</h4>
        {isLoading && timeline.length === 0 ? (
          <div className="flex items-center justify-center" style={{ height: height }}>
            <div className="animate-pulse text-gray-400">Loading timeline...</div>
          </div>
        ) : formatTimelineData.length > 0 ? (
          <ResponsiveContainer width="100%" height={height}>
            <BarChart data={formatTimelineData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis
                dataKey="time"
                tick={{ fontSize: 10 }}
                tickLine={false}
                interval="preserveStartEnd"
              />
              <YAxis tick={{ fontSize: 10 }} tickLine={false} />
              <Tooltip
                contentStyle={{
                  backgroundColor: "white",
                  borderRadius: "8px",
                  boxShadow: "0 2px 8px rgba(0,0,0,0.15)",
                  borderLeft: "4px solid #DC2626",
                }}
              />
              <Bar dataKey="critical" stackId="a" fill={SEVERITY_COLORS.critical} name="Critical" />
              <Bar dataKey="warning" stackId="a" fill={SEVERITY_COLORS.warning} name="Warning" />
              <Bar dataKey="info" stackId="a" fill={SEVERITY_COLORS.info} name="Info" />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <div
            className="flex items-center justify-center text-gray-400"
            style={{ height: height }}
          >
            <CheckCircle className="w-6 h-6 mr-2" />
            No alerts in the last 24 hours
          </div>
        )}
      </div>

      {/* Recent Alerts List */}
      <div>
        <h4 className="text-xs sm:text-sm font-medium text-gray-600 mb-2">Recent Alerts</h4>
        <div className="space-y-1.5 sm:space-y-2 max-h-48 sm:max-h-64 overflow-y-auto">
          {alerts.length === 0 ? (
            <div className="text-center py-3 sm:py-4 text-gray-400">
              <CheckCircle className="w-6 h-6 sm:w-8 sm:h-8 mx-auto mb-1.5 sm:mb-2" />
              <p className="text-xs sm:text-sm">All systems normal - no active alerts</p>
            </div>
          ) : (
            alerts.slice(0, 10).map((alert) => (
              <div
                key={alert.id}
                className={`p-2 sm:p-3 rounded-lg border ${SEVERITY_BG[alert.severity]} ${
                  alert.acknowledged ? "opacity-60" : ""
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start min-w-0 flex-1">
                    {alert.severity === "critical" ? (
                      <XCircle
                        className={`w-4 h-4 sm:w-5 sm:h-5 mr-1.5 sm:mr-2 mt-0.5 flex-shrink-0 ${SEVERITY_TEXT[alert.severity]}`}
                      />
                    ) : (
                      <AlertTriangle
                        className={`w-4 h-4 sm:w-5 sm:h-5 mr-1.5 sm:mr-2 mt-0.5 flex-shrink-0 ${SEVERITY_TEXT[alert.severity]}`}
                      />
                    )}
                    <div className="min-w-0 flex-1">
                      <p
                        className={`font-medium text-xs sm:text-sm ${SEVERITY_TEXT[alert.severity]}`}
                      >
                        {alert.target_id}
                      </p>
                      <p className="text-[10px] sm:text-sm text-gray-600 truncate">
                        {alert.message}
                      </p>
                      <div className="flex items-center mt-0.5 sm:mt-1 text-[10px] sm:text-xs text-gray-500 flex-wrap">
                        <Clock className="w-2.5 h-2.5 sm:w-3 sm:h-3 mr-0.5 sm:mr-1" />
                        <span className="truncate">{new Date(alert.time).toLocaleString()}</span>
                        {alert.current_value && (
                          <span className="ml-1 sm:ml-2">{alert.current_value.toFixed(1)}V</span>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="flex space-x-0.5 sm:space-x-1 flex-shrink-0 ml-1">
                    {!alert.acknowledged && (
                      <button
                        type="button"
                        onClick={() => acknowledgeAlert(alert.id)}
                        className="p-1 hover:bg-gray-200 rounded touch-manipulation"
                        title="Acknowledge"
                      >
                        <Check className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-gray-500" />
                      </button>
                    )}
                    <button
                      type="button"
                      onClick={() => resolveAlert(alert.id)}
                      className="p-1 hover:bg-gray-200 rounded touch-manipulation"
                      title="Resolve"
                    >
                      <CheckCircle className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-green-500" />
                    </button>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Footer */}
      <div className="mt-2 sm:mt-3 pt-2 sm:pt-3 border-t border-gray-100">
        <p className="text-[10px] sm:text-xs text-gray-500">
          <span className="hidden sm:inline">Voltage limits: </span>218V - 242V (±5%) |{" "}
          {alerts.length} alerts
          {enableRealtime && liveUpdateCount > 0 && (
            <span className="ml-1 sm:ml-2 text-green-600">| {liveUpdateCount} live</span>
          )}
        </p>
      </div>
    </div>
  );
}
