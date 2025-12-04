"use client";

import { AlertTriangle, CloudRain, Wind, X } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { getApiBaseUrl } from "@/lib/api";

interface WeatherAlert {
  id: string;
  timestamp: string;
  condition: string;
  severity: "info" | "warning" | "critical";
  region: string;
  description: string;
  expected_duration_minutes: number;
  recommended_action: string;
}

interface WeatherAlertBannerProps {
  autoRefresh?: boolean;
  refreshInterval?: number;
}

const severityConfig = {
  info: {
    bg: "bg-blue-50",
    border: "border-blue-200",
    text: "text-blue-800",
    icon: CloudRain,
  },
  warning: {
    bg: "bg-amber-50",
    border: "border-amber-200",
    text: "text-amber-800",
    icon: AlertTriangle,
  },
  critical: {
    bg: "bg-red-50",
    border: "border-red-200",
    text: "text-red-800",
    icon: Wind,
  },
};

export default function WeatherAlertBanner({
  autoRefresh = true,
  refreshInterval = 300000, // 5 minutes
}: WeatherAlertBannerProps) {
  const [alerts, setAlerts] = useState<WeatherAlert[]>([]);
  const [dismissedIds, setDismissedIds] = useState<Set<string>>(new Set());
  const [isLoading, setIsLoading] = useState(true);

  const fetchAlerts = useCallback(async () => {
    try {
      const response = await fetch(`${getApiBaseUrl()}/api/v1/weather/alerts`);
      if (response.ok) {
        const data = await response.json();
        if (data.status === "success") {
          setAlerts(data.data.alerts || []);
        }
      }
    } catch (error) {
      console.error("Error fetching weather alerts:", error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAlerts();

    if (autoRefresh) {
      const interval = setInterval(fetchAlerts, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [autoRefresh, refreshInterval, fetchAlerts]);

  const handleDismiss = (alertId: string) => {
    setDismissedIds((prev) => new Set([...prev, alertId]));
  };

  const visibleAlerts = alerts.filter((a) => !dismissedIds.has(a.id));

  if (isLoading || visibleAlerts.length === 0) {
    return null;
  }

  return (
    <div className="space-y-2 mb-4">
      {visibleAlerts.map((alert) => {
        const config = severityConfig[alert.severity];
        const Icon = config.icon;

        return (
          <div
            key={alert.id}
            className={`${config.bg} ${config.border} border rounded-lg p-2 sm:p-3 flex items-start gap-2 sm:gap-3`}
          >
            <Icon className={`w-4 h-4 sm:w-5 sm:h-5 ${config.text} flex-shrink-0 mt-0.5`} />

            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <span className={`font-semibold ${config.text} text-xs sm:text-sm`}>
                  {alert.condition.replace("_", " ").toUpperCase()}
                </span>
                <span className="text-[10px] sm:text-xs text-gray-500">{alert.region}</span>
              </div>

              <p className={`${config.text} text-xs sm:text-sm mt-0.5 sm:mt-1`}>
                {alert.description}
              </p>

              <p className="text-[10px] sm:text-xs text-gray-600 mt-0.5 sm:mt-1">
                <span className="font-medium">Action: </span>
                <span className="hidden sm:inline">{alert.recommended_action}</span>
                <span className="sm:hidden">{alert.recommended_action.slice(0, 40)}...</span>
                {alert.expected_duration_minutes > 0 && (
                  <span className="ml-1 sm:ml-2">({alert.expected_duration_minutes} min)</span>
                )}
              </p>
            </div>

            <button
              type="button"
              onClick={() => handleDismiss(alert.id)}
              className="p-1 hover:bg-white/50 rounded transition-colors touch-manipulation"
              aria-label="Dismiss alert"
            >
              <X className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-gray-500" />
            </button>
          </div>
        );
      })}
    </div>
  );
}
