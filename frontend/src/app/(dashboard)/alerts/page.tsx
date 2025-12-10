"use client";

import dynamic from "next/dynamic";

import { ErrorBoundary } from "@/components/ui";

const AlertDashboard = dynamic(
  () => import("@/components/dashboard").then((mod) => ({ default: mod.AlertDashboard })),
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

export default function AlertsPage() {
  return (
    <ErrorBoundary>
      <div className="space-y-4 sm:space-y-6">
        <AlertDashboard height={260} />

        <div className="bg-white rounded-lg shadow p-4 sm:p-6">
          <h3 className="text-base sm:text-lg font-semibold text-gray-800 mb-3 sm:mb-4 flex items-center gap-1">
            Alert Configuration
          </h3>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
            <div>
              <p className="text-xs sm:text-sm text-gray-500">Voltage Upper</p>
              <p className="font-semibold text-red-600 text-sm sm:text-base">242V (+5%)</p>
            </div>
            <div>
              <p className="text-xs sm:text-sm text-gray-500">Voltage Lower</p>
              <p className="font-semibold text-red-600 text-sm sm:text-base">218V (-5%)</p>
            </div>
            <div>
              <p className="text-xs sm:text-sm text-gray-500">Warning</p>
              <p className="font-semibold text-amber-600 text-sm sm:text-base">±3.5%</p>
            </div>
            <div>
              <p className="text-xs sm:text-sm text-gray-500">Nominal</p>
              <p className="font-semibold text-sm sm:text-base">230V</p>
            </div>
          </div>
        </div>
      </div>
    </ErrorBoundary>
  );
}
