"use client";

import {
  Background,
  BackgroundVariant,
  Controls,
  type Edge,
  Handle,
  MiniMap,
  type Node,
  type NodeProps,
  Panel,
  Position,
  ReactFlow,
  ReactFlowProvider,
  useEdgesState,
  useNodesState,
  useReactFlow,
} from "@xyflow/react";
import {
  AlertTriangle,
  Battery,
  Car,
  Grid3X3,
  Home,
  Info,
  LayoutGrid,
  List,
  Map as MapIcon,
  Maximize,
  Radio,
  RotateCcw,
  Sun,
  Zap,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import "@xyflow/react/dist/style.css";

// ============================================================================
// Custom CSS for electrical flow animation
// ============================================================================

const electricalFlowStyles = `
  @keyframes electricalFlow {
    0% {
      stroke-dashoffset: 24;
    }
    100% {
      stroke-dashoffset: 0;
    }
  }

  @keyframes electricalPulse {
    0%, 100% {
      opacity: 0.6;
      filter: drop-shadow(0 0 2px currentColor);
    }
    50% {
      opacity: 1;
      filter: drop-shadow(0 0 6px currentColor);
    }
  }

  .react-flow__edge.animated path {
    stroke-dasharray: 8 4;
    animation: electricalFlow 0.8s linear infinite, electricalPulse 2s ease-in-out infinite;
  }

  .react-flow__edge-path {
    transition: stroke 0.3s ease;
  }

  /* Main feeder lines from transformer */
  .electrical-main path {
    stroke-dasharray: 12 6;
    animation: electricalFlow 0.6s linear infinite, electricalPulse 1.5s ease-in-out infinite !important;
  }

  /* Phase distribution lines */
  .electrical-phase path {
    stroke-dasharray: 8 4;
    animation: electricalFlow 0.7s linear infinite, electricalPulse 2s ease-in-out infinite !important;
  }

  /* Prosumer connection lines */
  .electrical-prosumer path {
    stroke-dasharray: 6 3;
    animation: electricalFlow 0.9s linear infinite, electricalPulse 2.5s ease-in-out infinite !important;
  }
`;

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
  layout: "vertical" | "horizontal";
}

interface PhaseNodeData extends Record<string, unknown> {
  label: string;
  phase: string;
  avg_voltage: number | null;
  total_power: number | null;
  prosumerCount: number;
  layout: "vertical" | "horizontal";
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
  layout: "vertical" | "horizontal";
}

// ============================================================================
// Layout type
// ============================================================================

type LayoutDirection = "vertical" | "horizontal";

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
  const isHorizontal = data.layout === "horizontal";

  return (
    <div className="relative group">
      <Handle
        type="target"
        position={isHorizontal ? Position.Left : Position.Top}
        className="!bg-gray-400 !w-2 !h-2 !opacity-0"
      />

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
        <span className="text-xs text-[#D4A43D]">{data.capacity_kva} kVA</span>
        <span className="text-[10px] text-white/70">
          {data.voltage_primary / 1000}kV / {data.voltage_secondary}V
        </span>
      </div>

      <Handle
        type="source"
        position={isHorizontal ? Position.Right : Position.Bottom}
        className="!bg-[#D4A43D] !w-3 !h-3"
      />

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
  const isHorizontal = data.layout === "horizontal";

  return (
    <div className="relative group">
      <Handle
        type="target"
        position={isHorizontal ? Position.Left : Position.Top}
        className="!bg-gray-400 !w-2 !h-2"
      />

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
        <span className="text-xs text-gray-600">{data.avg_voltage?.toFixed(1) || "--"}V avg</span>
        <span className="text-[10px] text-gray-500">{data.prosumerCount} prosumers</span>
      </div>

      <Handle
        type="source"
        position={isHorizontal ? Position.Right : Position.Bottom}
        className="!bg-gray-400 !w-2 !h-2"
      />

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
  const isHorizontal = data.layout === "horizontal";

  const getPositionLabel = (pos: number) => {
    if (pos === 1) return "Near";
    if (pos === 2) return "Mid";
    return "Far";
  };

  return (
    <div className="relative group">
      <Handle
        type="target"
        position={isHorizontal ? Position.Left : Position.Top}
        className="!bg-gray-400 !w-2 !h-2"
      />

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
          {data.has_pv && <Sun className="w-4 h-4 text-amber-500 absolute -top-1 -right-1" />}
          {data.has_ev && <Car className="w-4 h-4 text-blue-500 absolute -bottom-1 -right-1" />}
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
          <span className="text-[10px] text-gray-500">{data.power.toFixed(2)} kW</span>
        )}

        {/* Position indicator */}
        <span className="text-[9px] text-gray-400 mt-1">{getPositionLabel(data.position)}</span>
      </div>

      <Handle
        type="source"
        position={isHorizontal ? Position.Right : Position.Bottom}
        className="!bg-gray-400 !w-2 !h-2 !opacity-0"
      />

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

function createNodesAndEdges(
  topology: TopologyData,
  layout: LayoutDirection
): { nodes: Node[]; edges: Edge[] } {
  const nodes: Node[] = [];
  const edges: Edge[] = [];

  const isHorizontal = layout === "horizontal";

  // Layout constants for vertical (top-to-bottom)
  const VERTICAL = {
    TRANSFORMER_X: 400,
    TRANSFORMER_Y: 50,
    PHASE_Y: 180,
    PROSUMER_START_Y: 320,
    PROSUMER_ROW_HEIGHT: 140,
    PHASE_SPACING: 250,
  };

  // Layout constants for horizontal (left-to-right)
  // Designed for 600px height container, centered vertically
  const HORIZONTAL = {
    TRANSFORMER_X: 80,
    TRANSFORMER_Y: 220, // Centered vertically for 600px height
    PHASE_X: 280, // More space from transformer
    PHASE_START_Y: 80, // Start phases from top with padding
    PROSUMER_START_X: 450, // More space from phase nodes
    PROSUMER_COL_WIDTH: 150, // More space between prosumers
    PHASE_SPACING: 200, // More space between phases to prevent overlap
  };

  // 1. Add Transformer node
  nodes.push({
    id: "transformer",
    type: "transformer",
    position: isHorizontal
      ? { x: HORIZONTAL.TRANSFORMER_X, y: HORIZONTAL.TRANSFORMER_Y }
      : { x: VERTICAL.TRANSFORMER_X - 80, y: VERTICAL.TRANSFORMER_Y },
    data: {
      label: topology.transformer.name,
      capacity_kva: topology.transformer.capacity_kva,
      voltage_primary: topology.transformer.voltage_primary,
      voltage_secondary: topology.transformer.voltage_secondary,
      layout,
    },
  });

  // 2. Add Phase nodes and prosumer nodes
  const phaseOrder = ["A", "B", "C"];
  const sortedPhases = [...topology.phases].sort(
    (a, b) => phaseOrder.indexOf(a.phase) - phaseOrder.indexOf(b.phase)
  );

  sortedPhases.forEach((phase, phaseIndex) => {
    const phaseId = `phase-${phase.phase}`;

    let phasePosition: { x: number; y: number };
    if (isHorizontal) {
      phasePosition = {
        x: HORIZONTAL.PHASE_X,
        y: HORIZONTAL.PHASE_START_Y + phaseIndex * HORIZONTAL.PHASE_SPACING,
      };
    } else {
      const phaseX = VERTICAL.TRANSFORMER_X + (phaseIndex - 1) * VERTICAL.PHASE_SPACING;
      phasePosition = { x: phaseX - 50, y: VERTICAL.PHASE_Y };
    }

    // Add phase node
    nodes.push({
      id: phaseId,
      type: "phase",
      position: phasePosition,
      data: {
        label: `Phase ${phase.phase}`,
        phase: phase.phase,
        avg_voltage: phase.avg_voltage,
        total_power: phase.total_power,
        prosumerCount: phase.prosumers.length,
        layout,
      },
    });

    // Edge from transformer to phase (main feeder)
    edges.push({
      id: `transformer-${phaseId}`,
      source: "transformer",
      target: phaseId,
      style: { stroke: "#74045F", strokeWidth: 3 },
      animated: true,
      className: "electrical-main",
    });

    // Add prosumer nodes for this phase
    const sortedProsumers = [...phase.prosumers].sort((a, b) => a.position - b.position);

    sortedProsumers.forEach((prosumer, prosumerIndex) => {
      let prosumerPosition: { x: number; y: number };
      if (isHorizontal) {
        prosumerPosition = {
          x: HORIZONTAL.PROSUMER_START_X + prosumerIndex * HORIZONTAL.PROSUMER_COL_WIDTH,
          y: phasePosition.y - 5, // Center align with phase node
        };
      } else {
        const phaseX = VERTICAL.TRANSFORMER_X + (phaseIndex - 1) * VERTICAL.PHASE_SPACING;
        prosumerPosition = {
          x: phaseX - 45,
          y: VERTICAL.PROSUMER_START_Y + prosumerIndex * VERTICAL.PROSUMER_ROW_HEIGHT,
        };
      }

      nodes.push({
        id: prosumer.id,
        type: "prosumer",
        position: prosumerPosition,
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
          layout,
        },
      });

      // Edge from phase to prosumer (or prosumer to prosumer for chain)
      const edgeColor =
        prosumer.voltage_status === "critical"
          ? "#EF4444"
          : prosumer.voltage_status === "warning"
            ? "#F59E0B"
            : "#22C55E";

      if (prosumerIndex === 0) {
        // First prosumer connects to phase
        edges.push({
          id: `${phaseId}-${prosumer.id}`,
          source: phaseId,
          target: prosumer.id,
          style: {
            stroke: edgeColor,
            strokeWidth: 2,
          },
          animated: true,
          className: "electrical-phase",
        });
      } else {
        // Chain prosumers together
        const prevProsumer = sortedProsumers[prosumerIndex - 1];
        edges.push({
          id: `${prevProsumer.id}-${prosumer.id}`,
          source: prevProsumer.id,
          target: prosumer.id,
          style: {
            stroke: edgeColor,
            strokeWidth: 1.5,
          },
          animated: true,
          className: "electrical-prosumer",
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
// Inner Flow Component (needs to be inside ReactFlowProvider)
// ============================================================================

interface ViewOptions {
  showLegend: boolean;
  showMinimap: boolean;
  showStats: boolean;
  snapToGrid: boolean;
}

function FlowContent({
  topology,
  onNodeSelect,
  layout,
  setLayout,
  viewOptions,
  setViewOptions,
}: {
  topology: TopologyData;
  onNodeSelect?: (nodeId: string | null) => void;
  layout: LayoutDirection;
  setLayout: (layout: LayoutDirection) => void;
  viewOptions: ViewOptions;
  setViewOptions: (options: ViewOptions) => void;
}) {
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);
  const { fitView } = useReactFlow();

  // Update nodes and edges when topology or layout changes
  useEffect(() => {
    if (topology) {
      const { nodes: newNodes, edges: newEdges } = createNodesAndEdges(topology, layout);
      setNodes(newNodes);
      setEdges(newEdges);
      // Fit view after layout change
      setTimeout(() => fitView({ padding: 0.2, duration: 300 }), 50);
    }
  }, [topology, layout, setNodes, setEdges, fitView]);

  const onNodeClick = useCallback(
    (_: React.MouseEvent, node: Node) => {
      // Only select prosumer nodes
      if (node.type === "prosumer") {
        onNodeSelect?.(node.id);
      }
    },
    [onNodeSelect]
  );

  // Auto fit handler
  const handleFitView = useCallback(() => {
    fitView({ padding: 0.2, duration: 300 });
  }, [fitView]);

  // Auto-layout handler - reset nodes to default positions
  const handleAutoLayout = useCallback(() => {
    if (topology) {
      const { nodes: newNodes, edges: newEdges } = createNodesAndEdges(topology, layout);
      setNodes(newNodes);
      setEdges(newEdges);
      setTimeout(() => fitView({ padding: 0.2, duration: 300 }), 50);
    }
  }, [topology, layout, setNodes, setEdges, fitView]);

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
      <div className="absolute bottom-2 sm:bottom-4 left-2 sm:left-4 bg-white/90 backdrop-blur-sm rounded-lg shadow-lg p-2 sm:p-3 z-10 max-w-[140px] sm:max-w-none">
        <h4 className="text-[10px] sm:text-xs font-bold text-gray-700 mb-1.5 sm:mb-2">Legend</h4>
        <div className="space-y-1 sm:space-y-1.5">
          <div className="flex items-center text-[10px] sm:text-xs">
            <Zap className="w-3 h-3 sm:w-4 sm:h-4 text-[#74045F] mr-1.5 sm:mr-2" />
            <span className="text-gray-600">Transformer</span>
          </div>
          <div className="flex items-center text-[10px] sm:text-xs">
            <div className="w-3 h-3 sm:w-4 sm:h-4 rounded bg-red-100 border border-red-400 mr-1.5 sm:mr-2" />
            <span className="text-gray-600">Phase A</span>
          </div>
          <div className="flex items-center text-[10px] sm:text-xs">
            <div className="w-3 h-3 sm:w-4 sm:h-4 rounded bg-yellow-100 border border-yellow-400 mr-1.5 sm:mr-2" />
            <span className="text-gray-600">Phase B</span>
          </div>
          <div className="flex items-center text-[10px] sm:text-xs">
            <div className="w-3 h-3 sm:w-4 sm:h-4 rounded bg-blue-100 border border-blue-400 mr-1.5 sm:mr-2" />
            <span className="text-gray-600">Phase C</span>
          </div>
          <div className="border-t border-gray-200 my-1.5 sm:my-2" />
          <div className="flex items-center text-[10px] sm:text-xs">
            <Home className="w-3 h-3 sm:w-4 sm:h-4 text-gray-600 mr-1.5 sm:mr-2" />
            <span className="text-gray-600">Prosumer</span>
          </div>
          <div className="flex items-center text-[10px] sm:text-xs flex-wrap gap-1">
            <Sun className="w-2.5 h-2.5 sm:w-3 sm:h-3 text-amber-500" />
            <span className="text-gray-500">PV</span>
            <Car className="w-2.5 h-2.5 sm:w-3 sm:h-3 text-blue-500" />
            <span className="text-gray-500">EV</span>
            <Battery className="w-2.5 h-2.5 sm:w-3 sm:h-3 text-green-500" />
            <span className="text-gray-500">Batt</span>
          </div>
          <div className="border-t border-gray-200 my-1.5 sm:my-2" />
          <div className="flex items-center text-[10px] sm:text-xs">
            <div className="w-2.5 h-2.5 sm:w-3 sm:h-3 rounded-full bg-green-500 mr-1.5 sm:mr-2" />
            <span className="text-gray-600">Normal</span>
          </div>
          <div className="flex items-center text-[10px] sm:text-xs">
            <div className="w-2.5 h-2.5 sm:w-3 sm:h-3 rounded-full bg-amber-500 mr-1.5 sm:mr-2" />
            <span className="text-gray-600">Warning</span>
          </div>
          <div className="flex items-center text-[10px] sm:text-xs">
            <div className="w-2.5 h-2.5 sm:w-3 sm:h-3 rounded-full bg-red-500 mr-1.5 sm:mr-2" />
            <span className="text-gray-600">Critical</span>
          </div>
        </div>
      </div>
    ),
    []
  );

  // Snap all nodes to grid
  const snapNodesToGrid = useCallback(() => {
    const gridSize = 20;
    setNodes((nds) =>
      nds.map((node) => ({
        ...node,
        position: {
          x: Math.round(node.position.x / gridSize) * gridSize,
          y: Math.round(node.position.y / gridSize) * gridSize,
        },
      }))
    );
  }, [setNodes]);

  // Toggle handler for view options
  const toggleOption = useCallback(
    (option: keyof ViewOptions) => {
      const newValue = !viewOptions[option];
      setViewOptions({ ...viewOptions, [option]: newValue });

      // When enabling snap-to-grid, snap all existing nodes to grid
      if (option === "snapToGrid" && newValue) {
        snapNodesToGrid();
      }
    },
    [viewOptions, setViewOptions, snapNodesToGrid]
  );

  // Toggle layout direction
  const toggleLayout = useCallback(() => {
    setLayout(layout === "horizontal" ? "vertical" : "horizontal");
  }, [layout, setLayout]);

  return (
    <>
      {/* Inject electrical flow animation styles */}
      <style>{electricalFlowStyles}</style>

      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={onNodeClick}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        snapToGrid={viewOptions.snapToGrid}
        snapGrid={[20, 20]}
        defaultEdgeOptions={{
          type: "smoothstep",
          style: { strokeWidth: 1.5 },
          animated: true,
        }}
      >
        <Background variant={BackgroundVariant.Dots} gap={20} size={1} color="#E5E7EB" />
        <Controls
          className="!bg-white !shadow-lg !rounded-lg !border !border-gray-200"
          showInteractive={false}
        />
        {viewOptions.showMinimap && (
          <MiniMap
            nodeColor={nodeColor}
            nodeStrokeWidth={3}
            className="!bg-white/80 !rounded-lg !shadow-lg !border !border-gray-200"
            maskColor="rgba(116, 4, 95, 0.1)"
          />
        )}

        {/* Custom Panel for Layout Controls - nodrag nopan to enable clicks */}
        <Panel position="top-left" className="!m-2">
          <div className="nodrag nopan bg-white/95 backdrop-blur-sm rounded-lg shadow-lg p-1.5 flex items-center gap-1.5">
            {/* Auto Fit Button */}
            <button
              type="button"
              onClick={handleFitView}
              className="flex items-center gap-1 px-2 py-1.5 text-xs font-medium bg-[#74045F] text-white rounded-md hover:bg-[#5a0349] transition-colors cursor-pointer"
              title="Fit to screen"
            >
              <Maximize className="w-3.5 h-3.5" />
              Fit
            </button>

            {/* Auto Layout Button */}
            <button
              type="button"
              onClick={handleAutoLayout}
              className="flex items-center gap-1 px-2 py-1.5 text-xs font-medium bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition-colors cursor-pointer"
              title="Reset to auto-layout (reorganize nodes)"
            >
              <LayoutGrid className="w-3.5 h-3.5" />
              Auto
            </button>

            {/* Layout Toggle - Single Button */}
            <button
              type="button"
              onClick={toggleLayout}
              className="flex items-center gap-1 px-2 py-1.5 text-xs font-medium bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition-colors cursor-pointer"
              title={`Switch to ${layout === "horizontal" ? "vertical" : "horizontal"} layout`}
            >
              <RotateCcw className="w-3.5 h-3.5" />
              {layout === "horizontal" ? "H" : "V"}
            </button>

            {/* Divider */}
            <div className="w-px h-5 bg-gray-300" />

            {/* Snap to Grid Toggle */}
            <button
              type="button"
              onClick={() => toggleOption("snapToGrid")}
              className={`p-1.5 rounded-md transition-colors cursor-pointer ${
                viewOptions.snapToGrid
                  ? "bg-[#74045F] text-white"
                  : "bg-gray-100 text-gray-500 hover:bg-gray-200"
              }`}
              title={viewOptions.snapToGrid ? "Disable snap to grid" : "Enable snap to grid"}
            >
              <Grid3X3 className="w-4 h-4" />
            </button>

            {/* Divider */}
            <div className="w-px h-5 bg-gray-300" />

            {/* Compact View Toggles */}
            <button
              type="button"
              onClick={() => toggleOption("showLegend")}
              className={`p-1.5 rounded-md transition-colors cursor-pointer ${
                viewOptions.showLegend
                  ? "bg-[#74045F] text-white"
                  : "bg-gray-100 text-gray-500 hover:bg-gray-200"
              }`}
              title={viewOptions.showLegend ? "Hide legend" : "Show legend"}
            >
              <List className="w-4 h-4" />
            </button>

            <button
              type="button"
              onClick={() => toggleOption("showMinimap")}
              className={`p-1.5 rounded-md transition-colors cursor-pointer ${
                viewOptions.showMinimap
                  ? "bg-[#74045F] text-white"
                  : "bg-gray-100 text-gray-500 hover:bg-gray-200"
              }`}
              title={viewOptions.showMinimap ? "Hide minimap" : "Show minimap"}
            >
              <MapIcon className="w-4 h-4" />
            </button>

            <button
              type="button"
              onClick={() => toggleOption("showStats")}
              className={`p-1.5 rounded-md transition-colors cursor-pointer ${
                viewOptions.showStats
                  ? "bg-[#74045F] text-white"
                  : "bg-gray-100 text-gray-500 hover:bg-gray-200"
              }`}
              title={viewOptions.showStats ? "Hide stats" : "Show stats"}
            >
              <Info className="w-4 h-4" />
            </button>
          </div>
        </Panel>
      </ReactFlow>

      {/* Legend - toggleable */}
      {viewOptions.showLegend && Legend}

      {/* Stats overlay - toggleable */}
      {viewOptions.showStats && (
        <div className="absolute top-12 sm:top-4 right-2 sm:right-4 bg-white/95 backdrop-blur-sm rounded-lg shadow-lg p-2 sm:p-3 z-10 max-w-[130px] sm:max-w-none">
          <h4 className="text-[10px] sm:text-xs font-bold text-gray-700 mb-1.5 sm:mb-2">Status</h4>
          <div className="grid grid-cols-2 gap-1.5 sm:gap-2 text-[10px] sm:text-xs">
            <div>
              <span className="text-gray-500">Prosumers:</span>{" "}
              <span className="font-semibold">{topology.summary.total_prosumers}</span>
            </div>
            <div>
              <span className="text-gray-500">PV:</span>{" "}
              <span className="font-semibold text-amber-600">
                {topology.summary.prosumers_with_pv}
              </span>
            </div>
            <div>
              <span className="text-gray-500">Avg:</span>{" "}
              <span className="font-semibold">
                {topology.summary.voltage_stats.avg_voltage?.toFixed(1) || "--"}V
              </span>
            </div>
            <div>
              <span className="text-gray-500">Crit:</span>{" "}
              <span className="font-semibold text-red-600">
                {topology.summary.voltage_stats.critical_count}
              </span>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

// ============================================================================
// Main Component
// ============================================================================

// Storage key for persistent preferences
const STORAGE_KEY = "pea-network-graph-preferences";

interface StoredPreferences {
  layout: LayoutDirection;
  viewOptions: ViewOptions;
}

function loadPreferences(): StoredPreferences {
  if (typeof window === "undefined") {
    return {
      layout: "horizontal",
      viewOptions: { showLegend: true, showMinimap: true, showStats: true, snapToGrid: false },
    };
  }
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      return JSON.parse(stored);
    }
  } catch {
    // Ignore parse errors
  }
  return {
    layout: "horizontal",
    viewOptions: { showLegend: true, showMinimap: true, showStats: true, snapToGrid: false },
  };
}

function savePreferences(prefs: StoredPreferences): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(prefs));
  } catch {
    // Ignore storage errors
  }
}

export default function NetworkGraphView({ topology, onNodeSelect }: NetworkGraphViewProps) {
  const [layout, setLayout] = useState<LayoutDirection>(() => loadPreferences().layout);
  const [viewOptions, setViewOptions] = useState<ViewOptions>(() => loadPreferences().viewOptions);

  // Persist preferences when they change
  useEffect(() => {
    savePreferences({ layout, viewOptions });
  }, [layout, viewOptions]);

  // Show loading state if no topology
  if (!topology) {
    return (
      <div className="relative w-full h-[400px] sm:h-[600px] rounded-lg overflow-hidden border border-gray-200 bg-gray-50 flex items-center justify-center">
        <div className="text-gray-400 flex items-center text-sm">
          <AlertTriangle className="w-4 h-4 sm:w-5 sm:h-5 mr-2" />
          No topology data available
        </div>
      </div>
    );
  }

  return (
    <div className="relative w-full h-[400px] sm:h-[600px] rounded-lg overflow-hidden border border-gray-200">
      <ReactFlowProvider>
        <FlowContent
          topology={topology}
          onNodeSelect={onNodeSelect}
          layout={layout}
          setLayout={setLayout}
          viewOptions={viewOptions}
          setViewOptions={setViewOptions}
        />
      </ReactFlowProvider>
    </div>
  );
}
