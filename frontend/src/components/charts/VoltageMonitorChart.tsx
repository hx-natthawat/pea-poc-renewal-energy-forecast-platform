"use client";

import { AlertTriangle, Radio, RefreshCw, Zap } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { useVoltageWebSocket } from "@/hooks";

interface VoltageDataPoint {
  time: string;
  prosumer1?: number;
  prosumer2?: number;
  prosumer3?: number;
  prosumer4?: number;
  prosumer5?: number;
  prosumer6?: number;
  prosumer7?: number;
}

interface ProsumerStatus {
  id: string;
  name: string;
  phase: string;
  voltage: number;
  status: "normal" | "warning" | "critical";
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// PEA Brand-inspired color scheme for prosumer phases
const PROSUMER_COLORS: Record<string, string> = {
  prosumer1: "#74045F", // PEA Purple (Phase A, far - critical point)
  prosumer2: "#8B1A75", // PEA Purple Light (Phase A, mid)
  prosumer3: "#A67814", // PEA Gold Dark (Phase A, near)
  prosumer4: "#C7911B", // PEA Gold (Phase B, mid)
  prosumer5: "#D4A43D", // PEA Gold Light (Phase B, far)
  prosumer6: "#5A0349", // PEA Purple Dark (Phase B, near)
  prosumer7: "#6B7280", // Gray (Phase C)
};

const PROSUMER_CONFIG: Record<string, { phase: string; position: number }> = {
  prosumer1: { phase: "A", position: 3 },
  prosumer2: { phase: "A", position: 2 },
  prosumer3: { phase: "A", position: 1 },
  prosumer4: { phase: "B", position: 2 },
  prosumer5: { phase: "B", position: 3 },
  prosumer6: { phase: "B", position: 1 },
  prosumer7: { phase: "C", position: 1 },
};

interface VoltageMonitorChartProps {
  height?: number;
  enableRealtime?: boolean;
}

export default function VoltageMonitorChart({ height = 300, enableRealtime = true }: VoltageMonitorChartProps) {
  const [data, setData] = useState<VoltageDataPoint[]>([]);
  const [prosumerStatus, setProsumerStatus] = useState<ProsumerStatus[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [violations, setViolations] = useState(0);
  const [selectedProsumers, setSelectedProsumers] = useState<string[]>([
    "prosumer1",
    "prosumer3",
    "prosumer5",
    "prosumer7",
  ]);
  const [error, setError] = useState<string | null>(null);
  const [liveUpdateCount, setLiveUpdateCount] = useState(0);

  // WebSocket connection for real-time updates
  const { isConnected: wsConnected } = useVoltageWebSocket(
    enableRealtime
      ? (update) => {
          // Update prosumer status from real-time data
          setProsumerStatus((prev) =>
            prev.map((ps) =>
              ps.id === update.prosumer_id
                ? { ...ps, voltage: update.voltage, status: update.status as ProsumerStatus["status"] }
                : ps
            )
          );

          // Check for violations
          if (update.status === "warning" || update.status === "critical") {
            setViolations((prev) => prev + 1);
          }

          setLiveUpdateCount((prev) => prev + 1);

          // Add new data point
          const time = new Date().toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" });
          setData((prevData) => {
            const lastPoint = prevData[prevData.length - 1];
            const newPoint: VoltageDataPoint = {
              ...lastPoint,
              time,
              [update.prosumer_id]: update.voltage,
            };
            const newData = [...prevData, newPoint];
            return newData.slice(-120); // Keep last 2 hours at 1-min intervals
          });
        }
      : undefined
  );

  const loadData = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_URL}/api/v1/data/voltage/latest?hours=2`);
      if (!response.ok) {
        throw new Error("Failed to fetch voltage data");
      }

      const result = await response.json();

      if (result.status === "success" && result.data) {
        setData(result.data.chart_data || []);
        setProsumerStatus(result.data.prosumer_status || []);
        setViolations(result.data.summary?.violations || 0);
      }
    } catch (err) {
      console.error("Error fetching voltage data:", err);
      setError("Could not load data from API");
      // Keep existing data if available
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [loadData]);

  const toggleProsumer = (id: string) => {
    setSelectedProsumers((prev) =>
      prev.includes(id) ? prev.filter((p) => p !== id) : [...prev, id]
    );
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-4 border-l-4 border-[#74045F]">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center">
          <Zap className="w-5 h-5 text-[#74045F] mr-2" />
          <h3 className="text-lg font-semibold text-gray-800">Voltage Monitoring</h3>
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
        <div className="flex items-center gap-2">
          {violations > 0 && (
            <span className="flex items-center text-amber-600 text-sm bg-amber-50 px-2 py-1 rounded">
              <AlertTriangle className="w-4 h-4 mr-1" />
              {violations} warning{violations > 1 ? "s" : ""}
            </span>
          )}
          <button
            type="button"
            onClick={loadData}
            className="p-2 hover:bg-gray-100 rounded-full transition-colors"
            title="Refresh data"
          >
            <RefreshCw className={`w-4 h-4 text-gray-500 ${isLoading ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="bg-amber-50 text-amber-700 px-3 py-2 rounded mb-4 text-sm">{error}</div>
      )}

      {/* Prosumer Status Grid */}
      <div className="grid grid-cols-7 gap-2 mb-4">
        {prosumerStatus.map((ps) => (
          <button
            type="button"
            key={ps.id}
            onClick={() => toggleProsumer(ps.id)}
            className={`p-2 rounded text-xs text-center transition-all ${
              selectedProsumers.includes(ps.id) ? "ring-2 ring-offset-1" : "opacity-50"
            } ${
              ps.status === "critical"
                ? "bg-red-50 ring-red-400"
                : ps.status === "warning"
                  ? "bg-amber-50 ring-amber-400"
                  : "bg-green-50 ring-green-400"
            }`}
            style={{ borderLeft: `3px solid ${PROSUMER_COLORS[ps.id]}` }}
          >
            <div className="font-semibold">P{ps.id.slice(-1)}</div>
            <div className="text-gray-600">{ps.voltage}V</div>
            <div className="text-[10px] text-gray-400">Phase {ps.phase}</div>
          </button>
        ))}
      </div>

      {/* Chart */}
      {isLoading && data.length === 0 ? (
        <div className="h-[300px] flex items-center justify-center">
          <div className="animate-pulse text-gray-400">Loading voltage data...</div>
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={height}>
          <LineChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis
              dataKey="time"
              tick={{ fontSize: 11 }}
              tickLine={false}
              interval="preserveStartEnd"
            />
            <YAxis
              domain={[215, 245]}
              tick={{ fontSize: 11 }}
              tickLine={false}
              label={{ value: "Voltage (V)", angle: -90, position: "insideLeft", fontSize: 11 }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "white",
                borderRadius: "8px",
                boxShadow: "0 2px 8px rgba(0,0,0,0.15)",
                borderLeft: "4px solid #74045F",
              }}
              formatter={(value: number, name: string) => [
                `${value.toFixed(1)} V`,
                `Prosumer ${name.slice(-1)} (Phase ${PROSUMER_CONFIG[name]?.phase})`,
              ]}
            />

            {/* Voltage limit reference lines */}
            <ReferenceLine
              y={242}
              stroke="#EF4444"
              strokeDasharray="5 5"
              label={{ value: "+5%", position: "right", fontSize: 10, fill: "#EF4444" }}
            />
            <ReferenceLine
              y={230}
              stroke="#74045F"
              strokeDasharray="3 3"
              label={{ value: "230V", position: "right", fontSize: 10, fill: "#74045F" }}
            />
            <ReferenceLine
              y={218}
              stroke="#EF4444"
              strokeDasharray="5 5"
              label={{ value: "-5%", position: "right", fontSize: 10, fill: "#EF4444" }}
            />

            {/* Prosumer lines */}
            {selectedProsumers.map((prosumerId) => (
              <Line
                key={prosumerId}
                type="monotone"
                dataKey={prosumerId}
                name={prosumerId}
                stroke={PROSUMER_COLORS[prosumerId]}
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 4 }}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      )}

      {/* Footer */}
      <div className="mt-3 pt-3 border-t border-gray-100 flex justify-between items-center">
        <p className="text-xs text-gray-500">
          Target: MAE &lt; 2V | Limits: 218V - 242V (±5%) | {data.length} data points
          {enableRealtime && liveUpdateCount > 0 && (
            <span className="ml-2 text-green-600">| {liveUpdateCount} live updates</span>
          )}
        </p>
        <div className="flex gap-2">
          {["A", "B", "C"].map((phase) => (
            <span key={phase} className="text-xs text-gray-400">
              Phase {phase}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
