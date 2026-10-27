"""Infografis satu halaman (PNG + PDF) dari CSV hasil."""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import common as C  # noqa: E402

R = lambda n: pd.read_csv(C.result(n))
k, hr, sc, pf = R("kpi_year.csv").iloc[0], R("hour_profile.csv"), R("scenarios.csv"), R("pf_hour.csv")
h = hr.groupby(["week_status", "hour"]).avg_kwh_per_hour.mean().unstack(0)
fig = plt.figure(figsize=(11.7, 8.3)); fig.suptitle("Project 6: Pola Konsumsi Listrik Pabrik Baja (2018)", fontsize=18, fontweight="bold", x=0.05, ha="left")
t = fig.add_axes([0.05, 0.80, 0.9, 0.1]); t.axis("off")
for i, (lb, v) in enumerate([("Energi setahun", f"{k.total_kwh/1000:,.0f} MWh"), ("Puncak", f"{k.peak_kw:,.0f} kW"), ("Load factor", f"{k.load_factor:.2f}"), ("Biaya jam peak", f"{k.peak_cost_share:.0%} (tarif asumsi)")]):
    t.text(i * 0.25, 0.55, v, fontsize=18, fontweight="bold", color="#174EA6"); t.text(i * 0.25, 0.1, lb, fontsize=11, color="#5f6368")
a1 = fig.add_axes([0.07, 0.42, 0.40, 0.30]); a1.plot(h.index, h.Weekday, label="Hari kerja", color="#1a73e8"); a1.plot(h.index, h.Weekend, label="Akhir pekan", color="#e37400")
a1.axvspan(17, 22, color="#d93025", alpha=.1); a1.set_title("kWh per jam (area merah = tarif peak)", fontsize=11, loc="left"); a1.legend(frameon=False)
a2 = fig.add_axes([0.57, 0.42, 0.38, 0.30]); a2.bar(pf.hour, pf.porsi_rendah, color="#188038"); a2.set_title("Porsi interval power factor rendah (<85) per jam", fontsize=11, loc="left")
a3 = fig.add_axes([0.07, 0.08, 0.40, 0.24]); a3.bar([f"{int(p*100)}%" for p in sc.pct], sc.penghematan_per_bulan / 1e6, color="#1a73e8"); a3.set_title("Penghematan bila beban peak dipindah (juta Rp/bulan, batas atas)", fontsize=11, loc="left")
n = fig.add_axes([0.57, 0.08, 0.38, 0.24]); n.axis("off")
n.text(0, 0.85, "Temuan", fontweight="bold", fontsize=12)
n.text(0, 0.75, "Puncak beban jam 9, bukan jam tarif peak (17-22).\nAkhir pekan ~35% dari hari kerja.\nPF rendah paling sering saat beban ringan.\nTarif dan penghematan adalah asumsi/estimasi.", fontsize=10.5, va="top", linespacing=1.6)
for a in (a1, a2, a3):
    a.spines[["top", "right"]].set_visible(False)
fig.savefig(C.RES_PRESENT / "infographic.png", dpi=150); fig.savefig(C.RES_PRESENT / "infographic.pdf")
print("infografis ditulis")
