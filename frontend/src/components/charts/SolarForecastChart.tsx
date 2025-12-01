"use client";

import { useState, useEffect } from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { Sun, TrendingUp, RefreshCw } from "lucide-react";

interface SolarDataPoint {
  time: string;
  power_kw: number;
  predicted_kw: number;
  irradiance: number;
}

// Generate mock solar data for visualization
function generateMockSolarData(): SolarDataPoint[] {
  const data: SolarDataPoint[] = [];
  const now = new Date();
  now.setHours(6, 0, 0, 0); // Start at 6 AM

  for (let i = 0; i < 48; i++) {
    // 4 hours of data at 5-min intervals
    const time = new Date(now.getTime() + i * 5 * 60 * 1000);
    const hour = time.getHours() + time.getMinutes() / 60;

    // Solar curve (bell curve centered at noon)
    let basePower = 0;
    if (hour >= 6 && hour <= 18) {
      const hourFactor = Math.exp(-0.5 * Math.pow((hour - 12) / 2.5, 2));
      basePower = 4500 * hourFactor * (0.9 + Math.random() * 0.2);
    }

    // Irradiance follows similar pattern
    const irradiance = hour >= 6 && hour <= 18
      ? 1000 * Math.exp(-0.5 * Math.pow((hour - 12) / 2.5, 2)) * (0.85 + Math.random() * 0.3)
      : 0;

    // Prediction with slight offset
    const predicted = basePower * (0.95 + Math.random() * 0.1);

    data.push({
      time: time.toLocaleTimeString("th-TH", { hour: "2-digit", minute: "2-digit" }),
      power_kw: Math.round(basePower),
      predicted_kw: Math.round(predicted),
      irradiance: Math.round(irradiance),
    });
  }

  return data;
}

interface SolarForecastChartProps {
  height?: number;
}

export default function SolarForecastChart({ height = 300 }: SolarForecastChartProps) {
  const [data, setData] = useState<SolarDataPoint[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [currentPower, setCurrentPower] = useState(0);
  const [peakPower, setPeakPower] = useState(0);

  const loadData = () => {
    setIsLoading(true);
    // Simulate API call delay
    setTimeout(() => {
      const mockData = generateMockSolarData();
      setData(mockData);

      // Calculate current and peak
      const now = new Date();
      const currentHour = now.getHours();
      const currentIndex = Math.min(Math.floor((currentHour - 6) * 12), mockData.length - 1);
      setCurrentPower(currentIndex >= 0 ? mockData[Math.max(0, currentIndex)].power_kw : 0);
      setPeakPower(Math.max(...mockData.map(d => d.power_kw)));

      setIsLoading(false);
    }, 500);
  };

  useEffect(() => {
    loadData();
    // Refresh every 5 minutes
    const interval = setInterval(loadData, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="bg-white rounded-lg shadow-md p-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center">
          <Sun className="w-5 h-5 text-amber-500 mr-2" />
          <h3 className="text-lg font-semibold text-gray-800">Solar Power Forecast</h3>
        </div>
        <button
          onClick={loadData}
          className="p-2 hover:bg-gray-100 rounded-full transition-colors"
          title="Refresh data"
        >
          <RefreshCw className={`w-4 h-4 text-gray-500 ${isLoading ? "animate-spin" : ""}`} />
        </button>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-3 gap-4 mb-4">
        <div className="bg-amber-50 rounded-lg p-3">
          <p className="text-xs text-amber-600 font-medium">Current Output</p>
          <p className="text-xl font-bold text-amber-700">{currentPower.toLocaleString()} kW</p>
        </div>
        <div className="bg-blue-50 rounded-lg p-3">
          <p className="text-xs text-blue-600 font-medium">Peak Today</p>
          <p className="text-xl font-bold text-blue-700">{peakPower.toLocaleString()} kW</p>
        </div>
        <div className="bg-green-50 rounded-lg p-3">
          <p className="text-xs text-green-600 font-medium">Accuracy</p>
          <div className="flex items-center">
            <TrendingUp className="w-4 h-4 text-green-600 mr-1" />
            <p className="text-xl font-bold text-green-700">94.2%</p>
          </div>
        </div>
      </div>

      {/* Chart */}
      {isLoading ? (
        <div className="h-[300px] flex items-center justify-center">
          <div className="animate-pulse text-gray-400">Loading chart data...</div>
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={height}>
          <AreaChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="colorPower" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.8} />
                <stop offset="95%" stopColor="#f59e0b" stopOpacity={0.1} />
              </linearGradient>
              <linearGradient id="colorPredicted" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.6} />
                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.1} />
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
              contentStyle={{ backgroundColor: "white", borderRadius: "8px", boxShadow: "0 2px 8px rgba(0,0,0,0.15)" }}
              formatter={(value: number, name: string) => [
                `${value.toLocaleString()} kW`,
                name === "power_kw" ? "Actual" : "Predicted"
              ]}
            />
            <Legend />
            <Area
              type="monotone"
              dataKey="predicted_kw"
              name="Predicted"
              stroke="#3b82f6"
              strokeWidth={2}
              strokeDasharray="5 5"
              fillOpacity={1}
              fill="url(#colorPredicted)"
            />
            <Area
              type="monotone"
              dataKey="power_kw"
              name="Actual"
              stroke="#f59e0b"
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
          Target: MAPE &lt; 10% | Data updates every 5 minutes
        </p>
      </div>
    </div>
  );
}
