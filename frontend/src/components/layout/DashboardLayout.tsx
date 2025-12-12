"use client";

import {
  Activity,
  AlertTriangle,
  BarChart3,
  Bell,
  Calendar,
  Gauge,
  Globe,
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

import { HelpSidebar, HelpTrigger } from "@/components/help";
import { ErrorBanner } from "@/components/ui";
import { getApiBaseUrl } from "@/lib/api";

interface HealthStatus {
  status: string;
  timestamp: string;
  service: string;
}

const navItems = [
  { id: "tor", path: "/", label: "TOR Functions", shortLabel: "TOR", icon: Globe },
  { id: "overview", path: "/overview", label: "Overview", shortLabel: "Home", icon: BarChart3 },
  { id: "solar", path: "/solar", label: "Solar Forecast", shortLabel: "Solar", icon: Sun },
  { id: "voltage", path: "/voltage", label: "Voltage Monitor", shortLabel: "Voltage", icon: Zap },
  { id: "grid", path: "/grid", label: "Grid Operations", shortLabel: "Grid", icon: Gauge },
  { id: "alerts", path: "/alerts", label: "Alerts", shortLabel: "Alerts", icon: Bell },
  { id: "history", path: "/history", label: "History", shortLabel: "History", icon: Calendar },
];

export function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);

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

  const isActive = (path: string) => {
    if (path === "/") return pathname === "/";
    return pathname.startsWith(path);
  };

  return (
    <main className="min-h-screen bg-gray-50">
      {/* Header - PEA Brand Purple (see design-guideline.md) */}
      <header className="bg-gradient-to-r from-pea-purple to-pea-purple-muted text-white shadow-lg sticky top-0 z-50">
        <div className="container mx-auto px-3 sm:px-4 py-3 sm:py-4">
          <div className="flex items-center justify-between">
            <Link href="/" className="flex items-center space-x-2 sm:space-x-4">
              <div className="bg-white/10 p-1.5 sm:p-2 rounded-lg">
                <BarChart3 className="w-6 h-6 sm:w-8 sm:h-8" />
              </div>
              <div>
                <h1 className="text-base sm:text-xl font-bold">PEA RE Forecast</h1>
                <p className="text-pea-gold-light text-xs sm:text-sm font-medium hidden sm:block">
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
                className="p-1.5 sm:p-2 hover:bg-white/10 rounded-lg transition-colors hidden sm:block"
                title="Audit Logs"
              >
                <Shield className="w-4 h-4 sm:w-5 sm:h-5" />
              </Link>
              <HelpTrigger
                sectionId="overview-summary"
                className="text-white/70 hover:text-white hover:bg-white/10"
                size="sm"
                label="Open help"
              />
              {/* Settings Dropdown */}
              <div className="relative hidden sm:block">
                <button
                  type="button"
                  className="p-1.5 sm:p-2 hover:bg-white/10 rounded-lg transition-colors"
                  onClick={() => setSettingsOpen(!settingsOpen)}
                >
                  <Settings className="w-4 h-4 sm:w-5 sm:h-5" />
                </button>
                {settingsOpen && (
                  <>
                    <button
                      type="button"
                      className="fixed inset-0 z-40 cursor-default"
                      onClick={() => setSettingsOpen(false)}
                      aria-label="Close settings menu"
                    />
                    <div className="absolute right-0 top-full mt-2 w-56 bg-white rounded-lg shadow-xl border border-gray-200 z-50 py-2">
                      <div className="px-3 py-2 border-b border-gray-100">
                        <p className="text-xs font-semibold text-gray-500 uppercase">Settings</p>
                      </div>
                      <Link
                        href="/audit"
                        className="flex items-center px-3 py-2 text-sm text-gray-700 hover:bg-gray-50"
                        onClick={() => setSettingsOpen(false)}
                      >
                        <Shield className="w-4 h-4 mr-3 text-gray-400" />
                        Audit Logs
                      </Link>
                      <Link
                        href="/alerts"
                        className="flex items-center px-3 py-2 text-sm text-gray-700 hover:bg-gray-50"
                        onClick={() => setSettingsOpen(false)}
                      >
                        <Bell className="w-4 h-4 mr-3 text-gray-400" />
                        Alert Settings
                      </Link>
                      <div className="border-t border-gray-100 mt-2 pt-2">
                        <div className="px-3 py-2">
                          <p className="text-xs text-gray-500">API Status</p>
                          <div className="flex items-center mt-1">
                            <span
                              className={`w-2 h-2 rounded-full mr-2 ${health ? "bg-green-500" : "bg-red-500"}`}
                            />
                            <span className="text-sm text-gray-700">
                              {health ? "Connected" : "Disconnected"}
                            </span>
                          </div>
                        </div>
                      </div>
                      <div className="border-t border-gray-100 mt-2 pt-2 px-3 py-2">
                        <p className="text-xs text-gray-400">Version 0.1.0 (POC)</p>
                      </div>
                    </div>
                  </>
                )}
              </div>
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
            {navItems.map((item) => (
              <Link
                key={item.id}
                href={item.path}
                className={`flex items-center px-3 md:px-4 py-2.5 md:py-3 text-xs md:text-sm font-medium transition-colors whitespace-nowrap ${
                  isActive(item.path)
                    ? "bg-white text-pea-purple rounded-t-lg"
                    : "text-pea-gold-light hover:text-white hover:bg-white/10 rounded-t-lg"
                }`}
              >
                <item.icon className="w-4 h-4 mr-1.5 md:mr-2" />
                <span className="hidden md:inline">{item.label}</span>
                <span className="md:hidden">{item.shortLabel}</span>
              </Link>
            ))}
          </nav>
        </div>

        {/* Mobile Navigation Menu */}
        {mobileMenuOpen && (
          <div className="sm:hidden bg-pea-purple-muted border-t border-white/10">
            <nav className="container mx-auto px-3 py-2" suppressHydrationWarning>
              {navItems.map((item) => (
                <Link
                  key={item.id}
                  href={item.path}
                  onClick={() => setMobileMenuOpen(false)}
                  className={`flex items-center w-full px-3 py-3 text-sm font-medium transition-colors rounded-lg mb-1 ${
                    isActive(item.path)
                      ? "bg-white text-pea-purple"
                      : "text-pea-gold-light hover:text-white hover:bg-white/10"
                  }`}
                >
                  <item.icon className="w-5 h-5 mr-3" />
                  {item.label}
                </Link>
              ))}
            </nav>
          </div>
        )}

        {/* Mobile Bottom Navigation */}
        <div className="sm:hidden fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 shadow-lg z-50 pb-safe">
          <nav
            className="flex overflow-x-auto scrollbar-hide snap-x snap-mandatory"
            suppressHydrationWarning
          >
            {navItems.map((item) => (
              <Link
                key={item.id}
                href={item.path}
                className={`flex flex-col items-center py-2 px-2 min-w-[52px] snap-center ${
                  isActive(item.path) ? "text-pea-purple" : "text-gray-500"
                }`}
              >
                <item.icon
                  className={`w-5 h-5 ${isActive(item.path) ? "text-pea-purple" : "text-gray-400"}`}
                />
                <span className="text-[9px] mt-0.5 font-medium whitespace-nowrap">
                  {item.shortLabel}
                </span>
              </Link>
            ))}
          </nav>
        </div>
      </header>

      {/* Main Content - Add bottom padding for mobile nav */}
      <div className="container mx-auto px-3 sm:px-4 py-4 sm:py-6 pb-20 sm:pb-6">
        {/* Status Banner */}
        {error && (
          <ErrorBanner
            message={error}
            severity="error"
            details="Run: docker compose up -d"
            className="mb-4 sm:mb-6"
          />
        )}

        {children}
      </div>

      {/* Footer - PEA Brand Purple - Hidden on mobile (bottom nav takes space) */}
      <footer className="bg-pea-purple-muted text-white py-4 sm:py-6 mt-4 sm:mt-8 hidden sm:block">
        <div className="container mx-auto px-4 text-center text-xs sm:text-sm">
          <p className="font-medium">PEA RE Forecast Platform - การไฟฟ้าส่วนภูมิภาค</p>
          <p className="mt-1 text-pea-gold-light">Provincial Electricity Authority of Thailand</p>
          <p className="mt-2 text-gray-300">Version 0.1.0 (POC) | TOR Compliant</p>
        </div>
      </footer>

      {/* Help Sidebar */}
      <HelpSidebar />
    </main>
  );
}
