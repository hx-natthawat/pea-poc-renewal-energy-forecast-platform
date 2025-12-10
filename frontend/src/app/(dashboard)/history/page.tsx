"use client";

import dynamic from "next/dynamic";

import { ErrorBoundary } from "@/components/ui";

const DayAheadReport = dynamic(
  () => import("@/components/dashboard").then((mod) => ({ default: mod.DayAheadReport })),
  { loading: () => <DashboardSkeleton /> }
);

const HistoricalAnalysis = dynamic(
  () => import("@/components/dashboard").then((mod) => ({ default: mod.HistoricalAnalysis })),
  { loading: () => <DashboardSkeleton /> }
);

function DashboardSkeleton() {
  return (
    <div className="bg-white rounded-lg shadow p-4 animate-pulse">
      <div className="h-6 w-1/4 bg-gray-200 rounded mb-4" />
      <div className="h-[180px] bg-gray-100 rounded" />
    </div>
  );
}

export default function HistoryPage() {
  return (
    <ErrorBoundary>
      <div className="space-y-4 sm:space-y-6">
        <DayAheadReport height={240} />
        <HistoricalAnalysis height={240} />
      </div>
    </ErrorBoundary>
  );
}
