"use client";

import { useState, useEffect } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Legend,
} from "recharts";
import { Zap, AlertTriangle, RefreshCw } from "lucide-react";

interface VoltageDataPoint {
  time: string;
  prosumer1: number;
  prosumer2: number;
  prosumer3: number;
  prosumer4: number;
  prosumer5: number;
  prosumer6: number;
  prosumer7: number;
}

interface ProsumerStatus {
  id: string;
  name: string;
  phase: string;
  voltage: number;
  status: "normal" | "warning" | "critical";
}

// Generate mock voltage data
function generateMockVoltageData(): VoltageDataPoint[] {
  const data: VoltageDataPoint[] = [];
  const now = new Date();
  now.setMinutes(Math.floor(now.getMinutes() / 5) * 5, 0, 0);

  // Go back 2 hours
  const startTime = new Date(now.getTime() - 2 * 60 * 60 * 1000);

  for (let i = 0; i < 24; i++) {
    const time = new Date(startTime.getTime() + i * 5 * 60 * 1000);
    const hour = time.getHours() + time.getMinutes() / 60;

    // Base voltage with time-of-day variation
    const loadFactor = hour >= 18 && hour <= 21 ? 1.3 : hour >= 7 && hour <= 9 ? 1.15 : 1.0;

    // PV generation effect (raises voltage during day)
    const pvFactor = hour >= 9 && hour <= 15
      ? 0.5 * Math.sin(Math.PI * (hour - 9) / 6)
      : 0;

    data.push({
      time: time.toLocaleTimeString("th-TH", { hour: "2-digit", minute: "2-digit" }),
      prosumer1: 230 - 4.5 * loadFactor + pvFactor * 1.5 + (Math.random() - 0.5) * 2,
      prosumer2: 230 - 3.0 * loadFactor + pvFactor * 2.0 + (Math.random() - 0.5) * 2,
      prosumer3: 230 - 1.5 * loadFactor + pvFactor * 2.5 + (Math.random() - 0.5) * 2,
      prosumer4: 230 - 3.0 * loadFactor + pvFactor * 2.0 + (Math.random() - 0.5) * 2,
      prosumer5: 230 - 4.5 * loadFactor + pvFactor * 1.5 + (Math.random() - 0.5) * 2,
      prosumer6: 230 - 1.5 * loadFactor + pvFactor * 2.5 + (Math.random() - 0.5) * 2,
      prosumer7: 230 - 1.5 * loadFactor + pvFactor * 2.5 + (Math.random() - 0.5) * 2,
    });
  }

  return data;
}

const PROSUMER_COLORS: Record<string, string> = {
  prosumer1: "#ef4444", // red (Phase A, far)
  prosumer2: "#f97316", // orange (Phase A, mid)
  prosumer3: "#eab308", // yellow (Phase A, near)
  prosumer4: "#22c55e", // green (Phase B, mid)
  prosumer5: "#06b6d4", // cyan (Phase B, far)
  prosumer6: "#3b82f6", // blue (Phase B, near)
  prosumer7: "#8b5cf6", // purple (Phase C)
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
}

export default function VoltageMonitorChart({ height = 300 }: VoltageMonitorChartProps) {
  const [data, setData] = useState<VoltageDataPoint[]>([]);
  const [prosumerStatus, setProsumerStatus] = useState<ProsumerStatus[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [violations, setViolations] = useState(0);
  const [selectedProsumers, setSelectedProsumers] = useState<string[]>([
    "prosumer1", "prosumer3", "prosumer5", "prosumer7"
  ]);

  const loadData = () => {
    setIsLoading(true);
    setTimeout(() => {
      const mockData = generateMockVoltageData();
      setData(mockData);

      // Calculate current status for each prosumer
      const latestData = mockData[mockData.length - 1];
      const statuses: ProsumerStatus[] = Object.keys(PROSUMER_CONFIG).map(id => {
        const voltage = latestData[id as keyof VoltageDataPoint] as number;
        let status: "normal" | "warning" | "critical" = "normal";
        if (voltage < 220 || voltage > 240) status = "critical";
        else if (voltage < 222 || voltage > 238) status = "warning";

        return {
          id,
          name: `Prosumer ${id.slice(-1)}`,
          phase: PROSUMER_CONFIG[id].phase,
          voltage: Math.round(voltage * 10) / 10,
          status,
        };
      });

      setProsumerStatus(statuses);
      setViolations(statuses.filter(s => s.status !== "normal").length);
      setIsLoading(false);
    }, 500);
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  const toggleProsumer = (id: string) => {
    setSelectedProsumers(prev =>
      prev.includes(id)
        ? prev.filter(p => p !== id)
        : [...prev, id]
    );
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center">
          <Zap className="w-5 h-5 text-blue-500 mr-2" />
          <h3 className="text-lg font-semibold text-gray-800">Voltage Monitoring</h3>
        </div>
        <div className="flex items-center gap-2">
          {violations > 0 && (
            <span className="flex items-center text-amber-600 text-sm bg-amber-50 px-2 py-1 rounded">
              <AlertTriangle className="w-4 h-4 mr-1" />
              {violations} warning{violations > 1 ? "s" : ""}
            </span>
          )}
          <button
            onClick={loadData}
            className="p-2 hover:bg-gray-100 rounded-full transition-colors"
            title="Refresh data"
          >
            <RefreshCw className={`w-4 h-4 text-gray-500 ${isLoading ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>

      {/* Prosumer Status Grid */}
      <div className="grid grid-cols-7 gap-2 mb-4">
        {prosumerStatus.map(ps => (
          <button
            key={ps.id}
            onClick={() => toggleProsumer(ps.id)}
            className={`p-2 rounded text-xs text-center transition-all ${
              selectedProsumers.includes(ps.id)
                ? "ring-2 ring-offset-1"
                : "opacity-50"
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
      {isLoading ? (
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
              contentStyle={{ backgroundColor: "white", borderRadius: "8px", boxShadow: "0 2px 8px rgba(0,0,0,0.15)" }}
              formatter={(value: number, name: string) => [
                `${value.toFixed(1)} V`,
                `Prosumer ${name.slice(-1)} (Phase ${PROSUMER_CONFIG[name]?.phase})`
              ]}
            />

            {/* Voltage limit reference lines */}
            <ReferenceLine y={242} stroke="#ef4444" strokeDasharray="5 5" label={{ value: "+5%", position: "right", fontSize: 10 }} />
            <ReferenceLine y={230} stroke="#6b7280" strokeDasharray="3 3" label={{ value: "Nominal", position: "right", fontSize: 10 }} />
            <ReferenceLine y={218} stroke="#ef4444" strokeDasharray="5 5" label={{ value: "-5%", position: "right", fontSize: 10 }} />

            {/* Prosumer lines */}
            {selectedProsumers.map(prosumerId => (
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
          Target: MAE &lt; 2V | Limits: 218V - 242V (±5%)
        </p>
        <div className="flex gap-2">
          {["A", "B", "C"].map(phase => (
            <span key={phase} className="text-xs text-gray-400">
              Phase {phase}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
