-- =============================================================================
-- PEA RE Forecast Platform - Database Initialization
-- =============================================================================

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS timescaledb;
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- =============================================================================
-- SOLAR MEASUREMENTS (RE Forecast Data)
-- =============================================================================
CREATE TABLE IF NOT EXISTS solar_measurements (
    time TIMESTAMPTZ NOT NULL,
    station_id VARCHAR(50) DEFAULT 'POC_STATION_1',

    -- Temperature sensors (°C)
    pvtemp1 DOUBLE PRECISION,
    pvtemp2 DOUBLE PRECISION,
    ambtemp DOUBLE PRECISION,

    -- Irradiance sensors (W/m²)
    pyrano1 DOUBLE PRECISION,
    pyrano2 DOUBLE PRECISION,

    -- Environmental
    windspeed DOUBLE PRECISION,

    -- Output (Target variable)
    power_kw DOUBLE PRECISION,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (time, station_id)
);

SELECT create_hypertable('solar_measurements', 'time',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE);

CREATE INDEX IF NOT EXISTS idx_solar_station ON solar_measurements (station_id, time DESC);

-- =============================================================================
-- PROSUMER NETWORK TOPOLOGY
-- =============================================================================
CREATE TABLE IF NOT EXISTS prosumers (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    phase CHAR(1) NOT NULL CHECK (phase IN ('A', 'B', 'C')),
    position_in_phase INTEGER NOT NULL,
    has_pv BOOLEAN DEFAULT false,
    has_ev BOOLEAN DEFAULT false,
    has_battery BOOLEAN DEFAULT false,
    pv_capacity_kw DOUBLE PRECISION,
    transformer_id VARCHAR(50) DEFAULT 'TX_50KVA_01',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Insert prosumer topology
INSERT INTO prosumers (id, name, phase, position_in_phase, has_pv, has_ev) VALUES
    ('prosumer1', 'Prosumer 1', 'A', 3, true, true),
    ('prosumer2', 'Prosumer 2', 'A', 2, true, false),
    ('prosumer3', 'Prosumer 3', 'A', 1, true, false),
    ('prosumer4', 'Prosumer 4', 'B', 2, true, false),
    ('prosumer5', 'Prosumer 5', 'B', 3, true, true),
    ('prosumer6', 'Prosumer 6', 'B', 1, true, false),
    ('prosumer7', 'Prosumer 7', 'C', 1, true, true)
ON CONFLICT (id) DO NOTHING;

-- =============================================================================
-- SINGLE-PHASE METER DATA (Voltage Prediction)
-- =============================================================================
CREATE TABLE IF NOT EXISTS single_phase_meters (
    time TIMESTAMPTZ NOT NULL,
    prosumer_id VARCHAR(50) NOT NULL REFERENCES prosumers(id),

    active_power DOUBLE PRECISION,
    reactive_power DOUBLE PRECISION,
    energy_meter_active_power DOUBLE PRECISION,
    energy_meter_current DOUBLE PRECISION,
    energy_meter_voltage DOUBLE PRECISION,
    energy_meter_reactive_power DOUBLE PRECISION,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (time, prosumer_id)
);

SELECT create_hypertable('single_phase_meters', 'time',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE);

CREATE INDEX IF NOT EXISTS idx_single_phase_prosumer ON single_phase_meters (prosumer_id, time DESC);

-- =============================================================================
-- THREE-PHASE METER DATA (Transformer level)
-- =============================================================================
CREATE TABLE IF NOT EXISTS three_phase_meters (
    time TIMESTAMPTZ NOT NULL,
    meter_id VARCHAR(50) NOT NULL DEFAULT 'TX_METER_01',

    p1_amp DOUBLE PRECISION,
    p1_volt DOUBLE PRECISION,
    p1_w DOUBLE PRECISION,

    p2_amp DOUBLE PRECISION,
    p2_volt DOUBLE PRECISION,
    p2_w DOUBLE PRECISION,

    p3_amp DOUBLE PRECISION,
    p3_volt DOUBLE PRECISION,
    p3_w DOUBLE PRECISION,

    q1_var DOUBLE PRECISION,
    q2_var DOUBLE PRECISION,
    q3_var DOUBLE PRECISION,

    total_w DOUBLE PRECISION,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (time, meter_id)
);

SELECT create_hypertable('three_phase_meters', 'time',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE);

-- =============================================================================
-- PREDICTIONS TABLE
-- =============================================================================
CREATE TABLE IF NOT EXISTS predictions (
    id BIGSERIAL,
    time TIMESTAMPTZ NOT NULL,
    model_type VARCHAR(20) NOT NULL CHECK (model_type IN ('solar', 'voltage')),
    model_version VARCHAR(50) NOT NULL,
    target_id VARCHAR(50),
    horizon_minutes INTEGER,

    predicted_value DOUBLE PRECISION NOT NULL,
    confidence_lower DOUBLE PRECISION,
    confidence_upper DOUBLE PRECISION,
    actual_value DOUBLE PRECISION,

    features JSONB,
    prediction_time_ms INTEGER,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (id, time)
);

SELECT create_hypertable('predictions', 'time',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE);

-- =============================================================================
-- ML MODEL REGISTRY
-- =============================================================================
CREATE TABLE IF NOT EXISTS ml_models (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    version VARCHAR(50) NOT NULL,
    model_type VARCHAR(20) NOT NULL,
    metrics JSONB NOT NULL DEFAULT '{}',
    parameters JSONB NOT NULL DEFAULT '{}',
    features_used JSONB NOT NULL DEFAULT '[]',
    file_path VARCHAR(500),
    is_active BOOLEAN DEFAULT false,
    is_production BOOLEAN DEFAULT false,
    trained_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(name, version)
);

-- =============================================================================
-- ALERTS TABLE
-- =============================================================================
CREATE TABLE IF NOT EXISTS alerts (
    id BIGSERIAL,
    time TIMESTAMPTZ NOT NULL,
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('info', 'warning', 'critical')),
    target_id VARCHAR(50),
    message TEXT NOT NULL,
    current_value DOUBLE PRECISION,
    threshold_value DOUBLE PRECISION,
    acknowledged BOOLEAN DEFAULT false,
    resolved BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (id, time)
);

SELECT create_hypertable('alerts', 'time',
    chunk_time_interval => INTERVAL '7 days',
    if_not_exists => TRUE);

-- =============================================================================
-- AUDIT LOG
-- =============================================================================
CREATE TABLE IF NOT EXISTS audit_log (
    id BIGSERIAL,
    time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    user_id VARCHAR(100),
    user_email VARCHAR(255),
    user_ip INET,
    action VARCHAR(50) NOT NULL,
    resource_type VARCHAR(50),
    resource_id VARCHAR(100),
    request_method VARCHAR(10),
    request_path TEXT,
    request_body JSONB,
    response_status INTEGER,
    user_agent TEXT,
    session_id VARCHAR(100),
    PRIMARY KEY (id, time)
);

SELECT create_hypertable('audit_log', 'time',
    chunk_time_interval => INTERVAL '7 days',
    if_not_exists => TRUE);

-- =============================================================================
-- DATA INGESTION LOG (Track file ingestion history)
-- =============================================================================
CREATE TABLE IF NOT EXISTS data_ingestion_log (
    id BIGSERIAL PRIMARY KEY,
    file_name VARCHAR(255) NOT NULL,
    file_hash VARCHAR(64) NOT NULL UNIQUE,
    status VARCHAR(20) NOT NULL CHECK (status IN ('success', 'partial', 'failed', 'skipped')),
    records_total INTEGER DEFAULT 0,
    records_inserted INTEGER DEFAULT 0,
    records_updated INTEGER DEFAULT 0,
    records_skipped INTEGER DEFAULT 0,
    errors TEXT,
    duration_seconds DOUBLE PRECISION,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ingestion_log_hash ON data_ingestion_log (file_hash);
CREATE INDEX IF NOT EXISTS idx_ingestion_log_created ON data_ingestion_log (created_at DESC);

-- =============================================================================
-- Grant permissions
-- =============================================================================
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;

-- Log completion
DO $$
BEGIN
    RAISE NOTICE 'Database initialization completed successfully!';
END $$;
