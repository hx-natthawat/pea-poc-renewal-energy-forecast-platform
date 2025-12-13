-- =============================================================================
-- PEA RE Forecast Platform - Network Model for DOE (Mock GIS Data)
-- =============================================================================
-- This provides a simulated network model based on the POC topology
-- for DOE (Dynamic Operating Envelope) calculations.
--
-- Replace with actual GIS data from กฟภ. when available.
-- =============================================================================

-- =============================================================================
-- NETWORK TRANSFORMERS
-- =============================================================================
CREATE TABLE IF NOT EXISTS network_transformers (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    name_th VARCHAR(100),

-- Ratings
rated_power_kva DOUBLE PRECISION NOT NULL,
primary_voltage_kv DOUBLE PRECISION NOT NULL,
secondary_voltage_v DOUBLE PRECISION NOT NULL,

-- Impedance (per unit)
impedance_pu DOUBLE PRECISION DEFAULT 0.04, -- 4% typical for distribution
x_r_ratio DOUBLE PRECISION DEFAULT 5.0,

-- Thermal limits
max_current_a DOUBLE PRECISION,
emergency_rating_pct DOUBLE PRECISION DEFAULT 120,

-- Location
latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Insert POC transformer (50 kVA, 22kV/0.4kV)
INSERT INTO
    network_transformers (
        id,
        name,
        name_th,
        rated_power_kva,
        primary_voltage_kv,
        secondary_voltage_v,
        max_current_a
    )
VALUES (
        'TX_50KVA_01',
        'POC Distribution Transformer',
        'หม้อแปลงทดสอบสาธิต',
        50,
        22,
        400,
        72.2
    ) ON CONFLICT (id) DO NOTHING;

-- =============================================================================
-- NETWORK NODES (Buses)
-- =============================================================================
CREATE TABLE IF NOT EXISTS network_nodes (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    node_type VARCHAR(20) NOT NULL CHECK (node_type IN ('slack', 'pq', 'pv', 'load')),
    phase CHAR(1) CHECK (phase IN ('A', 'B', 'C', 'N')),  -- N for 3-phase

-- Nominal values
nominal_voltage_v DOUBLE PRECISION NOT NULL,

-- Connected equipment
transformer_id VARCHAR(50) REFERENCES network_transformers (id),
prosumer_id VARCHAR(50) REFERENCES prosumers (id),

-- Position in feeder (meters from transformer)
distance_from_tx_m DOUBLE PRECISION DEFAULT 0,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Insert network nodes for POC topology
-- Node 0: LV busbar (slack reference)
INSERT INTO
    network_nodes (
        id,
        name,
        node_type,
        phase,
        nominal_voltage_v,
        transformer_id,
        distance_from_tx_m
    )
VALUES (
        'node_lv_bus',
        'LV Busbar',
        'slack',
        'N',
        400,
        'TX_50KVA_01',
        0
    ),
    -- Phase A nodes (prosumer3 -> prosumer2 -> prosumer1)
    (
        'node_a1',
        'Phase A Node 1',
        'pq',
        'A',
        230,
        'TX_50KVA_01',
        50
    ),
    (
        'node_a2',
        'Phase A Node 2',
        'pq',
        'A',
        230,
        'TX_50KVA_01',
        100
    ),
    (
        'node_a3',
        'Phase A Node 3',
        'pq',
        'A',
        230,
        'TX_50KVA_01',
        150
    ),
    -- Phase B nodes (prosumer6 -> prosumer4 -> prosumer5)
    (
        'node_b1',
        'Phase B Node 1',
        'pq',
        'B',
        230,
        'TX_50KVA_01',
        50
    ),
    (
        'node_b2',
        'Phase B Node 2',
        'pq',
        'B',
        230,
        'TX_50KVA_01',
        100
    ),
    (
        'node_b3',
        'Phase B Node 3',
        'pq',
        'B',
        230,
        'TX_50KVA_01',
        150
    ),
    -- Phase C nodes (prosumer7 only)
    (
        'node_c1',
        'Phase C Node 1',
        'pq',
        'C',
        230,
        'TX_50KVA_01',
        50
    ) ON CONFLICT (id) DO NOTHING;

-- Link prosumers to nodes
UPDATE network_nodes
SET
    prosumer_id = 'prosumer3'
WHERE
    id = 'node_a1';

UPDATE network_nodes
SET
    prosumer_id = 'prosumer2'
WHERE
    id = 'node_a2';

UPDATE network_nodes
SET
    prosumer_id = 'prosumer1'
WHERE
    id = 'node_a3';

UPDATE network_nodes
SET
    prosumer_id = 'prosumer6'
WHERE
    id = 'node_b1';

UPDATE network_nodes
SET
    prosumer_id = 'prosumer4'
WHERE
    id = 'node_b2';

UPDATE network_nodes
SET
    prosumer_id = 'prosumer5'
WHERE
    id = 'node_b3';

UPDATE network_nodes
SET
    prosumer_id = 'prosumer7'
WHERE
    id = 'node_c1';

-- =============================================================================
-- NETWORK BRANCHES (Lines/Cables)
-- =============================================================================
CREATE TABLE IF NOT EXISTS network_branches (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    branch_type VARCHAR(20) NOT NULL CHECK (branch_type IN ('line', 'cable', 'switch')),

-- Connectivity
from_node_id VARCHAR(50) NOT NULL REFERENCES network_nodes (id),
to_node_id VARCHAR(50) NOT NULL REFERENCES network_nodes (id),

-- Electrical parameters (per km)
length_m DOUBLE PRECISION NOT NULL,
r_ohm_per_km DOUBLE PRECISION NOT NULL, -- Resistance
x_ohm_per_km DOUBLE PRECISION NOT NULL, -- Reactance

-- Thermal limits
max_current_a DOUBLE PRECISION NOT NULL, -- Ampacity

-- Status
is_closed BOOLEAN DEFAULT true,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Insert LV cables for POC network
-- Typical LV cable: 95mm² Al, R=0.32 Ω/km, X=0.08 Ω/km, Imax=200A
INSERT INTO
    network_branches (
        id,
        name,
        branch_type,
        from_node_id,
        to_node_id,
        length_m,
        r_ohm_per_km,
        x_ohm_per_km,
        max_current_a
    )
VALUES
    -- Phase A feeder
    (
        'branch_a0',
        'LV Bus to A1',
        'cable',
        'node_lv_bus',
        'node_a1',
        50,
        0.32,
        0.08,
        200
    ),
    (
        'branch_a1',
        'A1 to A2',
        'cable',
        'node_a1',
        'node_a2',
        50,
        0.32,
        0.08,
        200
    ),
    (
        'branch_a2',
        'A2 to A3',
        'cable',
        'node_a2',
        'node_a3',
        50,
        0.32,
        0.08,
        200
    ),
    -- Phase B feeder
    (
        'branch_b0',
        'LV Bus to B1',
        'cable',
        'node_lv_bus',
        'node_b1',
        50,
        0.32,
        0.08,
        200
    ),
    (
        'branch_b1',
        'B1 to B2',
        'cable',
        'node_b1',
        'node_b2',
        50,
        0.32,
        0.08,
        200
    ),
    (
        'branch_b2',
        'B2 to B3',
        'cable',
        'node_b2',
        'node_b3',
        50,
        0.32,
        0.08,
        200
    ),
    -- Phase C feeder
    (
        'branch_c0',
        'LV Bus to C1',
        'cable',
        'node_lv_bus',
        'node_c1',
        50,
        0.32,
        0.08,
        200
    ) ON CONFLICT (id) DO NOTHING;

-- =============================================================================
-- DOE LIMITS (Calculated operating envelopes)
-- =============================================================================
CREATE TABLE IF NOT EXISTS doe_limits (
    id BIGSERIAL,
    time TIMESTAMPTZ NOT NULL,
    prosumer_id VARCHAR(50) NOT NULL REFERENCES prosumers(id),

-- Operating limits (kW)
export_limit_kw DOUBLE PRECISION NOT NULL,
import_limit_kw DOUBLE PRECISION NOT NULL,

-- Binding constraint
limiting_factor VARCHAR(50) NOT NULL, -- 'voltage', 'thermal', 'protection'

-- Predictions used
predicted_voltage_v DOUBLE PRECISION,
predicted_load_kw DOUBLE PRECISION,
predicted_re_kw DOUBLE PRECISION,

-- Confidence & validity
confidence DOUBLE PRECISION DEFAULT 0.95,
valid_until TIMESTAMPTZ NOT NULL,

-- Metadata
calculation_time_ms INTEGER,
    model_version VARCHAR(50),

    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (id, time)
);

SELECT create_hypertable (
        'doe_limits', 'time', chunk_time_interval = > INTERVAL '1 day', if_not_exists = > TRUE
    );

CREATE INDEX IF NOT EXISTS idx_doe_prosumer ON doe_limits (prosumer_id, time DESC);

-- =============================================================================
-- NETWORK CONSTRAINTS (Operating limits)
-- =============================================================================
CREATE TABLE IF NOT EXISTS network_constraints (
    id VARCHAR(50) PRIMARY KEY,
    constraint_type VARCHAR(50) NOT NULL,  -- 'voltage_upper', 'voltage_lower', 'thermal', 'protection'

-- Limits
limit_value DOUBLE PRECISION NOT NULL, unit VARCHAR(20) NOT NULL,

-- Applicability
applies_to VARCHAR(50), -- node_id, branch_id, or 'all'

-- Priority (lower = more critical)
priority INTEGER DEFAULT 1,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Insert voltage constraints (TOR: 230V ± 5%)
INSERT INTO
    network_constraints (
        id,
        constraint_type,
        limit_value,
        unit,
        applies_to,
        priority
    )
VALUES (
        'voltage_upper',
        'voltage_upper',
        242,
        'V',
        'all',
        1
    ), -- +5%
    (
        'voltage_lower',
        'voltage_lower',
        218,
        'V',
        'all',
        1
    ), -- -5%
    (
        'thermal_cable',
        'thermal',
        200,
        'A',
        'all',
        2
    ),
    (
        'thermal_tx',
        'thermal',
        72.2,
        'A',
        'TX_50KVA_01',
        1
    ) ON CONFLICT (id) DO NOTHING;

-- =============================================================================
-- VIEW: Network topology with current status
-- =============================================================================
CREATE OR REPLACE VIEW network_topology_view AS
SELECT
    n.id AS node_id,
    n.name AS node_name,
    n.phase,
    n.nominal_voltage_v,
    n.distance_from_tx_m,
    p.id AS prosumer_id,
    p.name AS prosumer_name,
    p.has_pv,
    p.has_ev,
    p.pv_capacity_kw,
    t.id AS transformer_id,
    t.rated_power_kva AS tx_capacity_kva
FROM
    network_nodes n
    LEFT JOIN prosumers p ON n.prosumer_id = p.id
    LEFT JOIN network_transformers t ON n.transformer_id = t.id
WHERE
    n.id != 'node_lv_bus'
ORDER BY n.phase, n.distance_from_tx_m;

-- =============================================================================
-- COMMENT
-- =============================================================================
COMMENT ON
TABLE network_transformers IS 'Distribution transformers for power flow analysis';

COMMENT ON
TABLE network_nodes IS 'Network buses/nodes for topology modeling';

COMMENT ON
TABLE network_branches IS 'Lines and cables connecting nodes';

COMMENT ON
TABLE doe_limits IS 'Calculated Dynamic Operating Envelope limits per prosumer';

COMMENT ON
TABLE network_constraints IS 'Operating constraints for DOE calculations';