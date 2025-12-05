-- =============================================================================
-- PEA RE Forecast Platform - Performance Indexes Migration
-- Version: 1.1.0
-- Purpose: Add indexes for frequently queried columns to improve performance
-- =============================================================================

-- =============================================================================
-- ALERTS TABLE INDEXES
-- These indexes support the high-frequency alert queries
-- =============================================================================

-- Index for filtering resolved/unresolved alerts with time ordering
CREATE INDEX IF NOT EXISTS idx_alerts_resolved_time
    ON alerts (resolved, time DESC);

-- Index for prosumer-specific alert queries
CREATE INDEX IF NOT EXISTS idx_alerts_prosumer_time
    ON alerts (target_id, time DESC);

-- Index for severity-based filtering and grouping
CREATE INDEX IF NOT EXISTS idx_alerts_severity
    ON alerts (severity);

-- Index for alert type filtering with time
CREATE INDEX IF NOT EXISTS idx_alerts_type_time
    ON alerts (alert_type, time DESC);

-- Composite index for common alert summary queries
CREATE INDEX IF NOT EXISTS idx_alerts_resolved_severity
    ON alerts (resolved, severity);

-- BRIN index for time-range queries on large tables (more efficient than B-tree)
CREATE INDEX IF NOT EXISTS idx_alerts_time_brin
    ON alerts USING BRIN (time);

-- =============================================================================
-- PREDICTIONS TABLE INDEXES
-- These indexes support forecast history and accuracy calculation queries
-- =============================================================================

-- Index for model type + time queries (forecast history)
CREATE INDEX IF NOT EXISTS idx_predictions_model_time
    ON predictions (model_type, time DESC);

-- Index for target-specific prediction queries
CREATE INDEX IF NOT EXISTS idx_predictions_model_target
    ON predictions (model_type, target_id, time DESC);

-- Partial index for predictions with actual values (accuracy calculations)
CREATE INDEX IF NOT EXISTS idx_predictions_with_actual
    ON predictions (model_type, time DESC, actual_value)
    WHERE actual_value IS NOT NULL;

-- Index for model version lookups
CREATE INDEX IF NOT EXISTS idx_predictions_model_version
    ON predictions (model_version, time DESC);

-- =============================================================================
-- ML MODELS TABLE INDEXES
-- =============================================================================

-- Index for active model lookups by type
CREATE INDEX IF NOT EXISTS idx_ml_models_type_active
    ON ml_models (model_type, is_active);

-- Index for production model queries
CREATE INDEX IF NOT EXISTS idx_ml_models_production
    ON ml_models (model_type, is_production) WHERE is_production = true;

-- =============================================================================
-- SOLAR MEASUREMENTS TABLE INDEXES
-- Additional indexes for drift detection and analysis queries
-- =============================================================================

-- Index for time-range queries (drift detection baseline/current)
CREATE INDEX IF NOT EXISTS idx_solar_time_desc
    ON solar_measurements (time DESC);

-- Index for irradiance-based queries
CREATE INDEX IF NOT EXISTS idx_solar_pyrano1
    ON solar_measurements (pyrano1);

-- =============================================================================
-- SINGLE PHASE METERS TABLE INDEXES
-- =============================================================================

-- Index for voltage range queries
CREATE INDEX IF NOT EXISTS idx_single_phase_voltage
    ON single_phase_meters (energy_meter_voltage);

-- Index for time-range queries with prosumer
CREATE INDEX IF NOT EXISTS idx_single_phase_time_desc
    ON single_phase_meters (time DESC);

-- =============================================================================
-- AUDIT LOG TABLE INDEXES
-- =============================================================================

-- Index for user activity queries
CREATE INDEX IF NOT EXISTS idx_audit_log_user
    ON audit_log (user_id, time DESC);

-- Index for action type queries
CREATE INDEX IF NOT EXISTS idx_audit_log_action
    ON audit_log (action, time DESC);

-- Index for resource queries
CREATE INDEX IF NOT EXISTS idx_audit_log_resource
    ON audit_log (resource_type, resource_id, time DESC);

-- =============================================================================
-- WEATHER EVENTS TABLE INDEXES
-- =============================================================================

-- Index for severity filtering
CREATE INDEX IF NOT EXISTS idx_weather_events_severity
    ON weather_events (severity, time DESC);

-- =============================================================================
-- TIMESCALEDB CONTINUOUS AGGREGATES (Pre-computed summaries)
-- =============================================================================

-- Hourly solar summary (already exists in schema, ensure it's refreshed)
DO $$
BEGIN
    -- Refresh hourly aggregates policy if exists
    IF EXISTS (
        SELECT 1 FROM timescaledb_information.continuous_aggregates
        WHERE view_name = 'solar_hourly'
    ) THEN
        PERFORM add_continuous_aggregate_policy('solar_hourly',
            start_offset => INTERVAL '3 hours',
            end_offset => INTERVAL '1 hour',
            schedule_interval => INTERVAL '1 hour',
            if_not_exists => TRUE
        );
    END IF;
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'Continuous aggregate policy already exists or not applicable';
END $$;

-- =============================================================================
-- CREATE MATERIALIZED VIEW FOR ALERT SUMMARY (Cached for performance)
-- =============================================================================

-- Drop existing view if it exists
DROP MATERIALIZED VIEW IF EXISTS mv_alert_summary_hourly;

-- Create materialized view for hourly alert summaries
CREATE MATERIALIZED VIEW mv_alert_summary_hourly AS
SELECT
    time_bucket('1 hour', time) AS bucket,
    COUNT(*) AS total_alerts,
    COUNT(*) FILTER (WHERE severity = 'critical') AS critical_count,
    COUNT(*) FILTER (WHERE severity = 'warning') AS warning_count,
    COUNT(*) FILTER (WHERE severity = 'info') AS info_count,
    COUNT(*) FILTER (WHERE resolved = false) AS unresolved_count
FROM alerts
GROUP BY bucket
WITH DATA;

-- Index on materialized view
CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_alert_summary_bucket
    ON mv_alert_summary_hourly (bucket);

-- =============================================================================
-- ANALYZE TABLES (Update statistics for query planner)
-- =============================================================================

ANALYZE alerts;
ANALYZE predictions;
ANALYZE ml_models;
ANALYZE solar_measurements;
ANALYZE single_phase_meters;
ANALYZE audit_log;
ANALYZE weather_events;

-- =============================================================================
-- Log completion
-- =============================================================================
DO $$
BEGIN
    RAISE NOTICE 'Performance indexes migration completed successfully!';
    RAISE NOTICE 'Created indexes for: alerts, predictions, ml_models, solar_measurements, single_phase_meters, audit_log, weather_events';
END $$;
