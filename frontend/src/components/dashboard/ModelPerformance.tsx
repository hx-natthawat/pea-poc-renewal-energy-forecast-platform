"use client";

import {
  Activity,
  AlertTriangle,
  BarChart2,
  CheckCircle,
  Clock,
  RefreshCw,
  TrendingDown,
  TrendingUp,
  XCircle,
  Zap,
} from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { getApiBaseUrl } from "@/lib/api";

interface ModelHealthData {
  model_type: string;
  model_version: string;
  is_healthy: boolean;
  last_prediction: string | null;
  predictions_24h: number;
  avg_latency_ms: number;
  accuracy_status: string;
  issues: string[];
}

interface MetricTimelinePoint {
  period: string;
  sample_count: number;
  mae: number | null;
  rmse: number | null;
  mape: number | null;
}

interface PerformanceData {
  model_type: string;
  overall_metrics: {
    total_predictions: number;
    mae: number | null;
    rmse: number | null;
  };
  targets: {
    mape?: number;
    mae?: number;
    rmse?: number;
    r2?: number;
  };
  metrics_timeline: MetricTimelinePoint[];
}

interface DriftIndicator {
  feature: string;
  drift_score: number;
  drift_detected: boolean;
  baseline_mean: number;
  current_mean: number;
  threshold: number;
}

interface DriftData {
  model_type: string;
  overall_drift_detected: boolean;
  drift_indicators: DriftIndicator[];
  recommendations: string[];
}

type ModelType = "solar" | "voltage";

interface ModelPerformanceProps {
  height?: number;
}

const _HEALTH_COLORS = {
  good: "#22C55E",
  warning: "#F59E0B",
  degraded: "#EF4444",
};

export default function ModelPerformance({ height = 250 }: ModelPerformanceProps) {
  const [selectedModel, setSelectedModel] = useState<ModelType>("solar");
  const [modelHealth, setModelHealth] = useState<ModelHealthData[]>([]);
  const [performance, setPerformance] = useState<PerformanceData | null>(null);
  const [drift, setDrift] = useState<DriftData | null>(null);

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<string>("");

  const loadData = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      // Load health status
      const healthRes = await fetch(`${getApiBaseUrl()}/api/v1/monitoring/health`);
      if (healthRes.ok) {
        const healthData = await healthRes.json();
        if (healthData.status === "success") {
          setModelHealth(healthData.data.models);
        }
      }

      // Load performance metrics
      const perfRes = await fetch(
        `${getApiBaseUrl()}/api/v1/monitoring/performance/${selectedModel}?days=7&interval=1d`
      );
      if (perfRes.ok) {
        const perfData = await perfRes.json();
        if (perfData.status === "success") {
          setPerformance(perfData.data);
        }
      }

      // Load drift data
      const driftRes = await fetch(
        `${getApiBaseUrl()}/api/v1/monitoring/drift/${selectedModel}?baseline_days=30&current_days=7`
      );
      if (driftRes.ok) {
        const driftData = await driftRes.json();
        if (driftData.status === "success") {
          setDrift(driftData.data);
        }
      }
    } catch (err) {
      console.error("Error fetching monitoring data:", err);
      setError("Could not load model monitoring data");
    } finally {
      setIsLoading(false);
      setLastUpdated(new Date().toLocaleString());
    }
  }, [selectedModel]);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 60000); // Refresh every minute
    return () => clearInterval(interval);
  }, [loadData]);

  const getHealthIcon = (status: string, small = false) => {
    const sizeClass = small ? "w-3 h-3 sm:w-4 sm:h-4" : "w-4 h-4 sm:w-5 sm:h-5";
    switch (status) {
      case "good":
        return <CheckCircle className={`${sizeClass} text-green-500`} />;
      case "warning":
        return <AlertTriangle className={`${sizeClass} text-amber-500`} />;
      case "degraded":
        return <XCircle className={`${sizeClass} text-red-500`} />;
      default:
        return <Activity className={`${sizeClass} text-gray-400`} />;
    }
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
    });
  };

  const selectedHealth = modelHealth.find((m) => m.model_type === selectedModel);

  return (
    <div className="bg-white rounded-lg shadow-md p-3 sm:p-4 border-l-4 border-[#74045F]">
      {/* Header */}
      <div className="flex items-center justify-between mb-3 sm:mb-4">
        <div className="flex items-center min-w-0">
          <BarChart2 className="w-4 h-4 sm:w-5 sm:h-5 text-[#74045F] mr-1 sm:mr-2 flex-shrink-0" />
          <h3 className="text-sm sm:text-lg font-semibold text-gray-800 truncate">
            Model Performance
          </h3>
        </div>
        <button
          type="button"
          onClick={loadData}
          className="p-1.5 sm:p-2 hover:bg-gray-100 rounded-full transition-colors touch-manipulation flex-shrink-0"
          title="Refresh"
        >
          <RefreshCw className={`w-4 h-4 text-gray-500 ${isLoading ? "animate-spin" : ""}`} />
        </button>
      </div>

      {/* Model Selector */}
      <div className="flex items-center flex-wrap gap-2 sm:gap-4 mb-3 sm:mb-4">
        <div className="flex rounded-lg border border-gray-200 overflow-hidden">
          <button
            type="button"
            onClick={() => setSelectedModel("solar")}
            className={`px-2 sm:px-4 py-1.5 sm:py-2 text-xs sm:text-sm font-medium touch-manipulation ${
              selectedModel === "solar"
                ? "bg-[#C7911B] text-white"
                : "bg-white text-gray-600 hover:bg-gray-50"
            }`}
          >
            <span className="hidden sm:inline">Solar Model</span>
            <span className="sm:hidden">Solar</span>
          </button>
          <button
            type="button"
            onClick={() => setSelectedModel("voltage")}
            className={`px-2 sm:px-4 py-1.5 sm:py-2 text-xs sm:text-sm font-medium touch-manipulation ${
              selectedModel === "voltage"
                ? "bg-[#74045F] text-white"
                : "bg-white text-gray-600 hover:bg-gray-50"
            }`}
          >
            <span className="hidden sm:inline">Voltage Model</span>
            <span className="sm:hidden">Voltage</span>
          </button>
        </div>

        {/* Quick Health Badge */}
        {selectedHealth && (
          <div
            className={`flex items-center px-2 sm:px-3 py-1 sm:py-1.5 rounded-full text-[10px] sm:text-sm font-medium ${
              selectedHealth.accuracy_status === "good"
                ? "bg-green-100 text-green-700"
                : selectedHealth.accuracy_status === "warning"
                  ? "bg-amber-100 text-amber-700"
                  : "bg-red-100 text-red-700"
            }`}
          >
            {getHealthIcon(selectedHealth.accuracy_status, true)}
            <span className="ml-0.5 sm:ml-1 capitalize">{selectedHealth.accuracy_status}</span>
          </div>
        )}
      </div>

      {/* Error Banner */}
      {error && (
        <div className="bg-amber-50 text-amber-700 px-2 sm:px-3 py-1.5 sm:py-2 rounded mb-3 sm:mb-4 text-xs sm:text-sm flex items-center">
          <AlertTriangle className="w-3.5 h-3.5 sm:w-4 sm:h-4 mr-1.5 sm:mr-2 flex-shrink-0" />
          {error}
        </div>
      )}

      {/* Loading State */}
      {isLoading && (
        <div className="flex items-center justify-center h-48 sm:h-64">
          <div className="animate-pulse text-gray-400 text-sm">Loading monitoring data...</div>
        </div>
      )}

      {/* Health Overview */}
      {!isLoading && selectedHealth && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-1.5 sm:gap-3 mb-3 sm:mb-4">
          <div className="bg-gray-50 rounded-lg p-2 sm:p-3 text-center">
            <p className="text-[10px] sm:text-xs text-gray-500 font-medium">Version</p>
            <p className="text-sm sm:text-lg font-bold text-gray-800">
              {selectedHealth.model_version}
            </p>
          </div>
          <div className="bg-blue-50 rounded-lg p-2 sm:p-3 text-center">
            <p className="text-[10px] sm:text-xs text-blue-600 font-medium truncate">
              Predictions (24h)
            </p>
            <p className="text-sm sm:text-lg font-bold text-blue-700">
              {selectedHealth.predictions_24h.toLocaleString()}
            </p>
          </div>
          <div className="bg-purple-50 rounded-lg p-2 sm:p-3 text-center">
            <p className="text-[10px] sm:text-xs text-purple-600 font-medium">Avg Latency</p>
            <p className="text-sm sm:text-lg font-bold text-purple-700">
              {selectedHealth.avg_latency_ms.toFixed(0)}ms
            </p>
          </div>
          <div
            className={`rounded-lg p-2 sm:p-3 text-center ${
              drift?.overall_drift_detected ? "bg-amber-50" : "bg-green-50"
            }`}
          >
            <p
              className={`text-[10px] sm:text-xs font-medium ${
                drift?.overall_drift_detected ? "text-amber-600" : "text-green-600"
              }`}
            >
              Data Drift
            </p>
            <p
              className={`text-sm sm:text-lg font-bold ${
                drift?.overall_drift_detected ? "text-amber-700" : "text-green-700"
              }`}
            >
              {drift?.overall_drift_detected ? "Detected" : "Normal"}
            </p>
          </div>
        </div>
      )}

      {/* Charts Row */}
      {!isLoading && performance && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 sm:gap-4 mb-3 sm:mb-4">
          {/* Metrics Timeline */}
          <div>
            <h4 className="text-xs sm:text-sm font-medium text-gray-600 mb-1.5 sm:mb-2">
              <span className="hidden sm:inline">Accuracy Metrics (7 Days)</span>
              <span className="sm:hidden">Accuracy (7d)</span>
            </h4>
            {performance.metrics_timeline.length > 0 ? (
              <ResponsiveContainer width="100%" height={height}>
                <LineChart data={performance.metrics_timeline}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis dataKey="period" tick={{ fontSize: 9 }} tickFormatter={formatDate} />
                  <YAxis tick={{ fontSize: 9 }} />
                  <Tooltip
                    formatter={(value: number, name: string) => [
                      value?.toFixed(2),
                      name.toUpperCase(),
                    ]}
                    labelFormatter={formatDate}
                    contentStyle={{
                      backgroundColor: "white",
                      borderRadius: "8px",
                      boxShadow: "0 2px 8px rgba(0,0,0,0.15)",
                    }}
                  />
                  <Legend wrapperStyle={{ fontSize: "10px" }} />
                  {selectedModel === "solar" ? (
                    <Line
                      type="monotone"
                      dataKey="mape"
                      stroke="#C7911B"
                      strokeWidth={2}
                      dot={{ r: 3 }}
                      name="MAPE (%)"
                    />
                  ) : (
                    <Line
                      type="monotone"
                      dataKey="mae"
                      stroke="#74045F"
                      strokeWidth={2}
                      dot={{ r: 3 }}
                      name="MAE (V)"
                    />
                  )}
                  <Line
                    type="monotone"
                    dataKey="rmse"
                    stroke="#6B7280"
                    strokeWidth={2}
                    dot={{ r: 3 }}
                    name="RMSE"
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-48 sm:h-64 text-gray-400 text-sm">
                No metrics data available
              </div>
            )}
          </div>

          {/* Drift Indicators */}
          <div>
            <h4 className="text-xs sm:text-sm font-medium text-gray-600 mb-1.5 sm:mb-2">
              <span className="hidden sm:inline">Feature Drift Analysis</span>
              <span className="sm:hidden">Drift Analysis</span>
            </h4>
            {drift && drift.drift_indicators.length > 0 ? (
              <ResponsiveContainer width="100%" height={height}>
                <BarChart data={drift.drift_indicators} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis type="number" domain={[0, 4]} tick={{ fontSize: 9 }} />
                  <YAxis type="category" dataKey="feature" tick={{ fontSize: 8 }} width={60} />
                  <Tooltip
                    formatter={(value: number) => [`${value.toFixed(2)}`, "Drift Score"]}
                    contentStyle={{
                      backgroundColor: "white",
                      borderRadius: "8px",
                      boxShadow: "0 2px 8px rgba(0,0,0,0.15)",
                    }}
                  />
                  <Bar dataKey="drift_score" name="Drift Score">
                    {drift.drift_indicators.map((entry) => (
                      <Cell
                        key={`cell-${entry.feature}`}
                        fill={entry.drift_detected ? "#F59E0B" : "#22C55E"}
                      />
                    ))}
                  </Bar>
                  {/* Threshold line */}
                  <Line
                    type="monotone"
                    dataKey={() => 2.0}
                    stroke="#EF4444"
                    strokeDasharray="5 5"
                    dot={false}
                  />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-48 sm:h-64 text-gray-400 text-sm">
                No drift data available
              </div>
            )}
          </div>
        </div>
      )}

      {/* Target Comparison */}
      {!isLoading && performance && (
        <div className="bg-gray-50 rounded-lg p-2 sm:p-4 mb-3 sm:mb-4">
          <h4 className="text-xs sm:text-sm font-medium text-gray-600 mb-2 sm:mb-3">
            TOR Target Compliance
          </h4>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2 sm:gap-4">
            {selectedModel === "solar" ? (
              <>
                <div className="text-center">
                  <p className="text-[10px] sm:text-xs text-gray-500">MAPE</p>
                  <div className="flex items-center justify-center">
                    <p className="text-sm sm:text-xl font-bold text-[#C7911B]">
                      {performance.metrics_timeline.length > 0
                        ? (
                            performance.metrics_timeline.reduce(
                              (sum, m) => sum + (m.mape || 0),
                              0
                            ) / performance.metrics_timeline.length
                          ).toFixed(1)
                        : "--"}
                      %
                    </p>
                    {performance.targets.mape && (
                      <span
                        className={`ml-1 sm:ml-2 ${
                          (
                            performance.metrics_timeline.reduce(
                              (sum, m) => sum + (m.mape || 0),
                              0
                            ) / (performance.metrics_timeline.length || 1)
                          ) < performance.targets.mape
                            ? "text-green-500"
                            : "text-red-500"
                        }`}
                      >
                        {performance.metrics_timeline.reduce((sum, m) => sum + (m.mape || 0), 0) /
                          (performance.metrics_timeline.length || 1) <
                        performance.targets.mape ? (
                          <TrendingDown className="w-3 h-3 sm:w-4 sm:h-4" />
                        ) : (
                          <TrendingUp className="w-3 h-3 sm:w-4 sm:h-4" />
                        )}
                      </span>
                    )}
                  </div>
                  <p className="text-[10px] sm:text-xs text-gray-400">
                    Target: &lt;{performance.targets.mape}%
                  </p>
                </div>
                <div className="text-center">
                  <p className="text-[10px] sm:text-xs text-gray-500">RMSE</p>
                  <p className="text-sm sm:text-xl font-bold text-[#C7911B]">
                    {performance.overall_metrics.rmse?.toFixed(1) || "--"}{" "}
                    <span className="text-[10px] sm:text-sm">kW</span>
                  </p>
                  <p className="text-[10px] sm:text-xs text-gray-400">
                    Target: &lt;{performance.targets.rmse} kW
                  </p>
                </div>
              </>
            ) : (
              <>
                <div className="text-center">
                  <p className="text-[10px] sm:text-xs text-gray-500">MAE</p>
                  <div className="flex items-center justify-center">
                    <p className="text-sm sm:text-xl font-bold text-[#74045F]">
                      {performance.overall_metrics.mae?.toFixed(2) || "--"}V
                    </p>
                    {performance.targets.mae && performance.overall_metrics.mae && (
                      <span
                        className={`ml-1 sm:ml-2 ${
                          performance.overall_metrics.mae < performance.targets.mae
                            ? "text-green-500"
                            : "text-red-500"
                        }`}
                      >
                        {performance.overall_metrics.mae < performance.targets.mae ? (
                          <TrendingDown className="w-3 h-3 sm:w-4 sm:h-4" />
                        ) : (
                          <TrendingUp className="w-3 h-3 sm:w-4 sm:h-4" />
                        )}
                      </span>
                    )}
                  </div>
                  <p className="text-[10px] sm:text-xs text-gray-400">
                    Target: &lt;{performance.targets.mae}V
                  </p>
                </div>
                <div className="text-center">
                  <p className="text-[10px] sm:text-xs text-gray-500">RMSE</p>
                  <p className="text-sm sm:text-xl font-bold text-[#74045F]">
                    {performance.overall_metrics.rmse?.toFixed(2) || "--"}V
                  </p>
                  <p className="text-[10px] sm:text-xs text-gray-400">
                    Target: &lt;{performance.targets.rmse}V
                  </p>
                </div>
              </>
            )}
            <div className="text-center">
              <p className="text-[10px] sm:text-xs text-gray-500 truncate">Total Predictions</p>
              <p className="text-sm sm:text-xl font-bold text-gray-800">
                {performance.overall_metrics.total_predictions.toLocaleString()}
              </p>
              <p className="text-[10px] sm:text-xs text-gray-400">Last 7 days</p>
            </div>
            <div className="text-center">
              <p className="text-[10px] sm:text-xs text-gray-500 truncate">Latency Target</p>
              <p className="text-sm sm:text-xl font-bold text-gray-800">
                {selectedHealth?.avg_latency_ms
                  ? selectedHealth.avg_latency_ms < 500
                    ? "Pass"
                    : "Fail"
                  : "--"}
              </p>
              <p className="text-[10px] sm:text-xs text-gray-400">Target: &lt;500ms</p>
            </div>
          </div>
        </div>
      )}

      {/* Issues & Recommendations */}
      {!isLoading && (selectedHealth?.issues.length || 0) > 0 && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-2 sm:p-3 mb-3 sm:mb-4">
          <h4 className="text-xs sm:text-sm font-medium text-amber-800 mb-1.5 sm:mb-2 flex items-center">
            <AlertTriangle className="w-3.5 h-3.5 sm:w-4 sm:h-4 mr-1.5 sm:mr-2 flex-shrink-0" />
            Issues Detected
          </h4>
          <ul className="text-xs sm:text-sm text-amber-700 space-y-0.5 sm:space-y-1">
            {selectedHealth?.issues.map((issue) => (
              <li key={issue} className="flex items-start">
                <span className="mr-1.5 sm:mr-2">•</span>
                <span className="flex-1">{issue}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {!isLoading && drift?.recommendations && drift.recommendations.length > 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-2 sm:p-3">
          <h4 className="text-xs sm:text-sm font-medium text-blue-800 mb-1.5 sm:mb-2 flex items-center">
            <Zap className="w-3.5 h-3.5 sm:w-4 sm:h-4 mr-1.5 sm:mr-2 flex-shrink-0" />
            Recommendations
          </h4>
          <ul className="text-xs sm:text-sm text-blue-700 space-y-0.5 sm:space-y-1">
            {drift.recommendations.map((rec) => (
              <li key={rec} className="flex items-start">
                <span className="mr-1.5 sm:mr-2">•</span>
                <span className="flex-1">{rec}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Footer */}
      <div className="mt-2 sm:mt-4 pt-2 sm:pt-3 border-t border-gray-100">
        <p className="text-[10px] sm:text-xs text-gray-500 flex items-center flex-wrap">
          <Clock className="w-2.5 h-2.5 sm:w-3 sm:h-3 mr-0.5 sm:mr-1 flex-shrink-0" />
          <span className="hidden sm:inline">
            Last updated: {lastUpdated || "Loading..."} | Auto-refresh: 60s
          </span>
          <span className="sm:hidden">
            {lastUpdated ? new Date(lastUpdated).toLocaleTimeString() : "..."} | 60s
          </span>
        </p>
      </div>
    </div>
  );
}
