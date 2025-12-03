# Weather Handling Feature - Implementation Guide

## Overview

This document provides the implementation details for the Weather Handling feature, including code structure, file locations, and step-by-step implementation instructions.

---

## File Structure

```
pea-re-forecast-platform/
├── backend/
│   └── app/
│       ├── api/v1/endpoints/
│       │   └── weather.py                    # Weather API endpoints
│       ├── services/
│       │   ├── weather_service.py            # Weather alert integration
│       │   ├── ramp_rate_service.py          # Ramp rate detection
│       │   └── probabilistic_forecast_service.py
│       ├── ml/
│       │   ├── weather_classifier.py         # Weather classification
│       │   ├── weather_adaptive_model.py     # Ensemble models
│       │   └── quantile_regression.py        # Probabilistic forecasting
│       └── models/
│           └── schemas/
│               └── weather.py                # Pydantic schemas
│
├── frontend/
│   └── src/
│       └── components/
│           └── dashboard/
│               ├── WeatherAlertBanner.tsx    # Alert display
│               ├── ProbabilisticChart.tsx    # P10/P50/P90 chart
│               └── RampRateMonitor.tsx       # Real-time monitor
│
├── ml/
│   └── src/
│       ├── training/
│       │   └── weather_models.py             # Model training scripts
│       └── evaluation/
│           └── weather_metrics.py            # Weather-specific metrics
│
└── requirements/
    └── features/
        └── weather-handling/
            ├── plan.md                       # This plan
            ├── spec.md                       # Technical specification
            └── implementation.md             # This file
```

---

## Backend Implementation

### 1. Weather Schemas (`backend/app/models/schemas/weather.py`)

```python
"""Weather handling schemas."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class WeatherCondition(str, Enum):
    """Weather condition classification."""
    CLEAR = "clear"
    PARTLY_CLOUDY = "partly_cloudy"
    CLOUDY = "cloudy"
    RAINY = "rainy"
    STORM = "storm"


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class WeatherAlert(BaseModel):
    """Weather alert from TMD."""
    id: str
    timestamp: datetime
    condition: WeatherCondition
    severity: AlertSeverity
    region: str
    description: str
    expected_duration_minutes: int
    recommended_action: str


class RampEvent(BaseModel):
    """Detected ramp rate event."""
    timestamp: datetime
    rate_percent: float
    direction: str = Field(description="'up' or 'down'")
    current_irradiance: float
    previous_irradiance: float


class CloudEvent(BaseModel):
    """Detected cloud shadow event."""
    start: datetime
    end: datetime
    duration_minutes: float
    min_clearness: float
    avg_clearness: float


class ProbabilisticForecast(BaseModel):
    """Probabilistic forecast with confidence intervals."""
    timestamp: datetime
    horizon_minutes: int
    point_forecast: float = Field(description="Best estimate (P50)")
    p10: float = Field(description="10th percentile (pessimistic)")
    p50: float = Field(description="50th percentile (median)")
    p90: float = Field(description="90th percentile (optimistic)")
    weather_condition: WeatherCondition
    clearness_index: float
    variability_index: float
    uncertainty_factor: float
    is_high_uncertainty: bool
    model_version: str


class WeatherEventLog(BaseModel):
    """Logged weather event for learning."""
    id: int
    timestamp: datetime
    event_type: str
    severity: AlertSeverity
    station_id: str
    min_irradiance: float
    max_irradiance: float
    min_clearness_index: float
    duration_minutes: int
    forecast_error_mape: float
    forecast_error_rmse: float
    tmd_alert_id: Optional[str]
```

### 2. Weather Service (`backend/app/services/weather_service.py`)

```python
"""Weather alert integration service."""

import asyncio
from datetime import datetime, timedelta
from typing import Optional

import httpx
from loguru import logger

from app.config import settings
from app.models.schemas.weather import (
    WeatherAlert,
    WeatherCondition,
    AlertSeverity,
)


class WeatherService:
    """Service for TMD weather alert integration."""

    def __init__(self):
        self.tmd_base_url = settings.TMD_API_URL
        self.api_key = settings.TMD_API_KEY
        self.cache_ttl = 300  # 5 minutes
        self._cache: dict = {}
        self._cache_time: Optional[datetime] = None

    async def get_current_alerts(
        self,
        region: Optional[str] = None
    ) -> list[WeatherAlert]:
        """
        Fetch current weather alerts from TMD.

        Args:
            region: Optional region filter

        Returns:
            List of active weather alerts
        """
        # Check cache
        if self._is_cache_valid():
            alerts = self._cache.get("alerts", [])
            if region:
                alerts = [a for a in alerts if a.region == region]
            return alerts

        # Fetch from TMD
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.tmd_base_url}/weather/alerts",
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                response.raise_for_status()
                data = response.json()

            alerts = [
                self._parse_tmd_alert(alert)
                for alert in data.get("alerts", [])
            ]

            # Update cache
            self._cache["alerts"] = alerts
            self._cache_time = datetime.utcnow()

            if region:
                alerts = [a for a in alerts if a.region == region]

            return alerts

        except httpx.HTTPError as e:
            logger.error(f"TMD API error: {e}")
            return self._cache.get("alerts", [])

    async def get_weather_condition(
        self,
        latitude: float,
        longitude: float
    ) -> WeatherCondition:
        """
        Get current weather condition for location.

        Args:
            latitude: Location latitude
            longitude: Location longitude

        Returns:
            Current weather condition
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.tmd_base_url}/weather/current",
                    params={"lat": latitude, "lon": longitude},
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                response.raise_for_status()
                data = response.json()

            return self._classify_weather(data)

        except httpx.HTTPError as e:
            logger.error(f"TMD API error: {e}")
            return WeatherCondition.PARTLY_CLOUDY  # Conservative default

    def _classify_weather(self, data: dict) -> WeatherCondition:
        """Classify weather from TMD response."""
        cloud_cover = data.get("cloud_cover", 50)
        precipitation = data.get("precipitation_mm", 0)
        wind_speed = data.get("wind_speed_kmh", 0)

        # Storm conditions
        if wind_speed > 60 or precipitation > 20:
            return WeatherCondition.STORM

        # Rain conditions
        if precipitation > 1:
            return WeatherCondition.RAINY

        # Cloud-based classification
        if cloud_cover < 20:
            return WeatherCondition.CLEAR
        elif cloud_cover < 50:
            return WeatherCondition.PARTLY_CLOUDY
        elif cloud_cover < 80:
            return WeatherCondition.CLOUDY
        else:
            return WeatherCondition.RAINY

    def _parse_tmd_alert(self, data: dict) -> WeatherAlert:
        """Parse TMD alert response to schema."""
        severity_map = {
            "info": AlertSeverity.INFO,
            "warning": AlertSeverity.WARNING,
            "severe": AlertSeverity.CRITICAL,
            "critical": AlertSeverity.CRITICAL,
        }

        return WeatherAlert(
            id=data.get("id", ""),
            timestamp=datetime.fromisoformat(data.get("timestamp")),
            condition=self._classify_weather(data),
            severity=severity_map.get(
                data.get("severity", "info"),
                AlertSeverity.INFO
            ),
            region=data.get("region", ""),
            description=data.get("description", ""),
            expected_duration_minutes=data.get("duration_minutes", 60),
            recommended_action=data.get("action", "Monitor conditions")
        )

    def _is_cache_valid(self) -> bool:
        """Check if cache is still valid."""
        if self._cache_time is None:
            return False
        return (datetime.utcnow() - self._cache_time).seconds < self.cache_ttl
```

### 3. Ramp Rate Service (`backend/app/services/ramp_rate_service.py`)

```python
"""Ramp rate detection service."""

from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd
from loguru import logger

from app.models.schemas.weather import RampEvent, CloudEvent


@dataclass
class RampRateConfig:
    """Configuration for ramp rate detection."""
    window_size_seconds: int = 300  # 5 minutes
    threshold_percent: float = 30.0  # 30% change
    min_irradiance: float = 50.0  # W/m² minimum
    alert_cooldown_seconds: int = 60


class RampRateService:
    """Service for detecting rapid irradiance changes."""

    def __init__(self, config: Optional[RampRateConfig] = None):
        self.config = config or RampRateConfig()
        self._last_alert_time: Optional[datetime] = None

    def detect_ramp_event(
        self,
        irradiance_series: pd.Series
    ) -> Optional[RampEvent]:
        """
        Detect sudden changes in irradiance.

        Args:
            irradiance_series: Time-indexed irradiance values (W/m²)

        Returns:
            RampEvent if detected, None otherwise
        """
        if len(irradiance_series) < 2:
            return None

        current = irradiance_series.iloc[-1]
        previous = irradiance_series.iloc[-2]

        # Skip if below minimum irradiance
        if previous < self.config.min_irradiance:
            return None

        # Calculate rate of change
        rate_of_change = (current - previous) / previous * 100

        # Check if exceeds threshold
        if abs(rate_of_change) >= self.config.threshold_percent:
            # Check cooldown
            if self._is_in_cooldown():
                return None

            self._last_alert_time = datetime.utcnow()

            return RampEvent(
                timestamp=irradiance_series.index[-1],
                rate_percent=rate_of_change,
                direction="down" if rate_of_change < 0 else "up",
                current_irradiance=current,
                previous_irradiance=previous
            )

        return None

    def detect_cloud_events(
        self,
        irradiance: np.ndarray,
        clear_sky: np.ndarray,
        timestamps: pd.DatetimeIndex
    ) -> list[CloudEvent]:
        """
        Detect cloud shadow events using clearness index.

        Args:
            irradiance: Measured irradiance values
            clear_sky: Theoretical clear sky irradiance
            timestamps: Corresponding timestamps

        Returns:
            List of detected cloud events
        """
        # Calculate clearness index
        kt = np.divide(
            irradiance,
            clear_sky,
            out=np.zeros_like(irradiance),
            where=clear_sky > 0
        )

        events = []
        in_cloud = False
        event_start_idx = None

        for i, (t, k) in enumerate(zip(timestamps, kt)):
            if k < 0.5 and not in_cloud:
                in_cloud = True
                event_start_idx = i
            elif k >= 0.7 and in_cloud:
                in_cloud = False
                if event_start_idx is not None:
                    event_kt = kt[event_start_idx:i]
                    duration = (timestamps[i] - timestamps[event_start_idx])

                    events.append(CloudEvent(
                        start=timestamps[event_start_idx],
                        end=timestamps[i],
                        duration_minutes=duration.total_seconds() / 60,
                        min_clearness=float(event_kt.min()),
                        avg_clearness=float(event_kt.mean())
                    ))

        return events

    def calculate_variability_index(
        self,
        irradiance: pd.Series,
        window_minutes: int = 10
    ) -> pd.Series:
        """
        Calculate variability index for irradiance data.

        VI = std(G) / mean(G) over rolling window

        Args:
            irradiance: Irradiance time series
            window_minutes: Rolling window size

        Returns:
            Variability index series
        """
        window = f"{window_minutes}T"
        rolling_mean = irradiance.rolling(window).mean()
        rolling_std = irradiance.rolling(window).std()

        return rolling_std / rolling_mean.replace(0, np.nan)

    def _is_in_cooldown(self) -> bool:
        """Check if still in alert cooldown period."""
        if self._last_alert_time is None:
            return False

        elapsed = (datetime.utcnow() - self._last_alert_time).seconds
        return elapsed < self.config.alert_cooldown_seconds
```

### 4. Weather API Endpoints (`backend/app/api/v1/endpoints/weather.py`)

```python
"""Weather API endpoints."""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.weather_service import WeatherService
from app.services.ramp_rate_service import RampRateService
from app.models.schemas.weather import (
    WeatherAlert,
    WeatherCondition,
    RampEvent,
    ProbabilisticForecast,
    WeatherEventLog,
)

router = APIRouter(prefix="/weather", tags=["weather"])

weather_service = WeatherService()
ramp_rate_service = RampRateService()


@router.get("/alerts", response_model=dict)
async def get_weather_alerts(
    region: Optional[str] = Query(None, description="Filter by region"),
    severity: Optional[str] = Query(None, description="Filter by severity")
):
    """
    Get current weather alerts from TMD.

    Returns active weather alerts for the specified region.
    """
    alerts = await weather_service.get_current_alerts(region=region)

    if severity:
        alerts = [a for a in alerts if a.severity.value == severity]

    return {
        "status": "success",
        "data": {
            "alerts": [a.dict() for a in alerts],
            "count": len(alerts),
            "timestamp": datetime.utcnow().isoformat()
        }
    }


@router.get("/condition", response_model=dict)
async def get_weather_condition(
    latitude: float = Query(..., description="Location latitude"),
    longitude: float = Query(..., description="Location longitude")
):
    """
    Get current weather condition for location.

    Returns classified weather condition (clear, cloudy, rainy, etc.)
    """
    condition = await weather_service.get_weather_condition(
        latitude=latitude,
        longitude=longitude
    )

    return {
        "status": "success",
        "data": {
            "condition": condition.value,
            "timestamp": datetime.utcnow().isoformat()
        }
    }


@router.get("/ramp-rate/current", response_model=dict)
async def get_current_ramp_rate(
    station_id: str = Query(default="POC_STATION_1")
):
    """
    Get current ramp rate status.

    Returns latest ramp rate detection results.
    """
    # This would fetch recent irradiance data from DB
    # and run ramp rate detection

    return {
        "status": "success",
        "data": {
            "current_ramp_rate_percent": 0.0,
            "threshold_percent": 30.0,
            "is_alert": False,
            "last_event": None,
            "timestamp": datetime.utcnow().isoformat()
        }
    }


@router.get("/events", response_model=dict)
async def get_weather_events(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    event_type: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Get historical weather events.

    Returns logged weather events for analysis and learning.
    """
    if start_date is None:
        start_date = datetime.utcnow() - timedelta(days=30)
    if end_date is None:
        end_date = datetime.utcnow()

    # Query weather events from database
    query = """
        SELECT * FROM weather_events
        WHERE time BETWEEN $1 AND $2
    """
    params = [start_date, end_date]

    if event_type:
        query += " AND event_type = $3"
        params.append(event_type)

    query += " ORDER BY time DESC LIMIT 100"

    # Execute query and return results
    # (simplified - actual implementation would use SQLAlchemy)

    return {
        "status": "success",
        "data": {
            "events": [],
            "count": 0,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        }
    }
```

---

## Frontend Implementation

### 1. Weather Alert Banner (`frontend/src/components/dashboard/WeatherAlertBanner.tsx`)

```tsx
"use client";

import { AlertTriangle, CloudRain, Wind, X } from "lucide-react";
import { useEffect, useState } from "react";
import { getApiBaseUrl } from "@/lib/api";

interface WeatherAlert {
  id: string;
  timestamp: string;
  condition: string;
  severity: "info" | "warning" | "critical";
  region: string;
  description: string;
  expected_duration_minutes: number;
  recommended_action: string;
}

interface WeatherAlertBannerProps {
  autoRefresh?: boolean;
  refreshInterval?: number;
}

const severityConfig = {
  info: {
    bg: "bg-blue-50",
    border: "border-blue-200",
    text: "text-blue-800",
    icon: CloudRain,
  },
  warning: {
    bg: "bg-amber-50",
    border: "border-amber-200",
    text: "text-amber-800",
    icon: AlertTriangle,
  },
  critical: {
    bg: "bg-red-50",
    border: "border-red-200",
    text: "text-red-800",
    icon: Wind,
  },
};

export default function WeatherAlertBanner({
  autoRefresh = true,
  refreshInterval = 300000, // 5 minutes
}: WeatherAlertBannerProps) {
  const [alerts, setAlerts] = useState<WeatherAlert[]>([]);
  const [dismissedIds, setDismissedIds] = useState<Set<string>>(new Set());
  const [isLoading, setIsLoading] = useState(true);

  const fetchAlerts = async () => {
    try {
      const response = await fetch(`${getApiBaseUrl()}/api/v1/weather/alerts`);
      if (response.ok) {
        const data = await response.json();
        if (data.status === "success") {
          setAlerts(data.data.alerts || []);
        }
      }
    } catch (error) {
      console.error("Error fetching weather alerts:", error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts();

    if (autoRefresh) {
      const interval = setInterval(fetchAlerts, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [autoRefresh, refreshInterval]);

  const handleDismiss = (alertId: string) => {
    setDismissedIds((prev) => new Set([...prev, alertId]));
  };

  const visibleAlerts = alerts.filter((a) => !dismissedIds.has(a.id));

  if (isLoading || visibleAlerts.length === 0) {
    return null;
  }

  return (
    <div className="space-y-2 mb-4">
      {visibleAlerts.map((alert) => {
        const config = severityConfig[alert.severity];
        const Icon = config.icon;

        return (
          <div
            key={alert.id}
            className={`${config.bg} ${config.border} border rounded-lg p-3 sm:p-4 flex items-start gap-3`}
          >
            <Icon className={`w-5 h-5 ${config.text} flex-shrink-0 mt-0.5`} />

            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <span className={`font-semibold ${config.text} text-sm sm:text-base`}>
                  {alert.condition.replace("_", " ").toUpperCase()}
                </span>
                <span className="text-xs text-gray-500">
                  {alert.region}
                </span>
              </div>

              <p className={`${config.text} text-sm mt-1`}>
                {alert.description}
              </p>

              <p className="text-xs text-gray-600 mt-1">
                <span className="font-medium">Recommended: </span>
                {alert.recommended_action}
                {alert.expected_duration_minutes > 0 && (
                  <span className="ml-2">
                    (Expected duration: {alert.expected_duration_minutes} min)
                  </span>
                )}
              </p>
            </div>

            <button
              onClick={() => handleDismiss(alert.id)}
              className="p-1 hover:bg-white/50 rounded transition-colors"
              aria-label="Dismiss alert"
            >
              <X className="w-4 h-4 text-gray-500" />
            </button>
          </div>
        );
      })}
    </div>
  );
}
```

### 2. Probabilistic Chart (`frontend/src/components/dashboard/ProbabilisticChart.tsx`)

```tsx
"use client";

import { useCallback, useEffect, useState } from "react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { RefreshCw, TrendingUp } from "lucide-react";
import { getApiBaseUrl } from "@/lib/api";

interface ForecastDataPoint {
  time: string;
  p10: number;
  p50: number;
  p90: number;
  actual?: number;
  weather_condition: string;
  is_high_uncertainty: boolean;
}

interface ProbabilisticChartProps {
  height?: number;
  showBands?: boolean;
}

const weatherColors: Record<string, string> = {
  clear: "#22C55E",
  partly_cloudy: "#F59E0B",
  cloudy: "#6B7280",
  rainy: "#3B82F6",
  storm: "#EF4444",
};

export default function ProbabilisticChart({
  height = 300,
  showBands = true,
}: ProbabilisticChartProps) {
  const [data, setData] = useState<ForecastDataPoint[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `${getApiBaseUrl()}/api/v1/forecast/solar/probabilistic?hours=24`
      );

      if (!response.ok) {
        throw new Error("Failed to fetch probabilistic forecast");
      }

      const result = await response.json();
      if (result.status === "success") {
        setData(result.data.forecasts || []);
      }
    } catch (err) {
      console.error("Error fetching probabilistic forecast:", err);
      setError("Could not load forecast data");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 300000); // 5 minutes
    return () => clearInterval(interval);
  }, [loadData]);

  if (isLoading && data.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-md p-4 border-l-4 border-amber-500">
        <div className="animate-pulse flex items-center justify-center h-64">
          <p className="text-gray-400 text-sm">Loading probabilistic forecast...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-4 border-l-4 border-amber-500">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center">
          <TrendingUp className="w-5 h-5 mr-2 text-amber-500" />
          <h3 className="text-lg font-semibold text-gray-800">
            Probabilistic Forecast (P10/P50/P90)
          </h3>
        </div>
        <button
          onClick={loadData}
          className="p-2 hover:bg-gray-100 rounded-full transition-colors"
          title="Refresh"
        >
          <RefreshCw
            className={`w-4 h-4 text-gray-500 ${isLoading ? "animate-spin" : ""}`}
          />
        </button>
      </div>

      {/* Legend for weather conditions */}
      <div className="flex flex-wrap gap-2 mb-3 text-xs">
        {Object.entries(weatherColors).map(([condition, color]) => (
          <div key={condition} className="flex items-center gap-1">
            <div
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: color }}
            />
            <span className="text-gray-600 capitalize">
              {condition.replace("_", " ")}
            </span>
          </div>
        ))}
      </div>

      {error && (
        <div className="bg-amber-50 text-amber-700 px-3 py-2 rounded mb-4 text-sm">
          {error}
        </div>
      )}

      {/* Chart */}
      {data.length > 0 ? (
        <ResponsiveContainer width="100%" height={height}>
          <AreaChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="colorP90" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#F59E0B" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#F59E0B" stopOpacity={0.05} />
              </linearGradient>
              <linearGradient id="colorP50" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#C7911B" stopOpacity={0.8} />
                <stop offset="95%" stopColor="#C7911B" stopOpacity={0.2} />
              </linearGradient>
            </defs>

            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />

            <XAxis
              dataKey="time"
              tick={{ fontSize: 10 }}
              tickLine={false}
              interval="preserveStartEnd"
            />

            <YAxis
              tick={{ fontSize: 10 }}
              tickLine={false}
              tickFormatter={(value) => `${(value / 1000).toFixed(1)}k`}
            />

            <Tooltip
              contentStyle={{
                backgroundColor: "white",
                borderRadius: "8px",
                boxShadow: "0 2px 8px rgba(0,0,0,0.15)",
                borderLeft: "4px solid #F59E0B",
              }}
              formatter={(value: number, name: string) => [
                `${value.toFixed(1)} kW`,
                name,
              ]}
            />

            <Legend />

            {showBands && (
              <>
                {/* P90 band (optimistic) */}
                <Area
                  type="monotone"
                  dataKey="p90"
                  name="P90 (Optimistic)"
                  stroke="#F59E0B"
                  strokeWidth={1}
                  strokeDasharray="3 3"
                  fillOpacity={1}
                  fill="url(#colorP90)"
                />

                {/* P10 band (pessimistic) */}
                <Area
                  type="monotone"
                  dataKey="p10"
                  name="P10 (Pessimistic)"
                  stroke="#9CA3AF"
                  strokeWidth={1}
                  strokeDasharray="3 3"
                  fillOpacity={0}
                />
              </>
            )}

            {/* P50 (main forecast) */}
            <Area
              type="monotone"
              dataKey="p50"
              name="P50 (Forecast)"
              stroke="#C7911B"
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#colorP50)"
            />

            {/* Actual values if available */}
            <Line
              type="monotone"
              dataKey="actual"
              name="Actual"
              stroke="#22C55E"
              strokeWidth={2}
              dot={false}
            />
          </AreaChart>
        </ResponsiveContainer>
      ) : (
        <div
          className="flex items-center justify-center text-gray-400"
          style={{ height }}
        >
          No forecast data available
        </div>
      )}

      {/* Footer */}
      <div className="mt-3 pt-3 border-t border-gray-100">
        <p className="text-xs text-gray-500">
          P10: 10% chance actual will be below | P50: Most likely | P90: 10% chance actual will exceed
        </p>
      </div>
    </div>
  );
}
```

### 3. Ramp Rate Monitor (`frontend/src/components/dashboard/RampRateMonitor.tsx`)

```tsx
"use client";

import { useEffect, useState } from "react";
import { Activity, AlertTriangle, TrendingDown, TrendingUp } from "lucide-react";
import { getApiBaseUrl } from "@/lib/api";

interface RampEvent {
  timestamp: string;
  rate_percent: number;
  direction: "up" | "down";
  current_irradiance: number;
  previous_irradiance: number;
}

interface RampRateData {
  current_ramp_rate_percent: number;
  threshold_percent: number;
  is_alert: boolean;
  last_event: RampEvent | null;
}

export default function RampRateMonitor() {
  const [data, setData] = useState<RampRateData | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const fetchData = async () => {
    try {
      const response = await fetch(
        `${getApiBaseUrl()}/api/v1/weather/ramp-rate/current`
      );
      if (response.ok) {
        const result = await response.json();
        if (result.status === "success") {
          setData(result.data);
        }
      }
    } catch (error) {
      console.error("Error fetching ramp rate:", error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 10000); // 10 seconds
    return () => clearInterval(interval);
  }, []);

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-4">
        <div className="animate-pulse h-24 bg-gray-100 rounded" />
      </div>
    );
  }

  if (!data) {
    return null;
  }

  const ratePercent = Math.abs(data.current_ramp_rate_percent);
  const thresholdPercent = data.threshold_percent;
  const fillPercent = Math.min((ratePercent / thresholdPercent) * 100, 100);

  const getStatusColor = () => {
    if (data.is_alert) return "bg-red-500";
    if (fillPercent > 70) return "bg-amber-500";
    return "bg-green-500";
  };

  const getStatusText = () => {
    if (data.is_alert) return "ALERT";
    if (fillPercent > 70) return "CAUTION";
    return "NORMAL";
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center">
          <Activity className="w-5 h-5 mr-2 text-purple-600" />
          <h3 className="text-sm font-semibold text-gray-800">
            Ramp Rate Monitor
          </h3>
        </div>
        <span
          className={`px-2 py-0.5 rounded text-xs font-medium text-white ${getStatusColor()}`}
        >
          {getStatusText()}
        </span>
      </div>

      {/* Ramp Rate Gauge */}
      <div className="mb-3">
        <div className="flex justify-between text-xs text-gray-500 mb-1">
          <span>Current: {ratePercent.toFixed(1)}%</span>
          <span>Threshold: {thresholdPercent}%</span>
        </div>
        <div className="h-3 bg-gray-200 rounded-full overflow-hidden">
          <div
            className={`h-full transition-all duration-300 ${getStatusColor()}`}
            style={{ width: `${fillPercent}%` }}
          />
        </div>
      </div>

      {/* Last Event */}
      {data.last_event && (
        <div className="bg-gray-50 rounded p-2 text-xs">
          <div className="flex items-center gap-1 text-gray-600 mb-1">
            {data.last_event.direction === "down" ? (
              <TrendingDown className="w-3 h-3 text-blue-500" />
            ) : (
              <TrendingUp className="w-3 h-3 text-amber-500" />
            )}
            <span className="font-medium">Last Event</span>
          </div>
          <p className="text-gray-500">
            {data.last_event.rate_percent.toFixed(1)}% {data.last_event.direction} at{" "}
            {new Date(data.last_event.timestamp).toLocaleTimeString()}
          </p>
        </div>
      )}

      {/* Alert Banner */}
      {data.is_alert && (
        <div className="mt-3 bg-red-50 border border-red-200 rounded p-2 flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-red-500" />
          <span className="text-xs text-red-700">
            Rapid irradiance change detected - Cloud shadow event likely
          </span>
        </div>
      )}
    </div>
  );
}
```

---

## Database Migration

```sql
-- migrations/003_weather_events.sql

-- Create weather events table
CREATE TABLE IF NOT EXISTS weather_events (
    id BIGSERIAL,
    time TIMESTAMPTZ NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    station_id VARCHAR(50),

    -- Weather metrics during event
    min_irradiance DOUBLE PRECISION,
    max_irradiance DOUBLE PRECISION,
    min_clearness_index DOUBLE PRECISION,
    precipitation_mm DOUBLE PRECISION,
    max_wind_speed DOUBLE PRECISION,

    -- Duration
    duration_minutes INTEGER,

    -- Forecast performance
    forecast_error_mape DOUBLE PRECISION,
    forecast_error_rmse DOUBLE PRECISION,

    -- Metadata
    tmd_alert_id VARCHAR(100),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),

    PRIMARY KEY (id, time)
);

-- Convert to hypertable
SELECT create_hypertable('weather_events', 'time',
    chunk_time_interval => INTERVAL '30 days',
    if_not_exists => TRUE);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_weather_events_type
    ON weather_events (event_type, time DESC);

CREATE INDEX IF NOT EXISTS idx_weather_events_station
    ON weather_events (station_id, time DESC);

-- Retention policy (1 year)
SELECT add_retention_policy('weather_events', INTERVAL '1 year',
    if_not_exists => TRUE);
```

---

## Configuration Updates

Add to `backend/app/config.py`:

```python
class Settings(BaseSettings):
    # ... existing settings ...

    # Weather handling
    TMD_API_URL: str = "https://data.tmd.go.th/api/v1"
    TMD_API_KEY: str = ""

    # Ramp rate detection
    RAMP_RATE_THRESHOLD_PERCENT: float = 30.0
    RAMP_RATE_WINDOW_SECONDS: int = 300
    RAMP_RATE_MIN_IRRADIANCE: float = 50.0

    # Uncertainty multipliers
    UNCERTAINTY_CLEAR: float = 1.0
    UNCERTAINTY_PARTLY_CLOUDY: float = 1.5
    UNCERTAINTY_CLOUDY: float = 2.0
    UNCERTAINTY_RAINY: float = 3.0
    UNCERTAINTY_STORM: float = 5.0
```

---

## Testing

### Unit Tests

```python
# tests/unit/test_weather_classifier.py

import pytest
from app.ml.weather_classifier import WeatherClassifier
from app.models.schemas.weather import WeatherCondition


class TestWeatherClassifier:
    def setup_method(self):
        self.classifier = WeatherClassifier()

    def test_clear_sky_classification(self):
        """Test clear sky detection with high clearness index."""
        # kt = 0.85 should be classified as CLEAR
        result = self.classifier.classify_by_clearness_index(0.85)
        assert result == WeatherCondition.CLEAR

    def test_cloudy_classification(self):
        """Test cloudy detection with low clearness index."""
        # kt = 0.35 should be classified as CLOUDY
        result = self.classifier.classify_by_clearness_index(0.35)
        assert result == WeatherCondition.CLOUDY

    def test_storm_override(self):
        """Test that storm alert overrides clearness-based classification."""
        result = self.classifier.classify(
            clearness_index=0.9,
            has_storm_alert=True
        )
        assert result == WeatherCondition.STORM
```

### Integration Tests

```python
# tests/integration/test_weather_api.py

import pytest
from httpx import AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_weather_alerts_endpoint():
    """Test weather alerts endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/weather/alerts")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "alerts" in data["data"]


@pytest.mark.asyncio
async def test_ramp_rate_endpoint():
    """Test ramp rate monitoring endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/weather/ramp-rate/current")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "current_ramp_rate_percent" in data["data"]
        assert "threshold_percent" in data["data"]
```

---

## Deployment Checklist

- [ ] TMD API credentials configured (using mock data for POC)
- [x] Database migration applied (`docker/init-db/01-init.sql` - weather_events table)
- [x] Backend weather endpoints deployed
  - `/api/v1/weather/alerts` - Weather alerts
  - `/api/v1/weather/condition` - Current condition
  - `/api/v1/weather/ramp-rate/current` - Ramp rate status
  - `/api/v1/weather/ramp-rate/events` - Ramp events history
  - `/api/v1/weather/clear-sky` - Clear sky irradiance
  - `/api/v1/weather/uncertainty-factors` - Uncertainty multipliers
  - `/api/v1/weather/classify` - Weather classification
  - `/api/v1/weather/events` - Historical weather events
- [x] Frontend components integrated
  - `WeatherAlertBanner.tsx` - Alert display with severity colors
  - `ProbabilisticChart.tsx` - P10/P50/P90 confidence bands
  - `RampRateMonitor.tsx` - Real-time ramp rate gauge
- [ ] Monitoring dashboards updated (Grafana panels)
- [ ] Alert notifications configured (Prometheus rules)
- [x] Documentation updated

---

*Document Version: 1.0*
*Created: December 2024*
*Author: Claude Code*
