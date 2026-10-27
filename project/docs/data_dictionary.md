# Kamus data (Project 6)

## Tabel DuckDB (`project/energy.duckdb`)
| Tabel | Kolom penting | Keterangan |
|---|---|---|
| readings | row_id (PK), ts (unik), usage_kwh, lag_kvarh, lead_kvarh, co2_t, lag_pf, lead_pf, load_type, fix_flag | 35.040 interval; CHECK kWh >= 0, PF 0-100, Load_Type dikenal |
| dim_time | ts (FK), ts_start, date, hour, nsm, day_of_week, week_status, month | Turunan waktu |
| dim_tariff | block (PK), start_hour, end_hour, is_peak, rate_per_kwh | 2 blok; tarif asumsi, ubah di sini maka biaya ikut |
| daily_summary | date (PK), total_kwh, peak_kw, load_factor, cost, peak_cost_share, peak_kwh | 365 hari, dari view v_daily |

## CSV mentah UCI
date, Usage_kWh, Lagging_Current_Reactive.Power_kVarh, Leading_Current_Reactive.Power_kVarh, CO2(tCO2), Lagging_Current_Power_Factor, Leading_Current_Power_Factor, NSM, WeekStatus, Day_of_week, Load_Type.

## Kolom hasil
Setiap CSV di `results/` diberi nama sesuai pertanyaan (lihat notebook `results/3-presentation/analysis.ipynb`).
