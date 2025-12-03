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
  Area,
  AreaChart,
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

const HEALTH_COLORS = {
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

  const getHealthIcon = (status: string) => {
    switch (status) {
      case "good":
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case "warning":
        return <AlertTriangle className="w-5 h-5 text-amber-500" />;
      case "degraded":
        return <XCircle className="w-5 h-5 text-red-500" />;
      default:
        return <Activity className="w-5 h-5 text-gray-400" />;
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
    <div className="bg-white rounded-lg shadow-md p-4 border-l-4 border-[#74045F]">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center">
          <BarChart2 className="w-5 h-5 text-[#74045F] mr-2" />
          <h3 className="text-lg font-semibold text-gray-800">Model Performance</h3>
        </div>
        <button
          type="button"
          onClick={loadData}
          className="p-2 hover:bg-gray-100 rounded-full transition-colors"
          title="Refresh"
        >
          <RefreshCw className={`w-4 h-4 text-gray-500 ${isLoading ? "animate-spin" : ""}`} />
        </button>
      </div>

      {/* Model Selector */}
      <div className="flex items-center space-x-4 mb-4">
        <div className="flex rounded-lg border border-gray-200 overflow-hidden">
          <button
            type="button"
            onClick={() => setSelectedModel("solar")}
            className={`px-4 py-2 text-sm font-medium ${
              selectedModel === "solar"
                ? "bg-[#C7911B] text-white"
                : "bg-white text-gray-600 hover:bg-gray-50"
            }`}
          >
            Solar Model
          </button>
          <button
            type="button"
            onClick={() => setSelectedModel("voltage")}
            className={`px-4 py-2 text-sm font-medium ${
              selectedModel === "voltage"
                ? "bg-[#74045F] text-white"
                : "bg-white text-gray-600 hover:bg-gray-50"
            }`}
          >
            Voltage Model
          </button>
        </div>

        {/* Quick Health Badge */}
        {selectedHealth && (
          <div
            className={`flex items-center px-3 py-1.5 rounded-full text-sm font-medium ${
              selectedHealth.accuracy_status === "good"
                ? "bg-green-100 text-green-700"
                : selectedHealth.accuracy_status === "warning"
                  ? "bg-amber-100 text-amber-700"
                  : "bg-red-100 text-red-700"
            }`}
          >
            {getHealthIcon(selectedHealth.accuracy_status)}
            <span className="ml-1 capitalize">{selectedHealth.accuracy_status}</span>
          </div>
        )}
      </div>

      {/* Error Banner */}
      {error && (
        <div className="bg-amber-50 text-amber-700 px-3 py-2 rounded mb-4 text-sm flex items-center">
          <AlertTriangle className="w-4 h-4 mr-2" />
          {error}
        </div>
      )}

      {/* Loading State */}
      {isLoading && (
        <div className="flex items-center justify-center h-64">
          <div className="animate-pulse text-gray-400">Loading monitoring data...</div>
        </div>
      )}

      {/* Health Overview */}
      {!isLoading && selectedHealth && (
        <div className="grid grid-cols-4 gap-3 mb-4">
          <div className="bg-gray-50 rounded-lg p-3 text-center">
            <p className="text-xs text-gray-500 font-medium">Version</p>
            <p className="text-lg font-bold text-gray-800">{selectedHealth.model_version}</p>
          </div>
          <div className="bg-blue-50 rounded-lg p-3 text-center">
            <p className="text-xs text-blue-600 font-medium">Predictions (24h)</p>
            <p className="text-lg font-bold text-blue-700">
              {selectedHealth.predictions_24h.toLocaleString()}
            </p>
          </div>
          <div className="bg-purple-50 rounded-lg p-3 text-center">
            <p className="text-xs text-purple-600 font-medium">Avg Latency</p>
            <p className="text-lg font-bold text-purple-700">
              {selectedHealth.avg_latency_ms.toFixed(0)}ms
            </p>
          </div>
          <div
            className={`rounded-lg p-3 text-center ${
              drift?.overall_drift_detected ? "bg-amber-50" : "bg-green-50"
            }`}
          >
            <p
              className={`text-xs font-medium ${
                drift?.overall_drift_detected ? "text-amber-600" : "text-green-600"
              }`}
            >
              Data Drift
            </p>
            <p
              className={`text-lg font-bold ${
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
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
          {/* Metrics Timeline */}
          <div>
            <h4 className="text-sm font-medium text-gray-600 mb-2">
              Accuracy Metrics (7 Days)
            </h4>
            {performance.metrics_timeline.length > 0 ? (
              <ResponsiveContainer width="100%" height={height}>
                <LineChart data={performance.metrics_timeline}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis dataKey="period" tick={{ fontSize: 10 }} tickFormatter={formatDate} />
                  <YAxis tick={{ fontSize: 10 }} />
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
                  <Legend />
                  {selectedModel === "solar" ? (
                    <Line
                      type="monotone"
                      dataKey="mape"
                      stroke="#C7911B"
                      strokeWidth={2}
                      dot={{ r: 4 }}
                      name="MAPE (%)"
                    />
                  ) : (
                    <Line
                      type="monotone"
                      dataKey="mae"
                      stroke="#74045F"
                      strokeWidth={2}
                      dot={{ r: 4 }}
                      name="MAE (V)"
                    />
                  )}
                  <Line
                    type="monotone"
                    dataKey="rmse"
                    stroke="#6B7280"
                    strokeWidth={2}
                    dot={{ r: 4 }}
                    name="RMSE"
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-64 text-gray-400">
                No metrics data available
              </div>
            )}
          </div>

          {/* Drift Indicators */}
          <div>
            <h4 className="text-sm font-medium text-gray-600 mb-2">
              Feature Drift Analysis
            </h4>
            {drift && drift.drift_indicators.length > 0 ? (
              <ResponsiveContainer width="100%" height={height}>
                <BarChart data={drift.drift_indicators} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis type="number" domain={[0, 4]} tick={{ fontSize: 10 }} />
                  <YAxis type="category" dataKey="feature" tick={{ fontSize: 10 }} width={80} />
                  <Tooltip
                    formatter={(value: number) => [`${value.toFixed(2)}`, "Drift Score"]}
                    contentStyle={{
                      backgroundColor: "white",
                      borderRadius: "8px",
                      boxShadow: "0 2px 8px rgba(0,0,0,0.15)",
                    }}
                  />
                  <Bar dataKey="drift_score" name="Drift Score">
                    {drift.drift_indicators.map((entry, index) => (
                      <Cell
                        key={`cell-${index}`}
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
              <div className="flex items-center justify-center h-64 text-gray-400">
                No drift data available
              </div>
            )}
          </div>
        </div>
      )}

      {/* Target Comparison */}
      {!isLoading && performance && (
        <div className="bg-gray-50 rounded-lg p-4 mb-4">
          <h4 className="text-sm font-medium text-gray-600 mb-3">
            TOR Target Compliance
          </h4>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {selectedModel === "solar" ? (
              <>
                <div className="text-center">
                  <p className="text-xs text-gray-500">MAPE</p>
                  <div className="flex items-center justify-center">
                    <p className="text-xl font-bold text-[#C7911B]">
                      {performance.metrics_timeline.length > 0
                        ? (
                            performance.metrics_timeline.reduce((sum, m) => sum + (m.mape || 0), 0) /
                            performance.metrics_timeline.length
                          ).toFixed(1)
                        : "--"}
                      %
                    </p>
                    {performance.targets.mape && (
                      <span
                        className={`ml-2 ${
                          (performance.metrics_timeline.reduce((sum, m) => sum + (m.mape || 0), 0) /
                            (performance.metrics_timeline.length || 1)) <
                          performance.targets.mape
                            ? "text-green-500"
                            : "text-red-500"
                        }`}
                      >
                        {(performance.metrics_timeline.reduce((sum, m) => sum + (m.mape || 0), 0) /
                          (performance.metrics_timeline.length || 1)) <
                        performance.targets.mape ? (
                          <TrendingDown className="w-4 h-4" />
                        ) : (
                          <TrendingUp className="w-4 h-4" />
                        )}
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-gray-400">Target: &lt;{performance.targets.mape}%</p>
                </div>
                <div className="text-center">
                  <p className="text-xs text-gray-500">RMSE</p>
                  <p className="text-xl font-bold text-[#C7911B]">
                    {performance.overall_metrics.rmse?.toFixed(1) || "--"} kW
                  </p>
                  <p className="text-xs text-gray-400">Target: &lt;{performance.targets.rmse} kW</p>
                </div>
              </>
            ) : (
              <>
                <div className="text-center">
                  <p className="text-xs text-gray-500">MAE</p>
                  <div className="flex items-center justify-center">
                    <p className="text-xl font-bold text-[#74045F]">
                      {performance.overall_metrics.mae?.toFixed(2) || "--"}V
                    </p>
                    {performance.targets.mae && performance.overall_metrics.mae && (
                      <span
                        className={`ml-2 ${
                          performance.overall_metrics.mae < performance.targets.mae
                            ? "text-green-500"
                            : "text-red-500"
                        }`}
                      >
                        {performance.overall_metrics.mae < performance.targets.mae ? (
                          <TrendingDown className="w-4 h-4" />
                        ) : (
                          <TrendingUp className="w-4 h-4" />
                        )}
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-gray-400">Target: &lt;{performance.targets.mae}V</p>
                </div>
                <div className="text-center">
                  <p className="text-xs text-gray-500">RMSE</p>
                  <p className="text-xl font-bold text-[#74045F]">
                    {performance.overall_metrics.rmse?.toFixed(2) || "--"}V
                  </p>
                  <p className="text-xs text-gray-400">Target: &lt;{performance.targets.rmse}V</p>
                </div>
              </>
            )}
            <div className="text-center">
              <p className="text-xs text-gray-500">Total Predictions</p>
              <p className="text-xl font-bold text-gray-800">
                {performance.overall_metrics.total_predictions.toLocaleString()}
              </p>
              <p className="text-xs text-gray-400">Last 7 days</p>
            </div>
            <div className="text-center">
              <p className="text-xs text-gray-500">Latency Target</p>
              <p className="text-xl font-bold text-gray-800">
                {selectedHealth?.avg_latency_ms
                  ? selectedHealth.avg_latency_ms < 500
                    ? "Pass"
                    : "Fail"
                  : "--"}
              </p>
              <p className="text-xs text-gray-400">Target: &lt;500ms</p>
            </div>
          </div>
        </div>
      )}

      {/* Issues & Recommendations */}
      {!isLoading && (selectedHealth?.issues.length || 0) > 0 && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 mb-4">
          <h4 className="text-sm font-medium text-amber-800 mb-2 flex items-center">
            <AlertTriangle className="w-4 h-4 mr-2" />
            Issues Detected
          </h4>
          <ul className="text-sm text-amber-700 space-y-1">
            {selectedHealth?.issues.map((issue, i) => (
              <li key={i} className="flex items-start">
                <span className="mr-2">•</span>
                {issue}
              </li>
            ))}
          </ul>
        </div>
      )}

      {!isLoading && drift?.recommendations && drift.recommendations.length > 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
          <h4 className="text-sm font-medium text-blue-800 mb-2 flex items-center">
            <Zap className="w-4 h-4 mr-2" />
            Recommendations
          </h4>
          <ul className="text-sm text-blue-700 space-y-1">
            {drift.recommendations.map((rec, i) => (
              <li key={i} className="flex items-start">
                <span className="mr-2">•</span>
                {rec}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Footer */}
      <div className="mt-4 pt-3 border-t border-gray-100">
        <p className="text-xs text-gray-500 flex items-center">
          <Clock className="w-3 h-3 mr-1" />
          Last updated: {lastUpdated || "Loading..."} | Auto-refresh: 60s
        </p>
      </div>
    </div>
  );
}
