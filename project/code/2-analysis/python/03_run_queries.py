"""Menjalankan view SQL dan menyimpan hasilnya ke CSV (Q1-Q9)."""
import sys
from pathlib import Path

import duckdb
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import common as C  # noqa: E402

C.chdir_root()
con = duckdb.connect(str(C.DB_PATH), read_only=True)
q = lambda sql: con.execute(sql).df()
q("SELECT * FROM v_hour_profile ORDER BY week_status, hour").to_csv(C.RES_ANALYSIS / "hour_profile.csv", index=False)
q("SELECT * FROM v_monthly ORDER BY month").to_csv(C.RES_ANALYSIS / "monthly.csv", index=False)
d = q("SELECT date, total_kwh, peak_kw, load_factor, cost, peak_cost_share, peak_kwh FROM daily_summary ORDER BY date")
d["ma7_kwh"] = d.total_kwh.rolling(7, min_periods=7).mean()
d.to_csv(C.RES_ANALYSIS / "daily_trend.csv", index=False)
q("SELECT * FROM v_dow_cost ORDER BY avg_cost_per_day DESC").to_csv(C.RES_ANALYSIS / "dow_cost.csv", index=False)
q("SELECT * FROM v_loadtype_hour ORDER BY hour, load_type").to_csv(C.RES_ANALYSIS / "loadtype_hour.csv", index=False)
q("SELECT * FROM v_pf_hour ORDER BY hour").to_csv(C.RES_ANALYSIS / "pf_hour.csv", index=False)
k = q("""SELECT count(*) AS n_intervals, sum(usage_kwh) AS total_kwh, sum(cost) AS cost, sum(CASE WHEN is_peak THEN cost ELSE 0 END) AS peak_cost,
         sum(CASE WHEN is_peak THEN usage_kwh ELSE 0 END) AS peak_kwh, max(usage_kwh) * 4 AS peak_kw, sum(co2_t) AS co2_t FROM v_interval""")
k["peak_cost_share"] = k.peak_cost / k.cost
k["load_factor"] = (k.total_kwh / (365 * 24)) / k.peak_kw
k.to_csv(C.RES_ANALYSIS / "kpi_year.csv", index=False)
print(k.round(3).T.to_string())
