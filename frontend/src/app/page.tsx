"use client";

import { useState, useEffect } from "react";
import { Sun, Zap, AlertTriangle, Activity } from "lucide-react";

interface HealthStatus {
  status: string;
  timestamp: string;
  service: string;
}

export default function Home() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        const response = await fetch(`${apiUrl}/api/v1/health`);
        const data = await response.json();
        setHealth(data);
        setError(null);
      } catch (err) {
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
      {/* Header */}
      <header className="bg-pea-primary text-white shadow-lg">
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold">PEA RE Forecast Platform</h1>
              <p className="text-blue-200 text-sm">
                แพลตฟอร์มศูนย์ข้อมูลพยากรณ์พลังงานหมุนเวียน
              </p>
            </div>
            <div className="flex items-center space-x-2">
              {health ? (
                <span className="flex items-center text-green-300">
                  <Activity className="w-4 h-4 mr-1" />
                  Online
                </span>
              ) : error ? (
                <span className="flex items-center text-red-300">
                  <AlertTriangle className="w-4 h-4 mr-1" />
                  Offline
                </span>
              ) : (
                <span className="text-gray-300">Connecting...</span>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="container mx-auto px-4 py-8">
        {/* Status Banner */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-6">
            <div className="flex items-center">
              <AlertTriangle className="w-5 h-5 mr-2" />
              <span>{error}</span>
            </div>
            <p className="text-sm mt-1">
              Make sure the backend is running: docker-compose up -d
            </p>
          </div>
        )}

        {/* Dashboard Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {/* Solar Forecast Card */}
          <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-amber-500">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-500 text-sm">Solar Forecast</p>
                <p className="text-2xl font-bold text-gray-800">-- kW</p>
              </div>
              <Sun className="w-10 h-10 text-amber-500" />
            </div>
            <p className="text-xs text-gray-400 mt-2">Next hour prediction</p>
          </div>

          {/* Voltage Status Card */}
          <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-blue-500">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-500 text-sm">Avg Voltage</p>
                <p className="text-2xl font-bold text-gray-800">-- V</p>
              </div>
              <Zap className="w-10 h-10 text-blue-500" />
            </div>
            <p className="text-xs text-gray-400 mt-2">7 prosumers monitored</p>
          </div>

          {/* Alerts Card */}
          <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-red-500">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-500 text-sm">Active Alerts</p>
                <p className="text-2xl font-bold text-gray-800">0</p>
              </div>
              <AlertTriangle className="w-10 h-10 text-red-500" />
            </div>
            <p className="text-xs text-gray-400 mt-2">No violations detected</p>
          </div>

          {/* System Status Card */}
          <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-green-500">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-500 text-sm">System Status</p>
                <p className="text-2xl font-bold text-gray-800">
                  {health ? "Online" : "Offline"}
                </p>
              </div>
              <Activity className="w-10 h-10 text-green-500" />
            </div>
            <p className="text-xs text-gray-400 mt-2">
              {health?.timestamp
                ? new Date(health.timestamp).toLocaleTimeString()
                : "Not connected"}
            </p>
          </div>
        </div>

        {/* Quick Start Section */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-bold text-gray-800 mb-4">Quick Start</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h3 className="font-semibold text-gray-700 mb-2">1. Start Backend</h3>
              <pre className="bg-gray-100 p-3 rounded text-sm overflow-x-auto">
                docker-compose -f docker/docker-compose.yml up -d
              </pre>
            </div>
            <div>
              <h3 className="font-semibold text-gray-700 mb-2">2. API Documentation</h3>
              <p className="text-gray-600">
                Visit{" "}
                <a
                  href="http://localhost:8000/api/v1/docs"
                  target="_blank"
                  className="text-blue-600 hover:underline"
                >
                  http://localhost:8000/api/v1/docs
                </a>
              </p>
            </div>
          </div>
        </div>

        {/* Features Grid */}
        <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-bold text-gray-800 mb-3 flex items-center">
              <Sun className="w-5 h-5 mr-2 text-amber-500" />
              RE Forecast Module
            </h3>
            <p className="text-gray-600 text-sm">
              Predicts solar PV power output from environmental parameters.
              Target accuracy: MAPE &lt; 10%, RMSE &lt; 100 kW, R² &gt; 0.95
            </p>
            <ul className="mt-3 text-sm text-gray-500 space-y-1">
              <li>• Day-ahead forecasting</li>
              <li>• Intraday forecasting</li>
              <li>• Real-time predictions</li>
            </ul>
          </div>

          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-bold text-gray-800 mb-3 flex items-center">
              <Zap className="w-5 h-5 mr-2 text-blue-500" />
              Voltage Prediction Module
            </h3>
            <p className="text-gray-600 text-sm">
              Predicts voltage levels across low-voltage distribution networks.
              Target accuracy: MAE &lt; 2V
            </p>
            <ul className="mt-3 text-sm text-gray-500 space-y-1">
              <li>• 3-phase monitoring</li>
              <li>• 7 prosumers tracked</li>
              <li>• Violation detection</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="bg-gray-800 text-gray-400 py-6 mt-12">
        <div className="container mx-auto px-4 text-center text-sm">
          <p>PEA RE Forecast Platform - Provincial Electricity Authority of Thailand</p>
          <p className="mt-1">Version 0.1.0 (POC)</p>
        </div>
      </footer>
    </main>
  );
}
