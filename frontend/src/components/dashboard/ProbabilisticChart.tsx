"use client";

import { AlertTriangle, RefreshCw, TrendingUp } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

interface ForecastDataPoint {
  time: string;
  p10: number;
  p50: number;
  p90: number;
  actual?: number;
  weather_condition: string;
  is_high_uncertainty: boolean;
}

interface ProbabilisticChartProps {
  height?: number;
  showBands?: boolean;
}

const weatherColors: Record<string, string> = {
  clear: "#22C55E",
  partly_cloudy: "#F59E0B",
  cloudy: "#6B7280",
  rainy: "#3B82F6",
  storm: "#EF4444",
};

export default function ProbabilisticChart({
  height = 250,
  showBands = true,
}: ProbabilisticChartProps) {
  const [data, setData] = useState<ForecastDataPoint[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      // In production, this would fetch from /api/v1/forecast/solar/probabilistic
      // For now, generate sample probabilistic data
      const now = new Date();
      const sampleData: ForecastDataPoint[] = [];

      for (let i = 0; i < 24; i++) {
        const hour = new Date(now);
        hour.setHours(now.getHours() + i);

        // Simulate solar curve with uncertainty bands
        const hourOfDay = hour.getHours();
        const solarFactor =
          hourOfDay >= 6 && hourOfDay <= 18 ? Math.sin(((hourOfDay - 6) * Math.PI) / 12) : 0;

        const basePower = solarFactor * 4000;
        const uncertainty = solarFactor > 0.3 ? basePower * 0.15 : basePower * 0.3;

        sampleData.push({
          time: hour.toLocaleTimeString("en-US", {
            hour: "2-digit",
            minute: "2-digit",
          }),
          p10: Math.max(0, basePower - uncertainty * 1.5),
          p50: basePower,
          p90: basePower + uncertainty * 1.5,
          weather_condition: solarFactor > 0.5 ? "clear" : "partly_cloudy",
          is_high_uncertainty: uncertainty > basePower * 0.2,
        });
      }

      setData(sampleData);
    } catch (err) {
      console.error("Error loading probabilistic forecast:", err);
      setError("Could not load forecast data");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 300000); // 5 minutes
    return () => clearInterval(interval);
  }, [loadData]);

  if (isLoading && data.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-md p-3 sm:p-4 border-l-4 border-amber-500">
        <div className="animate-pulse flex items-center justify-center h-48 sm:h-64">
          <p className="text-gray-400 text-sm">Loading probabilistic forecast...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-3 sm:p-4 border-l-4 border-amber-500">
      {/* Header */}
      <div className="flex items-center justify-between mb-3 sm:mb-4">
        <div className="flex items-center min-w-0">
          <TrendingUp className="w-4 h-4 sm:w-5 sm:h-5 mr-1 sm:mr-2 text-amber-500 flex-shrink-0" />
          <h3 className="text-sm sm:text-lg font-semibold text-gray-800 truncate">
            <span className="hidden sm:inline">Probabilistic Forecast (P10/P50/P90)</span>
            <span className="sm:hidden">Forecast P10/P50/P90</span>
          </h3>
        </div>
        <button
          type="button"
          onClick={loadData}
          className="p-1.5 sm:p-2 hover:bg-gray-100 rounded-full transition-colors touch-manipulation"
          title="Refresh"
        >
          <RefreshCw className={`w-4 h-4 text-gray-500 ${isLoading ? "animate-spin" : ""}`} />
        </button>
      </div>

      {/* Legend for weather conditions */}
      <div className="flex flex-wrap gap-1.5 sm:gap-2 mb-2 sm:mb-3 text-[10px] sm:text-xs">
        {Object.entries(weatherColors).map(([condition, color]) => (
          <div key={condition} className="flex items-center gap-0.5 sm:gap-1">
            <div
              className="w-2 h-2 sm:w-3 sm:h-3 rounded-full"
              style={{ backgroundColor: color }}
            />
            <span className="text-gray-600 capitalize">{condition.replace("_", " ")}</span>
          </div>
        ))}
      </div>

      {error && (
        <div className="bg-amber-50 text-amber-700 px-2 sm:px-3 py-1.5 sm:py-2 rounded mb-3 sm:mb-4 text-xs sm:text-sm flex items-center">
          <AlertTriangle className="w-3.5 h-3.5 sm:w-4 sm:h-4 mr-1.5 sm:mr-2 flex-shrink-0" />
          {error}
        </div>
      )}

      {/* Chart */}
      {data.length > 0 ? (
        <ResponsiveContainer width="100%" height={height}>
          <AreaChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="colorP90Band" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#F59E0B" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#F59E0B" stopOpacity={0.05} />
              </linearGradient>
              <linearGradient id="colorP50Main" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#C7911B" stopOpacity={0.8} />
                <stop offset="95%" stopColor="#C7911B" stopOpacity={0.2} />
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
            />

            <Tooltip
              contentStyle={{
                backgroundColor: "white",
                borderRadius: "8px",
                boxShadow: "0 2px 8px rgba(0,0,0,0.15)",
                borderLeft: "4px solid #F59E0B",
                fontSize: "12px",
              }}
              formatter={(value: number, name: string) => [
                `${value.toFixed(1)} kW`,
                name === "p10"
                  ? "P10 (Pessimistic)"
                  : name === "p50"
                    ? "P50 (Forecast)"
                    : name === "p90"
                      ? "P90 (Optimistic)"
                      : name,
              ]}
            />

            <Legend wrapperStyle={{ fontSize: "10px" }} />

            {showBands && (
              <>
                {/* P90 band (optimistic) */}
                <Area
                  type="monotone"
                  dataKey="p90"
                  name="P90"
                  stroke="#F59E0B"
                  strokeWidth={1}
                  strokeDasharray="3 3"
                  fillOpacity={1}
                  fill="url(#colorP90Band)"
                />

                {/* P10 band (pessimistic) */}
                <Area
                  type="monotone"
                  dataKey="p10"
                  name="P10"
                  stroke="#9CA3AF"
                  strokeWidth={1}
                  strokeDasharray="3 3"
                  fillOpacity={0}
                />
              </>
            )}

            {/* P50 (main forecast) */}
            <Area
              type="monotone"
              dataKey="p50"
              name="P50"
              stroke="#C7911B"
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#colorP50Main)"
            />

            {/* Actual values if available */}
            <Line
              type="monotone"
              dataKey="actual"
              name="Actual"
              stroke="#22C55E"
              strokeWidth={2}
              dot={false}
            />
          </AreaChart>
        </ResponsiveContainer>
      ) : (
        <div className="flex items-center justify-center text-gray-400" style={{ height }}>
          No forecast data available
        </div>
      )}

      {/* Footer */}
      <div className="mt-2 sm:mt-3 pt-2 sm:pt-3 border-t border-gray-100">
        <p className="text-[10px] sm:text-xs text-gray-500">
          <span className="hidden sm:inline">
            P10: 10% chance actual below | P50: Most likely | P90: 10% chance actual above
          </span>
          <span className="sm:hidden">P10/P50/P90 confidence bands</span>
        </p>
      </div>
    </div>
  );
}
