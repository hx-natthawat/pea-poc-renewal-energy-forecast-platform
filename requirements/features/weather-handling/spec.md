# Weather Handling Feature - Technical Specification

## 1. Overview

This specification defines the technical implementation for handling extreme weather conditions in the PEA RE Forecast Platform.

**Reference**: Q2.4 - "จะจัดการกับสภาพอากาศที่ผิดปกติ เช่น พายุ หรือ ฝนตกหนัก อย่างไร?"

---

## 2. Weather Alert Integration

### 2.1 TMD API Integration

**Endpoint**: Thai Meteorological Department Weather Alert API

```yaml
tmd_api:
  base_url: "https://data.tmd.go.th/api/v1"
  endpoints:
    current_weather: "/weather/current"
    forecast: "/weather/forecast"
    alerts: "/weather/alerts"
  polling_interval: 300  # 5 minutes
  retry_policy:
    max_retries: 3
    backoff_multiplier: 2
```

### 2.2 Weather Classification Schema

```typescript
enum WeatherCondition {
  CLEAR = "clear",           // kt >= 0.7
  PARTLY_CLOUDY = "partly_cloudy",  // 0.5 <= kt < 0.7
  CLOUDY = "cloudy",         // 0.3 <= kt < 0.5
  RAINY = "rainy",           // kt < 0.3
  STORM = "storm"            // Extreme event flag
}

enum AlertSeverity {
  INFO = "info",
  WARNING = "warning",
  CRITICAL = "critical"
}

interface WeatherAlert {
  id: string;
  timestamp: Date;
  condition: WeatherCondition;
  severity: AlertSeverity;
  region: string;
  description: string;
  expected_duration_minutes: number;
  recommended_action: string;
}
```

### 2.3 Conservative Forecasting Mode

When extreme weather is detected:

| Condition | Irradiance Factor | Uncertainty Multiplier |
|-----------|-------------------|------------------------|
| Clear | 1.0 | 1.0 |
| Partly Cloudy | 0.7 | 1.5 |
| Cloudy | 0.3-0.5 | 2.0 |
| Heavy Rain | 0.0-0.1 | 3.0 |
| Storm | 0.0 | 5.0 |

---

## 3. Ramp Rate Detection

### 3.1 Detection Algorithm

```python
@dataclass
class RampRateConfig:
    """Configuration for ramp rate detection."""
    window_size_seconds: int = 300  # 5 minutes
    threshold_percent: float = 30.0  # 30% change
    min_irradiance: float = 50.0    # W/m² minimum
    alert_cooldown_seconds: int = 60

def detect_ramp_event(
    irradiance_series: pd.Series,
    config: RampRateConfig
) -> Optional[RampEvent]:
    """
    Detect sudden changes in irradiance indicating cloud shadow.

    Args:
        irradiance_series: Time-indexed irradiance values (W/m²)
        config: Detection configuration

    Returns:
        RampEvent if detected, None otherwise
    """
    if len(irradiance_series) < 2:
        return None

    # Calculate rate of change
    current = irradiance_series.iloc[-1]
    previous = irradiance_series.iloc[-2]

    if previous < config.min_irradiance:
        return None

    rate_of_change = (current - previous) / previous * 100

    if abs(rate_of_change) >= config.threshold_percent:
        return RampEvent(
            timestamp=irradiance_series.index[-1],
            rate_percent=rate_of_change,
            direction="down" if rate_of_change < 0 else "up",
            current_irradiance=current,
            previous_irradiance=previous
        )

    return None
```

### 3.2 Cloud Shadow Detection

```python
def detect_cloud_shadow(
    irradiance: np.ndarray,
    clear_sky: np.ndarray,
    timestamps: np.ndarray
) -> list[CloudEvent]:
    """
    Detect cloud shadow events using clearness index.

    Clearness Index (kt) = Measured / Clear Sky

    Classifications:
    - kt >= 0.7: Clear sky
    - 0.5 <= kt < 0.7: Partly cloudy
    - 0.3 <= kt < 0.5: Cloudy
    - kt < 0.3: Heavy clouds/rain
    """
    kt = np.divide(
        irradiance,
        clear_sky,
        out=np.zeros_like(irradiance),
        where=clear_sky > 0
    )

    events = []
    in_cloud = False
    event_start = None

    for i, (t, k) in enumerate(zip(timestamps, kt)):
        if k < 0.5 and not in_cloud:
            in_cloud = True
            event_start = t
        elif k >= 0.7 and in_cloud:
            in_cloud = False
            events.append(CloudEvent(
                start=event_start,
                end=t,
                min_clearness=float(kt[event_start:i].min()),
                avg_clearness=float(kt[event_start:i].mean())
            ))

    return events
```

### 3.3 Variability Index Calculation

```python
def calculate_variability_index(
    irradiance: pd.Series,
    window_minutes: int = 10
) -> pd.Series:
    """
    Calculate variability index for irradiance data.

    VI = std(G) / mean(G) over rolling window

    Interpretation:
    - VI < 0.1: Stable conditions
    - 0.1 <= VI < 0.3: Moderate variability
    - VI >= 0.3: High variability (cloud events likely)
    """
    window = f"{window_minutes}T"
    rolling_mean = irradiance.rolling(window).mean()
    rolling_std = irradiance.rolling(window).std()

    return rolling_std / rolling_mean.replace(0, np.nan)
```

---

## 4. Weather-Adaptive ML Models

### 4.1 Model Architecture

```python
class WeatherAdaptiveForecaster:
    """
    Ensemble forecaster with weather-specific models.
    """

    def __init__(self):
        self.models = {
            WeatherCondition.CLEAR: self._load_model("solar_clear_v1"),
            WeatherCondition.PARTLY_CLOUDY: self._load_model("solar_partly_cloudy_v1"),
            WeatherCondition.CLOUDY: self._load_model("solar_cloudy_v1"),
            WeatherCondition.RAINY: self._load_model("solar_rainy_v1"),
            WeatherCondition.STORM: self._load_model("solar_storm_v1")
        }
        self.classifier = WeatherClassifier()

    def predict(
        self,
        features: pd.DataFrame,
        weather_data: WeatherData
    ) -> ForecastResult:
        """
        Generate weather-adaptive forecast.
        """
        # Classify current weather
        condition = self.classifier.classify(weather_data)

        # Get condition-specific model
        primary_model = self.models[condition]

        # Generate ensemble prediction
        predictions = {}
        weights = self._get_ensemble_weights(condition)

        for cond, model in self.models.items():
            predictions[cond] = model.predict(features)

        # Weighted ensemble
        ensemble_prediction = sum(
            predictions[c] * w
            for c, w in weights.items()
        )

        # Calculate uncertainty
        uncertainty = self._calculate_uncertainty(
            predictions, condition
        )

        return ForecastResult(
            prediction=ensemble_prediction,
            condition=condition,
            uncertainty=uncertainty,
            model_weights=weights
        )

    def _get_ensemble_weights(
        self,
        condition: WeatherCondition
    ) -> dict[WeatherCondition, float]:
        """
        Dynamic ensemble weights based on current condition.

        Primary model gets 60% weight, adjacent conditions share 40%.
        """
        weights = {c: 0.0 for c in WeatherCondition}
        weights[condition] = 0.6

        # Adjacent conditions
        condition_order = list(WeatherCondition)
        idx = condition_order.index(condition)

        if idx > 0:
            weights[condition_order[idx-1]] = 0.2
        if idx < len(condition_order) - 1:
            weights[condition_order[idx+1]] = 0.2

        return weights
```

### 4.2 Weather Classifier

```python
class WeatherClassifier:
    """
    Classify current weather conditions for model selection.
    """

    def __init__(self):
        self.thresholds = {
            "clear_kt": 0.7,
            "partly_cloudy_kt": 0.5,
            "cloudy_kt": 0.3,
            "min_irradiance": 50.0
        }

    def classify(self, weather_data: WeatherData) -> WeatherCondition:
        """
        Classify weather based on clearness index and alerts.
        """
        # Check for storm alerts first
        if weather_data.has_storm_alert:
            return WeatherCondition.STORM

        # Calculate clearness index
        kt = self._calculate_clearness_index(weather_data)

        # Rain check
        if weather_data.precipitation_mm > 1.0:
            return WeatherCondition.RAINY

        # Clearness-based classification
        if kt >= self.thresholds["clear_kt"]:
            return WeatherCondition.CLEAR
        elif kt >= self.thresholds["partly_cloudy_kt"]:
            return WeatherCondition.PARTLY_CLOUDY
        elif kt >= self.thresholds["cloudy_kt"]:
            return WeatherCondition.CLOUDY
        else:
            return WeatherCondition.RAINY

    def _calculate_clearness_index(
        self,
        weather_data: WeatherData
    ) -> float:
        """
        Calculate clearness index from measured and clear sky irradiance.
        """
        clear_sky = calculate_clear_sky_irradiance(
            latitude=weather_data.latitude,
            longitude=weather_data.longitude,
            timestamp=weather_data.timestamp,
            altitude=weather_data.altitude
        )

        if clear_sky < 1.0:
            return 0.0

        return weather_data.irradiance / clear_sky
```

---

## 5. Probabilistic Forecasting

### 5.1 Quantile Regression Model

```python
class ProbabilisticForecaster:
    """
    Generate probabilistic forecasts with P10, P50, P90 quantiles.
    """

    def __init__(self):
        self.quantiles = [0.10, 0.50, 0.90]
        self.models = {
            q: self._build_quantile_model(q)
            for q in self.quantiles
        }

    def predict(
        self,
        features: pd.DataFrame,
        weather_condition: WeatherCondition
    ) -> ProbabilisticForecast:
        """
        Generate forecast with confidence intervals.
        """
        predictions = {}

        for q, model in self.models.items():
            predictions[q] = model.predict(features)

        # Apply weather-based uncertainty adjustment
        uncertainty_multiplier = self._get_uncertainty_multiplier(
            weather_condition
        )

        p50 = predictions[0.50]
        p10 = p50 - (p50 - predictions[0.10]) * uncertainty_multiplier
        p90 = p50 + (predictions[0.90] - p50) * uncertainty_multiplier

        return ProbabilisticForecast(
            p10=np.maximum(p10, 0),  # Power cannot be negative
            p50=p50,
            p90=p90,
            weather_condition=weather_condition,
            uncertainty_factor=uncertainty_multiplier
        )

    def _get_uncertainty_multiplier(
        self,
        condition: WeatherCondition
    ) -> float:
        """
        Weather-dependent uncertainty scaling.
        """
        multipliers = {
            WeatherCondition.CLEAR: 1.0,
            WeatherCondition.PARTLY_CLOUDY: 1.5,
            WeatherCondition.CLOUDY: 2.0,
            WeatherCondition.RAINY: 3.0,
            WeatherCondition.STORM: 5.0
        }
        return multipliers.get(condition, 2.0)
```

### 5.2 Forecast Response Schema

```typescript
interface ProbabilisticForecast {
  timestamp: Date;
  horizon_minutes: number;
  point_forecast: number;          // Best estimate (P50)
  confidence_interval: {
    p10: number;                   // 10th percentile (pessimistic)
    p50: number;                   // 50th percentile (median)
    p90: number;                   // 90th percentile (optimistic)
  };
  weather: {
    condition: WeatherCondition;
    clearness_index: number;
    variability_index: number;
  };
  uncertainty: {
    factor: number;
    is_high_uncertainty: boolean;  // True if factor > 2.0
    reason?: string;               // e.g., "Approaching storm"
  };
  model: {
    version: string;
    primary_model: string;
    ensemble_weights: Record<WeatherCondition, number>;
  };
}
```

---

## 6. Post-Event Learning

### 6.1 Event Database Schema

```sql
-- Extreme weather events table
CREATE TABLE weather_events (
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

SELECT create_hypertable('weather_events', 'time',
    chunk_time_interval => INTERVAL '30 days');

-- Index for querying by event type
CREATE INDEX idx_weather_events_type
    ON weather_events (event_type, time DESC);
```

### 6.2 Event Logger Service

```python
class WeatherEventLogger:
    """
    Log and analyze extreme weather events.
    """

    async def log_event(
        self,
        event: WeatherEvent,
        forecast_data: ForecastData,
        actual_data: ActualData
    ) -> None:
        """
        Log weather event with forecast performance metrics.
        """
        # Calculate forecast error during event
        error_metrics = self._calculate_error_metrics(
            forecast_data, actual_data
        )

        # Store event
        await self.db.execute(
            """
            INSERT INTO weather_events (
                time, event_type, severity, station_id,
                min_irradiance, max_irradiance, min_clearness_index,
                duration_minutes, forecast_error_mape, forecast_error_rmse,
                tmd_alert_id
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            """,
            event.timestamp, event.type, event.severity, event.station_id,
            event.min_irradiance, event.max_irradiance, event.min_clearness_index,
            event.duration_minutes, error_metrics.mape, error_metrics.rmse,
            event.tmd_alert_id
        )

        # Check if retraining is needed
        await self._check_retraining_trigger(event, error_metrics)

    async def _check_retraining_trigger(
        self,
        event: WeatherEvent,
        error_metrics: ErrorMetrics
    ) -> None:
        """
        Trigger model retraining if event performance is poor.
        """
        threshold_mape = 20.0  # Trigger if MAPE > 20%

        if error_metrics.mape > threshold_mape:
            await self.retraining_queue.enqueue(
                RetrainingJob(
                    reason=f"High error during {event.type}",
                    event_id=event.id,
                    target_mape=15.0,
                    include_event_data=True
                )
            )
```

### 6.3 Retraining Pipeline

```python
class WeatherModelRetrainer:
    """
    Automated retraining pipeline for weather-adaptive models.
    """

    async def retrain_from_events(
        self,
        event_ids: list[int],
        condition: WeatherCondition
    ) -> RetrainingResult:
        """
        Retrain condition-specific model with new event data.
        """
        # Fetch event data
        event_data = await self._fetch_event_data(event_ids)

        # Prepare training dataset
        train_data = self._prepare_training_data(
            event_data,
            condition
        )

        # Train new model version
        new_model = self._train_model(train_data, condition)

        # Validate improvement
        validation_metrics = self._validate_model(new_model, condition)

        if validation_metrics.mape < self._get_current_mape(condition):
            # Deploy new model
            await self._deploy_model(new_model, condition)

            return RetrainingResult(
                success=True,
                new_version=new_model.version,
                improvement_percent=(
                    self._get_current_mape(condition) -
                    validation_metrics.mape
                ),
                events_used=len(event_ids)
            )

        return RetrainingResult(
            success=False,
            reason="New model did not improve performance"
        )
```

---

## 7. API Endpoints

### 7.1 Weather Alert Endpoint

```yaml
/api/v1/weather/alerts:
  get:
    summary: Get current weather alerts
    parameters:
      - name: region
        in: query
        type: string
        description: Filter by region
      - name: severity
        in: query
        type: string
        enum: [info, warning, critical]
    responses:
      200:
        content:
          application/json:
            schema:
              type: object
              properties:
                status: string
                data:
                  type: array
                  items:
                    $ref: '#/components/schemas/WeatherAlert'
```

### 7.2 Probabilistic Forecast Endpoint

```yaml
/api/v1/forecast/solar/probabilistic:
  post:
    summary: Get probabilistic solar forecast
    requestBody:
      content:
        application/json:
          schema:
            type: object
            properties:
              timestamp:
                type: string
                format: date-time
              horizon_minutes:
                type: integer
                default: 60
              include_weather:
                type: boolean
                default: true
    responses:
      200:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ProbabilisticForecast'
```

### 7.3 Weather Events Endpoint

```yaml
/api/v1/weather/events:
  get:
    summary: Get historical weather events
    parameters:
      - name: start_date
        in: query
        type: string
        format: date
      - name: end_date
        in: query
        type: string
        format: date
      - name: event_type
        in: query
        type: string
        enum: [storm, heavy_rain, cloud_event]
    responses:
      200:
        content:
          application/json:
            schema:
              type: object
              properties:
                status: string
                data:
                  type: array
                  items:
                    $ref: '#/components/schemas/WeatherEvent'
```

---

## 8. Frontend Components

### 8.1 Weather Alert Banner

```typescript
interface WeatherAlertBannerProps {
  alerts: WeatherAlert[];
  onDismiss: (alertId: string) => void;
}

// Displays critical weather alerts at top of dashboard
// Color-coded by severity: yellow (warning), red (critical)
// Auto-refreshes every 5 minutes
```

### 8.2 Probabilistic Forecast Chart

```typescript
interface ProbabilisticChartProps {
  forecasts: ProbabilisticForecast[];
  actuals?: ActualData[];
  showBands: boolean;
  height?: number;
}

// Shows P10, P50, P90 bands
// Highlights high uncertainty periods
// Color-coded by weather condition
```

### 8.3 Ramp Rate Monitor

```typescript
interface RampRateMonitorProps {
  currentRampRate: number;
  threshold: number;
  recentEvents: RampEvent[];
}

// Real-time ramp rate indicator
// Alerts when threshold exceeded
// Historical ramp events timeline
```

---

## 9. Configuration

```yaml
# config/weather_handling.yaml

weather:
  tmd_api:
    enabled: true
    polling_interval_seconds: 300
    timeout_seconds: 30
    retry_count: 3

  classification:
    clear_sky_threshold: 0.7
    partly_cloudy_threshold: 0.5
    cloudy_threshold: 0.3
    min_irradiance_for_classification: 50.0

  ramp_rate:
    detection_enabled: true
    window_seconds: 300
    threshold_percent: 30.0
    alert_cooldown_seconds: 60

  models:
    ensemble_enabled: true
    primary_weight: 0.6
    adjacent_weight: 0.2
    fallback_condition: "cloudy"

  uncertainty:
    base_multiplier: 1.0
    clear_multiplier: 1.0
    partly_cloudy_multiplier: 1.5
    cloudy_multiplier: 2.0
    rainy_multiplier: 3.0
    storm_multiplier: 5.0

  events:
    logging_enabled: true
    auto_retraining_enabled: true
    retraining_mape_threshold: 20.0
    min_events_for_retraining: 10
```

---

## 10. Testing Requirements

### 10.1 Unit Tests

- Weather classifier accuracy tests
- Ramp rate detection tests
- Uncertainty calculation tests
- Ensemble weight calculation tests

### 10.2 Integration Tests

- TMD API integration tests
- End-to-end forecast pipeline tests
- Event logging tests
- Retraining pipeline tests

### 10.3 Performance Tests

- Classification latency < 10ms
- Forecast generation < 500ms
- Ramp rate detection < 50ms

---

*Document Version: 1.0*
*Created: December 2024*
*Author: Claude Code*
