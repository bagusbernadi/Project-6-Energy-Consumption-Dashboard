-- Skema energy.duckdb: 4 tabel (readings, dim_time, dim_tariff, daily_summary). Dijalankan dari folder project/.
DROP VIEW IF EXISTS v_interval;
DROP TABLE IF EXISTS daily_summary;
DROP TABLE IF EXISTS dim_tariff;
DROP TABLE IF EXISTS dim_time;
DROP TABLE IF EXISTS readings;

CREATE TABLE readings (
    row_id      INTEGER PRIMARY KEY,
    ts          TIMESTAMP NOT NULL UNIQUE,                  -- akhir interval (label terkoreksi)
    usage_kwh   DOUBLE NOT NULL CHECK (usage_kwh >= 0),
    lag_kvarh   DOUBLE NOT NULL CHECK (lag_kvarh >= 0),
    lead_kvarh  DOUBLE NOT NULL CHECK (lead_kvarh >= 0),
    lag_pf      DOUBLE NOT NULL CHECK (lag_pf BETWEEN 0 AND 100),
    lead_pf     DOUBLE NOT NULL CHECK (lead_pf BETWEEN 0 AND 100),
    co2_t       DOUBLE NOT NULL CHECK (co2_t >= 0),
    load_type   VARCHAR NOT NULL CHECK (load_type IN ('Light_Load', 'Medium_Load', 'Maximum_Load')),
    fix_flag    VARCHAR NOT NULL CHECK (fix_flag IN ('ok', 'tanggal_00_00_digeser'))
);
CREATE TABLE dim_time (
    ts            TIMESTAMP PRIMARY KEY REFERENCES readings (ts),
    ts_start      TIMESTAMP NOT NULL,
    date          DATE NOT NULL,
    hour          INTEGER NOT NULL CHECK (hour BETWEEN 0 AND 23),
    nsm           INTEGER NOT NULL CHECK (nsm BETWEEN 0 AND 85500),   -- detik sejak tengah malam, awal interval
    day_of_week   VARCHAR NOT NULL,
    week_status   VARCHAR NOT NULL CHECK (week_status IN ('Weekday', 'Weekend')),
    month         INTEGER NOT NULL CHECK (month BETWEEN 1 AND 12)
);
CREATE TABLE dim_tariff (
    block         VARCHAR PRIMARY KEY,
    start_hour    INTEGER NOT NULL CHECK (start_hour BETWEEN 0 AND 23),
    end_hour      INTEGER NOT NULL CHECK (end_hour BETWEEN 1 AND 24),
    is_peak       BOOLEAN NOT NULL,
    rate_per_kwh  DOUBLE NOT NULL CHECK (rate_per_kwh > 0)    -- ASUMSI; ganti di sini, semua biaya ikut berubah
);
CREATE TABLE daily_summary (
    date             DATE PRIMARY KEY,
    total_kwh        DOUBLE NOT NULL,
    peak_kw          DOUBLE NOT NULL,       -- interval tertinggi x 4
    load_factor      DOUBLE NOT NULL,       -- rata-rata kW / peak_kw
    cost             DOUBLE NOT NULL,
    peak_cost_share  DOUBLE NOT NULL,
    peak_kwh         DOUBLE NOT NULL
);
