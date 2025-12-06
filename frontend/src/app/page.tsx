"use client";

import {
  Activity,
  AlertTriangle,
  BarChart3,
  Bell,
  Calendar,
  Gauge,
  Menu,
  Settings,
  Shield,
  Sun,
  X,
  Zap,
} from "lucide-react";
import dynamic from "next/dynamic";
import { useEffect, useState } from "react";
import { getApiBaseUrl } from "@/lib/api";

// Lazy load heavy chart components (recharts ~480KB)
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

// Lazy load dashboard components
const AlertDashboard = dynamic(
  () => import("@/components/dashboard").then((mod) => ({ default: mod.AlertDashboard })),
  { loading: () => <DashboardSkeleton /> }
);

const DayAheadReport = dynamic(
  () => import("@/components/dashboard").then((mod) => ({ default: mod.DayAheadReport })),
  { loading: () => <DashboardSkeleton /> }
);

const ForecastComparison = dynamic(
  () => import("@/components/dashboard").then((mod) => ({ default: mod.ForecastComparison })),
  { loading: () => <DashboardSkeleton /> }
);

const HistoricalAnalysis = dynamic(
  () => import("@/components/dashboard").then((mod) => ({ default: mod.HistoricalAnalysis })),
  { loading: () => <DashboardSkeleton /> }
);

const ModelPerformance = dynamic(
  () => import("@/components/dashboard").then((mod) => ({ default: mod.ModelPerformance })),
  { loading: () => <DashboardSkeleton /> }
);

const NetworkTopology = dynamic(
  () => import("@/components/dashboard").then((mod) => ({ default: mod.NetworkTopology })),
  { loading: () => <DashboardSkeleton /> }
);

// Loading skeletons
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

export default function Home() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<
    "overview" | "solar" | "voltage" | "grid" | "alerts" | "history"
  >("overview");
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const response = await fetch(`${getApiBaseUrl()}/api/v1/health`);
        const data = await response.json();
        setHealth(data);
        setError(null);
      } catch {
        setError("Cannot connect to backend API");
        setHealth(null);
      }
    };

    checkHealth();
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  const tabs = [
    { id: "overview", label: "Overview", shortLabel: "Home", icon: BarChart3 },
    { id: "solar", label: "Solar Forecast", shortLabel: "Solar", icon: Sun },
    { id: "voltage", label: "Voltage Monitor", shortLabel: "Voltage", icon: Zap },
    { id: "grid", label: "Grid Operations", shortLabel: "Grid", icon: Gauge },
    { id: "alerts", label: "Alerts", shortLabel: "Alerts", icon: Bell },
    { id: "history", label: "History", shortLabel: "History", icon: Calendar },
  ];

  return (
    <main className="min-h-screen bg-gray-50">
      {/* Header - PEA Brand Purple */}
      <header className="bg-gradient-to-r from-[#74045F] to-[#5A0349] text-white shadow-lg sticky top-0 z-50">
        <div className="container mx-auto px-3 sm:px-4 py-3 sm:py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2 sm:space-x-4">
              <div className="bg-white/10 p-1.5 sm:p-2 rounded-lg">
                <BarChart3 className="w-6 h-6 sm:w-8 sm:h-8" />
              </div>
              <div>
                <h1 className="text-base sm:text-xl font-bold">PEA RE Forecast</h1>
                <p className="text-[#D4A43D] text-xs sm:text-sm font-medium hidden sm:block">
                  แพลตฟอร์มศูนย์ข้อมูลพยากรณ์พลังงานหมุนเวียน
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-2 sm:space-x-4">
              {health ? (
                <span className="flex items-center text-green-300 bg-green-900/30 px-2 sm:px-3 py-1 rounded-full text-xs sm:text-sm">
                  <Activity className="w-3 h-3 sm:w-4 sm:h-4 mr-1" />
                  <span className="hidden xs:inline">Online</span>
                </span>
              ) : error ? (
                <span className="flex items-center text-red-300 bg-red-900/30 px-2 sm:px-3 py-1 rounded-full text-xs sm:text-sm">
                  <AlertTriangle className="w-3 h-3 sm:w-4 sm:h-4 mr-1" />
                  <span className="hidden xs:inline">Offline</span>
                </span>
              ) : (
                <span className="text-gray-300 text-xs sm:text-sm">...</span>
              )}
              <a
                href="/audit"
                className="p-1.5 sm:p-2 hover:bg-white/10 rounded-lg transition-colors hidden sm:block"
                title="Audit Logs"
              >
                <Shield className="w-4 h-4 sm:w-5 sm:h-5" />
              </a>
              <button
                type="button"
                className="p-1.5 sm:p-2 hover:bg-white/10 rounded-lg transition-colors hidden sm:block"
              >
                <Settings className="w-4 h-4 sm:w-5 sm:h-5" />
              </button>
              {/* Mobile menu button */}
              <button
                type="button"
                className="p-1.5 hover:bg-white/10 rounded-lg transition-colors sm:hidden"
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              >
                {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
              </button>
            </div>
          </div>
        </div>

        {/* Navigation Tabs - Desktop */}
        <div className="container mx-auto px-3 sm:px-4 hidden sm:block">
          <nav className="flex space-x-1 overflow-x-auto scrollbar-hide" suppressHydrationWarning>
            {tabs.map((tab) => (
              <button
                type="button"
                key={tab.id}
                onClick={() => setActiveTab(tab.id as typeof activeTab)}
                className={`flex items-center px-3 md:px-4 py-2.5 md:py-3 text-xs md:text-sm font-medium transition-colors whitespace-nowrap ${
                  activeTab === tab.id
                    ? "bg-white text-[#74045F] rounded-t-lg"
                    : "text-[#D4A43D] hover:text-white hover:bg-white/10 rounded-t-lg"
                }`}
              >
                <tab.icon className="w-4 h-4 mr-1.5 md:mr-2" />
                <span className="hidden md:inline">{tab.label}</span>
                <span className="md:hidden">{tab.shortLabel}</span>
              </button>
            ))}
          </nav>
        </div>

        {/* Mobile Navigation Menu */}
        {mobileMenuOpen && (
          <div className="sm:hidden bg-[#5A0349] border-t border-white/10">
            <nav className="container mx-auto px-3 py-2" suppressHydrationWarning>
              {tabs.map((tab) => (
                <button
                  type="button"
                  key={tab.id}
                  onClick={() => {
                    setActiveTab(tab.id as typeof activeTab);
                    setMobileMenuOpen(false);
                  }}
                  className={`flex items-center w-full px-3 py-3 text-sm font-medium transition-colors rounded-lg mb-1 ${
                    activeTab === tab.id
                      ? "bg-white text-[#74045F]"
                      : "text-[#D4A43D] hover:text-white hover:bg-white/10"
                  }`}
                >
                  <tab.icon className="w-5 h-5 mr-3" />
                  {tab.label}
                </button>
              ))}
            </nav>
          </div>
        )}

        {/* Mobile Bottom Navigation */}
        <div className="sm:hidden fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 shadow-lg z-50">
          <nav className="flex justify-around" suppressHydrationWarning>
            {tabs.map((tab) => (
              <button
                type="button"
                key={tab.id}
                onClick={() => setActiveTab(tab.id as typeof activeTab)}
                className={`flex flex-col items-center py-2 px-3 flex-1 ${
                  activeTab === tab.id ? "text-[#74045F]" : "text-gray-500"
                }`}
              >
                <tab.icon
                  className={`w-5 h-5 ${activeTab === tab.id ? "text-[#74045F]" : "text-gray-400"}`}
                />
                <span className="text-[10px] mt-0.5 font-medium">{tab.shortLabel}</span>
              </button>
            ))}
          </nav>
        </div>
      </header>

      {/* Main Content - Add bottom padding for mobile nav */}
      <div className="container mx-auto px-3 sm:px-4 py-4 sm:py-6 pb-20 sm:pb-6">
        {/* Status Banner */}
        {error && (
          <div className="bg-amber-50 border border-amber-200 text-amber-800 px-3 sm:px-4 py-2 sm:py-3 rounded-lg mb-4 sm:mb-6">
            <div className="flex items-center">
              <AlertTriangle className="w-4 h-4 sm:w-5 sm:h-5 mr-2 flex-shrink-0" />
              <span className="font-medium text-sm sm:text-base">{error}</span>
            </div>
            <p className="text-xs sm:text-sm mt-1 text-amber-600 overflow-x-auto">
              Run: <code className="bg-amber-100 px-1 rounded text-xs">docker compose up -d</code>
            </p>
          </div>
        )}

        {/* Overview Tab */}
        {activeTab === "overview" && (
          <>
            {/* Summary Cards - 2x2 on mobile, 4 on desktop */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-2 sm:gap-4 mb-4 sm:mb-6">
              <div className="bg-white rounded-lg shadow p-3 sm:p-4 border-l-4 border-[#C7911B]">
                <div className="flex items-center justify-between">
                  <div className="min-w-0 flex-1">
                    <p className="text-gray-500 text-xs sm:text-sm truncate">Solar Output</p>
                    <p className="text-lg sm:text-2xl font-bold text-gray-800">3,542 kW</p>
                    <p className="text-[10px] sm:text-xs text-green-600">+12% from avg</p>
                  </div>
                  <Sun className="w-8 h-8 sm:w-10 sm:h-10 text-[#C7911B] opacity-80 flex-shrink-0" />
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-3 sm:p-4 border-l-4 border-[#74045F]">
                <div className="flex items-center justify-between">
                  <div className="min-w-0 flex-1">
                    <p className="text-gray-500 text-xs sm:text-sm truncate">Avg Voltage</p>
                    <p className="text-lg sm:text-2xl font-bold text-gray-800">228.5 V</p>
                    <p className="text-[10px] sm:text-xs text-gray-500">7 prosumers</p>
                  </div>
                  <Zap className="w-8 h-8 sm:w-10 sm:h-10 text-[#74045F] opacity-80 flex-shrink-0" />
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-3 sm:p-4 border-l-4 border-red-500">
                <div className="flex items-center justify-between">
                  <div className="min-w-0 flex-1">
                    <p className="text-gray-500 text-xs sm:text-sm truncate">Active Alerts</p>
                    <p className="text-lg sm:text-2xl font-bold text-gray-800">0</p>
                    <p className="text-[10px] sm:text-xs text-green-600">All normal</p>
                  </div>
                  <AlertTriangle className="w-8 h-8 sm:w-10 sm:h-10 text-red-500 opacity-80 flex-shrink-0" />
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-3 sm:p-4 border-l-4 border-green-500">
                <div className="flex items-center justify-between">
                  <div className="min-w-0 flex-1">
                    <p className="text-gray-500 text-xs sm:text-sm truncate">System Status</p>
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
          </>
        )}

        {/* Solar Tab */}
        {activeTab === "solar" && (
          <div className="space-y-4 sm:space-y-6">
            <SolarForecastChart height={280} />
            <ForecastComparison modelType="solar" height={240} />
          </div>
        )}

        {/* Voltage Tab */}
        {activeTab === "voltage" && (
          <div className="space-y-4 sm:space-y-6">
            <VoltageMonitorChart height={280} />
            <NetworkTopology />
          </div>
        )}

        {/* Grid Operations Tab */}
        {activeTab === "grid" && (
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
        )}

        {/* Alerts Tab */}
        {activeTab === "alerts" && (
          <div className="space-y-4 sm:space-y-6">
            <AlertDashboard height={260} />

            <div className="bg-white rounded-lg shadow p-4 sm:p-6">
              <h3 className="text-base sm:text-lg font-semibold text-gray-800 mb-3 sm:mb-4">
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
        )}

        {/* History Tab */}
        {activeTab === "history" && (
          <div className="space-y-4 sm:space-y-6">
            <DayAheadReport height={240} />
            <HistoricalAnalysis height={240} />
          </div>
        )}
      </div>

      {/* Footer - PEA Brand Purple - Hidden on mobile (bottom nav takes space) */}
      <footer className="bg-[#5A0349] text-white py-4 sm:py-6 mt-4 sm:mt-8 hidden sm:block">
        <div className="container mx-auto px-4 text-center text-xs sm:text-sm">
          <p className="font-medium">PEA RE Forecast Platform - การไฟฟ้าส่วนภูมิภาค</p>
          <p className="mt-1 text-[#D4A43D]">Provincial Electricity Authority of Thailand</p>
          <p className="mt-2 text-gray-300">Version 0.1.0 (POC) | TOR Compliant</p>
        </div>
      </footer>
    </main>
  );
}
