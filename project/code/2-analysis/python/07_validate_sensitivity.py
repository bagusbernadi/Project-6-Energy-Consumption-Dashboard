"""Q13 sensitivitas label waktu, uji perubahan tarif lewat dim_tariff, dan verdict hipotesis."""
import shutil
import sys
import tempfile
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import common as C  # noqa: E402

C.chdir_root()
d = pd.read_csv(C.CLEAN_CSV, parse_dates=["ts", "ts_start"])
raw = pd.read_csv(C.RAW_CSV)
raw.columns = ["date", "kwh", "lag_kvarh", "lead_kvarh", "co2_t", "lag_pf", "lead_pf", "nsm", "week_status", "day_of_week", "load_type"]
raw["ts_raw"] = pd.to_datetime(raw.date, format="%d/%m/%Y %H:%M")

def prof(hour, day):
    t = pd.DataFrame({"h": hour, "d": day, "k": d.kwh.values}).groupby(["d", "h"]).k.sum().groupby("h").mean()
    return t

# Q13: tiga cara membaca label: A=akhir interval terkoreksi (dipakai), B=label mentah sebagai awal, C=akhir interval tanpa koreksi 00:00
a = prof(d.ts_start.dt.hour.values, d.ts_start.dt.date.values)
b = prof(raw.ts_raw.dt.hour.values, raw.ts_raw.dt.date.values)
c = prof(((raw.ts_raw - pd.Timedelta(minutes=15)).dt.hour).values, (raw.ts_raw - pd.Timedelta(minutes=15)).dt.date.values)
def cost(hours):
    rate = np.where((hours >= C.PEAK_START) & (hours < C.PEAK_END), C.RATE_PEAK, C.RATE_OFF)
    return float((d.kwh.values * rate).sum())
ha, hb, hc = d.ts_start.dt.hour.values, raw.ts_raw.dt.hour.values, (raw.ts_raw - pd.Timedelta(minutes=15)).dt.hour.values
rows = []
for name, p, h in [("A terkoreksi (dipakai)", a, ha), ("B label mentah = awal interval", b, hb), ("C akhir interval tanpa koreksi 00:00", c, hc)]:
    rows.append(dict(cara=name, jam_puncak=int(p.idxmax()), kwh_jam_puncak=float(p.max()), biaya_setahun=cost(h), selisih_biaya_vs_A=cost(h) - cost(ha),
                     jam_blok_peak_beda=int((((h >= C.PEAK_START) & (h < C.PEAK_END)) != ((ha >= C.PEAK_START) & (ha < C.PEAK_END))).sum())))
sens = pd.DataFrame(rows); sens.to_csv(C.RES_ANALYSIS / "sensitivity_label.csv", index=False)

# uji tarif: ubah dim_tariff di salinan DB, biaya harus ikut (rasio terhadap hitungan manual)
tmp = Path(tempfile.mkdtemp()) / "t.duckdb"; shutil.copy(C.DB_PATH, tmp)
con = duckdb.connect(str(tmp))
base = con.execute("SELECT sum(cost) FROM v_interval").fetchone()[0]
tr = []
for rp, ro in [(C.RATE_PEAK, C.RATE_OFF), (C.RATE_PEAK * 1.1, C.RATE_OFF), (C.RATE_PEAK, C.RATE_OFF * 1.1), (1500, 1500)]:
    con.execute("UPDATE dim_tariff SET rate_per_kwh = ? WHERE is_peak", [rp]); con.execute("UPDATE dim_tariff SET rate_per_kwh = ? WHERE NOT is_peak", [ro])
    got = con.execute("SELECT sum(cost) FROM v_interval").fetchone()[0]
    pk = d[(d.ts_start.dt.hour >= C.PEAK_START) & (d.ts_start.dt.hour < C.PEAK_END)].kwh.sum()
    exp = pk * rp + (d.kwh.sum() - pk) * ro
    tr.append(dict(tarif_peak=rp, tarif_offpeak=ro, biaya_view=got, biaya_hitung_manual=exp, selisih=got - exp, penghematan_10persen=0.1 * pk * (rp - ro)))
con.close(); shutil.rmtree(tmp.parent)
tt = pd.DataFrame(tr); assert (tt.selisih.abs() < 1).all()
tt.to_csv(C.RES_ANALYSIS / "tariff_test.csv", index=False)

# verdict hipotesis
ev = pd.read_csv(C.RES_ANALYSIS / "hypothesis_evidence.csv").iloc[0]
sc = pd.read_csv(C.RES_ANALYSIS / "scenarios.csv")
peak_share = float(pd.read_csv(C.RES_ANALYSIS / "kpi_year.csv").peak_cost_share.iloc[0])
hyp = pd.DataFrame([
    ("H1", "Pemakaian tertinggi di jam kerja siang, terendah di malam hari", "Terbukti", f"jam tertinggi {int(ev.peak_hour)}:00, terendah {int(ev.min_hour)}:00; 7 jam menyumbang 80% beban maksimum"),
    ("H2", "Pemakaian akhir pekan jauh lebih rendah daripada hari kerja", "Terbukti", f"rasio akhir pekan/hari kerja {ev.weekend_ratio:.3f}"),
    ("H3", "Jenis beban Maximum terkumpul di beberapa jam tertentu", "Terbukti", f"{int(ev.n_hours_80pct_max)} jam menampung 80% interval Maximum"),
    ("H4", "Power factor rendah lebih sering muncul saat beban ringan", "Terbukti", f"PF rendah: Light {ev.pf_low_light:.1%}, Medium {ev.pf_low_medium:.1%}, Maximum {ev.pf_low_max:.1%}"),
    ("H5", "Sebagian beban jam peak bisa dipindah tanpa menciptakan puncak baru", "Sebagian", f"puncak tahunan tidak berubah; hemat Rp{sc.penghematan_setahun[0]/1e6:.1f} juta/tahun pada 10% (tarif asumsi); pada {int(sc.hari_puncak_baru[0])} hari jam tujuan melampaui puncak harian lama"),
], columns=["id", "hipotesis", "verdict", "bukti"])
hyp.to_csv(C.RES_ANALYSIS / "hypotheses.csv", index=False)
print(sens.round(1).to_string()); print(tt.round(0).to_string()); print(hyp.to_string())
