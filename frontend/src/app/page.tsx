"use client";

import dynamic from "next/dynamic";

import { DashboardShell } from "@/components/layout";
import { ErrorBoundary } from "@/components/ui";

const TORPortal = dynamic(
  () => import("@/components/dashboard").then((mod) => ({ default: mod.TORPortal })),
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

export default function HomePage() {
  return (
    <DashboardShell>
      <ErrorBoundary>
        <TORPortal />
      </ErrorBoundary>
    </DashboardShell>
  );
}
