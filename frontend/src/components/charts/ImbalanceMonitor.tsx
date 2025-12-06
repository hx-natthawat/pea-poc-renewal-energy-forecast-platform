"use client";

import { AlertTriangle, CheckCircle, RefreshCw, Scale, XCircle } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { getApiBaseUrl } from "@/lib/api";

interface ImbalanceDataPoint {
  time: string;
  imbalance_mw: number;
  imbalance_pct: number;
  severity: "normal" | "warning" | "critical";
}

interface BalancingStatus {
  area: string;
  imbalance_mw: number;
  severity: string;
  reserves_available_mw: number;
}

interface ImbalanceMonitorProps {
  height?: number;
  area?: "system" | "central" | "north" | "northeast" | "south";
}

export default function ImbalanceMonitor({ height = 300, area = "system" }: ImbalanceMonitorProps) {
  const [data, setData] = useState<ImbalanceDataPoint[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [currentStatus, setCurrentStatus] = useState<BalancingStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      // Fetch both forecast and current status
      const [forecastRes, statusRes] = await Promise.all([
        fetch(
          `${getApiBaseUrl()}/api/v1/imbalance-forecast/predict?balancing_area=${area}&horizon_hours=24`
        ),
        fetch(`${getApiBaseUrl()}/api/v1/imbalance-forecast/status/${area}`),
      ]);

      if (forecastRes.ok) {
        const forecastResult = await forecastRes.json();
        if (forecastResult.status === "success" && forecastResult.data?.predictions) {
          const chartData = forecastResult.data.predictions.map(
            (p: {
              timestamp: string;
              imbalance_mw: number;
              imbalance_pct: number;
              severity: string;
            }) => ({
              time: new Date(p.timestamp).toLocaleTimeString("en-US", {
                hour: "2-digit",
                minute: "2-digit",
              }),
              imbalance_mw: Math.round(p.imbalance_mw),
              imbalance_pct: p.imbalance_pct,
              severity: p.severity.toLowerCase(),
            })
          );
          setData(chartData);
        }
      }

      if (statusRes.ok) {
        const statusResult = await statusRes.json();
        if (statusResult.status === "success" && statusResult.data) {
          setCurrentStatus(statusResult.data);
        }
      }
    } catch (err) {
      console.error("Error fetching imbalance data:", err);
      setError("Could not load imbalance data");

      // Generate simulation data for demo
      const simData = Array.from({ length: 24 }, (_, i) => {
        const hour = i;
        const baseImbalance = Math.sin(hour * (Math.PI / 6)) * 200 + (Math.random() - 0.5) * 100;
        const imbalancePct = (baseImbalance / 15000) * 100;
        let severity: "normal" | "warning" | "critical" = "normal";
        if (Math.abs(imbalancePct) > 2) severity = "critical";
        else if (Math.abs(imbalancePct) > 0.5) severity = "warning";

        return {
          time: `${hour.toString().padStart(2, "0")}:00`,
          imbalance_mw: Math.round(baseImbalance),
          imbalance_pct: Math.round(imbalancePct * 100) / 100,
          severity,
        };
      });
      setData(simData);
      setCurrentStatus({
        area: area,
        imbalance_mw: simData[simData.length - 1].imbalance_mw,
        severity: simData[simData.length - 1].severity,
        reserves_available_mw: 500 + Math.random() * 200,
      });
    } finally {
      setIsLoading(false);
    }
  }, [area]);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 60 * 1000); // Update every minute for imbalance
    return () => clearInterval(interval);
  }, [loadData]);

  const getBarColor = (severity: string) => {
    switch (severity) {
      case "critical":
        return "#EF4444";
      case "warning":
        return "#F59E0B";
      default:
        return "#10B981";
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case "critical":
        return <XCircle className="w-5 h-5 text-red-500" />;
      case "warning":
        return <AlertTriangle className="w-5 h-5 text-amber-500" />;
      default:
        return <CheckCircle className="w-5 h-5 text-green-500" />;
    }
  };

  const areaLabels: Record<string, string> = {
    system: "System-wide",
    central: "Central Region",
    north: "North Region",
    northeast: "Northeast Region",
    south: "South Region",
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-3 sm:p-4 border-l-4 border-orange-500">
      {/* Header */}
      <div className="flex items-center justify-between mb-3 sm:mb-4">
        <div className="flex items-center flex-wrap gap-1">
          <Scale className="w-4 h-4 sm:w-5 sm:h-5 text-orange-500 mr-1 sm:mr-2" />
          <h3 className="text-sm sm:text-lg font-semibold text-gray-800">Imbalance Monitor</h3>
          <span className="text-[10px] sm:text-xs px-1.5 sm:px-2 py-0.5 rounded-full bg-orange-100 text-orange-700">
            TOR 7.5.1.4
          </span>
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

      {/* Current Status */}
      {currentStatus && (
        <div className="grid grid-cols-3 gap-2 sm:gap-4 mb-3 sm:mb-4">
          <div
            className={`rounded-lg p-2 sm:p-3 ${
              currentStatus.severity === "critical"
                ? "bg-red-50"
                : currentStatus.severity === "warning"
                  ? "bg-amber-50"
                  : "bg-green-50"
            }`}
          >
            <p className="text-[10px] sm:text-xs text-gray-600 font-medium truncate">Status</p>
            <div className="flex items-center mt-1">
              {getSeverityIcon(currentStatus.severity)}
              <p className="text-sm sm:text-lg font-bold ml-1 capitalize">
                {currentStatus.severity}
              </p>
            </div>
          </div>
          <div className="bg-gray-50 rounded-lg p-2 sm:p-3">
            <p className="text-[10px] sm:text-xs text-gray-600 font-medium truncate">Imbalance</p>
            <p
              className={`text-sm sm:text-xl font-bold ${
                currentStatus.imbalance_mw > 0 ? "text-red-600" : "text-blue-600"
              }`}
            >
              {currentStatus.imbalance_mw > 0 ? "+" : ""}
              {Math.round(currentStatus.imbalance_mw).toLocaleString()}
              <span className="text-xs sm:text-sm"> MW</span>
            </p>
          </div>
          <div className="bg-blue-50 rounded-lg p-2 sm:p-3">
            <p className="text-[10px] sm:text-xs text-blue-600 font-medium truncate">Reserves</p>
            <p className="text-sm sm:text-xl font-bold text-blue-700">
              {Math.round(currentStatus.reserves_available_mw).toLocaleString()}
              <span className="text-xs sm:text-sm"> MW</span>
            </p>
          </div>
        </div>
      )}

      {/* Error Banner */}
      {error && (
        <div className="bg-amber-50 text-amber-700 px-2 sm:px-3 py-1.5 sm:py-2 rounded mb-3 sm:mb-4 text-xs sm:text-sm">
          {error} (showing simulation)
        </div>
      )}

      {/* Chart */}
      {isLoading && data.length === 0 ? (
        <div className="h-[200px] sm:h-[300px] flex items-center justify-center">
          <div className="animate-pulse text-gray-400 text-sm">Loading chart data...</div>
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={height}>
          <BarChart data={data} margin={{ top: 5, right: 10, left: -15, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis dataKey="time" tick={{ fontSize: 9 }} tickLine={false} interval={3} />
            <YAxis
              tick={{ fontSize: 9 }}
              tickLine={false}
              tickFormatter={(value) => `${value > 0 ? "+" : ""}${value}`}
              width={40}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "white",
                borderRadius: "8px",
                boxShadow: "0 2px 8px rgba(0,0,0,0.15)",
                borderLeft: "4px solid #F97316",
                fontSize: "12px",
              }}
              formatter={(value: number, name: string) => [
                `${value > 0 ? "+" : ""}${value.toLocaleString()} MW`,
                name,
              ]}
            />
            <Legend wrapperStyle={{ fontSize: "10px" }} />
            <ReferenceLine y={0} stroke="#374151" strokeWidth={2} />
            <ReferenceLine
              y={200}
              stroke="#F59E0B"
              strokeDasharray="5 5"
              label={{ value: "Warning", fontSize: 10 }}
            />
            <ReferenceLine y={-200} stroke="#F59E0B" strokeDasharray="5 5" />
            <ReferenceLine
              y={500}
              stroke="#EF4444"
              strokeDasharray="5 5"
              label={{ value: "Critical", fontSize: 10 }}
            />
            <ReferenceLine y={-500} stroke="#EF4444" strokeDasharray="5 5" />
            <Bar dataKey="imbalance_mw" name="Imbalance">
              {data.map((entry) => (
                <Cell key={`cell-${entry.time}`} fill={getBarColor(entry.severity)} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      )}

      {/* Footer */}
      <div className="mt-2 sm:mt-3 pt-2 sm:pt-3 border-t border-gray-100">
        <p className="text-[10px] sm:text-xs text-gray-500">
          Area: {areaLabels[area]} | Target: MAE &lt; 2% | {data.length} intervals
        </p>
      </div>
    </div>
  );
}
