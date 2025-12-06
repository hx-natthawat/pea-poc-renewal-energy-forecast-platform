"use client";

import { Activity, RefreshCw, TrendingDown, TrendingUp } from "lucide-react";
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
import { getApiBaseUrl } from "@/lib/api";

interface DemandDataPoint {
  time: string;
  net_demand_mw: number;
  gross_demand_mw: number;
  re_generation_mw: number;
}

interface DemandForecastChartProps {
  height?: number;
  tradingPoint?: string;
}

export default function DemandForecastChart({
  height = 300,
  tradingPoint = "PEA_SYSTEM",
}: DemandForecastChartProps) {
  const [data, setData] = useState<DemandDataPoint[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [currentDemand, setCurrentDemand] = useState(0);
  const [peakDemand, setPeakDemand] = useState(0);
  const [minDemand, setMinDemand] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `${getApiBaseUrl()}/api/v1/demand-forecast/predict?trading_point=${tradingPoint}&horizon_hours=24`
      );

      if (!response.ok) {
        throw new Error("Failed to fetch demand forecast");
      }

      const result = await response.json();

      if (result.status === "success" && result.data?.predictions) {
        const chartData = result.data.predictions.map(
          (p: {
            timestamp: string;
            net_demand_mw: number;
            gross_demand_mw: number;
            re_generation_mw: number;
          }) => ({
            time: new Date(p.timestamp).toLocaleTimeString("en-US", {
              hour: "2-digit",
              minute: "2-digit",
            }),
            net_demand_mw: Math.round(p.net_demand_mw),
            gross_demand_mw: Math.round(p.gross_demand_mw),
            re_generation_mw: Math.round(p.re_generation_mw),
          })
        );
        setData(chartData);

        const netDemands = chartData.map((d: DemandDataPoint) => d.net_demand_mw);
        setCurrentDemand(netDemands[netDemands.length - 1] || 0);
        setPeakDemand(Math.max(...netDemands));
        setMinDemand(Math.min(...netDemands));
      }
    } catch (err) {
      console.error("Error fetching demand forecast:", err);
      setError("Could not load forecast data");

      // Generate simulation data for demo
      const simData = Array.from({ length: 24 }, (_, i) => {
        const hour = i;
        const grossDemand = 15000 + Math.sin((hour - 6) * (Math.PI / 12)) * 5000;
        const reGen =
          2000 + (hour >= 6 && hour <= 18 ? Math.sin((hour - 6) * (Math.PI / 12)) * 3000 : 0);
        return {
          time: `${hour.toString().padStart(2, "0")}:00`,
          gross_demand_mw: Math.round(grossDemand + Math.random() * 500),
          re_generation_mw: Math.round(reGen + Math.random() * 200),
          net_demand_mw: Math.round(grossDemand - reGen + Math.random() * 300),
        };
      });
      setData(simData);
      const netDemands = simData.map((d) => d.net_demand_mw);
      setCurrentDemand(netDemands[netDemands.length - 1]);
      setPeakDemand(Math.max(...netDemands));
      setMinDemand(Math.min(...netDemands));
    } finally {
      setIsLoading(false);
    }
  }, [tradingPoint]);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [loadData]);

  return (
    <div className="bg-white rounded-lg shadow-md p-3 sm:p-4 border-l-4 border-emerald-500">
      {/* Header */}
      <div className="flex items-center justify-between mb-3 sm:mb-4">
        <div className="flex items-center flex-wrap gap-1">
          <Activity className="w-4 h-4 sm:w-5 sm:h-5 text-emerald-500 mr-1 sm:mr-2" />
          <h3 className="text-sm sm:text-lg font-semibold text-gray-800">Actual Demand Forecast</h3>
          <span className="text-[10px] sm:text-xs px-1.5 sm:px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-700">
            TOR 7.5.1.2
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

      {/* Stats Row */}
      <div className="grid grid-cols-3 gap-2 sm:gap-4 mb-3 sm:mb-4">
        <div className="bg-emerald-50 rounded-lg p-2 sm:p-3">
          <p className="text-[10px] sm:text-xs text-emerald-600 font-medium truncate">Net Demand</p>
          <p className="text-sm sm:text-xl font-bold text-emerald-700">
            {currentDemand.toLocaleString()}
            <span className="text-xs sm:text-sm"> MW</span>
          </p>
        </div>
        <div className="bg-red-50 rounded-lg p-2 sm:p-3">
          <p className="text-[10px] sm:text-xs text-red-600 font-medium truncate">Peak</p>
          <div className="flex items-center">
            <TrendingUp className="w-3 h-3 sm:w-4 sm:h-4 text-red-500 mr-0.5" />
            <p className="text-sm sm:text-xl font-bold text-red-600">
              {peakDemand.toLocaleString()}
              <span className="text-xs sm:text-sm"> MW</span>
            </p>
          </div>
        </div>
        <div className="bg-blue-50 rounded-lg p-2 sm:p-3">
          <p className="text-[10px] sm:text-xs text-blue-600 font-medium truncate">Min</p>
          <div className="flex items-center">
            <TrendingDown className="w-3 h-3 sm:w-4 sm:h-4 text-blue-500 mr-0.5" />
            <p className="text-sm sm:text-xl font-bold text-blue-600">
              {minDemand.toLocaleString()}
              <span className="text-xs sm:text-sm"> MW</span>
            </p>
          </div>
        </div>
      </div>

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
          <AreaChart data={data} margin={{ top: 5, right: 10, left: -15, bottom: 0 }}>
            <defs>
              <linearGradient id="colorNetDemand" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#10B981" stopOpacity={0.8} />
                <stop offset="95%" stopColor="#10B981" stopOpacity={0.1} />
              </linearGradient>
              <linearGradient id="colorGrossDemand" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#6366F1" stopOpacity={0.4} />
                <stop offset="95%" stopColor="#6366F1" stopOpacity={0.05} />
              </linearGradient>
              <linearGradient id="colorRE" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#F59E0B" stopOpacity={0.6} />
                <stop offset="95%" stopColor="#F59E0B" stopOpacity={0.1} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis dataKey="time" tick={{ fontSize: 9 }} tickLine={false} interval={3} />
            <YAxis
              tick={{ fontSize: 9 }}
              tickLine={false}
              tickFormatter={(value) => `${(value / 1000).toFixed(0)}k`}
              width={35}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "white",
                borderRadius: "8px",
                boxShadow: "0 2px 8px rgba(0,0,0,0.15)",
                borderLeft: "4px solid #10B981",
                fontSize: "12px",
              }}
              formatter={(value: number, name: string) => [`${value.toLocaleString()} MW`, name]}
            />
            <Legend wrapperStyle={{ fontSize: "10px" }} />
            <Area
              type="monotone"
              dataKey="gross_demand_mw"
              name="Gross Demand"
              stroke="#6366F1"
              strokeWidth={1}
              strokeDasharray="3 3"
              fillOpacity={1}
              fill="url(#colorGrossDemand)"
            />
            <Area
              type="monotone"
              dataKey="re_generation_mw"
              name="RE Generation"
              stroke="#F59E0B"
              strokeWidth={1.5}
              fillOpacity={1}
              fill="url(#colorRE)"
            />
            <Area
              type="monotone"
              dataKey="net_demand_mw"
              name="Net Demand"
              stroke="#10B981"
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#colorNetDemand)"
            />
          </AreaChart>
        </ResponsiveContainer>
      )}

      {/* Footer */}
      <div className="mt-2 sm:mt-3 pt-2 sm:pt-3 border-t border-gray-100">
        <p className="text-[10px] sm:text-xs text-gray-500">
          Net = Gross - RE | Trading Point: {tradingPoint} | {data.length} intervals
        </p>
      </div>
    </div>
  );
}
