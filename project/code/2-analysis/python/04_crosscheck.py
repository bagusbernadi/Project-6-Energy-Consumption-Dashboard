"""Cek silang (Q14): angka KPI dari view SQL dihitung ulang dengan pandas langsung dari CSV bersih."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import common as C  # noqa: E402

d = pd.read_csv(C.CLEAN_CSV, parse_dates=["ts", "ts_start"])
d["peak"] = (d.hour >= C.PEAK_START) & (d.hour < C.PEAK_END)
d["rate"] = np.where(d.peak, C.RATE_PEAK, C.RATE_OFF)
d["cost"] = d.kwh * d.rate
d["month"] = d.ts_start.dt.month
d["wk"] = np.where(d.ts_start.dt.dayofweek >= 5, "Weekend", "Weekday")
rows = []


def cmp(name, sql, pdv, tol=1e-6):
    sql, pdv = np.asarray(sql, float), np.asarray(pdv, float)
    ok = bool(np.allclose(sql, pdv, rtol=0, atol=tol, equal_nan=True))
    rows.append((name, len(np.atleast_1d(sql)), float(np.nanmax(np.abs(sql - pdv))), "PASS" if ok else "FAIL"))


k = pd.read_csv(C.result("kpi_year.csv")).iloc[0]
cmp("total kWh setahun", k.total_kwh, d.kwh.sum())
cmp("biaya setahun", k.cost, d.cost.sum(), 1e-3)
cmp("biaya peak setahun", k.peak_cost, d[d.peak].cost.sum(), 1e-3)
cmp("kWh peak setahun", k.peak_kwh, d[d.peak].kwh.sum())
cmp("beban puncak (kW)", k.peak_kw, d.kwh.max() * 4)
cmp("CO2 setahun", k.co2_t, d.co2_t.sum())
cmp("porsi biaya peak", k.peak_cost_share, d[d.peak].cost.sum() / d.cost.sum(), 1e-9)
m = pd.read_csv(C.result("monthly.csv")).set_index("month")
g = d.groupby("month")
for col, s in (("total_kwh", g.kwh.sum()), ("cost", g.cost.sum()), ("co2_t", g.co2_t.sum()), ("peak_kwh", d[d.peak].groupby("month").kwh.sum())):
    cmp(f"bulanan: {col}", m[col].values, s.values, 1e-3)
cmp("bulanan: peak_kw", m.peak_kw.values, g.kwh.max().values * 4)
dd = pd.read_csv(C.result("daily_trend.csv"), parse_dates=["date"]).set_index("date")
day = d.groupby(d.ts_start.dt.normalize())
cmp("harian: total_kwh", dd.total_kwh.values, day.kwh.sum().values)
cmp("harian: peak_kw", dd.peak_kw.values, day.kwh.max().values * 4)
cmp("harian: biaya", dd.cost.values, day.cost.sum().values, 1e-3)
cmp("harian: load_factor", dd.load_factor.values, (day.kwh.sum() / 24 / (day.kwh.max() * 4)).values, 1e-9)
cmp("harian: porsi biaya peak", dd.peak_cost_share.values, (d[d.peak].groupby(d.ts_start.dt.normalize()).cost.sum() / day.cost.sum()).values, 1e-9)
h = pd.read_csv(C.result("hour_profile.csv"))
hh = d.assign(date=d.ts_start.dt.normalize()).groupby(["wk", "date", "hour"]).kwh.sum().groupby(["wk", "hour"]).mean().reset_index()
cmp("profil jam (weekday dan weekend)", h.sort_values(["week_status", "hour"]).avg_kwh_per_hour.values, hh.sort_values(["wk", "hour"]).kwh.values, 1e-9)
dw = pd.read_csv(C.result("dow_cost.csv")).set_index("day_of_week")
cmp("biaya rata-rata per hari dalam minggu", dw.avg_cost_per_day.sort_index().values, (d.groupby(d.ts_start.dt.day_name()).cost.sum() / d.groupby(d.ts_start.dt.day_name()).ts_start.apply(lambda s: s.dt.normalize().nunique())).sort_index().values, 1e-3)
lt = pd.read_csv(C.result("loadtype_hour.csv"))
cmp("jumlah interval per jam dan Load_Type", lt.sort_values(["hour", "load_type"]).n_intervals.values, d.groupby(["hour", "load_type"]).size().reset_index().sort_values(["hour", "load_type"])[0].values)
pf = pd.read_csv(C.result("pf_hour.csv"))
cmp("interval PF rendah per jam", pf.n_low_pf.values, d.assign(low=d.lag_pf < C.PF_LIMIT).groupby("hour").low.sum().values)
out = pd.DataFrame(rows, columns=["pemeriksaan", "jumlah_nilai", "selisih_maks", "status"])
out.to_csv(C.RES_ANALYSIS / "crosscheck_pandas.csv", index=False)
assert (out.status == "PASS").all(), out
print(len(out), "pemeriksaan,", int(out.jumlah_nilai.sum()), "nilai dibandingkan, semua PASS")
