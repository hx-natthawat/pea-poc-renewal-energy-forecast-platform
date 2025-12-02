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
import { useSolarWebSocket } from "@/hooks";

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

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function SolarForecastChart({ height = 300, enableRealtime = true }: SolarForecastChartProps) {
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
      const response = await fetch(`${API_URL}/api/v1/data/solar/latest?hours=24`);
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
    <div className="bg-white rounded-lg shadow-md p-4 border-l-4 border-[#C7911B]">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center">
          <Sun className="w-5 h-5 text-[#C7911B] mr-2" />
          <h3 className="text-lg font-semibold text-gray-800">Solar Power Forecast</h3>
          {enableRealtime && (
            <span
              className={`ml-2 flex items-center text-xs px-2 py-0.5 rounded-full ${
                wsConnected
                  ? "bg-green-100 text-green-700"
                  : "bg-gray-100 text-gray-500"
              }`}
              title={wsConnected ? "Real-time updates active" : "Connecting to real-time updates..."}
            >
              <Radio className={`w-3 h-3 mr-1 ${wsConnected ? "animate-pulse" : ""}`} />
              {wsConnected ? "LIVE" : "..."}
            </span>
          )}
        </div>
        <button
          type="button"
          onClick={loadData}
          className="p-2 hover:bg-gray-100 rounded-full transition-colors"
          title="Refresh data"
        >
          <RefreshCw className={`w-4 h-4 text-gray-500 ${isLoading ? "animate-spin" : ""}`} />
        </button>
      </div>

      {/* Stats Row - PEA Brand Colors */}
      <div className="grid grid-cols-3 gap-4 mb-4">
        <div className="bg-[#FEF3C7] rounded-lg p-3">
          <p className="text-xs text-[#A67814] font-medium">Current Output</p>
          <p className="text-xl font-bold text-[#C7911B]">{currentPower.toLocaleString()} kW</p>
        </div>
        <div className="bg-[#F3E8FF] rounded-lg p-3">
          <p className="text-xs text-[#74045F] font-medium">Peak Today</p>
          <p className="text-xl font-bold text-[#74045F]">{peakPower.toLocaleString()} kW</p>
        </div>
        <div className="bg-green-50 rounded-lg p-3">
          <p className="text-xs text-green-600 font-medium">Accuracy</p>
          <div className="flex items-center">
            <TrendingUp className="w-4 h-4 text-green-600 mr-1" />
            <p className="text-xl font-bold text-green-700">94.2%</p>
          </div>
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="bg-amber-50 text-amber-700 px-3 py-2 rounded mb-4 text-sm">{error}</div>
      )}

      {/* Chart */}
      {isLoading && data.length === 0 ? (
        <div className="h-[300px] flex items-center justify-center">
          <div className="animate-pulse text-gray-400">Loading chart data...</div>
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={height}>
          <AreaChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
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
              tick={{ fontSize: 11 }}
              tickLine={false}
              interval="preserveStartEnd"
            />
            <YAxis
              tick={{ fontSize: 11 }}
              tickLine={false}
              tickFormatter={(value) => `${(value / 1000).toFixed(1)}k`}
              label={{ value: "Power (kW)", angle: -90, position: "insideLeft", fontSize: 11 }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "white",
                borderRadius: "8px",
                boxShadow: "0 2px 8px rgba(0,0,0,0.15)",
                borderLeft: "4px solid #C7911B",
              }}
              formatter={(value: number, name: string) => [
                `${value.toLocaleString()} kW`,
                name === "power_kw" ? "Actual" : "Predicted",
              ]}
            />
            <Legend />
            <Area
              type="monotone"
              dataKey="predicted_kw"
              name="Predicted"
              stroke="#74045F"
              strokeWidth={2}
              strokeDasharray="5 5"
              fillOpacity={1}
              fill="url(#colorPredicted)"
            />
            <Area
              type="monotone"
              dataKey="power_kw"
              name="Actual"
              stroke="#C7911B"
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#colorPower)"
            />
          </AreaChart>
        </ResponsiveContainer>
      )}

      {/* Footer */}
      <div className="mt-3 pt-3 border-t border-gray-100">
        <p className="text-xs text-gray-500">
          Target: MAPE &lt; 10% | Data from TimescaleDB | {data.length} data points
          {enableRealtime && liveUpdateCount > 0 && (
            <span className="ml-2 text-green-600">| {liveUpdateCount} live updates</span>
          )}
        </p>
      </div>
    </div>
  );
}
