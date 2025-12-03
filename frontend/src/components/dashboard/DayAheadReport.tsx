"use client";

import {
  AlertTriangle,
  Calendar,
  CheckCircle,
  ChevronLeft,
  ChevronRight,
  Clock,
  Download,
  FileText,
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

interface HourlyForecast {
  hour: number;
  timestamp: string;
  predicted_power_kw?: number;
  predicted_voltage?: number;
  confidence_lower: number;
  confidence_upper: number;
  status?: string;
  conditions?: {
    irradiance?: number;
    temperature?: number;
  };
}

interface SolarForecastData {
  forecast_date: string;
  station_id: string;
  generated_at: string;
  model_version: string;
  hourly_forecasts: HourlyForecast[];
  summary: {
    total_energy_kwh: number;
    peak_power_kw: number;
    peak_hour: number;
    generation_hours: number;
  };
}

interface ProsumerForecast {
  prosumer_id: string;
  name: string;
  phase: string;
  hourly_forecasts: HourlyForecast[];
  summary: {
    avg_voltage: number;
    min_voltage: number;
    max_voltage: number;
    violation_hours: number;
  };
}

interface VoltageForecastData {
  forecast_date: string;
  generated_at: string;
  model_version: string;
  prosumer_forecasts: ProsumerForecast[];
  summary: {
    total_prosumers: number;
    total_violation_hours: number;
  };
}

type ForecastType = "solar" | "voltage";

interface DayAheadReportProps {
  height?: number;
}

const STATUS_COLORS = {
  normal: "#22C55E",
  warning: "#F59E0B",
  critical: "#EF4444",
};

export default function DayAheadReport({ height = 280 }: DayAheadReportProps) {
  const [forecastType, setForecastType] = useState<ForecastType>("solar");
  const [targetDate, setTargetDate] = useState<string>(() => {
    const d = new Date();
    d.setDate(d.getDate() + 1);
    return d.toISOString().split("T")[0];
  });

  const [solarForecast, setSolarForecast] = useState<SolarForecastData | null>(null);
  const [voltageForecast, setVoltageForecast] = useState<VoltageForecastData | null>(null);
  const [selectedProsumer, setSelectedProsumer] = useState<string | null>(null);

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadForecast = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      if (forecastType === "solar") {
        const response = await fetch(
          `${getApiBaseUrl()}/api/v1/dayahead/solar?target_date=${targetDate}`
        );
        if (!response.ok) throw new Error("Failed to fetch solar forecast");
        const result = await response.json();
        if (result.status === "success") {
          setSolarForecast(result.data);
        }
      } else {
        const response = await fetch(
          `${getApiBaseUrl()}/api/v1/dayahead/voltage?target_date=${targetDate}`
        );
        if (!response.ok) throw new Error("Failed to fetch voltage forecast");
        const result = await response.json();
        if (result.status === "success") {
          setVoltageForecast(result.data);
          if (result.data.prosumer_forecasts.length > 0 && !selectedProsumer) {
            setSelectedProsumer(result.data.prosumer_forecasts[0].prosumer_id);
          }
        }
      }
    } catch (err) {
      console.error("Error fetching forecast:", err);
      setError("Could not load day-ahead forecast");
    } finally {
      setIsLoading(false);
    }
  }, [forecastType, targetDate, selectedProsumer]);

  useEffect(() => {
    loadForecast();
  }, [loadForecast]);

  const handlePrevDay = () => {
    const d = new Date(targetDate);
    d.setDate(d.getDate() - 1);
    setTargetDate(d.toISOString().split("T")[0]);
  };

  const handleNextDay = () => {
    const d = new Date(targetDate);
    d.setDate(d.getDate() + 1);
    setTargetDate(d.toISOString().split("T")[0]);
  };

  const handleDownloadReport = async (format: "json" | "html") => {
    try {
      const url = `${getApiBaseUrl()}/api/v1/dayahead/report?target_date=${targetDate}&format=${format}`;
      const response = await fetch(url);
      if (!response.ok) throw new Error("Download failed");

      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = downloadUrl;
      a.download = `dayahead_report_${targetDate}.${format}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(downloadUrl);
    } catch (err) {
      console.error("Download error:", err);
      setError("Report download failed");
    }
  };

  const formatHour = (hour: number) => `${hour.toString().padStart(2, "0")}:00`;

  const getSelectedProsumerData = (): ProsumerForecast | undefined => {
    return voltageForecast?.prosumer_forecasts.find((p) => p.prosumer_id === selectedProsumer);
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-4 border-l-4 border-[#C7911B]">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center">
          <FileText className="w-5 h-5 text-[#C7911B] mr-2" />
          <h3 className="text-lg font-semibold text-gray-800">Day-Ahead Forecast</h3>
        </div>
        <div className="flex items-center space-x-2">
          <button
            type="button"
            onClick={() => handleDownloadReport("html")}
            className="px-3 py-1.5 bg-[#74045F] text-white text-sm rounded-lg hover:bg-[#5A0349] flex items-center"
          >
            <Download className="w-4 h-4 mr-1" />
            Report
          </button>
          <button
            type="button"
            onClick={loadForecast}
            className="p-2 hover:bg-gray-100 rounded-full transition-colors"
            title="Refresh"
          >
            <RefreshCw className={`w-4 h-4 text-gray-500 ${isLoading ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>

      {/* Controls */}
      <div className="flex items-center justify-between mb-4">
        {/* Forecast Type Toggle */}
        <div className="flex rounded-lg border border-gray-200 overflow-hidden">
          <button
            type="button"
            onClick={() => setForecastType("solar")}
            className={`px-4 py-2 text-sm font-medium flex items-center ${
              forecastType === "solar"
                ? "bg-[#C7911B] text-white"
                : "bg-white text-gray-600 hover:bg-gray-50"
            }`}
          >
            <Sun className="w-4 h-4 mr-1" />
            Solar
          </button>
          <button
            type="button"
            onClick={() => setForecastType("voltage")}
            className={`px-4 py-2 text-sm font-medium flex items-center ${
              forecastType === "voltage"
                ? "bg-[#74045F] text-white"
                : "bg-white text-gray-600 hover:bg-gray-50"
            }`}
          >
            <Zap className="w-4 h-4 mr-1" />
            Voltage
          </button>
        </div>

        {/* Date Navigation */}
        <div className="flex items-center space-x-2">
          <button
            type="button"
            onClick={handlePrevDay}
            className="p-2 hover:bg-gray-100 rounded-full"
          >
            <ChevronLeft className="w-4 h-4 text-gray-500" />
          </button>
          <div className="flex items-center bg-gray-50 px-3 py-2 rounded-lg">
            <Calendar className="w-4 h-4 text-gray-400 mr-2" />
            <input
              type="date"
              value={targetDate}
              onChange={(e) => setTargetDate(e.target.value)}
              className="bg-transparent text-sm font-medium text-gray-700 outline-none"
            />
          </div>
          <button
            type="button"
            onClick={handleNextDay}
            className="p-2 hover:bg-gray-100 rounded-full"
          >
            <ChevronRight className="w-4 h-4 text-gray-500" />
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
          <div className="animate-pulse text-gray-400">Loading forecast...</div>
        </div>
      )}

      {/* Solar Forecast Content */}
      {!isLoading && forecastType === "solar" && solarForecast && (
        <>
          {/* Summary Stats */}
          <div className="grid grid-cols-4 gap-3 mb-4">
            <div className="bg-amber-50 rounded-lg p-3 text-center">
              <p className="text-xs text-amber-600 font-medium">Total Energy</p>
              <p className="text-xl font-bold text-amber-700">
                {solarForecast.summary.total_energy_kwh.toLocaleString()} kWh
              </p>
            </div>
            <div className="bg-green-50 rounded-lg p-3 text-center">
              <p className="text-xs text-green-600 font-medium">Peak Power</p>
              <p className="text-xl font-bold text-green-700">
                {solarForecast.summary.peak_power_kw.toFixed(1)} kW
              </p>
            </div>
            <div className="bg-blue-50 rounded-lg p-3 text-center">
              <p className="text-xs text-blue-600 font-medium">Peak Hour</p>
              <p className="text-xl font-bold text-blue-700">
                {formatHour(solarForecast.summary.peak_hour)}
              </p>
            </div>
            <div className="bg-purple-50 rounded-lg p-3 text-center">
              <p className="text-xs text-purple-600 font-medium">Generation Hours</p>
              <p className="text-xl font-bold text-purple-700">
                {solarForecast.summary.generation_hours}h
              </p>
            </div>
          </div>

          {/* Hourly Forecast Chart */}
          <div className="mb-4">
            <h4 className="text-sm font-medium text-gray-600 mb-2">
              24-Hour Power Forecast
            </h4>
            <ResponsiveContainer width="100%" height={height}>
              <AreaChart data={solarForecast.hourly_forecasts}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="hour" tick={{ fontSize: 10 }} tickFormatter={formatHour} />
                <YAxis tick={{ fontSize: 10 }} />
                <Tooltip
                  formatter={(value: number) => [`${value.toFixed(1)} kW`, ""]}
                  labelFormatter={(hour) => formatHour(hour as number)}
                  contentStyle={{
                    backgroundColor: "white",
                    borderRadius: "8px",
                    boxShadow: "0 2px 8px rgba(0,0,0,0.15)",
                  }}
                />
                <Legend />
                <Area
                  type="monotone"
                  dataKey="confidence_upper"
                  stroke="transparent"
                  fill="#C7911B"
                  fillOpacity={0.1}
                  name="Upper Bound"
                />
                <Area
                  type="monotone"
                  dataKey="predicted_power_kw"
                  stroke="#C7911B"
                  fill="#C7911B"
                  fillOpacity={0.4}
                  name="Predicted Power"
                />
                <Area
                  type="monotone"
                  dataKey="confidence_lower"
                  stroke="transparent"
                  fill="white"
                  fillOpacity={1}
                  name="Lower Bound"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          {/* Model Info */}
          <div className="text-xs text-gray-500 flex items-center">
            <Clock className="w-3 h-3 mr-1" />
            Generated: {new Date(solarForecast.generated_at).toLocaleString()} | Model:{" "}
            {solarForecast.model_version}
          </div>
        </>
      )}

      {/* Voltage Forecast Content */}
      {!isLoading && forecastType === "voltage" && voltageForecast && (
        <>
          {/* Summary Stats */}
          <div className="grid grid-cols-3 gap-3 mb-4">
            <div className="bg-purple-50 rounded-lg p-3 text-center">
              <p className="text-xs text-purple-600 font-medium">Prosumers</p>
              <p className="text-xl font-bold text-purple-700">
                {voltageForecast.summary.total_prosumers}
              </p>
            </div>
            <div className="bg-red-50 rounded-lg p-3 text-center">
              <p className="text-xs text-red-600 font-medium">Violation Hours</p>
              <p className="text-xl font-bold text-red-700">
                {voltageForecast.summary.total_violation_hours}
              </p>
            </div>
            <div className="bg-green-50 rounded-lg p-3 text-center">
              <p className="text-xs text-green-600 font-medium">Status</p>
              <p className="text-xl font-bold text-green-700 flex items-center justify-center">
                {voltageForecast.summary.total_violation_hours === 0 ? (
                  <>
                    <CheckCircle className="w-5 h-5 mr-1" /> Normal
                  </>
                ) : (
                  <>
                    <AlertTriangle className="w-5 h-5 mr-1 text-amber-500" /> Warnings
                  </>
                )}
              </p>
            </div>
          </div>

          {/* Prosumer Selector */}
          <div className="mb-4">
            <div className="flex flex-wrap gap-2">
              {voltageForecast.prosumer_forecasts.map((p) => (
                <button
                  key={p.prosumer_id}
                  type="button"
                  onClick={() => setSelectedProsumer(p.prosumer_id)}
                  className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                    selectedProsumer === p.prosumer_id
                      ? "bg-[#74045F] text-white"
                      : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                  }`}
                >
                  {p.name}
                  {p.summary.violation_hours > 0 && (
                    <span className="ml-1 px-1.5 py-0.5 bg-red-500 text-white text-xs rounded">
                      {p.summary.violation_hours}
                    </span>
                  )}
                </button>
              ))}
            </div>
          </div>

          {/* Selected Prosumer Chart */}
          {selectedProsumer && getSelectedProsumerData() && (
            <div className="mb-4">
              <h4 className="text-sm font-medium text-gray-600 mb-2">
                24-Hour Voltage Forecast - {getSelectedProsumerData()?.name} (Phase{" "}
                {getSelectedProsumerData()?.phase})
              </h4>
              <ResponsiveContainer width="100%" height={height}>
                <LineChart data={getSelectedProsumerData()?.hourly_forecasts}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis dataKey="hour" tick={{ fontSize: 10 }} tickFormatter={formatHour} />
                  <YAxis domain={[210, 250]} tick={{ fontSize: 10 }} />
                  <Tooltip
                    formatter={(value: number, name: string) => [
                      `${value.toFixed(1)}V`,
                      name === "predicted_voltage" ? "Voltage" : name,
                    ]}
                    labelFormatter={(hour) => formatHour(hour as number)}
                    contentStyle={{
                      backgroundColor: "white",
                      borderRadius: "8px",
                      boxShadow: "0 2px 8px rgba(0,0,0,0.15)",
                    }}
                  />
                  {/* Limit lines */}
                  <Line
                    type="monotone"
                    dataKey={() => 242}
                    stroke="#EF4444"
                    strokeDasharray="5 5"
                    dot={false}
                    name="Upper Limit"
                  />
                  <Line
                    type="monotone"
                    dataKey={() => 218}
                    stroke="#EF4444"
                    strokeDasharray="5 5"
                    dot={false}
                    name="Lower Limit"
                  />
                  <Line
                    type="monotone"
                    dataKey="predicted_voltage"
                    stroke="#74045F"
                    strokeWidth={2}
                    dot={(props) => {
                      const { cx, cy, payload } = props;
                      const color =
                        payload.status === "critical"
                          ? STATUS_COLORS.critical
                          : payload.status === "warning"
                            ? STATUS_COLORS.warning
                            : STATUS_COLORS.normal;
                      return <circle cx={cx} cy={cy} r={4} fill={color} />;
                    }}
                    name="Voltage"
                  />
                </LineChart>
              </ResponsiveContainer>

              {/* Prosumer Summary */}
              <div className="grid grid-cols-4 gap-2 mt-2">
                <div className="text-center p-2 bg-gray-50 rounded">
                  <p className="text-xs text-gray-500">Avg</p>
                  <p className="font-semibold">{getSelectedProsumerData()?.summary.avg_voltage}V</p>
                </div>
                <div className="text-center p-2 bg-gray-50 rounded">
                  <p className="text-xs text-gray-500">Min</p>
                  <p className="font-semibold">{getSelectedProsumerData()?.summary.min_voltage}V</p>
                </div>
                <div className="text-center p-2 bg-gray-50 rounded">
                  <p className="text-xs text-gray-500">Max</p>
                  <p className="font-semibold">{getSelectedProsumerData()?.summary.max_voltage}V</p>
                </div>
                <div className="text-center p-2 bg-gray-50 rounded">
                  <p className="text-xs text-gray-500">Violations</p>
                  <p
                    className={`font-semibold ${
                      (getSelectedProsumerData()?.summary.violation_hours || 0) > 0
                        ? "text-red-600"
                        : "text-green-600"
                    }`}
                  >
                    {getSelectedProsumerData()?.summary.violation_hours}h
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Model Info */}
          <div className="text-xs text-gray-500 flex items-center">
            <Clock className="w-3 h-3 mr-1" />
            Generated: {new Date(voltageForecast.generated_at).toLocaleString()} | Model:{" "}
            {voltageForecast.model_version}
          </div>
        </>
      )}

      {/* Footer */}
      <div className="mt-4 pt-3 border-t border-gray-100">
        <p className="text-xs text-gray-500">
          Forecast Date: {targetDate} | Nominal: 230V | Limits: 218V - 242V (±5%)
        </p>
      </div>
    </div>
  );
}
