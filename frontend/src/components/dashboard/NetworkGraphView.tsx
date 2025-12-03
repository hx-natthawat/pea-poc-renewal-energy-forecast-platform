"use client";

import {
  AlertTriangle,
  Battery,
  Building2,
  Car,
  Cloud,
  Factory,
  Home,
  Radio,
  Server,
  Sun,
  Wind,
  Zap,
} from "lucide-react";
import { useCallback, useMemo, useState } from "react";
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

// Node data interfaces - with index signature for ReactFlow compatibility
interface RouterNodeData extends Record<string, unknown> {
  label: string;
  status: "normal" | "warning" | "critical";
  connections: number;
}

interface DeviceNodeData extends Record<string, unknown> {
  label: string;
  type: "ev_station" | "solar" | "house_solar" | "house_solar_ev" | "factory" | "wind" | "battery";
  status: "normal" | "warning" | "critical" | "offline";
  voltage?: number;
  power?: number;
}

interface BrokerNodeData extends Record<string, unknown> {
  label: string;
  status: "online" | "offline";
  connectedDevices: number;
}

// Status colors following PEA brand
const STATUS_COLORS = {
  normal: { bg: "#22C55E", border: "#16A34A", text: "#FFFFFF" },
  warning: { bg: "#F59E0B", border: "#D97706", text: "#FFFFFF" },
  critical: { bg: "#EF4444", border: "#DC2626", text: "#FFFFFF" },
  offline: { bg: "#9CA3AF", border: "#6B7280", text: "#FFFFFF" },
  online: { bg: "#22C55E", border: "#16A34A", text: "#FFFFFF" },
};

// PEA Brand Colors
const PEA_PURPLE = "#74045F";
const PEA_GOLD = "#C7911B";

// Custom Router Node Component
function RouterNode({ data }: NodeProps<Node<RouterNodeData>>) {
  const statusColor = STATUS_COLORS[data.status];

  return (
    <div className="relative group">
      <Handle type="target" position={Position.Top} className="!bg-gray-400 !w-2 !h-2" />
      <Handle type="target" position={Position.Left} className="!bg-gray-400 !w-2 !h-2" />

      <div
        className="flex flex-col items-center justify-center p-2 rounded-xl shadow-lg transition-transform hover:scale-105"
        style={{
          backgroundColor: "#E0F2FE",
          border: `2px solid #0EA5E9`,
          minWidth: "60px",
        }}
      >
        <div className="relative">
          <Cloud className="w-8 h-8 text-sky-500" />
          <Zap className="w-4 h-4 text-sky-600 absolute -bottom-1 -right-1" />
        </div>
        <span className="text-xs font-bold text-sky-800 mt-1">{data.label}</span>

        {/* Status indicator */}
        {data.status !== "normal" && (
          <div
            className="absolute -top-1 -right-1 w-3 h-3 rounded-full animate-pulse"
            style={{ backgroundColor: statusColor.bg }}
          />
        )}
      </div>

      <Handle type="source" position={Position.Bottom} className="!bg-gray-400 !w-2 !h-2" />
      <Handle type="source" position={Position.Right} className="!bg-gray-400 !w-2 !h-2" />

      {/* Tooltip on hover */}
      <div className="absolute -bottom-12 left-1/2 -translate-x-1/2 bg-gray-800 text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-10">
        Connections: {data.connections} | Status: {data.status}
      </div>
    </div>
  );
}

// Custom Device Node Component
function DeviceNode({ data }: NodeProps<Node<DeviceNodeData>>) {
  const statusColor = STATUS_COLORS[data.status];

  const getDeviceIcon = () => {
    switch (data.type) {
      case "ev_station":
        return (
          <div className="flex flex-col items-center">
            <div className="bg-blue-100 p-2 rounded-lg mb-1">
              <Zap className="w-6 h-6 text-blue-600" />
            </div>
            <Car className="w-8 h-8 text-amber-500" />
          </div>
        );
      case "solar":
        return (
          <div className="bg-amber-50 p-3 rounded-lg">
            <Sun className="w-10 h-10 text-amber-500" />
          </div>
        );
      case "house_solar":
        return (
          <div className="relative">
            <Home className="w-12 h-12 text-amber-600" />
            <Sun className="w-5 h-5 text-amber-400 absolute -top-1 -right-1" />
          </div>
        );
      case "house_solar_ev":
        return (
          <div className="relative">
            <Home className="w-12 h-12 text-amber-600" />
            <Sun className="w-5 h-5 text-amber-400 absolute -top-1 -right-1" />
            <Car className="w-5 h-5 text-blue-500 absolute -bottom-1 -right-1" />
          </div>
        );
      case "factory":
        return (
          <div className="relative">
            <Factory className="w-12 h-12 text-gray-600" />
            <Sun className="w-5 h-5 text-amber-400 absolute -top-1 -right-1" />
          </div>
        );
      case "wind":
        return (
          <div className="bg-sky-50 p-3 rounded-lg">
            <Wind className="w-10 h-10 text-sky-500" />
          </div>
        );
      case "battery":
        return (
          <div className="bg-green-50 p-3 rounded-lg">
            <Battery className="w-10 h-10 text-green-500" />
          </div>
        );
      default:
        return <Home className="w-10 h-10 text-gray-500" />;
    }
  };

  return (
    <div className="relative group">
      <Handle type="target" position={Position.Top} className="!bg-gray-400 !w-2 !h-2" />

      <div
        className="flex flex-col items-center p-3 rounded-xl shadow-lg bg-white transition-transform hover:scale-105"
        style={{ border: `2px solid ${statusColor.border}` }}
      >
        {/* Cloud icon at top */}
        <div className="absolute -top-3 left-1/2 -translate-x-1/2">
          <Cloud className="w-6 h-6 text-sky-400" />
        </div>

        {/* Device icon */}
        {getDeviceIcon()}

        {/* Label */}
        <span className="text-xs font-bold text-gray-700 mt-2">{data.label}</span>

        {/* Voltage/Power display */}
        {data.voltage !== undefined && (
          <span className="text-[10px] text-gray-500">
            {data.voltage.toFixed(1)}V
          </span>
        )}

        {/* Status indicator */}
        <div
          className="absolute -top-1 -right-1 w-3 h-3 rounded-full"
          style={{ backgroundColor: statusColor.bg }}
        />
      </div>

      {/* Tooltip */}
      <div className="absolute -bottom-14 left-1/2 -translate-x-1/2 bg-gray-800 text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-10">
        {data.label} | {data.status}
        {data.power !== undefined && ` | ${data.power.toFixed(1)} kW`}
      </div>
    </div>
  );
}

// Custom Broker Node Component
function BrokerNode({ data }: NodeProps<Node<BrokerNodeData>>) {
  return (
    <div className="relative group">
      <Handle type="target" position={Position.Left} className="!bg-gray-400 !w-3 !h-3" />

      <div
        className="flex flex-col items-center p-4 rounded-xl shadow-xl transition-transform hover:scale-105"
        style={{
          backgroundColor: "#FEF3C7",
          border: `3px solid ${PEA_GOLD}`,
          minWidth: "120px",
        }}
      >
        {/* Antenna */}
        <Radio className="w-6 h-6 text-gray-600 absolute -top-5" />

        {/* Building */}
        <div className="relative">
          <Building2 className="w-16 h-16 text-gray-700" />
          <Server className="w-5 h-5 text-blue-500 absolute bottom-2 right-2" />
        </div>

        <span className="text-sm font-bold text-gray-800 mt-2">{data.label}</span>
        <span className="text-xs text-gray-500">
          {data.connectedDevices} devices
        </span>

        {/* Status indicator */}
        <div
          className={`absolute -top-1 -right-1 w-4 h-4 rounded-full ${
            data.status === "online" ? "bg-green-500 animate-pulse" : "bg-gray-400"
          }`}
        />
      </div>
    </div>
  );
}

// Node types registration
const nodeTypes = {
  router: RouterNode,
  device: DeviceNode,
  broker: BrokerNode,
};

// Initial nodes and edges based on the provided diagram
const createInitialNodes = (): Node[] => [
  // Broker node
  {
    id: "broker",
    type: "broker",
    position: { x: 900, y: 50 },
    data: { label: "The Broker", status: "online", connectedDevices: 7 },
  },

  // Router nodes (R1-R17)
  { id: "R1", type: "router", position: { x: 450, y: 450 }, data: { label: "R1", status: "critical", connections: 4 } },
  { id: "R2", type: "router", position: { x: 450, y: 300 }, data: { label: "R2", status: "normal", connections: 3 } },
  { id: "R3", type: "router", position: { x: 550, y: 370 }, data: { label: "R3", status: "normal", connections: 3 } },
  { id: "R4", type: "router", position: { x: 500, y: 150 }, data: { label: "R4", status: "normal", connections: 3 } },
  { id: "R5", type: "router", position: { x: 650, y: 220 }, data: { label: "R5", status: "critical", connections: 2 } },
  { id: "R6", type: "router", position: { x: 780, y: 220 }, data: { label: "R6", status: "critical", connections: 3 } },
  { id: "R7", type: "router", position: { x: 700, y: 370 }, data: { label: "R7", status: "normal", connections: 3 } },
  { id: "R8", type: "router", position: { x: 780, y: 450 }, data: { label: "R8", status: "critical", connections: 2 } },
  { id: "R9", type: "router", position: { x: 600, y: 520 }, data: { label: "R9", status: "normal", connections: 3 } },
  { id: "R10", type: "router", position: { x: 350, y: 200 }, data: { label: "R10", status: "normal", connections: 2 } },
  { id: "R11", type: "router", position: { x: 280, y: 300 }, data: { label: "R11", status: "critical", connections: 2 } },
  { id: "R12", type: "router", position: { x: 450, y: 580 }, data: { label: "R12", status: "critical", connections: 2 } },
  { id: "R13", type: "router", position: { x: 880, y: 350 }, data: { label: "R13", status: "critical", connections: 2 } },
  { id: "R14", type: "router", position: { x: 320, y: 420 }, data: { label: "R14", status: "critical", connections: 2 } },
  { id: "R15", type: "router", position: { x: 200, y: 350 }, data: { label: "R15", status: "normal", connections: 2 } },
  { id: "R16", type: "router", position: { x: 350, y: 520 }, data: { label: "R16", status: "normal", connections: 2 } },
  { id: "R17", type: "router", position: { x: 350, y: 340 }, data: { label: "R17", status: "normal", connections: 2 } },

  // Device nodes (D1-D7)
  { id: "D1", type: "device", position: { x: 480, y: 30 }, data: { label: "D1", type: "ev_station", status: "normal", voltage: 230.5, power: 7.2 } },
  { id: "D2", type: "device", position: { x: 650, y: 580 }, data: { label: "D2", type: "solar", status: "normal", voltage: 229.8, power: 5.5 } },
  { id: "D3", type: "device", position: { x: 280, y: 120 }, data: { label: "D3", type: "house_solar_ev", status: "warning", voltage: 235.2, power: 3.8 } },
  { id: "D4", type: "device", position: { x: 920, y: 280 }, data: { label: "D4", type: "factory", status: "normal", voltage: 228.9, power: 45.0 } },
  { id: "D5", type: "device", position: { x: 100, y: 280 }, data: { label: "D5", type: "house_solar", status: "normal", voltage: 231.2, power: 2.5 } },
  { id: "D6", type: "device", position: { x: 250, y: 580 }, data: { label: "D6", type: "wind", status: "normal", voltage: 230.0, power: 15.0 } },
  { id: "D7", type: "device", position: { x: 350, y: 280 }, data: { label: "D7", type: "house_solar", status: "normal", voltage: 229.5, power: 2.8 } },
];

const createInitialEdges = (): Edge[] => [
  // Broker connections
  { id: "broker-R4", source: "R4", target: "broker", animated: true, style: { stroke: "#22C55E", strokeWidth: 2 } },
  { id: "broker-R5", source: "R5", target: "broker", animated: true, style: { stroke: "#22C55E", strokeWidth: 2 } },
  { id: "broker-R6", source: "R6", target: "broker", animated: true, style: { stroke: "#22C55E", strokeWidth: 2 } },

  // Router interconnections
  { id: "R1-R2", source: "R1", target: "R2", style: { stroke: "#94A3B8" } },
  { id: "R1-R3", source: "R1", target: "R3", style: { stroke: "#94A3B8" } },
  { id: "R1-R9", source: "R1", target: "R9", style: { stroke: "#94A3B8" } },
  { id: "R1-R14", source: "R1", target: "R14", style: { stroke: "#94A3B8" } },
  { id: "R2-R3", source: "R2", target: "R3", style: { stroke: "#94A3B8" } },
  { id: "R2-R4", source: "R2", target: "R4", style: { stroke: "#94A3B8" } },
  { id: "R2-R17", source: "R2", target: "R17", style: { stroke: "#94A3B8" } },
  { id: "R3-R7", source: "R3", target: "R7", style: { stroke: "#94A3B8" } },
  { id: "R3-R5", source: "R3", target: "R5", style: { stroke: "#94A3B8" } },
  { id: "R4-R5", source: "R4", target: "R5", style: { stroke: "#94A3B8" } },
  { id: "R4-R10", source: "R4", target: "R10", style: { stroke: "#94A3B8" } },
  { id: "R5-R6", source: "R5", target: "R6", style: { stroke: "#94A3B8" } },
  { id: "R6-R7", source: "R6", target: "R7", style: { stroke: "#94A3B8" } },
  { id: "R6-R13", source: "R6", target: "R13", style: { stroke: "#94A3B8" } },
  { id: "R7-R8", source: "R7", target: "R8", style: { stroke: "#94A3B8" } },
  { id: "R8-R9", source: "R8", target: "R9", style: { stroke: "#94A3B8" } },
  { id: "R8-R13", source: "R8", target: "R13", style: { stroke: "#94A3B8" } },
  { id: "R9-R12", source: "R9", target: "R12", style: { stroke: "#94A3B8" } },
  { id: "R10-R11", source: "R10", target: "R11", style: { stroke: "#94A3B8" } },
  { id: "R11-R15", source: "R11", target: "R15", style: { stroke: "#94A3B8" } },
  { id: "R11-R17", source: "R11", target: "R17", style: { stroke: "#94A3B8" } },
  { id: "R12-R16", source: "R12", target: "R16", style: { stroke: "#94A3B8" } },
  { id: "R14-R15", source: "R14", target: "R15", style: { stroke: "#94A3B8" } },
  { id: "R14-R16", source: "R14", target: "R16", style: { stroke: "#94A3B8" } },
  { id: "R14-R17", source: "R14", target: "R17", style: { stroke: "#94A3B8" } },

  // Device connections
  { id: "D1-R4", source: "D1", target: "R4", style: { stroke: "#94A3B8" } },
  { id: "D2-R9", source: "D2", target: "R9", style: { stroke: "#94A3B8" } },
  { id: "D3-R10", source: "D3", target: "R10", style: { stroke: "#94A3B8" } },
  { id: "D4-R13", source: "D4", target: "R13", style: { stroke: "#94A3B8" } },
  { id: "D5-R15", source: "D5", target: "R15", style: { stroke: "#94A3B8" } },
  { id: "D6-R16", source: "D6", target: "R16", style: { stroke: "#94A3B8" } },
  { id: "D7-R17", source: "D7", target: "R17", style: { stroke: "#94A3B8" } },
];

interface NetworkGraphViewProps {
  onNodeSelect?: (nodeId: string | null) => void;
}

export default function NetworkGraphView({ onNodeSelect }: NetworkGraphViewProps) {
  const [nodes, setNodes, onNodesChange] = useNodesState(createInitialNodes());
  const [edges, setEdges, onEdgesChange] = useEdgesState(createInitialEdges());
  const [selectedNode, setSelectedNode] = useState<string | null>(null);

  const onNodeClick = useCallback(
    (_: React.MouseEvent, node: Node) => {
      setSelectedNode(node.id === selectedNode ? null : node.id);
      onNodeSelect?.(node.id === selectedNode ? null : node.id);
    },
    [selectedNode, onNodeSelect]
  );

  // Custom minimap node color
  const nodeColor = useCallback((node: Node) => {
    if (node.type === "broker") return PEA_GOLD;
    if (node.type === "router") {
      const data = node.data as RouterNodeData;
      return data.status === "critical" ? "#EF4444" : data.status === "warning" ? "#F59E0B" : "#0EA5E9";
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
            <Cloud className="w-4 h-4 text-sky-500 mr-2" />
            <span className="text-gray-600">Router Node</span>
          </div>
          <div className="flex items-center text-xs">
            <Home className="w-4 h-4 text-amber-600 mr-2" />
            <span className="text-gray-600">Device/Prosumer</span>
          </div>
          <div className="flex items-center text-xs">
            <Building2 className="w-4 h-4 text-gray-700 mr-2" />
            <span className="text-gray-600">Broker/Data Center</span>
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

      {/* Selected node info panel */}
      {selectedNode && (
        <div className="absolute top-4 right-4 bg-white/95 backdrop-blur-sm rounded-lg shadow-lg p-4 z-10 min-w-[200px]">
          <h4 className="text-sm font-bold text-gray-800 mb-2 flex items-center">
            <AlertTriangle className="w-4 h-4 mr-2 text-[#74045F]" />
            Node Details
          </h4>
          <div className="space-y-1 text-xs">
            <p>
              <span className="text-gray-500">ID:</span>{" "}
              <span className="font-semibold">{selectedNode}</span>
            </p>
            {nodes.find((n) => n.id === selectedNode)?.data && (
              <>
                <p>
                  <span className="text-gray-500">Type:</span>{" "}
                  <span className="font-semibold capitalize">
                    {nodes.find((n) => n.id === selectedNode)?.type}
                  </span>
                </p>
                <p>
                  <span className="text-gray-500">Status:</span>{" "}
                  <span
                    className={`font-semibold ${
                      (nodes.find((n) => n.id === selectedNode)?.data as RouterNodeData | DeviceNodeData).status === "critical"
                        ? "text-red-600"
                        : (nodes.find((n) => n.id === selectedNode)?.data as RouterNodeData | DeviceNodeData).status === "warning"
                          ? "text-amber-600"
                          : "text-green-600"
                    }`}
                  >
                    {(nodes.find((n) => n.id === selectedNode)?.data as RouterNodeData | DeviceNodeData).status}
                  </span>
                </p>
              </>
            )}
          </div>
          <button
            type="button"
            onClick={() => {
              setSelectedNode(null);
              onNodeSelect?.(null);
            }}
            className="mt-3 w-full text-xs text-gray-500 hover:text-gray-700 underline"
          >
            Clear selection
          </button>
        </div>
      )}
    </div>
  );
}
