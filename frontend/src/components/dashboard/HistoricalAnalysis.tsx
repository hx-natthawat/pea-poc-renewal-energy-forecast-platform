"use client";

import {
  AlertTriangle,
  Calendar,
  Download,
  FileSpreadsheet,
  RefreshCw,
  Sun,
  Zap,
} from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { getApiBaseUrl } from "@/lib/api";

interface SolarSummary {
  total_measurements: number;
  avg_power_kw: number;
  min_power_kw: number;
  max_power_kw: number;
  std_power_kw: number;
  total_energy_kwh: number;
  avg_irradiance: number;
  avg_temperature: number;
}

interface HourlyDistribution {
  hour: number;
  avg_power: number;
  count: number;
}

interface DailyAggregate {
  date: string;
  avg_power: number;
  peak_power: number;
  energy_kwh: number;
}

interface VoltageSummary {
  total_measurements: number;
  avg_voltage: number | null;
  min_voltage: number | null;
  max_voltage: number | null;
  total_violations: number;
}

interface ProsumerStats {
  prosumer_id: string;
  phase: string;
  name: string;
  measurements: number;
  avg_voltage: number | null;
  min_voltage: number | null;
  max_voltage: number | null;
  violations: number;
}

interface PhaseStats {
  phase: string;
  measurements: number;
  avg_voltage: number | null;
  violations: number;
}

type DataType = "solar" | "voltage";

interface HistoricalAnalysisProps {
  height?: number;
}

export default function HistoricalAnalysis({ height = 280 }: HistoricalAnalysisProps) {
  const [dataType, setDataType] = useState<DataType>("solar");
  const [startDate, setStartDate] = useState<string>(() => {
    const d = new Date();
    d.setDate(d.getDate() - 7);
    return d.toISOString().split("T")[0];
  });
  const [endDate, setEndDate] = useState<string>(() => {
    return new Date().toISOString().split("T")[0];
  });

  // Solar data state
  const [solarSummary, setSolarSummary] = useState<SolarSummary | null>(null);
  const [hourlyDistribution, setHourlyDistribution] = useState<HourlyDistribution[]>([]);
  const [dailyAggregates, setDailyAggregates] = useState<DailyAggregate[]>([]);

  // Voltage data state
  const [voltageSummary, setVoltageSummary] = useState<VoltageSummary | null>(null);
  const [prosumerStats, setProsumerStats] = useState<ProsumerStats[]>([]);
  const [phaseStats, setPhaseStats] = useState<PhaseStats[]>([]);

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const start = new Date(startDate).toISOString();
      const end = new Date(endDate + "T23:59:59").toISOString();

      if (dataType === "solar") {
        const response = await fetch(
          `${getApiBaseUrl()}/api/v1/history/solar/summary?start_date=${encodeURIComponent(start)}&end_date=${encodeURIComponent(end)}`
        );

        if (!response.ok) {
          throw new Error("Failed to fetch solar summary");
        }

        const result = await response.json();
        if (result.status === "success") {
          setSolarSummary(result.data.statistics);
          setHourlyDistribution(result.data.hourly_distribution || []);
          setDailyAggregates(result.data.daily_aggregates || []);
        }
      } else {
        const response = await fetch(
          `${getApiBaseUrl()}/api/v1/history/voltage/summary?start_date=${encodeURIComponent(start)}&end_date=${encodeURIComponent(end)}`
        );

        if (!response.ok) {
          throw new Error("Failed to fetch voltage summary");
        }

        const result = await response.json();
        if (result.status === "success") {
          setVoltageSummary(result.data.overall);
          setProsumerStats(result.data.by_prosumer || []);
          setPhaseStats(result.data.by_phase || []);
        }
      }
    } catch (err) {
      console.error("Error fetching historical data:", err);
      setError("Could not load historical data");
    } finally {
      setIsLoading(false);
    }
  }, [dataType, startDate, endDate]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleExport = async (format: "csv" | "json") => {
    try {
      const start = new Date(startDate).toISOString();
      const end = new Date(endDate + "T23:59:59").toISOString();

      const url = `${getApiBaseUrl()}/api/v1/history/export?data_type=${dataType}&start_date=${encodeURIComponent(start)}&end_date=${encodeURIComponent(end)}&format=${format}`;

      const response = await fetch(url);
      if (!response.ok) {
        throw new Error("Export failed");
      }

      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = downloadUrl;
      a.download = `${dataType}_export_${startDate}_${endDate}.${format}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(downloadUrl);
    } catch (err) {
      console.error("Export error:", err);
      setError("Export failed. Please try again.");
    }
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
    });
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-4 border-l-4 border-[#74045F]">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center">
          <Calendar className="w-5 h-5 text-[#74045F] mr-2" />
          <h3 className="text-lg font-semibold text-gray-800">Historical Analysis</h3>
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

      {/* Controls */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-3 mb-4">
        {/* Data Type Toggle */}
        <div className="flex rounded-lg border border-gray-200 overflow-hidden">
          <button
            type="button"
            onClick={() => setDataType("solar")}
            className={`flex-1 px-3 py-2 text-sm font-medium flex items-center justify-center ${
              dataType === "solar"
                ? "bg-[#C7911B] text-white"
                : "bg-white text-gray-600 hover:bg-gray-50"
            }`}
          >
            <Sun className="w-4 h-4 mr-1" />
            Solar
          </button>
          <button
            type="button"
            onClick={() => setDataType("voltage")}
            className={`flex-1 px-3 py-2 text-sm font-medium flex items-center justify-center ${
              dataType === "voltage"
                ? "bg-[#74045F] text-white"
                : "bg-white text-gray-600 hover:bg-gray-50"
            }`}
          >
            <Zap className="w-4 h-4 mr-1" />
            Voltage
          </button>
        </div>

        {/* Date Range */}
        <div>
          <input
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm"
          />
        </div>
        <div>
          <input
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm"
          />
        </div>

        {/* Export Buttons */}
        <div className="flex space-x-2">
          <button
            type="button"
            onClick={() => handleExport("csv")}
            className="flex-1 px-3 py-2 bg-green-600 text-white text-sm rounded-lg hover:bg-green-700 flex items-center justify-center"
          >
            <FileSpreadsheet className="w-4 h-4 mr-1" />
            CSV
          </button>
          <button
            type="button"
            onClick={() => handleExport("json")}
            className="flex-1 px-3 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 flex items-center justify-center"
          >
            <Download className="w-4 h-4 mr-1" />
            JSON
          </button>
        </div>
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
          <div className="animate-pulse text-gray-400">Loading historical data...</div>
        </div>
      )}

      {/* Solar Content */}
      {!isLoading && dataType === "solar" && solarSummary && (
        <>
          {/* Summary Stats */}
          <div className="grid grid-cols-4 gap-3 mb-4">
            <div className="bg-amber-50 rounded-lg p-3 text-center">
              <p className="text-xs text-amber-600 font-medium">Total Energy</p>
              <p className="text-xl font-bold text-amber-700">
                {solarSummary.total_energy_kwh.toLocaleString()} kWh
              </p>
            </div>
            <div className="bg-gray-50 rounded-lg p-3 text-center">
              <p className="text-xs text-gray-500 font-medium">Avg Power</p>
              <p className="text-xl font-bold text-gray-800">
                {solarSummary.avg_power_kw.toFixed(1)} kW
              </p>
            </div>
            <div className="bg-green-50 rounded-lg p-3 text-center">
              <p className="text-xs text-green-600 font-medium">Peak Power</p>
              <p className="text-xl font-bold text-green-700">
                {solarSummary.max_power_kw.toFixed(1)} kW
              </p>
            </div>
            <div className="bg-blue-50 rounded-lg p-3 text-center">
              <p className="text-xs text-blue-600 font-medium">Avg Irradiance</p>
              <p className="text-xl font-bold text-blue-700">
                {solarSummary.avg_irradiance.toFixed(0)} W/m²
              </p>
            </div>
          </div>

          {/* Charts Row */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Hourly Distribution */}
            <div>
              <h4 className="text-sm font-medium text-gray-600 mb-2">
                Hourly Power Distribution
              </h4>
              <ResponsiveContainer width="100%" height={height}>
                <BarChart data={hourlyDistribution}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis
                    dataKey="hour"
                    tick={{ fontSize: 10 }}
                    tickFormatter={(h) => `${h}:00`}
                  />
                  <YAxis tick={{ fontSize: 10 }} />
                  <Tooltip
                    formatter={(value: number) => [`${value.toFixed(1)} kW`, "Avg Power"]}
                    labelFormatter={(hour) => `Hour: ${hour}:00`}
                    contentStyle={{
                      backgroundColor: "white",
                      borderRadius: "8px",
                      boxShadow: "0 2px 8px rgba(0,0,0,0.15)",
                    }}
                  />
                  <Bar dataKey="avg_power" fill="#C7911B" name="Avg Power (kW)" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Daily Trend */}
            <div>
              <h4 className="text-sm font-medium text-gray-600 mb-2">
                Daily Energy Production
              </h4>
              <ResponsiveContainer width="100%" height={height}>
                <AreaChart data={dailyAggregates}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis dataKey="date" tick={{ fontSize: 10 }} tickFormatter={formatDate} />
                  <YAxis tick={{ fontSize: 10 }} />
                  <Tooltip
                    formatter={(value: number, name: string) => [
                      `${value.toFixed(1)} ${name === "energy_kwh" ? "kWh" : "kW"}`,
                      name === "energy_kwh" ? "Energy" : name === "peak_power" ? "Peak" : "Avg",
                    ]}
                    labelFormatter={formatDate}
                    contentStyle={{
                      backgroundColor: "white",
                      borderRadius: "8px",
                      boxShadow: "0 2px 8px rgba(0,0,0,0.15)",
                    }}
                  />
                  <Legend />
                  <Area
                    type="monotone"
                    dataKey="energy_kwh"
                    stroke="#C7911B"
                    fill="#C7911B"
                    fillOpacity={0.3}
                    name="Energy (kWh)"
                  />
                  <Area
                    type="monotone"
                    dataKey="peak_power"
                    stroke="#16a34a"
                    fill="#16a34a"
                    fillOpacity={0.2}
                    name="Peak (kW)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
        </>
      )}

      {/* Voltage Content */}
      {!isLoading && dataType === "voltage" && voltageSummary && (
        <>
          {/* Summary Stats */}
          <div className="grid grid-cols-4 gap-3 mb-4">
            <div className="bg-gray-50 rounded-lg p-3 text-center">
              <p className="text-xs text-gray-500 font-medium">Measurements</p>
              <p className="text-xl font-bold text-gray-800">
                {voltageSummary.total_measurements.toLocaleString()}
              </p>
            </div>
            <div className="bg-purple-50 rounded-lg p-3 text-center">
              <p className="text-xs text-purple-600 font-medium">Avg Voltage</p>
              <p className="text-xl font-bold text-purple-700">
                {voltageSummary.avg_voltage?.toFixed(1) || "--"}V
              </p>
            </div>
            <div className="bg-blue-50 rounded-lg p-3 text-center">
              <p className="text-xs text-blue-600 font-medium">Range</p>
              <p className="text-xl font-bold text-blue-700">
                {voltageSummary.min_voltage?.toFixed(0)}-{voltageSummary.max_voltage?.toFixed(0)}V
              </p>
            </div>
            <div className="bg-red-50 rounded-lg p-3 text-center">
              <p className="text-xs text-red-600 font-medium">Violations</p>
              <p className="text-xl font-bold text-red-700">
                {voltageSummary.total_violations}
              </p>
            </div>
          </div>

          {/* Charts Row */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Phase Comparison */}
            <div>
              <h4 className="text-sm font-medium text-gray-600 mb-2">
                Voltage by Phase
              </h4>
              <ResponsiveContainer width="100%" height={height}>
                <BarChart data={phaseStats} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis type="number" domain={[210, 250]} tick={{ fontSize: 10 }} />
                  <YAxis type="category" dataKey="phase" tick={{ fontSize: 12 }} width={60} />
                  <Tooltip
                    formatter={(value: number) => [`${value.toFixed(1)}V`, "Avg Voltage"]}
                    contentStyle={{
                      backgroundColor: "white",
                      borderRadius: "8px",
                      boxShadow: "0 2px 8px rgba(0,0,0,0.15)",
                    }}
                  />
                  <Bar
                    dataKey="avg_voltage"
                    fill="#74045F"
                    name="Avg Voltage"
                    radius={[0, 4, 4, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Prosumer Table */}
            <div>
              <h4 className="text-sm font-medium text-gray-600 mb-2">
                Prosumer Statistics
              </h4>
              <div className="overflow-auto max-h-64 border border-gray-200 rounded-lg">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50 sticky top-0">
                    <tr>
                      <th className="px-3 py-2 text-left font-medium text-gray-600">Prosumer</th>
                      <th className="px-3 py-2 text-center font-medium text-gray-600">Phase</th>
                      <th className="px-3 py-2 text-right font-medium text-gray-600">Avg (V)</th>
                      <th className="px-3 py-2 text-right font-medium text-gray-600">Range</th>
                      <th className="px-3 py-2 text-right font-medium text-gray-600">Violations</th>
                    </tr>
                  </thead>
                  <tbody>
                    {prosumerStats.map((p) => (
                      <tr key={p.prosumer_id} className="border-t border-gray-100 hover:bg-gray-50">
                        <td className="px-3 py-2 font-medium">{p.name}</td>
                        <td className="px-3 py-2 text-center">
                          <span
                            className={`px-2 py-0.5 rounded text-xs font-medium ${
                              p.phase === "A"
                                ? "bg-red-100 text-red-700"
                                : p.phase === "B"
                                  ? "bg-yellow-100 text-yellow-700"
                                  : "bg-blue-100 text-blue-700"
                            }`}
                          >
                            {p.phase}
                          </span>
                        </td>
                        <td className="px-3 py-2 text-right">{p.avg_voltage?.toFixed(1) || "--"}</td>
                        <td className="px-3 py-2 text-right text-gray-500">
                          {p.min_voltage?.toFixed(0)}-{p.max_voltage?.toFixed(0)}
                        </td>
                        <td className="px-3 py-2 text-right">
                          {p.violations > 0 ? (
                            <span className="text-red-600 font-medium">{p.violations}</span>
                          ) : (
                            <span className="text-green-600">0</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </>
      )}

      {/* Footer */}
      <div className="mt-4 pt-3 border-t border-gray-100">
        <p className="text-xs text-gray-500">
          Date Range: {startDate} to {endDate} |{" "}
          {dataType === "solar"
            ? `${solarSummary?.total_measurements.toLocaleString() || 0} measurements`
            : `${voltageSummary?.total_measurements.toLocaleString() || 0} measurements`}
        </p>
      </div>
    </div>
  );
}
