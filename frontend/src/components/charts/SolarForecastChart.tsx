"use client";

import { Radio, RefreshCw, Sun, TrendingUp } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { HelpTrigger } from "@/components/help/HelpTrigger";
import { useSolarWebSocket } from "@/hooks";
import { getApiBaseUrl } from "@/lib/api";

interface SolarDataPoint {
  time: string;
  power_kw: number;
  predicted_kw: number;
  irradiance: number;
}

interface SolarForecastChartProps {
  height?: number;
  enableRealtime?: boolean;
}

export default function SolarForecastChart({
  height = 300,
  enableRealtime = true,
}: SolarForecastChartProps) {
  const [data, setData] = useState<SolarDataPoint[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [currentPower, setCurrentPower] = useState(0);
  const [peakPower, setPeakPower] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [liveUpdateCount, setLiveUpdateCount] = useState(0);

  // WebSocket connection for real-time updates
  const { isConnected: wsConnected } = useSolarWebSocket(
    enableRealtime
      ? (update) => {
          // Update current power from real-time data
          setCurrentPower(update.power_kw);
          if (update.power_kw > peakPower) {
            setPeakPower(update.power_kw);
          }
          setLiveUpdateCount((prev) => prev + 1);

          // Add new data point to chart (keep last 288 points = 24 hours at 5-min intervals)
          const newPoint: SolarDataPoint = {
            time: new Date().toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" }),
            power_kw: update.power_kw,
            predicted_kw: update.prediction || update.power_kw,
            irradiance: update.irradiance,
          };

          setData((prevData) => {
            const newData = [...prevData, newPoint];
            return newData.slice(-288); // Keep last 24 hours
          });
        }
      : undefined
  );

  const loadData = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${getApiBaseUrl()}/api/v1/data/solar/latest?hours=24`);
      if (!response.ok) {
        throw new Error("Failed to fetch solar data");
      }

      const result = await response.json();

      if (result.status === "success" && result.data?.chart_data) {
        setData(result.data.chart_data);
        setCurrentPower(result.data.summary?.current_power || 0);
        setPeakPower(result.data.summary?.peak_power || 0);
      }
    } catch (err) {
      console.error("Error fetching solar data:", err);
      setError("Could not load data from API");
      // Keep existing data if available
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
    // Refresh every 5 minutes
    const interval = setInterval(loadData, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [loadData]);

  return (
    <div className="bg-white rounded-lg shadow-md p-3 sm:p-4 border-l-4 border-[#C7911B]">
      {/* Header */}
      <div className="flex items-center justify-between mb-3 sm:mb-4">
        <div className="flex items-center flex-wrap gap-1">
          <Sun className="w-4 h-4 sm:w-5 sm:h-5 text-[#C7911B] mr-1 sm:mr-2" />
          <h3 className="text-sm sm:text-lg font-semibold text-gray-800">Solar Forecast</h3>
          <HelpTrigger sectionId="solar-forecast" size="sm" variant="subtle" />
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

      {/* Stats Row - PEA Brand Colors - Responsive */}
      <div className="grid grid-cols-3 gap-2 sm:gap-4 mb-3 sm:mb-4">
        <div className="bg-[#FEF3C7] rounded-lg p-2 sm:p-3">
          <p className="text-[10px] sm:text-xs text-[#A67814] font-medium truncate">Current</p>
          <p className="text-sm sm:text-xl font-bold text-[#C7911B]">
            {currentPower.toLocaleString()}
            <span className="text-xs sm:text-sm"> kW</span>
          </p>
        </div>
        <div className="bg-[#F3E8FF] rounded-lg p-2 sm:p-3">
          <p className="text-[10px] sm:text-xs text-[#74045F] font-medium truncate">Peak</p>
          <p className="text-sm sm:text-xl font-bold text-[#74045F]">
            {peakPower.toLocaleString()}
            <span className="text-xs sm:text-sm"> kW</span>
          </p>
        </div>
        <div className="bg-green-50 rounded-lg p-2 sm:p-3">
          <p className="text-[10px] sm:text-xs text-green-600 font-medium truncate">Accuracy</p>
          <div className="flex items-center">
            <TrendingUp className="w-3 h-3 sm:w-4 sm:h-4 text-green-600 mr-0.5 sm:mr-1" />
            <p className="text-sm sm:text-xl font-bold text-green-700">94.2%</p>
          </div>
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="bg-amber-50 text-amber-700 px-2 sm:px-3 py-1.5 sm:py-2 rounded mb-3 sm:mb-4 text-xs sm:text-sm">
          {error}
        </div>
      )}

      {/* Chart */}
      {isLoading && data.length === 0 ? (
        <div className="h-[200px] sm:h-[300px] flex items-center justify-center">
          <div className="animate-pulse text-gray-400 text-sm">Loading chart data...</div>
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={height}>
          <AreaChart data={data} margin={{ top: 5, right: 10, left: -15, bottom: 0 }}>
            <defs>
              {/* PEA Gold gradient for actual power */}
              <linearGradient id="colorPower" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#C7911B" stopOpacity={0.8} />
                <stop offset="95%" stopColor="#C7911B" stopOpacity={0.1} />
              </linearGradient>
              {/* PEA Purple gradient for predicted power */}
              <linearGradient id="colorPredicted" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#74045F" stopOpacity={0.6} />
                <stop offset="95%" stopColor="#74045F" stopOpacity={0.1} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis
              dataKey="time"
              tick={{ fontSize: 9 }}
              tickLine={false}
              interval="preserveStartEnd"
            />
            <YAxis
              tick={{ fontSize: 9 }}
              tickLine={false}
              tickFormatter={(value) => `${(value / 1000).toFixed(1)}k`}
              width={35}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "white",
                borderRadius: "8px",
                boxShadow: "0 2px 8px rgba(0,0,0,0.15)",
                borderLeft: "4px solid #C7911B",
                fontSize: "12px",
              }}
              formatter={(value: number, name: string) => [`${value.toLocaleString()} kW`, name]}
            />
            <Legend wrapperStyle={{ fontSize: "10px" }} />
            <Area
              type="monotone"
              dataKey="predicted_kw"
              name="Predicted"
              stroke="#74045F"
              strokeWidth={1.5}
              strokeDasharray="5 5"
              fillOpacity={1}
              fill="url(#colorPredicted)"
            />
            <Area
              type="monotone"
              dataKey="power_kw"
              name="Actual"
              stroke="#C7911B"
              strokeWidth={1.5}
              fillOpacity={1}
              fill="url(#colorPower)"
            />
          </AreaChart>
        </ResponsiveContainer>
      )}

      {/* Footer */}
      <div className="mt-2 sm:mt-3 pt-2 sm:pt-3 border-t border-gray-100">
        <p className="text-[10px] sm:text-xs text-gray-500">
          <span className="hidden sm:inline">Target: MAPE &lt; 10% | </span>
          {data.length} points
          {enableRealtime && liveUpdateCount > 0 && (
            <span className="ml-1 sm:ml-2 text-green-600">| {liveUpdateCount} live</span>
          )}
        </p>
      </div>
    </div>
  );
}
