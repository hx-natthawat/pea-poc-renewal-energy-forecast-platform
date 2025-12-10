"use client";

import dynamic from "next/dynamic";

import { ErrorBoundary } from "@/components/ui";

const LoadForecastChart = dynamic(
  () => import("@/components/charts").then((mod) => ({ default: mod.LoadForecastChart })),
  {
    loading: () => <ChartSkeleton />,
    ssr: false,
  }
);

const DemandForecastChart = dynamic(
  () => import("@/components/charts").then((mod) => ({ default: mod.DemandForecastChart })),
  {
    loading: () => <ChartSkeleton />,
    ssr: false,
  }
);

const ImbalanceMonitor = dynamic(
  () => import("@/components/charts").then((mod) => ({ default: mod.ImbalanceMonitor })),
  {
    loading: () => <ChartSkeleton />,
    ssr: false,
  }
);

function ChartSkeleton() {
  return (
    <div className="bg-white rounded-lg shadow p-4 animate-pulse">
      <div className="h-6 w-1/3 bg-gray-200 rounded mb-4" />
      <div className="h-[200px] bg-gray-100 rounded" />
    </div>
  );
}

export default function GridPage() {
  return (
    <ErrorBoundary>
      <div className="space-y-4 sm:space-y-6">
        {/* TOR Functions Header */}
        <div className="bg-white rounded-lg shadow p-4">
          <h2 className="text-lg font-semibold text-gray-800 mb-2">
            Grid Operations - TOR Extended Functions
          </h2>
          <p className="text-sm text-gray-600">
            Load Forecast (7.5.1.3) | Demand Forecast (7.5.1.2) | Imbalance Forecast (7.5.1.4)
          </p>
        </div>

        {/* Load and Demand Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
          <LoadForecastChart height={260} level="system" />
          <DemandForecastChart height={260} />
        </div>

        {/* Imbalance Monitor */}
        <ImbalanceMonitor height={280} area="system" />
      </div>
    </ErrorBoundary>
  );
}
