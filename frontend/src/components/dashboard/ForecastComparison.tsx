"use client";

import {
  CheckCircle,
  RefreshCw,
  Target,
  TrendingDown,
  TrendingUp,
  XCircle,
} from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { getApiBaseUrl } from "@/lib/api";

interface ComparisonDataPoint {
  time: string;
  predicted: number;
  actual: number;
  error: number;
  error_percent?: number;
}

interface AccuracyMetrics {
  mape: number | null;
  mae: number;
  rmse: number;
  r_squared: number | null;
  bias: number;
  count: number;
}

interface TargetStatus {
  target: number;
  unit: string;
  met: boolean;
}

interface ForecastComparisonProps {
  modelType?: "solar" | "voltage";
  height?: number;
}

const MODEL_CONFIG = {
  solar: {
    title: "Solar Power Forecast Accuracy",
    color: "#C7911B",
    colorLight: "#FEF3C7",
    unit: "kW",
    targets: {
      mape: { label: "MAPE", target: "< 10%", key: "mape" },
      rmse: { label: "RMSE", target: "< 100 kW", key: "rmse" },
      r_squared: { label: "R²", target: "> 0.95", key: "r_squared" },
    },
  },
  voltage: {
    title: "Voltage Forecast Accuracy",
    color: "#74045F",
    colorLight: "#F3E8FF",
    unit: "V",
    targets: {
      mae: { label: "MAE", target: "< 2V", key: "mae" },
      rmse: { label: "RMSE", target: "< 3V", key: "rmse" },
      r_squared: { label: "R²", target: "> 0.90", key: "r_squared" },
    },
  },
};

export default function ForecastComparison({
  modelType = "solar",
  height = 300,
}: ForecastComparisonProps) {
  const [data, setData] = useState<ComparisonDataPoint[]>([]);
  const [metrics, setMetrics] = useState<AccuracyMetrics | null>(null);
  const [targets, setTargets] = useState<Record<string, TargetStatus>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<"comparison" | "error">("comparison");

  const config = MODEL_CONFIG[modelType];

  const loadData = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `${getApiBaseUrl()}/api/v1/comparison/${modelType}?hours=24`
      );

      if (!response.ok) {
        throw new Error("Failed to fetch comparison data");
      }

      const result = await response.json();

      if (result.status === "success") {
        setData(result.data.comparison || []);
        setMetrics(result.data.metrics || null);
        setTargets(result.data.targets || {});
      }
    } catch (err) {
      console.error("Error fetching comparison data:", err);
      setError("Could not load comparison data");
    } finally {
      setIsLoading(false);
    }
  }, [modelType]);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 60000); // Refresh every minute
    return () => clearInterval(interval);
  }, [loadData]);

  const renderMetricCard = (
    label: string,
    value: number | null,
    unit: string,
    target: string,
    met: boolean
  ) => (
    <div
      className={`p-3 rounded-lg ${met ? "bg-green-50" : "bg-red-50"} border ${
        met ? "border-green-200" : "border-red-200"
      }`}
    >
      <div className="flex items-center justify-between mb-1">
        <span className="text-xs text-gray-500">{label}</span>
        {met ? (
          <CheckCircle className="w-4 h-4 text-green-500" />
        ) : (
          <XCircle className="w-4 h-4 text-red-500" />
        )}
      </div>
      <p className={`text-xl font-bold ${met ? "text-green-700" : "text-red-700"}`}>
        {value !== null ? `${value.toFixed(2)}${unit}` : "N/A"}
      </p>
      <p className="text-xs text-gray-500">Target: {target}</p>
    </div>
  );

  if (isLoading && data.length === 0) {
    return (
      <div
        className="bg-white rounded-lg shadow-md p-6 border-l-4"
        style={{ borderColor: config.color }}
      >
        <div className="animate-pulse flex items-center justify-center h-64">
          <p className="text-gray-400">Loading comparison data...</p>
        </div>
      </div>
    );
  }

  return (
    <div
      className="bg-white rounded-lg shadow-md p-4 border-l-4"
      style={{ borderColor: config.color }}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center">
          <Target className="w-5 h-5 mr-2" style={{ color: config.color }} />
          <h3 className="text-lg font-semibold text-gray-800">{config.title}</h3>
        </div>
        <div className="flex items-center space-x-2">
          {/* View Mode Toggle */}
          <div className="flex bg-gray-100 rounded-lg p-0.5">
            <button
              type="button"
              onClick={() => setViewMode("comparison")}
              className={`px-3 py-1 text-xs rounded-md transition-colors ${
                viewMode === "comparison"
                  ? "bg-white shadow text-gray-800"
                  : "text-gray-500"
              }`}
            >
              Comparison
            </button>
            <button
              type="button"
              onClick={() => setViewMode("error")}
              className={`px-3 py-1 text-xs rounded-md transition-colors ${
                viewMode === "error"
                  ? "bg-white shadow text-gray-800"
                  : "text-gray-500"
              }`}
            >
              Error
            </button>
          </div>
          <button
            type="button"
            onClick={loadData}
            className="p-2 hover:bg-gray-100 rounded-full transition-colors"
            title="Refresh"
          >
            <RefreshCw
              className={`w-4 h-4 text-gray-500 ${isLoading ? "animate-spin" : ""}`}
            />
          </button>
        </div>
      </div>

      {/* Metrics Row */}
      {metrics && (
        <div className="grid grid-cols-3 gap-3 mb-4">
          {Object.entries(config.targets).map(([key, targetConfig]) => {
            const targetStatus = targets[key];
            const metricValue = metrics[targetConfig.key as keyof AccuracyMetrics] as number | null;
            return (
              <div key={key}>
                {renderMetricCard(
                  targetConfig.label,
                  metricValue,
                  key === "r_squared" ? "" : config.unit === "kW" && key !== "mape" ? " kW" : key === "mape" ? "%" : " V",
                  targetConfig.target,
                  targetStatus?.met ?? false
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Additional Stats */}
      {metrics && (
        <div className="flex items-center justify-between mb-4 text-sm">
          <div className="flex items-center space-x-4">
            <span className="text-gray-500">
              Bias:{" "}
              <span
                className={`font-semibold ${
                  metrics.bias > 0 ? "text-amber-600" : "text-blue-600"
                }`}
              >
                {metrics.bias > 0 ? "+" : ""}
                {metrics.bias.toFixed(2)} {config.unit}
                {metrics.bias > 0 ? (
                  <TrendingUp className="w-3 h-3 inline ml-1" />
                ) : (
                  <TrendingDown className="w-3 h-3 inline ml-1" />
                )}
              </span>
            </span>
            <span className="text-gray-500">
              Data points: <span className="font-semibold">{metrics.count}</span>
            </span>
          </div>
        </div>
      )}

      {/* Error Banner */}
      {error && (
        <div className="bg-amber-50 text-amber-700 px-3 py-2 rounded mb-4 text-sm">
          {error}
        </div>
      )}

      {/* Chart */}
      {data.length > 0 ? (
        <ResponsiveContainer width="100%" height={height}>
          {viewMode === "comparison" ? (
            <AreaChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id={`colorActual-${modelType}`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={config.color} stopOpacity={0.8} />
                  <stop offset="95%" stopColor={config.color} stopOpacity={0.1} />
                </linearGradient>
                <linearGradient id={`colorPredicted-${modelType}`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#6B7280" stopOpacity={0.6} />
                  <stop offset="95%" stopColor="#6B7280" stopOpacity={0.1} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis
                dataKey="time"
                tick={{ fontSize: 10 }}
                tickLine={false}
                interval="preserveStartEnd"
              />
              <YAxis
                tick={{ fontSize: 10 }}
                tickLine={false}
                tickFormatter={(value) =>
                  modelType === "solar" ? `${(value / 1000).toFixed(1)}k` : `${value}`
                }
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: "white",
                  borderRadius: "8px",
                  boxShadow: "0 2px 8px rgba(0,0,0,0.15)",
                  borderLeft: `4px solid ${config.color}`,
                }}
                formatter={(value: number, name: string) => [
                  `${value.toFixed(1)} ${config.unit}`,
                  name,
                ]}
              />
              <Legend />
              <Area
                type="monotone"
                dataKey="predicted"
                name="Predicted"
                stroke="#6B7280"
                strokeWidth={2}
                strokeDasharray="5 5"
                fillOpacity={1}
                fill={`url(#colorPredicted-${modelType})`}
              />
              <Area
                type="monotone"
                dataKey="actual"
                name="Actual"
                stroke={config.color}
                strokeWidth={2}
                fillOpacity={1}
                fill={`url(#colorActual-${modelType})`}
              />
            </AreaChart>
          ) : (
            <LineChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis
                dataKey="time"
                tick={{ fontSize: 10 }}
                tickLine={false}
                interval="preserveStartEnd"
              />
              <YAxis
                tick={{ fontSize: 10 }}
                tickLine={false}
                domain={["auto", "auto"]}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: "white",
                  borderRadius: "8px",
                  boxShadow: "0 2px 8px rgba(0,0,0,0.15)",
                }}
                formatter={(value: number) => [`${value.toFixed(2)} ${config.unit}`, "Error"]}
              />
              <Line
                type="monotone"
                dataKey="error"
                name="Error"
                stroke={config.color}
                strokeWidth={2}
                dot={false}
              />
              {/* Zero reference line */}
              <Line
                type="monotone"
                dataKey={() => 0}
                stroke="#9CA3AF"
                strokeWidth={1}
                strokeDasharray="3 3"
                dot={false}
                name="Zero"
              />
            </LineChart>
          )}
        </ResponsiveContainer>
      ) : (
        <div
          className="flex items-center justify-center text-gray-400"
          style={{ height }}
        >
          No comparison data available
        </div>
      )}

      {/* Footer */}
      <div className="mt-3 pt-3 border-t border-gray-100">
        <p className="text-xs text-gray-500">
          {modelType === "solar"
            ? "Target: MAPE < 10%, RMSE < 100 kW, R² > 0.95 (per TOR)"
            : "Target: MAE < 2V, RMSE < 3V, R² > 0.90 (per TOR)"}{" "}
          | Last 24 hours
        </p>
      </div>
    </div>
  );
}
