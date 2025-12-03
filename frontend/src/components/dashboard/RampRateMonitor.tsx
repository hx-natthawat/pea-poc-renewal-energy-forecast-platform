"use client";

import { useEffect, useState } from "react";
import { Activity, AlertTriangle, RefreshCw, TrendingDown, TrendingUp } from "lucide-react";
import { getApiBaseUrl } from "@/lib/api";

interface RampEvent {
  timestamp: string;
  rate_percent: number;
  direction: "up" | "down";
  current_irradiance: number;
  previous_irradiance: number;
}

interface RampRateData {
  current_ramp_rate_percent: number;
  threshold_percent: number;
  is_alert: boolean;
  last_event: RampEvent | null;
  station_id: string;
  timestamp: string;
}

interface RampRateMonitorProps {
  stationId?: string;
  refreshInterval?: number;
}

export default function RampRateMonitor({
  stationId = "POC_STATION_1",
  refreshInterval = 10000, // 10 seconds
}: RampRateMonitorProps) {
  const [data, setData] = useState<RampRateData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    try {
      const response = await fetch(
        `${getApiBaseUrl()}/api/v1/weather/ramp-rate/current?station_id=${stationId}`
      );
      if (response.ok) {
        const result = await response.json();
        if (result.status === "success") {
          setData(result.data);
          setError(null);
        }
      }
    } catch (err) {
      console.error("Error fetching ramp rate:", err);
      setError("Could not load ramp rate data");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, refreshInterval);
    return () => clearInterval(interval);
  }, [stationId, refreshInterval]);

  if (isLoading && !data) {
    return (
      <div className="bg-white rounded-lg shadow-md p-3 sm:p-4">
        <div className="animate-pulse h-24 sm:h-32 bg-gray-100 rounded" />
      </div>
    );
  }

  const ratePercent = data ? Math.abs(data.current_ramp_rate_percent) : 0;
  const thresholdPercent = data?.threshold_percent || 30;
  const fillPercent = Math.min((ratePercent / thresholdPercent) * 100, 100);

  const getStatusColor = () => {
    if (data?.is_alert) return "bg-red-500";
    if (fillPercent > 70) return "bg-amber-500";
    return "bg-green-500";
  };

  const getStatusText = () => {
    if (data?.is_alert) return "ALERT";
    if (fillPercent > 70) return "CAUTION";
    return "NORMAL";
  };

  const getStatusBgClass = () => {
    if (data?.is_alert) return "bg-red-100 text-red-700";
    if (fillPercent > 70) return "bg-amber-100 text-amber-700";
    return "bg-green-100 text-green-700";
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-3 sm:p-4 border-l-4 border-purple-600">
      {/* Header */}
      <div className="flex items-center justify-between mb-2 sm:mb-3">
        <div className="flex items-center min-w-0">
          <Activity className="w-4 h-4 sm:w-5 sm:h-5 mr-1 sm:mr-2 text-purple-600 flex-shrink-0" />
          <h3 className="text-sm sm:text-base font-semibold text-gray-800 truncate">
            <span className="hidden sm:inline">Ramp Rate Monitor</span>
            <span className="sm:hidden">Ramp Rate</span>
          </h3>
        </div>
        <div className="flex items-center gap-1 sm:gap-2">
          <span
            className={`px-1.5 sm:px-2 py-0.5 rounded text-[10px] sm:text-xs font-medium ${getStatusBgClass()}`}
          >
            {getStatusText()}
          </span>
          <button
            type="button"
            onClick={fetchData}
            className="p-1 hover:bg-gray-100 rounded-full transition-colors touch-manipulation"
            title="Refresh"
          >
            <RefreshCw
              className={`w-3.5 h-3.5 sm:w-4 sm:h-4 text-gray-500 ${isLoading ? "animate-spin" : ""}`}
            />
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-amber-50 text-amber-700 px-2 py-1.5 rounded mb-2 text-xs flex items-center">
          <AlertTriangle className="w-3 h-3 mr-1 flex-shrink-0" />
          {error}
        </div>
      )}

      {/* Ramp Rate Gauge */}
      <div className="mb-2 sm:mb-3">
        <div className="flex justify-between text-[10px] sm:text-xs text-gray-500 mb-1">
          <span>Current: {ratePercent.toFixed(1)}%</span>
          <span>Threshold: {thresholdPercent}%</span>
        </div>
        <div className="h-2 sm:h-3 bg-gray-200 rounded-full overflow-hidden">
          <div
            className={`h-full transition-all duration-300 ${getStatusColor()}`}
            style={{ width: `${fillPercent}%` }}
          />
        </div>
      </div>

      {/* Current Rate Display */}
      <div className="grid grid-cols-2 gap-2 mb-2 sm:mb-3">
        <div className="bg-gray-50 rounded p-2 text-center">
          <p className="text-[10px] sm:text-xs text-gray-500">Rate</p>
          <p className="text-sm sm:text-lg font-bold text-gray-800">
            {ratePercent.toFixed(1)}%
          </p>
        </div>
        <div className="bg-gray-50 rounded p-2 text-center">
          <p className="text-[10px] sm:text-xs text-gray-500">Direction</p>
          <div className="flex items-center justify-center">
            {data?.last_event?.direction === "down" ? (
              <>
                <TrendingDown className="w-4 h-4 sm:w-5 sm:h-5 text-blue-500 mr-0.5" />
                <span className="text-sm sm:text-lg font-bold text-blue-600">Down</span>
              </>
            ) : data?.last_event?.direction === "up" ? (
              <>
                <TrendingUp className="w-4 h-4 sm:w-5 sm:h-5 text-amber-500 mr-0.5" />
                <span className="text-sm sm:text-lg font-bold text-amber-600">Up</span>
              </>
            ) : (
              <span className="text-sm sm:text-lg font-bold text-gray-400">--</span>
            )}
          </div>
        </div>
      </div>

      {/* Last Event */}
      {data?.last_event && (
        <div className="bg-gray-50 rounded p-2 text-xs">
          <div className="flex items-center gap-1 text-gray-600 mb-1">
            {data.last_event.direction === "down" ? (
              <TrendingDown className="w-3 h-3 text-blue-500" />
            ) : (
              <TrendingUp className="w-3 h-3 text-amber-500" />
            )}
            <span className="font-medium text-[10px] sm:text-xs">Last Event</span>
          </div>
          <p className="text-[10px] sm:text-xs text-gray-500">
            {data.last_event.rate_percent.toFixed(1)}%{" "}
            {data.last_event.direction} at{" "}
            {new Date(data.last_event.timestamp).toLocaleTimeString()}
          </p>
          <p className="text-[10px] sm:text-xs text-gray-400 mt-0.5">
            {data.last_event.previous_irradiance.toFixed(0)} {"->"}
            {data.last_event.current_irradiance.toFixed(0)} W/m²
          </p>
        </div>
      )}

      {/* Alert Banner */}
      {data?.is_alert && (
        <div className="mt-2 sm:mt-3 bg-red-50 border border-red-200 rounded p-2 flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-red-500 flex-shrink-0" />
          <span className="text-[10px] sm:text-xs text-red-700">
            <span className="hidden sm:inline">
              Rapid irradiance change detected - Cloud shadow event likely
            </span>
            <span className="sm:hidden">Cloud shadow detected</span>
          </span>
        </div>
      )}

      {/* Footer */}
      <div className="mt-2 sm:mt-3 pt-2 border-t border-gray-100">
        <p className="text-[10px] sm:text-xs text-gray-500">
          Station: {stationId} | Updates: {refreshInterval / 1000}s
        </p>
      </div>
    </div>
  );
}
