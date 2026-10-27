-- View KPI: semua rumus dibuat sekali di sini. Blok tarif ditentukan dari jam interval (blok Off-peak melewati tengah malam).
CREATE OR REPLACE VIEW v_interval AS
SELECT r.ts, t.ts_start, t.date, t.hour, t.day_of_week, t.week_status, t.month, r.usage_kwh, r.lag_pf, r.lag_kvarh, r.co2_t, r.load_type,
       f.block, f.is_peak, f.rate_per_kwh, r.usage_kwh * f.rate_per_kwh AS cost
FROM readings r JOIN dim_time t USING (ts)
JOIN dim_tariff f ON (f.start_hour < f.end_hour AND t.hour >= f.start_hour AND t.hour < f.end_hour)
                  OR (f.start_hour > f.end_hour AND (t.hour >= f.start_hour OR t.hour < f.end_hour));

CREATE OR REPLACE VIEW v_hour_profile AS      -- Q1, Q2: rata-rata kWh per jam (jumlah 4 interval), per status hari
SELECT week_status, hour, avg(hour_kwh) AS avg_kwh_per_hour, count(*) AS n_hours
FROM (SELECT date, week_status, hour, sum(usage_kwh) AS hour_kwh FROM v_interval GROUP BY ALL) GROUP BY ALL;

CREATE OR REPLACE VIEW v_monthly AS           -- Q3, Q6, Q9
SELECT month, sum(usage_kwh) AS total_kwh, sum(cost) AS cost, sum(CASE WHEN is_peak THEN cost ELSE 0 END) AS peak_cost,
       sum(CASE WHEN is_peak THEN usage_kwh ELSE 0 END) AS peak_kwh, sum(co2_t) AS co2_t, max(usage_kwh) * 4 AS peak_kw
FROM v_interval GROUP BY month;

CREATE OR REPLACE VIEW v_dow_cost AS          -- Q7
SELECT day_of_week, count(DISTINCT date) AS n_days, sum(cost) / count(DISTINCT date) AS avg_cost_per_day, sum(usage_kwh) / count(DISTINCT date) AS avg_kwh_per_day
FROM v_interval GROUP BY day_of_week;

CREATE OR REPLACE VIEW v_loadtype_hour AS     -- Q4
SELECT hour, load_type, count(*) AS n_intervals, sum(usage_kwh) AS kwh FROM v_interval GROUP BY ALL;

CREATE OR REPLACE VIEW v_pf_hour AS           -- Q8
SELECT hour, count(*) AS n_intervals, sum(CASE WHEN lag_pf < 85 THEN 1 ELSE 0 END) AS n_low_pf FROM v_interval GROUP BY hour;

CREATE OR REPLACE VIEW v_daily AS             -- sumber tabel daily_summary
SELECT date, sum(usage_kwh) AS total_kwh, max(usage_kwh) * 4 AS peak_kw, (sum(usage_kwh) / 24.0) / (max(usage_kwh) * 4) AS load_factor,
       sum(cost) AS cost, sum(CASE WHEN is_peak THEN cost ELSE 0 END) / sum(cost) AS peak_cost_share,
       sum(CASE WHEN is_peak THEN usage_kwh ELSE 0 END) AS peak_kwh
FROM v_interval GROUP BY date;
