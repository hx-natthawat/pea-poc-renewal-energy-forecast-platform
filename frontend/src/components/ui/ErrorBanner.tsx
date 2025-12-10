"use client";

import { AlertCircle, AlertTriangle, RefreshCw, X, XCircle } from "lucide-react";

type ErrorSeverity = "error" | "warning" | "info";

interface ErrorBannerProps {
  message: string;
  severity?: ErrorSeverity;
  onRetry?: () => void;
  onDismiss?: () => void;
  details?: string;
  className?: string;
}

const SEVERITY_STYLES: Record<ErrorSeverity, { bg: string; text: string; border: string }> = {
  error: {
    bg: "bg-red-50",
    text: "text-red-700",
    border: "border-red-200",
  },
  warning: {
    bg: "bg-amber-50",
    text: "text-amber-700",
    border: "border-amber-200",
  },
  info: {
    bg: "bg-blue-50",
    text: "text-blue-700",
    border: "border-blue-200",
  },
};

const SEVERITY_ICONS: Record<ErrorSeverity, typeof AlertCircle> = {
  error: XCircle,
  warning: AlertTriangle,
  info: AlertCircle,
};

export function ErrorBanner({
  message,
  severity = "warning",
  onRetry,
  onDismiss,
  details,
  className = "",
}: ErrorBannerProps) {
  const styles = SEVERITY_STYLES[severity];
  const Icon = SEVERITY_ICONS[severity];

  return (
    <div
      className={`${styles.bg} ${styles.text} border ${styles.border} rounded-lg p-2.5 sm:p-3 ${className}`}
      role="alert"
    >
      <div className="flex items-start gap-2 sm:gap-3">
        <Icon className="w-4 h-4 sm:w-5 sm:h-5 flex-shrink-0 mt-0.5" />
        <div className="flex-1 min-w-0">
          <p className="text-xs sm:text-sm font-medium">{message}</p>
          {details && <p className="text-[10px] sm:text-xs mt-0.5 opacity-80">{details}</p>}
        </div>
        <div className="flex items-center gap-1 flex-shrink-0">
          {onRetry && (
            <button
              type="button"
              onClick={onRetry}
              className={`p-1 sm:p-1.5 rounded hover:bg-black/5 transition-colors touch-manipulation ${styles.text}`}
              title="Retry"
            >
              <RefreshCw className="w-3.5 h-3.5 sm:w-4 sm:h-4" />
            </button>
          )}
          {onDismiss && (
            <button
              type="button"
              onClick={onDismiss}
              className={`p-1 sm:p-1.5 rounded hover:bg-black/5 transition-colors touch-manipulation ${styles.text}`}
              title="Dismiss"
            >
              <X className="w-3.5 h-3.5 sm:w-4 sm:h-4" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
