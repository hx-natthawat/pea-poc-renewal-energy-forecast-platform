"use client";

import {
  AlertTriangle,
  Battery,
  Car,
  Home,
  Radio,
  Sun,
  Zap,
} from "lucide-react";
import { useCallback, useEffect, useMemo } from "react";
import {
  Background,
  BackgroundVariant,
  Controls,
  Handle,
  MiniMap,
  Position,
  ReactFlow,
  useEdgesState,
  useNodesState,
  type Edge,
  type Node,
  type NodeProps,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

// ============================================================================
// Types matching NetworkTopology.tsx
// ============================================================================

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

// ============================================================================
// Node data interfaces - with index signature for ReactFlow compatibility
// ============================================================================

interface TransformerNodeData extends Record<string, unknown> {
  label: string;
  capacity_kva: number;
  voltage_primary: number;
  voltage_secondary: number;
}

interface PhaseNodeData extends Record<string, unknown> {
  label: string;
  phase: string;
  avg_voltage: number | null;
  total_power: number | null;
  prosumerCount: number;
}

interface ProsumerGraphNodeData extends Record<string, unknown> {
  label: string;
  name: string;
  phase: string;
  position: number;
  has_pv: boolean;
  has_ev: boolean;
  has_battery: boolean;
  voltage: number | null;
  power: number | null;
  status: "normal" | "warning" | "critical" | "unknown";
}

// ============================================================================
// Status colors following PEA brand
// ============================================================================

const STATUS_COLORS = {
  normal: { bg: "#22C55E", border: "#16A34A" },
  warning: { bg: "#F59E0B", border: "#D97706" },
  critical: { bg: "#EF4444", border: "#DC2626" },
  unknown: { bg: "#9CA3AF", border: "#6B7280" },
};

const PHASE_COLORS = {
  A: { bg: "#FEE2E2", border: "#EF4444", text: "#B91C1C" },
  B: { bg: "#FEF3C7", border: "#F59E0B", text: "#B45309" },
  C: { bg: "#DBEAFE", border: "#3B82F6", text: "#1D4ED8" },
};

// PEA Brand Colors
const PEA_PURPLE = "#74045F";
const PEA_GOLD = "#C7911B";

// ============================================================================
// Custom Transformer Node Component
// ============================================================================

function TransformerNode({ data }: NodeProps<Node<TransformerNodeData>>) {
  return (
    <div className="relative group">
      <div
        className="flex flex-col items-center p-4 rounded-xl shadow-xl transition-transform hover:scale-105"
        style={{
          backgroundColor: PEA_PURPLE,
          border: `3px solid ${PEA_GOLD}`,
          minWidth: "160px",
        }}
      >
        {/* Antenna */}
        <Radio className="w-5 h-5 text-white/80 absolute -top-4" />

        {/* Icon */}
        <div className="relative mb-2">
          <Zap className="w-12 h-12 text-[#D4A43D]" />
        </div>

        <span className="text-sm font-bold text-white">{data.label}</span>
        <span className="text-xs text-[#D4A43D]">
          {data.capacity_kva} kVA
        </span>
        <span className="text-[10px] text-white/70">
          {data.voltage_primary / 1000}kV / {data.voltage_secondary}V
        </span>
      </div>

      <Handle type="source" position={Position.Bottom} className="!bg-[#D4A43D] !w-3 !h-3" />

      {/* Tooltip */}
      <div className="absolute -bottom-10 left-1/2 -translate-x-1/2 bg-gray-800 text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-10">
        Distribution Transformer
      </div>
    </div>
  );
}

// ============================================================================
// Custom Phase Node Component
// ============================================================================

function PhaseNode({ data }: NodeProps<Node<PhaseNodeData>>) {
  const colors = PHASE_COLORS[data.phase as keyof typeof PHASE_COLORS] || PHASE_COLORS.A;

  return (
    <div className="relative group">
      <Handle type="target" position={Position.Top} className="!bg-gray-400 !w-2 !h-2" />

      <div
        className="flex flex-col items-center p-3 rounded-lg shadow-md transition-transform hover:scale-105"
        style={{
          backgroundColor: colors.bg,
          border: `2px solid ${colors.border}`,
          minWidth: "100px",
        }}
      >
        <span className="text-sm font-bold" style={{ color: colors.text }}>
          Phase {data.phase}
        </span>
        <span className="text-xs text-gray-600">
          {data.avg_voltage?.toFixed(1) || "--"}V avg
        </span>
        <span className="text-[10px] text-gray-500">
          {data.prosumerCount} prosumers
        </span>
      </div>

      <Handle type="source" position={Position.Bottom} className="!bg-gray-400 !w-2 !h-2" />

      {/* Tooltip */}
      <div className="absolute -bottom-10 left-1/2 -translate-x-1/2 bg-gray-800 text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-10">
        Total: {data.total_power?.toFixed(2) || "--"} kW
      </div>
    </div>
  );
}

// ============================================================================
// Custom Prosumer Node Component
// ============================================================================

function ProsumerGraphNode({ data }: NodeProps<Node<ProsumerGraphNodeData>>) {
  const statusColor = STATUS_COLORS[data.status];

  const getPositionLabel = (pos: number) => {
    if (pos === 1) return "Near";
    if (pos === 2) return "Mid";
    return "Far";
  };

  return (
    <div className="relative group">
      <Handle type="target" position={Position.Top} className="!bg-gray-400 !w-2 !h-2" />

      <div
        className="flex flex-col items-center p-3 rounded-xl shadow-lg bg-white transition-transform hover:scale-105"
        style={{ border: `2px solid ${statusColor.border}`, minWidth: "90px" }}
      >
        {/* Status indicator */}
        <div
          className={`absolute -top-1 -right-1 w-3 h-3 rounded-full ${
            data.status === "critical" || data.status === "warning" ? "animate-pulse" : ""
          }`}
          style={{ backgroundColor: statusColor.bg }}
        />

        {/* Device icon with equipment indicators */}
        <div className="relative mb-1">
          <Home className="w-10 h-10 text-gray-600" />
          {data.has_pv && (
            <Sun className="w-4 h-4 text-amber-500 absolute -top-1 -right-1" />
          )}
          {data.has_ev && (
            <Car className="w-4 h-4 text-blue-500 absolute -bottom-1 -right-1" />
          )}
          {data.has_battery && (
            <Battery className="w-4 h-4 text-green-500 absolute -bottom-1 -left-1" />
          )}
        </div>

        {/* Label */}
        <span className="text-xs font-bold text-gray-700">{data.name}</span>

        {/* Voltage display */}
        <span
          className={`text-sm font-bold ${
            data.status === "critical"
              ? "text-red-600"
              : data.status === "warning"
                ? "text-amber-600"
                : "text-green-600"
          }`}
        >
          {data.voltage !== null ? `${data.voltage.toFixed(1)}V` : "--"}
        </span>

        {/* Power display */}
        {data.power !== null && (
          <span className="text-[10px] text-gray-500">
            {data.power.toFixed(2)} kW
          </span>
        )}

        {/* Position indicator */}
        <span className="text-[9px] text-gray-400 mt-1">
          {getPositionLabel(data.position)}
        </span>
      </div>

      {/* Tooltip */}
      <div className="absolute -bottom-14 left-1/2 -translate-x-1/2 bg-gray-800 text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-10">
        {data.name} | Phase {data.phase} | {data.status}
      </div>
    </div>
  );
}

// ============================================================================
// Node types registration
// ============================================================================

const nodeTypes = {
  transformer: TransformerNode,
  phase: PhaseNode,
  prosumer: ProsumerGraphNode,
};

// ============================================================================
// Helper function to create nodes and edges from topology data
// ============================================================================

function createNodesAndEdges(topology: TopologyData): { nodes: Node[]; edges: Edge[] } {
  const nodes: Node[] = [];
  const edges: Edge[] = [];

  // Layout constants
  const TRANSFORMER_Y = 50;
  const PHASE_Y = 180;
  const PROSUMER_START_Y = 320;
  const PROSUMER_ROW_HEIGHT = 140;
  const CENTER_X = 400;
  const PHASE_SPACING = 250;

  // 1. Add Transformer node
  nodes.push({
    id: "transformer",
    type: "transformer",
    position: { x: CENTER_X - 80, y: TRANSFORMER_Y },
    data: {
      label: topology.transformer.name,
      capacity_kva: topology.transformer.capacity_kva,
      voltage_primary: topology.transformer.voltage_primary,
      voltage_secondary: topology.transformer.voltage_secondary,
    },
  });

  // 2. Add Phase nodes and prosumer nodes
  const phaseOrder = ["A", "B", "C"];
  const sortedPhases = [...topology.phases].sort(
    (a, b) => phaseOrder.indexOf(a.phase) - phaseOrder.indexOf(b.phase)
  );

  sortedPhases.forEach((phase, phaseIndex) => {
    const phaseX = CENTER_X + (phaseIndex - 1) * PHASE_SPACING;
    const phaseId = `phase-${phase.phase}`;

    // Add phase node
    nodes.push({
      id: phaseId,
      type: "phase",
      position: { x: phaseX - 50, y: PHASE_Y },
      data: {
        label: `Phase ${phase.phase}`,
        phase: phase.phase,
        avg_voltage: phase.avg_voltage,
        total_power: phase.total_power,
        prosumerCount: phase.prosumers.length,
      },
    });

    // Edge from transformer to phase
    edges.push({
      id: `transformer-${phaseId}`,
      source: "transformer",
      target: phaseId,
      style: { stroke: "#6B7280", strokeWidth: 2 },
      animated: false,
    });

    // Add prosumer nodes for this phase
    const sortedProsumers = [...phase.prosumers].sort((a, b) => a.position - b.position);

    sortedProsumers.forEach((prosumer, prosumerIndex) => {
      const prosumerX = phaseX - 45;
      const prosumerY = PROSUMER_START_Y + prosumerIndex * PROSUMER_ROW_HEIGHT;

      nodes.push({
        id: prosumer.id,
        type: "prosumer",
        position: { x: prosumerX, y: prosumerY },
        data: {
          label: prosumer.id,
          name: prosumer.name,
          phase: prosumer.phase,
          position: prosumer.position,
          has_pv: prosumer.has_pv,
          has_ev: prosumer.has_ev,
          has_battery: prosumer.has_battery,
          voltage: prosumer.current_voltage,
          power: prosumer.active_power,
          status: prosumer.voltage_status,
        },
      });

      // Edge from phase to prosumer (or prosumer to prosumer for chain)
      if (prosumerIndex === 0) {
        edges.push({
          id: `${phaseId}-${prosumer.id}`,
          source: phaseId,
          target: prosumer.id,
          style: {
            stroke: prosumer.voltage_status === "critical" ? "#EF4444" :
                   prosumer.voltage_status === "warning" ? "#F59E0B" : "#94A3B8",
            strokeWidth: 1.5,
          },
        });
      } else {
        // Chain prosumers together
        const prevProsumer = sortedProsumers[prosumerIndex - 1];
        edges.push({
          id: `${prevProsumer.id}-${prosumer.id}`,
          source: prevProsumer.id,
          target: prosumer.id,
          style: {
            stroke: prosumer.voltage_status === "critical" ? "#EF4444" :
                   prosumer.voltage_status === "warning" ? "#F59E0B" : "#94A3B8",
            strokeWidth: 1.5,
          },
        });
      }
    });
  });

  return { nodes, edges };
}

// ============================================================================
// Component Props
// ============================================================================

interface NetworkGraphViewProps {
  topology?: TopologyData | null;
  onNodeSelect?: (nodeId: string | null) => void;
}

// ============================================================================
// Main Component
// ============================================================================

export default function NetworkGraphView({ topology, onNodeSelect }: NetworkGraphViewProps) {
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);

  // Update nodes and edges when topology changes
  useEffect(() => {
    if (topology) {
      const { nodes: newNodes, edges: newEdges } = createNodesAndEdges(topology);
      setNodes(newNodes);
      setEdges(newEdges);
    }
  }, [topology, setNodes, setEdges]);

  const onNodeClick = useCallback(
    (_: React.MouseEvent, node: Node) => {
      // Only select prosumer nodes
      if (node.type === "prosumer") {
        onNodeSelect?.(node.id);
      }
    },
    [onNodeSelect]
  );

  // Custom minimap node color
  const nodeColor = useCallback((node: Node) => {
    if (node.type === "transformer") return PEA_PURPLE;
    if (node.type === "phase") {
      const phase = (node.data as PhaseNodeData).phase;
      return PHASE_COLORS[phase as keyof typeof PHASE_COLORS]?.border || "#6B7280";
    }
    if (node.type === "prosumer") {
      const status = (node.data as ProsumerGraphNodeData).status;
      return STATUS_COLORS[status]?.bg || "#6B7280";
    }
    return "#6B7280";
  }, []);

  // Legend component
  const Legend = useMemo(
    () => (
      <div className="absolute bottom-4 left-4 bg-white/90 backdrop-blur-sm rounded-lg shadow-lg p-3 z-10">
        <h4 className="text-xs font-bold text-gray-700 mb-2">Legend</h4>
        <div className="space-y-1.5">
          <div className="flex items-center text-xs">
            <Zap className="w-4 h-4 text-[#74045F] mr-2" />
            <span className="text-gray-600">Transformer</span>
          </div>
          <div className="flex items-center text-xs">
            <div className="w-4 h-4 rounded bg-red-100 border border-red-400 mr-2" />
            <span className="text-gray-600">Phase A</span>
          </div>
          <div className="flex items-center text-xs">
            <div className="w-4 h-4 rounded bg-yellow-100 border border-yellow-400 mr-2" />
            <span className="text-gray-600">Phase B</span>
          </div>
          <div className="flex items-center text-xs">
            <div className="w-4 h-4 rounded bg-blue-100 border border-blue-400 mr-2" />
            <span className="text-gray-600">Phase C</span>
          </div>
          <div className="border-t border-gray-200 my-2" />
          <div className="flex items-center text-xs">
            <Home className="w-4 h-4 text-gray-600 mr-2" />
            <span className="text-gray-600">Prosumer</span>
          </div>
          <div className="flex items-center text-xs">
            <Sun className="w-3 h-3 text-amber-500 mr-1" />
            <span className="text-gray-500 mr-2">PV</span>
            <Car className="w-3 h-3 text-blue-500 mr-1" />
            <span className="text-gray-500 mr-2">EV</span>
            <Battery className="w-3 h-3 text-green-500 mr-1" />
            <span className="text-gray-500">Battery</span>
          </div>
          <div className="border-t border-gray-200 my-2" />
          <div className="flex items-center text-xs">
            <div className="w-3 h-3 rounded-full bg-green-500 mr-2" />
            <span className="text-gray-600">Normal</span>
          </div>
          <div className="flex items-center text-xs">
            <div className="w-3 h-3 rounded-full bg-amber-500 mr-2" />
            <span className="text-gray-600">Warning</span>
          </div>
          <div className="flex items-center text-xs">
            <div className="w-3 h-3 rounded-full bg-red-500 mr-2" />
            <span className="text-gray-600">Critical</span>
          </div>
        </div>
      </div>
    ),
    []
  );

  // Show loading state if no topology
  if (!topology) {
    return (
      <div className="relative w-full h-[600px] rounded-lg overflow-hidden border border-gray-200 bg-gray-50 flex items-center justify-center">
        <div className="text-gray-400 flex items-center">
          <AlertTriangle className="w-5 h-5 mr-2" />
          No topology data available
        </div>
      </div>
    );
  }

  return (
    <div className="relative w-full h-[600px] rounded-lg overflow-hidden border border-gray-200">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={onNodeClick}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        defaultEdgeOptions={{
          type: "smoothstep",
          style: { strokeWidth: 1.5 },
        }}
      >
        <Background variant={BackgroundVariant.Dots} gap={20} size={1} color="#E5E7EB" />
        <Controls
          className="!bg-white !shadow-lg !rounded-lg !border !border-gray-200"
          showInteractive={false}
        />
        <MiniMap
          nodeColor={nodeColor}
          nodeStrokeWidth={3}
          className="!bg-white/80 !rounded-lg !shadow-lg !border !border-gray-200"
          maskColor="rgba(116, 4, 95, 0.1)"
        />
      </ReactFlow>

      {Legend}

      {/* Stats overlay */}
      <div className="absolute top-4 right-4 bg-white/95 backdrop-blur-sm rounded-lg shadow-lg p-3 z-10">
        <h4 className="text-xs font-bold text-gray-700 mb-2">Network Status</h4>
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div>
            <span className="text-gray-500">Prosumers:</span>{" "}
            <span className="font-semibold">{topology.summary.total_prosumers}</span>
          </div>
          <div>
            <span className="text-gray-500">With PV:</span>{" "}
            <span className="font-semibold text-amber-600">{topology.summary.prosumers_with_pv}</span>
          </div>
          <div>
            <span className="text-gray-500">Avg V:</span>{" "}
            <span className="font-semibold">
              {topology.summary.voltage_stats.avg_voltage?.toFixed(1) || "--"}V
            </span>
          </div>
          <div>
            <span className="text-gray-500">Critical:</span>{" "}
            <span className="font-semibold text-red-600">
              {topology.summary.voltage_stats.critical_count}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
