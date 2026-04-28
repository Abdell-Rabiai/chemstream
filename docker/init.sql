-- ===================================================================
-- ChemStream — TimescaleDB schema initialization
-- Runs automatically on first container startup.
-- ===================================================================

-- 1. Enable the TimescaleDB extension on this database.
--    The extension binary ships with the image; this step "turns it on"
--    for our specific database.
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- 2. Main table: every sensor reading processed by Faust lands here.
CREATE TABLE IF NOT EXISTS sensor_readings (
    time       TIMESTAMPTZ      NOT NULL,
    sensor_id  TEXT             NOT NULL,
    value_raw  DOUBLE PRECISION NOT NULL,
    value_avg  DOUBLE PRECISION,                 -- NULL while rolling window is filling
    fault      INTEGER          NOT NULL DEFAULT 0,
    sample     INTEGER          NOT NULL
);

-- 3. Convert the regular table into a TimescaleDB hypertable.
--    'time' is the partitioning column. TimescaleDB will create chunks
--    automatically (default: one chunk per 7 days of data).
SELECT create_hypertable(
    'sensor_readings',
    'time',
    if_not_exists => TRUE
);

-- 4. Index for the most common query pattern:
--    "give me values for sensor X over time range Y".
--    Composite index on (sensor_id, time DESC) makes those queries fast.
CREATE INDEX IF NOT EXISTS idx_sensor_readings_sensor_time
    ON sensor_readings (sensor_id, time DESC);

-- 5. Index for fault-based queries (e.g., "show all readings during fault episodes").
CREATE INDEX IF NOT EXISTS idx_sensor_readings_fault_time
    ON sensor_readings (fault, time DESC)
    WHERE fault <> 0;   -- partial index: only index actual faults, ignore the 95%+ "fault=0" rows

-- 6. Sanity-check view: quick summary of what's in the table.
CREATE OR REPLACE VIEW sensor_readings_summary AS
SELECT
    sensor_id,
    COUNT(*)         AS row_count,
    MIN(time)        AS first_seen,
    MAX(time)        AS last_seen,
    ROUND(AVG(value_raw)::numeric, 4) AS avg_value
FROM sensor_readings
GROUP BY sensor_id
ORDER BY sensor_id;