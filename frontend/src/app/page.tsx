"use client";

import { Activity, AlertTriangle, BarChart3, Bell, Settings, Sun, Zap } from "lucide-react";
import { useEffect, useState } from "react";
import { SolarForecastChart, VoltageMonitorChart } from "@/components/charts";
import { AlertDashboard, ForecastComparison, NetworkTopology } from "@/components/dashboard";
import { getApiBaseUrl } from "@/lib/api";

interface HealthStatus {
  status: string;
  timestamp: string;
  service: string;
}

export default function Home() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"overview" | "solar" | "voltage" | "alerts">("overview");

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
    <main className="min-h-screen">
      {/* Header - PEA Brand Purple */}
      <header className="bg-gradient-to-r from-[#74045F] to-[#5A0349] text-white shadow-lg">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="bg-white/10 p-2 rounded-lg">
                <BarChart3 className="w-8 h-8" />
              </div>
              <div>
                <h1 className="text-xl font-bold">PEA RE Forecast Platform</h1>
                <p className="text-[#D4A43D] text-sm font-medium">
                  แพลตฟอร์มศูนย์ข้อมูลพยากรณ์พลังงานหมุนเวียน
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              {health ? (
                <span className="flex items-center text-green-300 bg-green-900/30 px-3 py-1 rounded-full text-sm">
                  <Activity className="w-4 h-4 mr-1" />
                  Online
                </span>
              ) : error ? (
                <span className="flex items-center text-red-300 bg-red-900/30 px-3 py-1 rounded-full text-sm">
                  <AlertTriangle className="w-4 h-4 mr-1" />
                  Offline
                </span>
              ) : (
                <span className="text-gray-300 text-sm">Connecting...</span>
              )}
              <button type="button" className="p-2 hover:bg-white/10 rounded-lg transition-colors">
                <Settings className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="container mx-auto px-4">
          <nav className="flex space-x-1">
            {[
              { id: "overview", label: "Overview", icon: BarChart3 },
              { id: "solar", label: "Solar Forecast", icon: Sun },
              { id: "voltage", label: "Voltage Monitor", icon: Zap },
              { id: "alerts", label: "Alerts", icon: Bell },
            ].map((tab) => (
              <button
                type="button"
                key={tab.id}
                onClick={() => setActiveTab(tab.id as typeof activeTab)}
                className={`flex items-center px-4 py-3 text-sm font-medium transition-colors ${
                  activeTab === tab.id
                    ? "bg-white text-[#74045F] rounded-t-lg"
                    : "text-[#D4A43D] hover:text-white hover:bg-white/10 rounded-t-lg"
                }`}
              >
                <tab.icon className="w-4 h-4 mr-2" />
                {tab.label}
              </button>
            ))}
          </nav>
        </div>
      </header>

      {/* Main Content */}
      <div className="container mx-auto px-4 py-6">
        {/* Status Banner */}
        {error && (
          <div className="bg-amber-50 border border-amber-200 text-amber-800 px-4 py-3 rounded-lg mb-6">
            <div className="flex items-center">
              <AlertTriangle className="w-5 h-5 mr-2" />
              <span className="font-medium">{error}</span>
            </div>
            <p className="text-sm mt-1 text-amber-600">
              Run:{" "}
              <code className="bg-amber-100 px-1 rounded">
                docker compose -f docker/docker-compose.yml up -d
              </code>
            </p>
          </div>
        )}

        {/* Overview Tab */}
        {activeTab === "overview" && (
          <>
            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
              <div className="bg-white rounded-lg shadow p-4 border-l-4 border-[#C7911B]">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-gray-500 text-sm">Solar Output</p>
                    <p className="text-2xl font-bold text-gray-800">3,542 kW</p>
                    <p className="text-xs text-green-600">+12% from avg</p>
                  </div>
                  <Sun className="w-10 h-10 text-[#C7911B] opacity-80" />
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-4 border-l-4 border-[#74045F]">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-gray-500 text-sm">Avg Voltage</p>
                    <p className="text-2xl font-bold text-gray-800">228.5 V</p>
                    <p className="text-xs text-gray-500">7 prosumers</p>
                  </div>
                  <Zap className="w-10 h-10 text-[#74045F] opacity-80" />
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-4 border-l-4 border-red-500">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-gray-500 text-sm">Active Alerts</p>
                    <p className="text-2xl font-bold text-gray-800">0</p>
                    <p className="text-xs text-green-600">All systems normal</p>
                  </div>
                  <AlertTriangle className="w-10 h-10 text-red-500 opacity-80" />
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-4 border-l-4 border-green-500">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-gray-500 text-sm">System Status</p>
                    <p className="text-2xl font-bold text-gray-800">
                      {health ? "Online" : "Offline"}
                    </p>
                    <p className="text-xs text-gray-500">
                      {health?.timestamp
                        ? new Date(health.timestamp).toLocaleTimeString()
                        : "Not connected"}
                    </p>
                  </div>
                  <Activity className="w-10 h-10 text-green-500 opacity-80" />
                </div>
              </div>
            </div>

            {/* Charts Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <SolarForecastChart height={280} />
              <VoltageMonitorChart height={280} />
            </div>

            {/* Model Performance */}
            <div className="mt-6 bg-white rounded-lg shadow p-6 border-l-4 border-[#74045F]">
              <h3 className="text-lg font-semibold text-gray-800 mb-4">Model Performance</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="text-center p-4 bg-gray-50 rounded-lg">
                  <p className="text-sm text-gray-500">Solar MAPE</p>
                  <p className="text-2xl font-bold text-[#C7911B]">8.2%</p>
                  <p className="text-xs text-green-600">Target: &lt;10%</p>
                </div>
                <div className="text-center p-4 bg-gray-50 rounded-lg">
                  <p className="text-sm text-gray-500">Solar RMSE</p>
                  <p className="text-2xl font-bold text-[#C7911B]">78 kW</p>
                  <p className="text-xs text-green-600">Target: &lt;100kW</p>
                </div>
                <div className="text-center p-4 bg-gray-50 rounded-lg">
                  <p className="text-sm text-gray-500">Voltage MAE</p>
                  <p className="text-2xl font-bold text-[#74045F]">1.4 V</p>
                  <p className="text-xs text-green-600">Target: &lt;2V</p>
                </div>
                <div className="text-center p-4 bg-gray-50 rounded-lg">
                  <p className="text-sm text-gray-500">Voltage R²</p>
                  <p className="text-2xl font-bold text-[#74045F]">0.94</p>
                  <p className="text-xs text-green-600">Target: &gt;0.90</p>
                </div>
              </div>
            </div>
          </>
        )}

        {/* Solar Tab */}
        {activeTab === "solar" && (
          <div className="space-y-6">
            <SolarForecastChart height={350} />
            <ForecastComparison modelType="solar" height={280} />
          </div>
        )}

        {/* Voltage Tab */}
        {activeTab === "voltage" && (
          <div className="space-y-6">
            <VoltageMonitorChart height={350} />
            <NetworkTopology />
          </div>
        )}

        {/* Alerts Tab */}
        {activeTab === "alerts" && (
          <div className="space-y-6">
            <AlertDashboard height={300} />

            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-4">Alert Configuration</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <p className="text-sm text-gray-500">Voltage Upper Limit</p>
                  <p className="font-semibold text-red-600">242V (+5%)</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Voltage Lower Limit</p>
                  <p className="font-semibold text-red-600">218V (-5%)</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Warning Threshold</p>
                  <p className="font-semibold text-amber-600">±3.5%</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Nominal Voltage</p>
                  <p className="font-semibold">230V</p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Footer - PEA Brand Purple */}
      <footer className="bg-[#5A0349] text-white py-6 mt-8">
        <div className="container mx-auto px-4 text-center text-sm">
          <p className="font-medium">PEA RE Forecast Platform - การไฟฟ้าส่วนภูมิภาค</p>
          <p className="mt-1 text-[#D4A43D]">Provincial Electricity Authority of Thailand</p>
          <p className="mt-2 text-gray-300">Version 0.1.0 (POC) | TOR Compliant</p>
        </div>
      </footer>
    </main>
  );
}
