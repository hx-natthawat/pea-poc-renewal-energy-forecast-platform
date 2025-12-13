"use client";

import {
  AlertTriangle,
  Battery,
  CheckCircle,
  RefreshCw,
  Thermometer,
  XCircle,
  Zap,
} from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { HelpTrigger } from "@/components/help/HelpTrigger";
import { getApiBaseUrl } from "@/lib/api";

interface DOELimit {
  prosumer_id: string;
  export_limit_kw: number;
  import_limit_kw: number;
  limiting_factor: "voltage" | "thermal" | "none";
  status: "normal" | "constrained" | "critical";
  predicted_voltage_v: number;
  voltage_headroom_v: number;
  thermal_headroom_pct: number;
  confidence: number;
}

interface DOESummary {
  total_export_capacity_kw: number;
  avg_export_limit_kw: number;
  min_export_limit_kw: number;
  max_export_limit_kw: number;
  constrained_count: number;
  voltage_limited_count: number;
  thermal_limited_count: number;
}

interface DOEDashboardProps {
  height?: number;
}

export default function DOEDashboard({ height = 300 }: DOEDashboardProps) {
  const [limits, setLimits] = useState<DOELimit[]>([]);
  const [summary, setSummary] = useState<DOESummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${getApiBaseUrl()}/api/v1/doe/limits`);

      if (response.ok) {
        const result = await response.json();
        if (result.status === "success") {
          setLimits(result.data || []);
          setSummary(result.summary || null);
        }
      } else {
        throw new Error("API not available");
      }
    } catch (err) {
      console.error("Error fetching DOE data:", err);
      setError("Could not load DOE data");

      // Generate simulation data for demo
      const simLimits: DOELimit[] = [
        {
          prosumer_id: "prosumer1",
          export_limit_kw: 4.2,
          import_limit_kw: 12.0,
          limiting_factor: "voltage",
          status: "constrained",
          predicted_voltage_v: 237.5,
          voltage_headroom_v: 2.5,
          thermal_headroom_pct: 35,
          confidence: 0.95,
        },
        {
          prosumer_id: "prosumer2",
          export_limit_kw: 6.8,
          import_limit_kw: 12.0,
          limiting_factor: "none",
          status: "normal",
          predicted_voltage_v: 234.2,
          voltage_headroom_v: 5.8,
          thermal_headroom_pct: 35,
          confidence: 0.95,
        },
        {
          prosumer_id: "prosumer3",
          export_limit_kw: 8.5,
          import_limit_kw: 12.0,
          limiting_factor: "none",
          status: "normal",
          predicted_voltage_v: 232.1,
          voltage_headroom_v: 7.9,
          thermal_headroom_pct: 35,
          confidence: 0.95,
        },
        {
          prosumer_id: "prosumer4",
          export_limit_kw: 7.2,
          import_limit_kw: 12.0,
          limiting_factor: "none",
          status: "normal",
          predicted_voltage_v: 233.8,
          voltage_headroom_v: 6.2,
          thermal_headroom_pct: 35,
          confidence: 0.95,
        },
        {
          prosumer_id: "prosumer5",
          export_limit_kw: 3.8,
          import_limit_kw: 12.0,
          limiting_factor: "voltage",
          status: "critical",
          predicted_voltage_v: 238.2,
          voltage_headroom_v: 1.8,
          thermal_headroom_pct: 35,
          confidence: 0.95,
        },
        {
          prosumer_id: "prosumer6",
          export_limit_kw: 8.2,
          import_limit_kw: 12.0,
          limiting_factor: "none",
          status: "normal",
          predicted_voltage_v: 231.5,
          voltage_headroom_v: 8.5,
          thermal_headroom_pct: 35,
          confidence: 0.95,
        },
        {
          prosumer_id: "prosumer7",
          export_limit_kw: 8.0,
          import_limit_kw: 12.0,
          limiting_factor: "none",
          status: "normal",
          predicted_voltage_v: 232.0,
          voltage_headroom_v: 8.0,
          thermal_headroom_pct: 35,
          confidence: 0.95,
        },
      ];

      const exportLimits = simLimits.map((l) => l.export_limit_kw);
      const simSummary: DOESummary = {
        total_export_capacity_kw: exportLimits.reduce((a, b) => a + b, 0),
        avg_export_limit_kw: exportLimits.reduce((a, b) => a + b, 0) / exportLimits.length,
        min_export_limit_kw: Math.min(...exportLimits),
        max_export_limit_kw: Math.max(...exportLimits),
        constrained_count: simLimits.filter((l) => l.status !== "normal").length,
        voltage_limited_count: simLimits.filter((l) => l.limiting_factor === "voltage").length,
        thermal_limited_count: simLimits.filter((l) => l.limiting_factor === "thermal").length,
      };

      setLimits(simLimits);
      setSummary(simSummary);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 15 * 60 * 1000); // Update every 15 minutes
    return () => clearInterval(interval);
  }, [loadData]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case "critical":
        return "#EF4444";
      case "constrained":
        return "#F59E0B";
      default:
        return "#10B981";
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "critical":
        return <XCircle className="w-4 h-4 text-red-500" />;
      case "constrained":
        return <AlertTriangle className="w-4 h-4 text-amber-500" />;
      default:
        return <CheckCircle className="w-4 h-4 text-green-500" />;
    }
  };

  const getLimitingIcon = (factor: string) => {
    switch (factor) {
      case "voltage":
        return <Zap className="w-3 h-3 text-yellow-500" />;
      case "thermal":
        return <Thermometer className="w-3 h-3 text-red-500" />;
      default:
        return null;
    }
  };

  const chartData = limits.map((l) => ({
    name: l.prosumer_id.replace("prosumer", "P"),
    export: l.export_limit_kw,
    import: l.import_limit_kw,
    pvCapacity: 10, // PV capacity for reference
    status: l.status,
  }));

  return (
    <div className="bg-white rounded-lg shadow-md p-3 sm:p-4 border-l-4 border-green-500">
      {/* Header */}
      <div className="flex items-center justify-between mb-3 sm:mb-4">
        <div className="flex items-center flex-wrap gap-1">
          <Battery className="w-4 h-4 sm:w-5 sm:h-5 text-green-500 mr-1 sm:mr-2" />
          <h3 className="text-sm sm:text-lg font-semibold text-gray-800">
            Dynamic Operating Envelope
          </h3>
          <HelpTrigger sectionId="doe-dashboard" size="sm" variant="subtle" />
          <span className="text-[10px] sm:text-xs px-1.5 sm:px-2 py-0.5 rounded-full bg-green-100 text-green-700">
            TOR 7.5.1.6
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

      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 sm:gap-3 mb-3 sm:mb-4">
          <div className="bg-green-50 rounded-lg p-2 sm:p-3">
            <p className="text-[10px] sm:text-xs text-green-600 font-medium">Total Export</p>
            <p className="text-sm sm:text-xl font-bold text-green-700">
              {summary.total_export_capacity_kw.toFixed(1)}
              <span className="text-xs sm:text-sm"> kW</span>
            </p>
          </div>
          <div className="bg-blue-50 rounded-lg p-2 sm:p-3">
            <p className="text-[10px] sm:text-xs text-blue-600 font-medium">Avg Export</p>
            <p className="text-sm sm:text-xl font-bold text-blue-700">
              {summary.avg_export_limit_kw.toFixed(1)}
              <span className="text-xs sm:text-sm"> kW</span>
            </p>
          </div>
          <div className="bg-amber-50 rounded-lg p-2 sm:p-3">
            <p className="text-[10px] sm:text-xs text-amber-600 font-medium">Constrained</p>
            <p className="text-sm sm:text-xl font-bold text-amber-700">
              {summary.constrained_count}
              <span className="text-xs sm:text-sm"> / {limits.length}</span>
            </p>
          </div>
          <div className="bg-purple-50 rounded-lg p-2 sm:p-3">
            <p className="text-[10px] sm:text-xs text-purple-600 font-medium">Voltage Limited</p>
            <p className="text-sm sm:text-xl font-bold text-purple-700">
              {summary.voltage_limited_count}
              <span className="text-xs sm:text-sm"> prosumers</span>
            </p>
          </div>
        </div>
      )}

      {/* Error Banner */}
      {error && (
        <div className="bg-amber-50 text-amber-700 px-2 sm:px-3 py-1.5 sm:py-2 rounded mb-3 sm:mb-4 text-xs sm:text-sm">
          {error} (showing simulation)
        </div>
      )}

      {/* Chart */}
      {isLoading && limits.length === 0 ? (
        <div className="h-[200px] sm:h-[300px] flex items-center justify-center">
          <div className="animate-pulse text-gray-400 text-sm">Loading DOE data...</div>
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={height}>
          <BarChart data={chartData} margin={{ top: 5, right: 10, left: -15, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis dataKey="name" tick={{ fontSize: 10 }} tickLine={false} />
            <YAxis
              tick={{ fontSize: 10 }}
              tickLine={false}
              tickFormatter={(value) => `${value}`}
              width={30}
              domain={[0, 15]}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "white",
                borderRadius: "8px",
                boxShadow: "0 2px 8px rgba(0,0,0,0.15)",
                borderLeft: "4px solid #10B981",
                fontSize: "12px",
              }}
              formatter={(value: number, name: string) => [
                `${value.toFixed(1)} kW`,
                name === "export" ? "Export Limit" : "Import Limit",
              ]}
            />
            <Legend wrapperStyle={{ fontSize: "10px" }} />
            <ReferenceLine
              y={10}
              stroke="#9333EA"
              strokeDasharray="5 5"
              label={{ value: "PV Capacity", fontSize: 9, fill: "#9333EA" }}
            />
            <Bar dataKey="export" name="Export Limit" radius={[4, 4, 0, 0]}>
              {chartData.map((entry) => (
                <Cell key={`cell-${entry.name}`} fill={getStatusColor(entry.status)} />
              ))}
            </Bar>
            <Bar
              dataKey="import"
              name="Import Limit"
              fill="#3B82F6"
              opacity={0.5}
              radius={[4, 4, 0, 0]}
            />
          </BarChart>
        </ResponsiveContainer>
      )}

      {/* Prosumer Details Table */}
      <div className="mt-3 sm:mt-4 overflow-x-auto">
        <table className="w-full text-xs sm:text-sm">
          <thead>
            <tr className="border-b border-gray-200">
              <th className="text-left py-2 font-medium text-gray-600">Prosumer</th>
              <th className="text-center py-2 font-medium text-gray-600">Status</th>
              <th className="text-right py-2 font-medium text-gray-600">Export</th>
              <th className="text-right py-2 font-medium text-gray-600">Voltage</th>
              <th className="text-center py-2 font-medium text-gray-600">Limiting</th>
            </tr>
          </thead>
          <tbody>
            {limits.map((limit) => (
              <tr key={limit.prosumer_id} className="border-b border-gray-100 hover:bg-gray-50">
                <td className="py-2 font-medium">{limit.prosumer_id}</td>
                <td className="py-2 text-center">
                  <div className="flex items-center justify-center gap-1">
                    {getStatusIcon(limit.status)}
                    <span className="capitalize text-[10px] sm:text-xs">{limit.status}</span>
                  </div>
                </td>
                <td className="py-2 text-right font-mono">{limit.export_limit_kw.toFixed(1)} kW</td>
                <td className="py-2 text-right font-mono">
                  {limit.predicted_voltage_v.toFixed(1)} V
                </td>
                <td className="py-2 text-center">
                  <div className="flex items-center justify-center gap-1">
                    {getLimitingIcon(limit.limiting_factor)}
                    <span className="capitalize text-[10px] sm:text-xs text-gray-500">
                      {limit.limiting_factor === "none" ? "-" : limit.limiting_factor}
                    </span>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Footer */}
      <div className="mt-2 sm:mt-3 pt-2 sm:pt-3 border-t border-gray-100">
        <p className="text-[10px] sm:text-xs text-gray-500">
          Target: Violation Rate &lt; 1% | Update: 15 min | Confidence: 95% | Mock GIS data
        </p>
      </div>
    </div>
  );
}
