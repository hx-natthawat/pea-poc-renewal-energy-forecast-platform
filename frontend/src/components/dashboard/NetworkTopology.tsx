"use client";

import {
  AlertTriangle,
  Battery,
  Car,
  CheckCircle,
  Grid3X3,
  Network,
  Radio,
  RefreshCw,
  Sun,
  Zap,
} from "lucide-react";
import dynamic from "next/dynamic";
import { useCallback, useEffect, useState } from "react";
import { useVoltageWebSocket } from "@/hooks";
import { getApiBaseUrl } from "@/lib/api";

// Dynamically import ReactFlow component to avoid SSR issues
const NetworkGraphView = dynamic(() => import("./NetworkGraphView"), {
  ssr: false,
  loading: () => (
    <div className="h-[600px] flex items-center justify-center bg-gray-50 rounded-lg">
      <div className="animate-pulse text-gray-400">Loading graph view...</div>
    </div>
  ),
});

type ViewMode = "grid" | "graph";

interface ProsumerNode {
  id: string;
  name: string;
  phase: string;
  position: number;
  has_pv: boolean;
  has_ev: boolean;
  has_battery: boolean;
  pv_capacity_kw: number | null;
  current_voltage: number | null;
  voltage_status: "normal" | "warning" | "critical" | "unknown";
  active_power: number | null;
  reactive_power: number | null;
}

interface PhaseGroup {
  phase: string;
  prosumers: ProsumerNode[];
  avg_voltage: number | null;
  total_power: number | null;
}

interface TopologyData {
  transformer: {
    id: string;
    name: string;
    capacity_kva: number;
    voltage_primary: number;
    voltage_secondary: number;
  };
  phases: PhaseGroup[];
  summary: {
    total_prosumers: number;
    prosumers_with_pv: number;
    prosumers_with_ev: number;
    voltage_stats: {
      avg_voltage: number | null;
      min_voltage: number | null;
      max_voltage: number | null;
      critical_count: number;
      warning_count: number;
    };
  };
  limits: {
    nominal: number;
    upper_limit: number;
    lower_limit: number;
    warning_upper: number;
    warning_lower: number;
  };
}

interface NetworkTopologyProps {
  enableRealtime?: boolean;
}

const STATUS_COLORS = {
  normal: "bg-green-100 border-green-400 text-green-800",
  warning: "bg-amber-100 border-amber-400 text-amber-800",
  critical: "bg-red-100 border-red-400 text-red-800",
  unknown: "bg-gray-100 border-gray-400 text-gray-600",
};

const STATUS_DOT = {
  normal: "bg-green-500",
  warning: "bg-amber-500",
  critical: "bg-red-500",
  unknown: "bg-gray-400",
};

export default function NetworkTopology({ enableRealtime = true }: NetworkTopologyProps) {
  const [topology, setTopology] = useState<TopologyData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedProsumer, setSelectedProsumer] = useState<string | null>(null);
  const [liveUpdateCount, setLiveUpdateCount] = useState(0);
  const [viewMode, setViewMode] = useState<ViewMode>("grid");

  // WebSocket for real-time voltage updates
  const { isConnected: wsConnected } = useVoltageWebSocket(
    enableRealtime
      ? (update) => {
          // Update voltage for specific prosumer
          if (update.prosumer_id && topology) {
            setTopology((prev) => {
              if (!prev) return prev;

              const newPhases = prev.phases.map((phase) => ({
                ...phase,
                prosumers: phase.prosumers.map((p) => {
                  if (p.id === update.prosumer_id) {
                    const voltage = update.voltage || update.prediction;
                    return {
                      ...p,
                      current_voltage: voltage ?? p.current_voltage,
                      voltage_status: voltage ? getVoltageStatus(voltage, prev.limits) : p.voltage_status,
                    };
                  }
                  return p;
                }),
              }));

              return { ...prev, phases: newPhases };
            });
            setLiveUpdateCount((prev) => prev + 1);
          }
        }
      : undefined
  );

  const getVoltageStatus = (
    voltage: number | null,
    limits: TopologyData["limits"]
  ): ProsumerNode["voltage_status"] => {
    if (voltage === null) return "unknown";
    if (voltage < limits.lower_limit || voltage > limits.upper_limit) return "critical";
    if (voltage < limits.warning_lower || voltage > limits.warning_upper) return "warning";
    return "normal";
  };

  const loadTopology = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${getApiBaseUrl()}/api/v1/topology/`);
      if (!response.ok) {
        throw new Error("Failed to fetch topology");
      }

      const result = await response.json();
      if (result.status === "success") {
        setTopology(result.data);
      }
    } catch (err) {
      console.error("Error fetching topology:", err);
      setError("Could not load network topology");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadTopology();
    const interval = setInterval(loadTopology, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, [loadTopology]);

  const renderProsumerNode = (prosumer: ProsumerNode) => {
    const isSelected = selectedProsumer === prosumer.id;

    return (
      <div
        key={prosumer.id}
        onClick={() => setSelectedProsumer(isSelected ? null : prosumer.id)}
        className={`
          relative p-3 rounded-lg border-2 cursor-pointer transition-all
          ${STATUS_COLORS[prosumer.voltage_status]}
          ${isSelected ? "ring-2 ring-[#74045F] ring-offset-2" : "hover:shadow-md"}
        `}
      >
        {/* Status indicator */}
        <div
          className={`absolute -top-1 -right-1 w-3 h-3 rounded-full ${STATUS_DOT[prosumer.voltage_status]}`}
        />

        {/* Prosumer name and icons */}
        <div className="flex items-center justify-between mb-2">
          <span className="font-semibold text-sm">{prosumer.name}</span>
          <div className="flex space-x-1">
            {prosumer.has_pv && <span title="Solar PV"><Sun className="w-4 h-4 text-amber-500" /></span>}
            {prosumer.has_ev && <span title="EV Charger"><Car className="w-4 h-4 text-blue-500" /></span>}
            {prosumer.has_battery && <span title="Battery"><Battery className="w-4 h-4 text-green-500" /></span>}
          </div>
        </div>

        {/* Voltage display */}
        <div className="text-center">
          <p className="text-2xl font-bold">
            {prosumer.current_voltage !== null
              ? `${prosumer.current_voltage.toFixed(1)}V`
              : "--"}
          </p>
          {prosumer.active_power !== null && (
            <p className="text-xs opacity-75">
              {prosumer.active_power.toFixed(2)} kW
            </p>
          )}
        </div>

        {/* Position indicator */}
        <div className="mt-2 text-xs opacity-60 text-center">
          Position: {prosumer.position === 1 ? "Near" : prosumer.position === 2 ? "Mid" : "Far"}
        </div>
      </div>
    );
  };

  if (isLoading && !topology) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-[#74045F]">
        <div className="animate-pulse flex items-center justify-center h-64">
          <p className="text-gray-400">Loading network topology...</p>
        </div>
      </div>
    );
  }

  if (error && !topology) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-red-500">
        <div className="flex items-center justify-center h-64 text-red-500">
          <AlertTriangle className="w-6 h-6 mr-2" />
          <p>{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-4 border-l-4 border-[#74045F]">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center">
          <Zap className="w-5 h-5 text-[#74045F] mr-2" />
          <h3 className="text-lg font-semibold text-gray-800">Network Topology</h3>
          {enableRealtime && (
            <span
              className={`ml-2 flex items-center text-xs px-2 py-0.5 rounded-full ${
                wsConnected
                  ? "bg-green-100 text-green-700"
                  : "bg-gray-100 text-gray-500"
              }`}
            >
              <Radio className={`w-3 h-3 mr-1 ${wsConnected ? "animate-pulse" : ""}`} />
              {wsConnected ? "LIVE" : "..."}
            </span>
          )}
        </div>
        <div className="flex items-center space-x-2">
          {/* View Toggle */}
          <div className="flex rounded-lg border border-gray-200 overflow-hidden">
            <button
              type="button"
              onClick={() => setViewMode("grid")}
              className={`px-3 py-1.5 text-xs font-medium flex items-center transition-colors ${
                viewMode === "grid"
                  ? "bg-[#74045F] text-white"
                  : "bg-white text-gray-600 hover:bg-gray-50"
              }`}
              title="Grid View"
            >
              <Grid3X3 className="w-4 h-4 mr-1" />
              Grid
            </button>
            <button
              type="button"
              onClick={() => setViewMode("graph")}
              className={`px-3 py-1.5 text-xs font-medium flex items-center transition-colors ${
                viewMode === "graph"
                  ? "bg-[#74045F] text-white"
                  : "bg-white text-gray-600 hover:bg-gray-50"
              }`}
              title="Graph View"
            >
              <Network className="w-4 h-4 mr-1" />
              Graph
            </button>
          </div>
          <button
            type="button"
            onClick={loadTopology}
            className="p-2 hover:bg-gray-100 rounded-full transition-colors"
            title="Refresh"
          >
            <RefreshCw className={`w-4 h-4 text-gray-500 ${isLoading ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>

      {/* Summary Stats */}
      {topology && (
        <div className="grid grid-cols-4 gap-3 mb-4">
          <div className="bg-gray-50 rounded-lg p-2 text-center">
            <p className="text-xs text-gray-500">Avg Voltage</p>
            <p className="text-lg font-bold text-gray-800">
              {topology.summary.voltage_stats.avg_voltage?.toFixed(1) || "--"}V
            </p>
          </div>
          <div className="bg-green-50 rounded-lg p-2 text-center">
            <p className="text-xs text-green-600">Normal</p>
            <p className="text-lg font-bold text-green-700">
              {topology.summary.total_prosumers -
                (topology.summary.voltage_stats.critical_count +
                  topology.summary.voltage_stats.warning_count)}
            </p>
          </div>
          <div className="bg-amber-50 rounded-lg p-2 text-center">
            <p className="text-xs text-amber-600">Warning</p>
            <p className="text-lg font-bold text-amber-700">
              {topology.summary.voltage_stats.warning_count}
            </p>
          </div>
          <div className="bg-red-50 rounded-lg p-2 text-center">
            <p className="text-xs text-red-600">Critical</p>
            <p className="text-lg font-bold text-red-700">
              {topology.summary.voltage_stats.critical_count}
            </p>
          </div>
        </div>
      )}

      {/* Graph View */}
      {viewMode === "graph" && (
        <NetworkGraphView onNodeSelect={setSelectedProsumer} />
      )}

      {/* Grid View - Network Diagram */}
      {viewMode === "grid" && topology && (
        <div className="relative">
          {/* Transformer */}
          <div className="flex justify-center mb-4">
            <div className="bg-[#74045F] text-white px-6 py-3 rounded-lg text-center">
              <p className="font-semibold">{topology.transformer.name}</p>
              <p className="text-xs text-[#D4A43D]">
                {topology.transformer.capacity_kva} kVA |{" "}
                {topology.transformer.voltage_primary / 1000}kV /{" "}
                {topology.transformer.voltage_secondary}V
              </p>
            </div>
          </div>

          {/* Main Bus */}
          <div className="flex justify-center mb-4">
            <div className="w-3/4 h-1 bg-gray-800 rounded" />
          </div>

          {/* Phase Groups */}
          <div className="space-y-4">
            {topology.phases.map((phase) => (
              <div key={phase.phase} className="relative">
                {/* Phase Label */}
                <div className="flex items-center mb-2">
                  <div
                    className={`
                    px-3 py-1 rounded-full text-sm font-semibold
                    ${phase.phase === "A" ? "bg-red-100 text-red-700" : ""}
                    ${phase.phase === "B" ? "bg-yellow-100 text-yellow-700" : ""}
                    ${phase.phase === "C" ? "bg-blue-100 text-blue-700" : ""}
                  `}
                  >
                    Phase {phase.phase}
                  </div>
                  <div className="flex-1 h-0.5 bg-gray-300 mx-2" />
                  <div className="text-xs text-gray-500">
                    Avg: {phase.avg_voltage?.toFixed(1) || "--"}V |{" "}
                    {phase.total_power?.toFixed(2) || "--"} kW
                  </div>
                </div>

                {/* Prosumer Nodes */}
                <div className="grid grid-cols-3 gap-3 pl-8">
                  {phase.prosumers
                    .sort((a, b) => a.position - b.position)
                    .map((prosumer) => renderProsumerNode(prosumer))}
                  {/* Fill empty slots */}
                  {phase.prosumers.length < 3 &&
                    Array.from({ length: 3 - phase.prosumers.length }).map((_, i) => (
                      <div
                        key={`empty-${phase.phase}-${i}`}
                        className="p-3 rounded-lg border-2 border-dashed border-gray-200 opacity-30"
                      />
                    ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Selected Prosumer Details */}
      {selectedProsumer && topology && viewMode === "grid" && (
        <div className="mt-4 p-4 bg-gray-50 rounded-lg">
          <h4 className="font-semibold text-gray-800 mb-2">Prosumer Details</h4>
          {topology.phases.flatMap((p) => p.prosumers).map((prosumer) => {
            if (prosumer.id !== selectedProsumer) return null;
            return (
              <div key={prosumer.id} className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <p className="text-gray-500">ID</p>
                  <p className="font-semibold">{prosumer.id}</p>
                </div>
                <div>
                  <p className="text-gray-500">Phase</p>
                  <p className="font-semibold">Phase {prosumer.phase}</p>
                </div>
                <div>
                  <p className="text-gray-500">Current Voltage</p>
                  <p className="font-semibold">
                    {prosumer.current_voltage?.toFixed(1) || "--"}V
                  </p>
                </div>
                <div>
                  <p className="text-gray-500">Active Power</p>
                  <p className="font-semibold">
                    {prosumer.active_power?.toFixed(2) || "--"} kW
                  </p>
                </div>
                <div>
                  <p className="text-gray-500">Equipment</p>
                  <div className="flex items-center space-x-2">
                    {prosumer.has_pv && (
                      <span className="flex items-center text-amber-600">
                        <Sun className="w-4 h-4 mr-1" /> PV
                      </span>
                    )}
                    {prosumer.has_ev && (
                      <span className="flex items-center text-blue-600">
                        <Car className="w-4 h-4 mr-1" /> EV
                      </span>
                    )}
                    {!prosumer.has_pv && !prosumer.has_ev && (
                      <span className="text-gray-400">None</span>
                    )}
                  </div>
                </div>
                <div>
                  <p className="text-gray-500">Status</p>
                  <span
                    className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${STATUS_COLORS[prosumer.voltage_status]}`}
                  >
                    {prosumer.voltage_status === "normal" && <CheckCircle className="w-3 h-3 mr-1" />}
                    {prosumer.voltage_status === "warning" && <AlertTriangle className="w-3 h-3 mr-1" />}
                    {prosumer.voltage_status === "critical" && <AlertTriangle className="w-3 h-3 mr-1" />}
                    {prosumer.voltage_status.charAt(0).toUpperCase() + prosumer.voltage_status.slice(1)}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Footer */}
      <div className="mt-4 pt-3 border-t border-gray-100">
        <p className="text-xs text-gray-500">
          Limits: {topology?.limits.lower_limit}V - {topology?.limits.upper_limit}V (±5%) |{" "}
          {topology?.summary.total_prosumers} prosumers
          {enableRealtime && liveUpdateCount > 0 && (
            <span className="ml-2 text-green-600">| {liveUpdateCount} live updates</span>
          )}
        </p>
      </div>
    </div>
  );
}
