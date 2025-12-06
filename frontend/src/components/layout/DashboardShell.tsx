"use client";

import {
  Activity,
  AlertTriangle,
  BarChart3,
  Bell,
  Calendar,
  Menu,
  Settings,
  Shield,
  Sun,
  X,
  Zap,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { getApiBaseUrl } from "@/lib/api";

interface HealthStatus {
  status: string;
  timestamp: string;
  service: string;
}

interface NavTab {
  id: string;
  href: string;
  label: string;
  shortLabel: string;
  icon: typeof BarChart3;
}

const navTabs: NavTab[] = [
  { id: "overview", href: "/", label: "Overview", shortLabel: "Home", icon: BarChart3 },
  { id: "solar", href: "/?tab=solar", label: "Solar Forecast", shortLabel: "Solar", icon: Sun },
  {
    id: "voltage",
    href: "/?tab=voltage",
    label: "Voltage Monitor",
    shortLabel: "Voltage",
    icon: Zap,
  },
  { id: "alerts", href: "/?tab=alerts", label: "Alerts", shortLabel: "Alerts", icon: Bell },
  { id: "history", href: "/?tab=history", label: "History", shortLabel: "History", icon: Calendar },
];

interface DashboardShellProps {
  children: React.ReactNode;
  activeTab?: string;
  showTabs?: boolean;
}

export function DashboardShell({ children, activeTab, showTabs = true }: DashboardShellProps) {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const pathname = usePathname();

  // Determine active state based on pathname
  const isAuditPage = pathname === "/audit";
  const currentActiveTab = activeTab || (isAuditPage ? "audit" : "overview");

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

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header - PEA Brand Purple */}
      <header className="bg-gradient-to-r from-[#74045F] to-[#5A0349] text-white shadow-lg sticky top-0 z-50">
        <div className="container mx-auto px-3 sm:px-4 py-3 sm:py-4">
          <div className="flex items-center justify-between">
            <Link href="/" className="flex items-center space-x-2 sm:space-x-4">
              <div className="bg-white/10 p-1.5 sm:p-2 rounded-lg">
                <BarChart3 className="w-6 h-6 sm:w-8 sm:h-8" />
              </div>
              <div>
                <h1 className="text-base sm:text-xl font-bold">PEA RE Forecast</h1>
                <p className="text-[#D4A43D] text-xs sm:text-sm font-medium hidden sm:block">
                  แพลตฟอร์มศูนย์ข้อมูลพยากรณ์พลังงานหมุนเวียน
                </p>
              </div>
            </Link>
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
              <Link
                href="/audit"
                className={`p-1.5 sm:p-2 hover:bg-white/10 rounded-lg transition-colors hidden sm:block ${
                  isAuditPage ? "bg-white/20" : ""
                }`}
                title="Audit Logs"
              >
                <Shield className="w-4 h-4 sm:w-5 sm:h-5" />
              </Link>
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
        {showTabs && (
          <div className="container mx-auto px-3 sm:px-4 hidden sm:block">
            <nav className="flex space-x-1 overflow-x-auto scrollbar-hide">
              {navTabs.map((tab) => (
                <Link
                  key={tab.id}
                  href={tab.href}
                  className={`flex items-center px-3 md:px-4 py-2.5 md:py-3 text-xs md:text-sm font-medium transition-colors whitespace-nowrap ${
                    currentActiveTab === tab.id
                      ? "bg-white text-[#74045F] rounded-t-lg"
                      : "text-[#D4A43D] hover:text-white hover:bg-white/10 rounded-t-lg"
                  }`}
                >
                  <tab.icon className="w-4 h-4 mr-1.5 md:mr-2" />
                  <span className="hidden md:inline">{tab.label}</span>
                  <span className="md:hidden">{tab.shortLabel}</span>
                </Link>
              ))}
              {/* Audit tab in nav when on audit page */}
              {isAuditPage && (
                <Link
                  href="/audit"
                  className="flex items-center px-3 md:px-4 py-2.5 md:py-3 text-xs md:text-sm font-medium transition-colors whitespace-nowrap bg-white text-[#74045F] rounded-t-lg"
                >
                  <Shield className="w-4 h-4 mr-1.5 md:mr-2" />
                  <span className="hidden md:inline">Audit Logs</span>
                  <span className="md:hidden">Audit</span>
                </Link>
              )}
            </nav>
          </div>
        )}

        {/* Mobile Navigation Menu */}
        {mobileMenuOpen && (
          <div className="sm:hidden bg-[#5A0349] border-t border-white/10">
            <nav className="container mx-auto px-3 py-2">
              {navTabs.map((tab) => (
                <Link
                  key={tab.id}
                  href={tab.href}
                  onClick={() => setMobileMenuOpen(false)}
                  className={`flex items-center w-full px-3 py-3 text-sm font-medium transition-colors rounded-lg mb-1 ${
                    currentActiveTab === tab.id
                      ? "bg-white text-[#74045F]"
                      : "text-[#D4A43D] hover:text-white hover:bg-white/10"
                  }`}
                >
                  <tab.icon className="w-5 h-5 mr-3" />
                  {tab.label}
                </Link>
              ))}
              <Link
                href="/audit"
                onClick={() => setMobileMenuOpen(false)}
                className={`flex items-center w-full px-3 py-3 text-sm font-medium transition-colors rounded-lg mb-1 ${
                  isAuditPage
                    ? "bg-white text-[#74045F]"
                    : "text-[#D4A43D] hover:text-white hover:bg-white/10"
                }`}
              >
                <Shield className="w-5 h-5 mr-3" />
                Audit Logs
              </Link>
            </nav>
          </div>
        )}
      </header>

      {/* Main Content */}
      <main className="flex-1 container mx-auto px-3 sm:px-4 py-4 sm:py-6 pb-20 sm:pb-6">
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
        {children}
      </main>

      {/* Mobile Bottom Navigation */}
      {showTabs && (
        <div className="sm:hidden fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 shadow-lg z-50">
          <nav className="flex justify-around">
            {navTabs.slice(0, 4).map((tab) => (
              <Link
                key={tab.id}
                href={tab.href}
                className={`flex flex-col items-center py-2 px-3 flex-1 ${
                  currentActiveTab === tab.id ? "text-[#74045F]" : "text-gray-500"
                }`}
              >
                <tab.icon
                  className={`w-5 h-5 ${currentActiveTab === tab.id ? "text-[#74045F]" : "text-gray-400"}`}
                />
                <span className="text-[10px] mt-0.5 font-medium">{tab.shortLabel}</span>
              </Link>
            ))}
            <Link
              href="/audit"
              className={`flex flex-col items-center py-2 px-3 flex-1 ${
                isAuditPage ? "text-[#74045F]" : "text-gray-500"
              }`}
            >
              <Shield className={`w-5 h-5 ${isAuditPage ? "text-[#74045F]" : "text-gray-400"}`} />
              <span className="text-[10px] mt-0.5 font-medium">Audit</span>
            </Link>
          </nav>
        </div>
      )}

      {/* Footer - PEA Brand Purple */}
      <footer className="bg-[#5A0349] text-white py-4 sm:py-6 mt-auto hidden sm:block">
        <div className="container mx-auto px-4 text-center text-xs sm:text-sm">
          <p className="font-medium">PEA RE Forecast Platform - การไฟฟ้าส่วนภูมิภาค</p>
          <p className="mt-1 text-[#D4A43D]">Provincial Electricity Authority of Thailand</p>
          <p className="mt-2 text-gray-300">Version 1.0.0 | TOR Compliant</p>
        </div>
      </footer>
    </div>
  );
}
