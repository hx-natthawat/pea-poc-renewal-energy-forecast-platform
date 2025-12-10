"use client";

import dynamic from "next/dynamic";

import { ErrorBoundary } from "@/components/ui";

const SolarForecastChart = dynamic(
  () => import("@/components/charts").then((mod) => ({ default: mod.SolarForecastChart })),
  {
    loading: () => <ChartSkeleton />,
    ssr: false,
  }
);

const ForecastComparison = dynamic(
  () => import("@/components/dashboard").then((mod) => ({ default: mod.ForecastComparison })),
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

export default function SolarPage() {
  return (
    <ErrorBoundary>
      <div className="space-y-4 sm:space-y-6">
        <SolarForecastChart height={280} />
        <ForecastComparison modelType="solar" height={240} />
      </div>
    </ErrorBoundary>
  );
}
