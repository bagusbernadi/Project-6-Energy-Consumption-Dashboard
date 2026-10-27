"""Membaca CSV UCI, profiling, audit interval (Q13), cleaning bertanda, dan menulis data bersih."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import common as C  # noqa: E402

if not C.RAW_CSV.exists():
    sys.exit(f"File tidak ada: {C.RAW_CSV}\nUnduh dataset 851 dari {C.SOURCE_URL} dan simpan sebagai {C.RAW_CSV.name} (lihat project/data/README.md).")

COLS = ["date", "kwh", "lag_kvarh", "lead_kvarh", "co2_t", "lag_pf", "lead_pf", "nsm", "week_status", "day_of_week", "load_type"]
d = pd.read_csv(C.RAW_CSV)
assert len(d.columns) == len(COLS)
d.columns = COLS
d.insert(0, "row_id", np.arange(1, len(d) + 1))
d["ts_raw"] = pd.to_datetime(d.date, format="%d/%m/%Y %H:%M")

# ---- profiling kolom
prof = pd.DataFrame({"tipe": d.dtypes.astype(str), "kosong": d.isna().sum(), "unik": d.nunique()})
num = d.select_dtypes("number").drop(columns="row_id")
prof = prof.join(num.agg(["min", "median", "max"]).T)
prof.index.name = "kolom"
prof.round(3).to_csv(C.RES_PREP / "profile_columns.csv")

# ---- audit interval: baris berlabel 00:00 sebenarnya adalah akhir hari (24:00)
is_mid = d.ts_raw.dt.hour.eq(0) & d.ts_raw.dt.minute.eq(0)
d["ts"] = d.ts_raw + pd.to_timedelta(is_mid.astype(int), unit="D")    # label = akhir interval; 00:00 -> 00:00 hari berikutnya
d["fix_flag"] = np.where(is_mid, "tanggal_00_00_digeser", "ok")
step = d.ts.diff().dropna()
c0 = d.ts_raw.diff().dropna()
audit = {
    "baris": len(d), "kolom": len(COLS), "periode_awal_label": str(d.ts_raw.min()), "periode_akhir_label": str(d.ts_raw.max()),
    "nilai_kosong": int(d.isna().sum().sum()), "nilai_negatif_kwh": int((d.kwh < 0).sum()),
    "timestamp_ganda_label_asli": int(d.ts_raw.duplicated().sum()), "timestamp_ganda_setelah_koreksi": int(d.ts.duplicated().sum()),
    "baris_00_00_salah_tanggal": int(is_mid.sum()),
    "total_kwh_mentah": round(float(d.kwh.sum()), 2),
    "label_asli_tidak_menaik": int((c0 <= pd.Timedelta(0)).sum()),
    "interval_bukan_15_menit_asli": int((c0 != pd.Timedelta(minutes=15)).sum()),
    "interval_bukan_15_menit_setelah_koreksi": int((step != pd.Timedelta(minutes=15)).sum()),
    "hari_dengan_96_interval": int((d.groupby(d.ts_raw.dt.date).size() == C.PER_DAY).sum()), "jumlah_hari": int(d.ts_raw.dt.normalize().nunique()),
    "nsm_tidak_cocok_label": int((d.nsm != d.ts_raw.dt.hour * 3600 + d.ts_raw.dt.minute * 60).sum()),
    "co2_nol_padahal_kwh_positif": int(((d.co2_t == 0) & (d.kwh > 5)).sum()),
    "lag_pf_nol_dengan_kvarh_positif": int(((d.lag_pf == 0) & (d.lag_kvarh > 0)).sum()),
    "lag_kvarh_dan_lead_kvarh_sama_sama_positif": int(((d.lag_kvarh > 0) & (d.lead_kvarh > 0)).sum()),
}
# bukti arah koreksi: baris 00:00 lebih mirip 23:45 hari yang sama (dan 00:15 hari berikutnya) daripada 00:15 hari yang sama
p = d.assign(day=d.ts_raw.dt.normalize(), hm=d.ts_raw.dt.strftime("%H:%M")).pivot(index="day", columns="hm", values="kwh")
audit["selisih_00_00_vs_23_45_sama_hari"] = round(float((p["00:00"] - p["23:45"]).abs().mean()), 3)
audit["selisih_00_00_vs_00_15_sama_hari"] = round(float((p["00:00"] - p["00:15"]).abs().mean()), 3)
audit["selisih_00_00_vs_00_15_hari_berikut"] = round(float((p["00:00"].iloc[:-1].values - p["00:15"].iloc[1:].values).__abs__().mean()), 3)
assert audit["timestamp_ganda_setelah_koreksi"] == 0 and audit["interval_bukan_15_menit_setelah_koreksi"] == 0
assert audit["selisih_00_00_vs_23_45_sama_hari"] < audit["selisih_00_00_vs_00_15_sama_hari"]
pd.DataFrame({"ukuran": audit.keys(), "nilai": audit.values()}).to_csv(C.RES_PREP / "data_quality.csv", index=False)

# ---- turunan waktu: interval dimulai 15 menit sebelum label
d["ts_start"] = d.ts - pd.Timedelta(minutes=C.INTERVAL_MIN)
d["date_d"] = d.ts_start.dt.date.astype(str)
d["hour"] = d.ts_start.dt.hour
d["dow_calc"] = d.ts_start.dt.day_name()
wk_calc = np.where(d.ts_start.dt.dayofweek >= 5, "Weekend", "Weekday")
audit_rows = [("WeekStatus dataset = akhir pekan menurut kalender (hari interval dimulai)", int((wk_calc == d.week_status).sum()), len(d)),
              ("Day_of_week dataset = nama hari menurut kalender", int((d.dow_calc == d.day_of_week).sum()), len(d)),
              ("Load_Type berurutan Light < Medium < Maximum menurut kWh rata-rata", int(d.groupby("load_type").kwh.mean().loc[["Light_Load", "Medium_Load", "Maximum_Load"]].is_monotonic_increasing), 1)]
pd.DataFrame(audit_rows, columns=["pemeriksaan", "cocok", "dari"]).to_csv(C.RES_PREP / "label_checks.csv", index=False)
assert (wk_calc == d.week_status).all(), "WeekStatus tidak cocok dengan kalender hari interval"

log = pd.DataFrame([
    ("L1", "Baris berlabel 00:00 (akhir hari) bertanggal sama dengan awal hari", int(is_mid.sum()), "diperbaiki (tanggal +1 hari)", "Setelah koreksi 35.040 timestamp unik dan selisih tepat 15 menit"),
    ("L2", "Nilai kosong atau negatif", audit["nilai_kosong"] + audit["nilai_negatif_kwh"], "tidak ada", "-"),
    ("L3", "Interval ganda atau hilang", audit["timestamp_ganda_setelah_koreksi"] + audit["interval_bukan_15_menit_setelah_koreksi"], "tidak ada setelah L1", "-"),
    ("L4", "Kolom NSM mengikuti label asli, bukan label terkoreksi", audit["nsm_tidak_cocok_label"], "tidak dipakai", "NSM dihitung ulang dari timestamp bila perlu"),
    ("L5", "CO2 dibulatkan 0,01 tCO2 per interval", int(((d.co2_t == 0) & (d.kwh > 5)).sum()), "dipakai dengan catatan", "Total CO2 bulanan diperlakukan sebagai perkiraan"),
], columns=["kode", "masalah", "baris", "keputusan", "catatan"])
log.to_csv(C.RES_PREP / "cleaning_log.csv", index=False)

out = d[["row_id", "ts", "ts_start", "date_d", "hour", "kwh", "lag_kvarh", "lead_kvarh", "co2_t", "lag_pf", "lead_pf", "week_status", "day_of_week", "load_type", "fix_flag"]]
out.to_csv(C.CLEAN_CSV, index=False)
tot_raw, tot_clean = float(d.kwh.sum()), float(out.kwh.sum())
assert abs(tot_raw - tot_clean) < 1e-6
print("bersih:", len(out), "baris; total kWh", round(tot_clean, 1), "; baris digeser", int(is_mid.sum()))
print(pd.Series(audit).to_string())
