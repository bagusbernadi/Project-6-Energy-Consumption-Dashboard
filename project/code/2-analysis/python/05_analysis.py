"""Analisis Q2, Q4, Q5, Q8 dan bukti untuk hipotesis 1-4 (hipotesis 5 dihitung di 06_scenarios.py)."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import common as C  # noqa: E402

d = pd.read_csv(C.CLEAN_CSV, parse_dates=["ts", "ts_start"])
d["day"] = d.ts_start.dt.normalize()
d["wk"] = np.where(d.ts_start.dt.dayofweek >= 5, "Weekend", "Weekday")
hp = pd.read_csv(C.result("hour_profile.csv"))

# Q2: hari kerja vs akhir pekan
dayk = d.groupby(["wk", "day"]).kwh.sum().reset_index()
wv = dayk.groupby("wk").kwh.agg(hari="count", kwh_per_hari="mean", std="std").reset_index()
wv["rasio_terhadap_weekday"] = wv.kwh_per_hari / wv.set_index("wk").kwh_per_hari["Weekday"]
mx = hp.loc[hp.groupby("week_status").avg_kwh_per_hour.idxmax()][["week_status", "hour", "avg_kwh_per_hour"]].rename(columns={"week_status": "wk", "hour": "jam_tertinggi", "avg_kwh_per_hour": "kwh_jam_tertinggi"})
wv.merge(mx, on="wk").to_csv(C.RES_ANALYSIS / "weekday_weekend.csv", index=False)

# Q4: porsi Load_Type dan konsentrasi Maximum per jam
lt = d.groupby("load_type").agg(n=("kwh", "size"), kwh=("kwh", "sum")).reset_index()
lt["porsi_waktu"], lt["porsi_energi"] = lt.n / lt.n.sum(), lt.kwh / lt.kwh.sum()
lt.to_csv(C.RES_ANALYSIS / "loadtype_summary.csv", index=False)
mh = d[d.load_type == "Maximum_Load"].groupby("hour").size().reindex(range(24), fill_value=0)
srt = mh.sort_values(ascending=False)
cum = srt.cumsum() / srt.sum()
conc = pd.DataFrame({"hour": srt.index, "n_maximum": srt.values, "porsi": (srt / srt.sum()).values, "kumulatif": cum.values})
conc.to_csv(C.RES_ANALYSIS / "maximum_by_hour.csv", index=False)
n80 = int((cum < 0.8).sum() + 1)

# Q5: kejadian di atas persentil 90 (interval berturut-turut)
thr = float(d.kwh.quantile(C.HIGH_Q))
above = (d.kwh > thr).values
grp = np.cumsum(np.r_[True, above[1:] != above[:-1]])
ev = d.assign(above=above, grp=grp)[above].groupby("grp").agg(mulai=("ts_start", "min"), n_interval=("kwh", "size"), kwh=("kwh", "sum"), peak_kw=("kwh", lambda s: s.max() * 4)).reset_index(drop=True)
ev["durasi_jam"] = ev.n_interval * C.INTERVAL_MIN / 60
ev["jam_mulai"] = ev.mulai.dt.hour
ev.to_csv(C.RES_ANALYSIS / "high_load_events.csv", index=False)
es = pd.DataFrame([{"ambang_kwh_interval": thr, "persentil": C.HIGH_Q, "n_kejadian": len(ev), "durasi_median_jam": ev.durasi_jam.median(), "durasi_p90_jam": ev.durasi_jam.quantile(0.9),
                    "durasi_maks_jam": ev.durasi_jam.max(), "kejadian_per_hari": len(ev) / 365, "porsi_waktu_di_atas": above.mean(),
                    "jam_mulai_tersering": int(ev.jam_mulai.mode().iloc[0]), "porsi_mulai_jam_tersering": float((ev.jam_mulai == ev.jam_mulai.mode().iloc[0]).mean()),
                    "kejadian_mulai_di_blok_peak": float(((ev.jam_mulai >= C.PEAK_START) & (ev.jam_mulai < C.PEAK_END)).mean())}])
es.to_csv(C.RES_ANALYSIS / "high_load_summary.csv", index=False)

# Q8 dan hipotesis 4: power factor rendah per jenis beban
d["low_pf"] = d.lag_pf < C.PF_LIMIT
pl = d.groupby("load_type").agg(n=("low_pf", "size"), n_low=("low_pf", "sum")).reset_index()
pl["porsi_rendah"] = pl.n_low / pl.n
pl.to_csv(C.RES_ANALYSIS / "pf_by_load.csv", index=False)
pfh = pd.read_csv(C.result("pf_hour.csv"))
pfh["porsi_rendah"] = pfh.n_low_pf / pfh.n_intervals
pfh.to_csv(C.RES_ANALYSIS / "pf_hour.csv", index=False)

hpv = hp.groupby("hour").avg_kwh_per_hour.mean()
hyp = {
    "peak_hour": int(hpv.idxmax()), "min_hour": int(hpv.idxmin()), "peak_hour_wd": int(hp[hp.week_status == "Weekday"].set_index("hour").avg_kwh_per_hour.idxmax()),
    "weekend_ratio": float(wv.set_index("wk").loc["Weekend", "rasio_terhadap_weekday"]), "n_hours_80pct_max": n80,
    "pf_low_light": float(pl.set_index("load_type").loc["Light_Load", "porsi_rendah"]), "pf_low_max": float(pl.set_index("load_type").loc["Maximum_Load", "porsi_rendah"]),
    "pf_low_medium": float(pl.set_index("load_type").loc["Medium_Load", "porsi_rendah"]), "pf_low_all": float(d.low_pf.mean()),
}
pd.DataFrame([hyp]).to_csv(C.RES_ANALYSIS / "hypothesis_evidence.csv", index=False)
print(pd.Series(hyp).round(3).to_string()); print(es.round(3).T.to_string()); print(wv.round(3).to_string())
