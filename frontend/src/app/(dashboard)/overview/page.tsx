"use client";

import { Activity, AlertTriangle, Sun, Zap } from "lucide-react";
import dynamic from "next/dynamic";
import { useEffect, useState } from "react";

import { HelpTrigger } from "@/components/help";
import { ErrorBoundary } from "@/components/ui";
import { getApiBaseUrl } from "@/lib/api";

const SolarForecastChart = dynamic(
  () => import("@/components/charts").then((mod) => ({ default: mod.SolarForecastChart })),
  {
    loading: () => <ChartSkeleton />,
    ssr: false,
  }
);

const VoltageMonitorChart = dynamic(
  () => import("@/components/charts").then((mod) => ({ default: mod.VoltageMonitorChart })),
  {
    loading: () => <ChartSkeleton />,
    ssr: false,
  }
);

const ModelPerformance = dynamic(
  () => import("@/components/dashboard").then((mod) => ({ default: mod.ModelPerformance })),
  { loading: () => <DashboardSkeleton /> }
);

function ChartSkeleton() {
  return (
    <div className="bg-white rounded-lg shadow p-4 animate-pulse">
      <div className="h-6 w-1/3 bg-gray-200 rounded mb-4" />
      <div className="h-[200px] bg-gray-100 rounded" />
    </div>
  );
}

function DashboardSkeleton() {
  return (
    <div className="bg-white rounded-lg shadow p-4 animate-pulse">
      <div className="h-6 w-1/4 bg-gray-200 rounded mb-4" />
      <div className="h-[180px] bg-gray-100 rounded" />
    </div>
  );
}

interface HealthStatus {
  status: string;
  timestamp: string;
  service: string;
}

export default function OverviewPage() {
  const [health, setHealth] = useState<HealthStatus | null>(null);

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const response = await fetch(`${getApiBaseUrl()}/api/v1/health`);
        const data = await response.json();
        setHealth(data);
      } catch {
        setHealth(null);
      }
    };

    checkHealth();
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <ErrorBoundary>
      {/* Summary Cards - 2x2 on mobile, 4 on desktop */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-2 sm:gap-4 mb-4 sm:mb-6">
        <div className="bg-white rounded-lg shadow p-3 sm:p-4 border-l-4 border-[#C7911B]">
          <div className="flex items-center justify-between">
            <div className="min-w-0 flex-1">
              <p className="text-gray-500 text-xs sm:text-sm truncate flex items-center gap-1">
                Solar Output
                <HelpTrigger sectionId="solar-output-card" size="sm" variant="subtle" />
              </p>
              <p className="text-lg sm:text-2xl font-bold text-gray-800">3,542 kW</p>
              <p className="text-[10px] sm:text-xs text-green-600">+12% from avg</p>
            </div>
            <Sun className="w-8 h-8 sm:w-10 sm:h-10 text-[#C7911B] opacity-80 flex-shrink-0" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-3 sm:p-4 border-l-4 border-[#74045F]">
          <div className="flex items-center justify-between">
            <div className="min-w-0 flex-1">
              <p className="text-gray-500 text-xs sm:text-sm truncate flex items-center gap-1">
                Avg Voltage
                <HelpTrigger sectionId="voltage-card" size="sm" variant="subtle" />
              </p>
              <p className="text-lg sm:text-2xl font-bold text-gray-800">228.5 V</p>
              <p className="text-[10px] sm:text-xs text-gray-500">7 prosumers</p>
            </div>
            <Zap className="w-8 h-8 sm:w-10 sm:h-10 text-[#74045F] opacity-80 flex-shrink-0" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-3 sm:p-4 border-l-4 border-red-500">
          <div className="flex items-center justify-between">
            <div className="min-w-0 flex-1">
              <p className="text-gray-500 text-xs sm:text-sm truncate flex items-center gap-1">
                Active Alerts
                <HelpTrigger sectionId="alerts-card" size="sm" variant="subtle" />
              </p>
              <p className="text-lg sm:text-2xl font-bold text-gray-800">0</p>
              <p className="text-[10px] sm:text-xs text-green-600">All normal</p>
            </div>
            <AlertTriangle className="w-8 h-8 sm:w-10 sm:h-10 text-red-500 opacity-80 flex-shrink-0" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-3 sm:p-4 border-l-4 border-green-500">
          <div className="flex items-center justify-between">
            <div className="min-w-0 flex-1">
              <p className="text-gray-500 text-xs sm:text-sm truncate flex items-center gap-1">
                System Status
                <HelpTrigger sectionId="system-status-card" size="sm" variant="subtle" />
              </p>
              <p className="text-lg sm:text-2xl font-bold text-gray-800">
                {health ? "Online" : "Offline"}
              </p>
              <p className="text-[10px] sm:text-xs text-gray-500 truncate">
                {health?.timestamp
                  ? new Date(health.timestamp).toLocaleTimeString()
                  : "Not connected"}
              </p>
            </div>
            <Activity className="w-8 h-8 sm:w-10 sm:h-10 text-green-500 opacity-80 flex-shrink-0" />
          </div>
        </div>
      </div>

      {/* Charts Grid - Stack on mobile */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
        <SolarForecastChart height={240} />
        <VoltageMonitorChart height={240} />
      </div>

      {/* Model Performance */}
      <div className="mt-4 sm:mt-6">
        <ModelPerformance height={220} />
      </div>
    </ErrorBoundary>
  );
}
