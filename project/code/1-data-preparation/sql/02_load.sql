-- Memuat data bersih dan tarif (parameter: $peak_start, $peak_end, $rate_peak, $rate_off lewat skrip 02_build_db.py).
INSERT INTO readings
SELECT row_id, ts, kwh, lag_kvarh, lead_kvarh, lag_pf, lead_pf, co2_t, load_type, fix_flag
FROM read_csv('data/clean/readings_clean.csv', header = true, timestampformat = '%Y-%m-%d %H:%M:%S');

INSERT INTO dim_time
SELECT ts, ts_start, CAST(ts_start AS DATE), EXTRACT(hour FROM ts_start),
       EXTRACT(hour FROM ts_start) * 3600 + EXTRACT(minute FROM ts_start) * 60,
       dayname(ts_start), CASE WHEN dayofweek(ts_start) IN (0, 6) THEN 'Weekend' ELSE 'Weekday' END, EXTRACT(month FROM ts_start)
FROM (SELECT r.ts, r.ts - INTERVAL 15 MINUTE AS ts_start FROM readings r);

INSERT INTO dim_tariff VALUES ('Peak', $peak_start, $peak_end, TRUE, $rate_peak), ('Off-peak', $peak_end, $peak_start, FALSE, $rate_off);
