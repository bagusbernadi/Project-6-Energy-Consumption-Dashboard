"""Data kecil untuk dashboard: heatmap jam x hari, profil per jam, tren harian, bulanan, skenario."""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import common as C  # noqa: E402

d = pd.read_csv(C.CLEAN_CSV)
h = d.groupby(["date_d", "day_of_week", "hour"]).kwh.sum().reset_index().groupby(["day_of_week", "hour"]).kwh.mean().reset_index().rename(columns={"kwh": "kwh_per_jam"})
h.round(8).to_csv(C.RES_PRESENT / "dash_heatmap.csv", index=False)
for src, dst in [("hour_profile.csv", "dash_hour.csv"), ("daily_trend.csv", "dash_daily.csv"), ("monthly.csv", "dash_monthly.csv"), ("scenarios.csv", "dash_scenarios.csv"),
                 ("pf_hour.csv", "dash_pf.csv"), ("loadtype_summary.csv", "dash_loadtype.csv")]:
    pd.read_csv(C.result(src)).to_csv(C.RES_PRESENT / dst, index=False)
print("dash: heatmap", len(h), "sel")
