"""Skenario pemindahan beban jam peak ke jam off-peak (Q10-Q12). Semua angka berlabel estimated (tarif asumsi)."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import common as C  # noqa: E402

d = pd.read_csv(C.CLEAN_CSV, parse_dates=["ts", "ts_start"])
d["day"] = d.ts_start.dt.normalize()
d["month"] = d.ts_start.dt.month
d["peak"] = (d.hour >= C.PEAK_START) & (d.hour < C.PEAK_END)
d["rate"] = np.where(d.peak, C.RATE_PEAK, C.RATE_OFF)

# Q12: jam tujuan = jam off-peak dengan beban rata-rata terendah
hourly = d.groupby(["day", "hour"]).kwh.sum().groupby("hour").agg(["mean", "max"]).reset_index().rename(columns={"mean": "kwh_rata2", "max": "kwh_maks"})
hourly["blok"] = np.where((hourly.hour >= C.PEAK_START) & (hourly.hour < C.PEAK_END), "Peak", "Off-peak")
hourly["tarif"] = np.where(hourly.blok == "Peak", C.RATE_PEAK, C.RATE_OFF)
cand = hourly[hourly.blok == "Off-peak"].sort_values("kwh_rata2")
dest = sorted(cand.head(C.N_DEST_HOURS).hour.tolist())
hourly["dipilih_tujuan"] = hourly.hour.isin(dest)
hourly["peringkat_beban_terendah"] = hourly.kwh_rata2.rank(method="first").astype(int)
hourly.to_csv(C.RES_ANALYSIS / "dest_hours.csv", index=False)

base_max = float(d.kwh.max())
base_peak_block_max = float(d[d.peak].kwh.max())
thr = float(d.kwh.quantile(C.HIGH_Q))
base_cost = float((d.kwh * d.rate).sum())
isdest = d.hour.isin(dest).values
rows, mrows, prows = [], [], []
for pct in C.SHIFT_PCTS + [C.MAX_SHIFT]:
    k = d.kwh.values.copy()
    moved_day = d[d.peak].groupby("day").kwh.sum() * pct
    k[d.peak.values] *= (1 - pct)
    nd = d[isdest].groupby("day").size()
    add = (moved_day / nd).reindex(d.day).values
    k[isdest] += add[isdest]
    n = d.assign(k=k)
    moved = float(moved_day.sum())
    sav = n.assign(c0=d.kwh * d.rate, c1=n.k * n.rate)
    dayb = d.groupby("day").kwh.max()
    dest_after = n[isdest].groupby("day").k.max()
    new_peak_days = int((dest_after > dayb).sum())
    m_sav = sav.groupby("month").apply(lambda g: (g.c0 - g.c1).sum(), include_groups=False)
    for mo, v in m_sav.items():
        mrows.append((pct, mo, v))
    rows.append(dict(pct=pct, kwh_dipindah_setahun=moved, kwh_dipindah_per_bulan=moved / 12, penghematan_setahun=float((sav.c0 - sav.c1).sum()), penghematan_per_bulan=float((sav.c0 - sav.c1).sum()) / 12,
                     penghematan_porsi_biaya=float((sav.c0 - sav.c1).sum()) / base_cost, peak_kw_sebelum=base_max * 4, peak_kw_sesudah=float(n.k.max()) * 4,
                     peak_blok_peak_kw_sebelum=base_peak_block_max * 4, peak_blok_peak_kw_sesudah=float(n[n.peak].k.max()) * 4, maks_kw_jam_tujuan_sesudah=float(n[isdest].k.max()) * 4,
                     hari_puncak_baru=new_peak_days, interval_di_atas_p90_sebelum=int((d.kwh > thr).sum()), interval_di_atas_p90_sesudah=int((n.k > thr).sum()),
                     energi_total_beda=float(n.k.sum() - d.kwh.sum())))
    prows.append(pct)
sc = pd.DataFrame(rows)
assert (sc.energi_total_beda.abs() < 1e-6).all(), "energi harus dipertahankan"
assert abs(sc.penghematan_setahun[0] - sc.kwh_dipindah_setahun[0] * (C.RATE_PEAK - C.RATE_OFF)) < 1e-3
sc.to_csv(C.RES_ANALYSIS / "scenarios.csv", index=False)
pd.DataFrame(mrows, columns=["pct", "month", "penghematan"]).to_csv(C.RES_ANALYSIS / "scenarios_monthly.csv", index=False)
print("jam tujuan:", dest); print(sc.round(1).T.to_string())
