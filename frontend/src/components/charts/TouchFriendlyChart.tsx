"use client";

import { type ReactNode, type TouchEvent, useCallback, useRef, useState } from "react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { cn } from "@/lib/utils";

/**
 * Touch-Friendly Chart Wrapper
 * Provides pinch-to-zoom and swipe gestures for mobile chart interactions.
 * Part of v1.1.0 Mobile-Responsive Dashboard (PWA) feature.
 */

interface TouchFriendlyChartProps {
  children: ReactNode;
  className?: string;
  height?: number;
  allowZoom?: boolean;
  allowPan?: boolean;
}

export function TouchFriendlyChart({
  children,
  className,
  height = 300,
  allowZoom = true,
  allowPan = true,
}: TouchFriendlyChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [scale, setScale] = useState(1);
  const [translateX, setTranslateX] = useState(0);
  const [isPinching, setIsPinching] = useState(false);
  const [isPanning, setIsPanning] = useState(false);
  const lastTouchRef = useRef<{ x: number; y: number } | null>(null);
  const lastPinchRef = useRef<number | null>(null);

  const handleTouchStart = useCallback(
    (e: TouchEvent) => {
      if (e.touches.length === 2 && allowZoom) {
        const touch1 = e.touches[0];
        const touch2 = e.touches[1];
        const distance = Math.hypot(
          touch2.clientX - touch1.clientX,
          touch2.clientY - touch1.clientY
        );
        lastPinchRef.current = distance;
        setIsPinching(true);
      } else if (e.touches.length === 1 && allowPan) {
        lastTouchRef.current = {
          x: e.touches[0].clientX,
          y: e.touches[0].clientY,
        };
        setIsPanning(true);
      }
    },
    [allowZoom, allowPan]
  );

  const handleTouchMove = useCallback(
    (e: TouchEvent) => {
      if (isPinching && e.touches.length === 2) {
        const touch1 = e.touches[0];
        const touch2 = e.touches[1];
        const distance = Math.hypot(
          touch2.clientX - touch1.clientX,
          touch2.clientY - touch1.clientY
        );

        if (lastPinchRef.current) {
          const scaleChange = distance / lastPinchRef.current;
          setScale((prev) => Math.min(Math.max(prev * scaleChange, 0.5), 3));
        }
        lastPinchRef.current = distance;
      } else if (isPanning && e.touches.length === 1 && lastTouchRef.current) {
        const deltaX = e.touches[0].clientX - lastTouchRef.current.x;
        setTranslateX((prev) => prev + deltaX);
        lastTouchRef.current = {
          x: e.touches[0].clientX,
          y: e.touches[0].clientY,
        };
      }
    },
    [isPinching, isPanning]
  );

  const handleTouchEnd = useCallback(() => {
    setIsPinching(false);
    setIsPanning(false);
    lastTouchRef.current = null;
    lastPinchRef.current = null;
  }, []);

  const handleReset = useCallback(() => {
    setScale(1);
    setTranslateX(0);
  }, []);

  return (
    <div className={cn("relative", className)}>
      {(scale !== 1 || translateX !== 0) && (
        <button
          type="button"
          onClick={handleReset}
          className="absolute top-2 right-2 z-10 px-2 py-1 text-xs bg-white/90 border border-gray-200 rounded-md shadow-sm hover:bg-gray-50"
        >
          Reset
        </button>
      )}

      <div
        ref={containerRef}
        className="touch-pan-y"
        onTouchStart={handleTouchStart}
        onTouchMove={handleTouchMove}
        onTouchEnd={handleTouchEnd}
        style={{
          transform: `scale(${scale}) translateX(${translateX}px)`,
          transformOrigin: "center center",
          transition: isPinching || isPanning ? "none" : "transform 0.2s ease-out",
        }}
      >
        <ResponsiveContainer width="100%" height={height}>
          {children as React.ReactElement}
        </ResponsiveContainer>
      </div>

      <p className="text-xs text-gray-400 text-center mt-2 lg:hidden">
        Pinch to zoom • Swipe to pan
      </p>
    </div>
  );
}

/**
 * Custom Mobile-Friendly Tooltip
 */
interface TooltipPayloadItem {
  name?: string;
  value?: number | string;
  color?: string;
}

interface MobileTooltipProps {
  active?: boolean;
  payload?: TooltipPayloadItem[];
  label?: string;
  labelFormatter?: (value: string) => string;
}

export function MobileTooltip({ active, payload, label, labelFormatter }: MobileTooltipProps) {
  if (!active || !payload || !payload.length) {
    return null;
  }

  return (
    <div className="bg-white/95 backdrop-blur-sm border border-gray-200 rounded-lg shadow-lg p-3 min-w-[140px]">
      <p className="text-sm font-medium text-gray-900 mb-2">
        {labelFormatter ? labelFormatter(label ?? "") : label}
      </p>
      {payload.map((entry: TooltipPayloadItem) => (
        <div
          key={entry.name ?? entry.value}
          className="flex items-center justify-between gap-4 text-sm"
        >
          <span className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full" style={{ backgroundColor: entry.color }} />
            <span className="text-gray-600">{entry.name}</span>
          </span>
          <span className="font-medium text-gray-900">
            {typeof entry.value === "number" ? entry.value.toLocaleString("th-TH") : entry.value}
          </span>
        </div>
      ))}
    </div>
  );
}

/**
 * Pre-configured Solar Power Chart
 */
interface SolarChartData {
  time: string;
  predicted: number;
  actual?: number;
  upper?: number;
  lower?: number;
}

interface SolarChartProps {
  data: SolarChartData[];
  height?: number;
  showConfidence?: boolean;
}

export function SolarPowerChart({ data, height = 300, showConfidence = true }: SolarChartProps) {
  return (
    <TouchFriendlyChart height={height}>
      <AreaChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
        <defs>
          <linearGradient id="colorPredicted" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.3} />
            <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
          </linearGradient>
          <linearGradient id="colorActual" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#22c55e" stopOpacity={0.3} />
            <stop offset="95%" stopColor="#22c55e" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
        <XAxis
          dataKey="time"
          tick={{ fontSize: 11 }}
          tickLine={false}
          axisLine={{ stroke: "#e5e7eb" }}
        />
        <YAxis
          tick={{ fontSize: 11 }}
          tickLine={false}
          axisLine={{ stroke: "#e5e7eb" }}
          tickFormatter={(value: number) => `${value} kW`}
        />
        <Tooltip content={<MobileTooltip />} />
        <Legend wrapperStyle={{ fontSize: "12px" }} iconType="circle" iconSize={8} />
        {showConfidence && (
          <Area
            type="monotone"
            dataKey="upper"
            stroke="transparent"
            fill="#8b5cf6"
            fillOpacity={0.1}
            name="Upper Bound"
          />
        )}
        <Area
          type="monotone"
          dataKey="predicted"
          stroke="#8b5cf6"
          strokeWidth={2}
          fill="url(#colorPredicted)"
          name="Predicted"
        />
        {data.some((d) => d.actual !== undefined) && (
          <Area
            type="monotone"
            dataKey="actual"
            stroke="#22c55e"
            strokeWidth={2}
            fill="url(#colorActual)"
            name="Actual"
          />
        )}
      </AreaChart>
    </TouchFriendlyChart>
  );
}

/**
 * Pre-configured Voltage Chart
 */
interface VoltageChartData {
  prosumer: string;
  voltage: number;
  status: "normal" | "warning" | "critical";
}

interface VoltageChartProps {
  data: VoltageChartData[];
  height?: number;
}

export function VoltageBarChart({ data, height = 300 }: VoltageChartProps) {
  const getBarColor = (status: string) => {
    switch (status) {
      case "critical":
        return "#ef4444";
      case "warning":
        return "#f59e0b";
      default:
        return "#22c55e";
    }
  };

  return (
    <TouchFriendlyChart height={height}>
      <BarChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" vertical={false} />
        <XAxis
          dataKey="prosumer"
          tick={{ fontSize: 11 }}
          tickLine={false}
          axisLine={{ stroke: "#e5e7eb" }}
        />
        <YAxis
          domain={[210, 250]}
          tick={{ fontSize: 11 }}
          tickLine={false}
          axisLine={{ stroke: "#e5e7eb" }}
          tickFormatter={(value: number) => `${value}V`}
        />
        <Tooltip content={<MobileTooltip />} />
        <Bar dataKey="voltage" radius={[4, 4, 0, 0]} name="Voltage">
          {data.map((entry) => (
            <Cell key={`cell-${entry.prosumer}`} fill={getBarColor(entry.status)} />
          ))}
        </Bar>
      </BarChart>
    </TouchFriendlyChart>
  );
}
