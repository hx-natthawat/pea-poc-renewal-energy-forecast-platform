"use client";

import { AlertTriangle, RefreshCw, WifiOff } from "lucide-react";

interface ChartErrorProps {
  message?: string;
  onRetry?: () => void;
  height?: number;
  isNetworkError?: boolean;
}

export function ChartError({
  message = "Unable to load chart data",
  onRetry,
  height = 300,
  isNetworkError = false,
}: ChartErrorProps) {
  const Icon = isNetworkError ? WifiOff : AlertTriangle;

  return (
    <div
      className="flex flex-col items-center justify-center bg-gray-50 rounded-lg border border-gray-200"
      style={{ height }}
    >
      <div className="text-center p-4">
        <div className="w-12 h-12 sm:w-14 sm:h-14 mx-auto mb-3 rounded-full bg-amber-100 flex items-center justify-center">
          <Icon className="w-6 h-6 sm:w-7 sm:h-7 text-amber-600" />
        </div>
        <h4 className="text-sm sm:text-base font-medium text-gray-800 mb-1">
          {isNetworkError ? "Connection Issue" : "Data Unavailable"}
        </h4>
        <p className="text-xs sm:text-sm text-gray-500 mb-3 max-w-xs">{message}</p>
        {onRetry && (
          <button
            type="button"
            onClick={onRetry}
            className="inline-flex items-center px-3 py-1.5 sm:px-4 sm:py-2 text-xs sm:text-sm font-medium text-white bg-[#74045F] hover:bg-[#5a0349] rounded-md transition-colors touch-manipulation"
          >
            <RefreshCw className="w-3.5 h-3.5 sm:w-4 sm:h-4 mr-1.5" />
            Retry
          </button>
        )}
      </div>
    </div>
  );
}
