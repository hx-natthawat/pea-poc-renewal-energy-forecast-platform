# ADR-001: Database Selection

## Status

**Accepted**

## Context

The PEA RE Forecast Platform requires a database for storing:

- Time-series sensor data (solar measurements, voltage readings)
- Predictions with timestamps
- Audit logs
- Configuration data

The TOR specifies PostgreSQL as a required database technology.

## Decision

We will use **TimescaleDB** as the primary database.

### Rationale

1. **TOR Compliance**: TimescaleDB is a PostgreSQL extension, fully compliant with the PostgreSQL requirement
2. **Time-Series Optimization**: Purpose-built for time-series data with hypertables
3. **Continuous Aggregates**: Built-in support for pre-computed aggregations
4. **Data Retention**: Native retention policies for automatic data management
5. **Compression**: Automatic time-series compression reduces storage by 90%+
6. **SQL Compatibility**: Standard SQL queries work without modification

### Alternatives Considered

| Option | Pros | Cons |
|--------|------|------|
| Plain PostgreSQL | TOR compliant, simple | No time-series optimization |
| InfluxDB | Time-series native | Not in TOR software list |
| TimescaleDB | TOR compliant, optimized | Learning curve for hypertables |

## Consequences

### Positive

- Efficient storage of high-frequency sensor data
- Fast time-range queries for predictions
- Automatic data lifecycle management
- Standard PostgreSQL tooling works

### Negative

- Additional complexity vs plain PostgreSQL
- Team needs to learn TimescaleDB specifics

### Risks

- TimescaleDB-specific features create vendor lock-in (mitigated: can fallback to plain PostgreSQL)

## Implementation Notes

```sql
-- Example hypertable creation
CREATE TABLE solar_measurements (
    time TIMESTAMPTZ NOT NULL,
    station_id VARCHAR(50),
    power_kw DOUBLE PRECISION
);

SELECT create_hypertable('solar_measurements', 'time',
    chunk_time_interval => INTERVAL '1 day');
```
