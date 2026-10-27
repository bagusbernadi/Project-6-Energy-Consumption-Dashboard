"""Membuat design-and-report/index.html (Report Project versi 2) dari page_v1.html dan CSV hasil.

- Pane Design diambil apa adanya dari page_v1.html (dicek identik).
- Semua angka di Report berasal dari project/results/*.csv lewat helper I/D/P/cs (report_lib.py) dan diaudit di akhir.
Jalankan dari folder mana saja:  python design-and-report/src/build_report.py
"""
import re
import sys
from pathlib import Path

import duckdb
import pandas as pd

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "project" / "code"))
sys.path.insert(0, str(HERE))
from common import (ACCESS_DATE, DB_PATH, HIGH_Q, MAX_SHIFT, N_DEST_HOURS, PEAK_END, PEAK_START, PF_LIMIT, RATE_OFF, RATE_PEAK,  # noqa: E402
                    RES_ANALYSIS, RES_PREP, RES_PRESENT, result)
from report_lib import (BLUE, D, GREY, HI, I, NO, OK, P, PART, SOFT, audit, bars, cs, esc, gbars, legend, lines,  # noqa: E402
                        pill, qa, table)

R = lambda n: pd.read_csv(result(n))
PRIO = {1: "Utama", 2: "Utama", 3: "Pendukung", 4: "Utama", 5: "Utama", 6: "Utama", 7: "Pendukung", 8: "Pendukung",
        9: "Tambahan", 10: "Utama", 11: "Utama", 12: "Pendukung", 13: "Utama", 14: "Utama"}
QT = {1: "Bagaimana pola pemakaian listrik per jam dalam sehari, dan jam berapa beban puncak biasanya terjadi?",
      2: "Seberapa berbeda pola hari kerja dan akhir pekan?",
      3: "Bagaimana tren pemakaian dari bulan ke bulan sepanjang tahun?",
      4: "Berapa persen waktu dan energi yang jatuh di jenis beban Maximum, dan di jam berapa?",
      5: "Berapa kali beban melewati ambang tinggi, dan berapa lama setiap kejadian berlangsung?",
      6: "Berapa biaya energi per bulan, dan berapa porsinya yang dibayar di jam peak?",
      7: "Hari apa dalam seminggu yang paling mahal?",
      8: "Seberapa sering power factor turun di bawah 0,85, dan pada jam berapa?",
      9: "Berapa emisi CO2 per bulan, dan bulan apa yang tertinggi?",
      10: "Jika sebagian beban jam peak dipindah ke jam off-peak, berapa penghematan per bulan?",
      11: "Berapa turunnya beban puncak tertinggi setelah beban dipindah, dan apakah muncul puncak baru di jam lain?",
      12: "Jam mana yang paling aman menjadi tujuan pemindahan beban?",
      13: "Apakah ada interval yang hilang, ganda, atau bernilai tidak wajar, dan apakah hasil berubah setelah diperbaiki?",
      14: "Apakah angka KPI dari database sama persis dengan hitungan manual (Excel atau pandas)?"}
WARN = set()


def Q(n, ans, warn=False):
    if warn:
        WARN.add(n)
    return qa(f"Q{n}", QT[n], PRIO[n], ans, "Terjawab dengan catatan" if warn else "Terjawab", warn)


mk = lambda *a: "".join(a)
MONTH = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]
MN = lambda m: MONTH[int(m) - 1]
DAYID = {"Monday": "Senin", "Tuesday": "Selasa", "Wednesday": "Rabu", "Thursday": "Kamis", "Friday": "Jumat", "Saturday": "Sabtu", "Sunday": "Minggu"}
LT = {"Light_Load": "Light", "Medium_Load": "Medium", "Maximum_Load": "Maximum"}
juta = lambda v, d=1: D(v / 1e6, d)

# ---------------------------------------------------------------- data
dq = R("data_quality.csv").set_index("ukuran").nilai
ctest, cons, rows_t, dlog = R("constraint_tests.csv"), R("consistency_checks.csv"), R("table_rows.csv"), R("cleaning_log.csv")
lchk, prof = R("label_checks.csv"), R("profile_columns.csv")
kpi = R("kpi_year.csv").iloc[0]
hp, mon, dow, wk = R("hour_profile.csv"), R("monthly.csv"), R("dow_cost.csv"), R("weekday_weekend.csv").set_index("wk")
daily = R("daily_trend.csv")
lts, mxh, hls, hle = R("loadtype_summary.csv").set_index("load_type"), R("maximum_by_hour.csv"), R("high_load_summary.csv").iloc[0], R("high_load_events.csv")
pfl, pfh, ev = R("pf_by_load.csv").set_index("load_type"), R("pf_hour.csv"), R("hypothesis_evidence.csv").iloc[0]
sc, scm, dest = R("scenarios.csv"), R("scenarios_monthly.csv"), R("dest_hours.csv")
sens, tt, hyp = R("sensitivity_label.csv"), R("tariff_test.csv"), R("hypotheses.csv")
cc = R("crosscheck_pandas.csv")
con = duckdb.connect(str(DB_PATH), read_only=True)
dbc = {t: con.execute(f"SELECT count(*) FROM {t}").fetchone()[0] for t in ("readings", "dim_time", "dim_tariff", "daily_summary")}
db_kwh = con.execute("SELECT sum(usage_kwh) FROM readings").fetchone()[0]
tariff = con.execute("SELECT block, start_hour, end_hour, is_peak, rate_per_kwh FROM dim_tariff ORDER BY is_peak").fetchall()
smp = con.execute("SELECT ts, usage_kwh, lag_kvarh, lag_pf, co2_t, load_type, fix_flag FROM readings WHERE ts BETWEEN '2018-01-01 23:30' AND '2018-01-02 00:30' ORDER BY ts").fetchall()
con.close()

hall = hp.assign(w=hp.avg_kwh_per_hour * hp.n_hours).groupby("hour").apply(lambda g: g.w.sum() / g.n_hours.sum(), include_groups=False)
hwd = hp[hp.week_status == "Weekday"].set_index("hour").avg_kwh_per_hour
hwe = hp[hp.week_status == "Weekend"].set_index("hour").avg_kwh_per_hour
pk_h, mn_h = int(hall.idxmax()), int(hall.idxmin())
mon = mon.assign(offpeak_cost=mon.cost - mon.peak_cost, share=mon.peak_cost / mon.cost)
dowi = dow.set_index("day_of_week")
ord_dow = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
s10, s20, s30, s40 = (sc.iloc[i] for i in range(4))
dest_sel = dest[dest.dipilih_tujuan]
hrs_dest = sorted(dest_sel.hour)
peak_blk = dest[dest.blok == "Peak"]
pkh = int(mxh.shape[0])
n80 = int(ev.n_hours_80pct_max)
cc_n, cc_v = len(cc), int(cc.jumlah_nilai.sum())
npr = {k: sum(1 for v in PRIO.values() if v == k) for k in ("Utama", "Pendukung", "Tambahan")}

# pernyataan yang dipakai di teks harus benar menurut data
assert (cc.status == "PASS").all() and (ctest.outcome == "ditolak").all() and (cons.violations == 0).all()
assert abs(db_kwh - float(dq["total_kwh_mentah"])) < 0.01 and float(dq["timestamp_ganda_setelah_koreksi"]) == 0 and float(dq["interval_bukan_15_menit_setelah_koreksi"]) == 0
assert pk_h == int(ev.peak_hour) and mn_h == int(ev.min_hour) and 9 <= pk_h <= 16
assert (hyp.set_index("id").verdict == pd.Series({"H1": "Terbukti", "H2": "Terbukti", "H3": "Terbukti", "H4": "Terbukti", "H5": "Sebagian"})).all()
assert PEAK_START <= 17 and set(hrs_dest) <= set(range(0, PEAK_START)) | set(range(PEAK_END, 24)) and not (set(hrs_dest) & set(range(PEAK_START, PEAK_END)))
assert sc.peak_kw_sebelum.eq(sc.peak_kw_sesudah).all() and (sc.penghematan_setahun.diff().dropna() > 0).all()
assert pfl.porsi_rendah.idxmax() == "Light_Load" and wk.loc["Weekend", "rasio_terhadap_weekday"] < 0.5
assert abs(kpi.peak_cost_share - mon.peak_cost.sum() / mon.cost.sum()) < 1e-9

# ---------------------------------------------------------------- 1. data
kp = lambda c, v, l, d: f'<div class="card kpi" style="--h:var(--{c}H)"><span class="v">{v}</span><span class="l">{l}</span><span class="d">{d}</span></div>'
rp1 = mk(
    '<div class="kpis">',
    kp("navy", I(dbc["readings"]), "interval 15 menit", f"Satu pabrik baja (DAEWOO Steel, Gwangyang), 1 Januari sampai 31 Desember 2018, {I(dq['jumlah_hari'])} hari penuh (masing-masing 96 interval)."),
    kp("amber", I(dq["baris_00_00_salah_tanggal"]), "baris salah tanggal diperbaiki", "Baris berlabel 00:00 adalah akhir hari (24:00) tetapi bertanggal sama dengan awal hari; tanggalnya digeser satu hari dan dicatat di <code>fix_flag</code>."),
    kp("teal", f"{D(kpi.total_kwh / 1000, 0)} MWh", "energi setahun", f"Total kWh setelah cleaning sama dengan data mentah ({I(db_kwh)} kWh); cleaning hanya mengubah tanggal, bukan nilai."),
    kp("plum", f"{D(kpi.peak_kw, 0)} kW", "beban puncak setahun", f"Beban puncak = kWh interval × 4. Load factor {D(kpi.load_factor, 2)}."),
    kp("rose", I(cc_v), "nilai dicek silang SQL vs pandas", f"{I(cc_n)} pemeriksaan, semuanya PASS (selisih terbesar di bawah 1E-6)."),
    kp("sky", I(len(ctest)), "uji aturan database", f"Setiap jenis data salah ditolak oleh constraint; {I(len(cons))} pemeriksaan konsistensi menghasilkan 0 pelanggaran."),
    '</div><h3>1.1 Data UCI (mentah dan bersih)</h3>')
rp1 += '<div class="card"><h4>Cuplikan readings di sekitar pergantian hari (setelah koreksi 00:00)</h4>' + table(
    ["ts (akhir interval)", "kWh", "lag kVArh", "lag PF", "CO2 (t)", "Load_Type", "fix_flag"],
    [[cs(str(r[0])[:16]), D(r[1], 2), D(r[2], 2), D(r[3], 2), D(r[4], 2), LT[r[5]], f"<code>{r[6]}</code>"] for r in smp]) + \
    '<p>Label waktu di CSV adalah akhir interval. Baris yang berlabel 00:00 pada 2 Januari adalah interval terakhir 1 Januari (23:45 sampai 24:00), jadi tanggalnya digeser satu hari sebelum dipakai.</p></div>'
rp1 += '<div class="card"><h4>Tabel 1.1. Kualitas data dan keputusan cleaning</h4>' + table(
    ["Pemeriksaan", "Hasil", "Keputusan"],
    [["Baris dan kolom", f"{I(dq['baris'])} baris, {I(dq['kolom'])} kolom", "Sesuai perkiraan rancangan (±35.040)"],
     ["Nilai kosong atau kWh negatif", f"{I(dq['nilai_kosong'])} dan {I(dq['nilai_negatif_kwh'])}", "Tidak ada penanganan"],
     ["Timestamp ganda pada label asli", I(dq["timestamp_ganda_label_asli"]), "Tidak ada yang ganda, tetapi label tidak menaik"],
     ["Label tidak menaik (baris 00:00)", I(dq["label_asli_tidak_menaik"]), "Diperbaiki: tanggal +1 hari (L1)"],
     ["Interval bukan 15 menit pada label asli", I(dq["interval_bukan_15_menit_asli"]), f"Setelah koreksi: {I(dq['interval_bukan_15_menit_setelah_koreksi'])}"],
     ["Hari dengan 96 interval", f"{I(dq['hari_dengan_96_interval'])} dari {I(dq['jumlah_hari'])}", "Lengkap setelah koreksi"],
     ["NSM tidak cocok dengan label", I(dq["nsm_tidak_cocok_label"]), "NSM dihitung dari label asli; tidak dipakai (L4)"],
     ["CO2 nol padahal kWh positif", I(dq["co2_nol_padahal_kwh_positif"]), "CO2 dibulatkan 0,01 t per interval; dipakai dengan catatan (L5)"],
     ["Bukti arah koreksi: selisih rata-rata kWh baris 00:00", f"{D(dq['selisih_00_00_vs_23_45_sama_hari'], 2)} (vs 23:45 hari sama), {D(dq['selisih_00_00_vs_00_15_hari_berikut'], 2)} (vs 00:15 hari berikut), {D(dq['selisih_00_00_vs_00_15_sama_hari'], 2)} (vs 00:15 hari sama)", "Baris 00:00 mirip akhir hari, bukan awal hari: koreksi benar"]]) + \
    f'<p>Sumber: UCI dataset 851, versi 1, tanggal akses {cs(ACCESS_DATE)}. Data mentah dan bersih tidak di-commit; dibuat ulang oleh skrip.</p></div>'
rp1 += '<h3>1.2 Tabel di database (<code>energy.duckdb</code>)</h3><div class="card"><h4>Tabel 1.2a. Isi database</h4>' + table(
    ["Tabel", "Baris", "Isi"],
    [["readings", I(dbc["readings"]), "Satu bacaan meteran per 15 menit. Kunci utama <code>row_id</code>, <code>ts</code> unik."],
     ["dim_time", I(dbc["dim_time"]), "Jam, hari, status hari, bulan untuk satu bacaan (kunci asing ke readings)."],
     ["dim_tariff", I(dbc["dim_tariff"]), "Dua blok tarif (asumsi): " + "; ".join(f"{b} {I(s)}-{I(e)} Rp{I(r)}" for b, s, e, _, r in tariff) + ". Ubah di sini, biaya ikut berubah."],
     ["daily_summary", I(dbc["daily_summary"]), "Ringkasan satu hari: kWh, beban puncak, load factor, biaya, porsi biaya peak."]]) + \
    '<h4>Tabel 1.2b. Uji aturan pengecekan (constraint)</h4>' + table(
    ["Baris salah yang dicoba dimasukkan", "Hasil"], [[r.test, OK("Ditolak") if r.outcome == "ditolak" else NO("Diterima")] for r in ctest.itertuples()]) + \
    f'<p>Seluruh {I(len(ctest))} jenis data salah ditolak. {I(len(cons))} pemeriksaan konsistensi antar tabel menghasilkan 0 pelanggaran.</p></div>'
FILES = {"cleaning_log": ("Log cleaning L1 sampai L5", "Q13"), "consistency_checks": ("Pemeriksaan konsistensi database", "Q13, Q14"), "constraint_tests": ("Uji constraint database", "Q13"),
         "data_quality": ("Ringkasan kualitas data", "Q13"), "label_checks": ("Cek label hari dan Load_Type terhadap kalender", "Q13"), "profile_columns": ("Profil kolom (tipe, kosong, rentang)", "Q13"),
         "table_rows": ("Baris per tabel", "Q13"), "crosscheck_pandas": ("KPI SQL vs pandas", "Q14"), "daily_trend": ("Total harian dan rata-rata bergerak 7 hari", "Q3"),
         "dest_hours": ("Beban rata-rata per jam dan jam tujuan pemindahan", "Q12"), "dow_cost": ("Biaya rata-rata per hari dalam minggu", "Q7"), "high_load_events": ("Kejadian beban tinggi (di atas P90)", "Q5"),
         "high_load_summary": ("Ringkasan kejadian beban tinggi", "Q5"), "hour_profile": ("Rata-rata kWh per jam, hari kerja dan akhir pekan", "Q1, Q2"), "hypothesis_evidence": ("Angka bukti hipotesis", "Hipotesis"),
         "hypotheses": ("Verdict lima hipotesis", "Hipotesis"), "kpi_year": ("KPI setahun", "Q6"), "loadtype_hour": ("kWh dan interval per jam dan Load_Type", "Q4"),
         "loadtype_summary": ("Porsi waktu dan energi per Load_Type", "Q4"), "maximum_by_hour": ("Sebaran interval Maximum per jam", "Q4"), "monthly": ("Energi, biaya, CO2, beban puncak per bulan", "Q3, Q6, Q9"),
         "pf_by_load": ("Porsi PF rendah per Load_Type", "Q8"), "pf_hour": ("Porsi PF rendah per jam", "Q8"), "scenarios": ("Skenario pemindahan 10, 20, 30, 40 persen", "Q10, Q11"),
         "scenarios_monthly": ("Penghematan per bulan per skenario", "Q10"), "sensitivity_label": ("Sensitivitas cara membaca label waktu", "Q13"), "tariff_test": ("Uji perubahan tarif di dim_tariff", "Q6, kriteria 5"),
         "weekday_weekend": ("Hari kerja vs akhir pekan", "Q2")}
resfiles = sorted(p for d in (RES_PREP, RES_ANALYSIS) for p in d.glob("*.csv"))
miss = [p.stem for p in resfiles if p.stem not in FILES]
assert not miss, f"CSV hasil belum didokumentasikan di FILES: {miss}"
rp1 += '<div class="card"><h4>Tabel 1.2c. Data hasil analisis (<code>project/results/</code>)</h4>' + table(
    ["File", "Isi", "Baris", "Menjawab"], [[f"<code>{p.stem}.csv</code>", FILES[p.stem][0], I(len(pd.read_csv(p))), FILES[p.stem][1]] for p in resfiles]) + \
    f'<p>{I(len(resfiles))} file CSV, ditambah {I(len(list(RES_PRESENT.glob("dash_*.csv"))))} CSV data dashboard.</p></div>'
rp1 += '<h3>1.3 Angka kunci (KPI)</h3><div class="card"><h4>Tabel 1.3. Lima KPI (definisi di <code>project/docs/definitions.md</code>)</h4>' + table(
    ["KPI", "Rumus ringkas", "Hasil", "Jumlah data"],
    [["Total energi", "jumlah kWh semua interval", f"{I(kpi.total_kwh)} kWh", f"{I(kpi.n_intervals)} interval"],
     ["Beban puncak", "kWh interval × 4 (kW), maksimum", f"{D(kpi.peak_kw, 1)} kW", "1 tahun"],
     ["Load factor", "beban rata-rata ÷ beban puncak", D(kpi.load_factor, 2), "1 tahun"],
     ["Biaya energi (estimated)", f"kWh × tarif blok (Rp{I(RATE_PEAK)} peak, Rp{I(RATE_OFF)} off-peak; asumsi)", f"Rp{juta(kpi.cost, 0)} juta", f"{I(dbc['daily_summary'])} hari"],
     ["Porsi biaya peak (estimated)", "biaya blok peak ÷ biaya total", P(kpi.peak_cost_share, 1), f"peak = jam {I(PEAK_START)} sampai {I(PEAK_END)}"]]) + \
    '<p>Biaya dan porsi biaya bergantung pada tarif asumsi, bukan tagihan nyata.</p></div>'

# ---------------------------------------------------------------- 2. business questions
HX = [f"{h:02d}" for h in range(24)]
bgm = mon.copy()
sec21 = mk(
    '<h3 id="sec21">2.1 Pola waktu: kapan listrik paling banyak dipakai <span class="qlist">Q1, Q2, Q3</span></h3><div class="card">',
    Q(1, f"Pemakaian rendah di malam hari (terendah jam {I(mn_h)}: {D(hall[mn_h], 1)} kWh per jam), naik tajam mulai jam 8, dan tertinggi di jam {I(pk_h)} ({D(hall[pk_h], 1)} kWh per jam rata-rata, {D(hwd[pk_h], 1)} pada hari kerja). "
         f"Ada turunan jam makan siang di jam 12 ({D(hall[12], 1)} kWh per jam), lalu beban siang kembali tinggi sampai jam 16 dan turun setelah jam 21. Hipotesis 1 terbukti."),
    Q(2, f"Sangat berbeda. Hari kerja rata-rata {D(wk.loc['Weekday', 'kwh_per_hari'], 0)} kWh per hari ({I(wk.loc['Weekday', 'hari'])} hari), akhir pekan {D(wk.loc['Weekend', 'kwh_per_hari'], 0)} kWh per hari ({I(wk.loc['Weekend', 'hari'])} hari), yaitu {P(ev.weekend_ratio, 1)} dari hari kerja. "
         f"Akhir pekan juga lebih bervariasi (simpangan baku {D(wk.loc['Weekend', 'std'], 0)} vs {D(wk.loc['Weekday', 'std'], 0)} kWh). Hipotesis 2 terbukti."),
    Q(3, f"Pemakaian tertinggi di bulan {MN(mon.loc[mon.total_kwh.idxmax(), 'month'])} ({D(mon.total_kwh.max(), 0)} kWh) dan terendah di bulan {MN(mon.loc[mon.total_kwh.idxmin(), 'month'])} ({D(mon.total_kwh.min(), 0)} kWh), "
         f"selisih {P(mon.total_kwh.max() / mon.total_kwh.min() - 1, 0)}. Rata-rata bergerak 7 hari tersedia di <code>daily_trend.csv</code> dan di dashboard."),
    '<h4>Grafik 2.1a. Rata-rata kWh per jam: hari kerja vs akhir pekan</h4>',
    lines(HX, [("Hari kerja", BLUE, 2.5, list(hwd.reindex(range(24)))), ("Akhir pekan", HI, 2.5, list(hwe.reindex(range(24))))], lambda v: D(v, 0), "Rata-rata kWh per jam", zero=True),
    legend([(BLUE, "Hari kerja"), (HI, "Akhir pekan")]),
    '<h4>Grafik 2.1b. Energi per bulan (kWh)</h4>',
    bars([(MN(r.month), r.total_kwh, BLUE, f"{MN(r.month)}: {I(r.total_kwh)} kWh, puncak {D(r.peak_kw, 0)} kW") for r in bgm.itertuples()], lambda v: D(v / 1000, 0) + " rb", "Energi per bulan", rot=0, small=True),
    '<h4>Tabel 2.1c. Hari kerja vs akhir pekan</h4>',
    table(["Status hari", "Jumlah hari", "kWh per hari", "Simpangan baku", "Jam tertinggi", "kWh jam tertinggi"],
          [[("Hari kerja" if w == "Weekday" else "Akhir pekan"), I(r.hari), D(r.kwh_per_hari, 0), D(r["std"], 0), I(r.jam_tertinggi), D(r.kwh_jam_tertinggi, 1)] for w, r in wk.iterrows()]), '</div>')
mxh_s = mxh.sort_values("hour")
hrs80 = mxh[mxh.kumulatif <= 0.8 + 1e-9].hour.tolist()
sec22 = mk(
    '<h3 id="sec22">2.2 Beban puncak: seberapa tinggi dan seberapa sering <span class="qlist">Q4, Q5</span></h3><div class="card">',
    Q(4, f"Beban Maximum memakai {P(lts.loc['Maximum_Load', 'porsi_waktu'], 1)} dari waktu tetapi {P(lts.loc['Maximum_Load', 'porsi_energi'], 1)} dari energi. Interval Maximum terkumpul di {I(n80)} jam saja (jam {I(min(hrs80))} sampai {I(max(hrs80))} dengan jeda makan siang), yang menampung 80% kejadiannya. "
         f"Jam tersibuk jam {I(pk_h)}, bukan blok tarif peak (jam {I(PEAK_START)} sampai {I(PEAK_END)}). Hipotesis 3 terbukti."),
    Q(5, f"Ada {I(hls.n_kejadian)} kejadian beban tinggi (interval di atas persentil {I(HIGH_Q * 100)}, yaitu {D(hls.ambang_kwh_interval, 1)} kWh per interval), rata-rata {D(hls.kejadian_per_hari, 1)} per hari. Durasi median {D(hls.durasi_median_jam, 1)} jam, persentil 90 {D(hls.durasi_p90_jam, 1)} jam, terpanjang {D(hls.durasi_maks_jam, 1)} jam. "
         f"Kejadian paling sering dimulai jam {I(hls.jam_mulai_tersering)} ({P(hls.porsi_mulai_jam_tersering, 0)}); hanya {P(hls.kejadian_mulai_di_blok_peak, 0)} dimulai di blok tarif peak."),
    '<h4>Grafik 2.2a. Porsi interval Maximum per jam</h4>',
    bars([(f"{int(r.hour):02d}", r.porsi, BLUE, f"Jam {int(r.hour)}: {I(r.n_maximum)} interval ({P(r.porsi, 1)})") for r in mxh_s.itertuples()], lambda v: P(v, 0), "Porsi interval Maximum per jam", rot=0, small=True),
    '<h4>Tabel 2.2b. Jenis beban</h4>',
    table(["Load_Type", "Interval", "kWh", "Porsi waktu", "Porsi energi"], [[LT[k], I(r.n), I(r.kwh), P(r.porsi_waktu, 1), P(r.porsi_energi, 1)] for k, r in lts.loc[["Light_Load", "Medium_Load", "Maximum_Load"]].iterrows()]),
    '<p>Kejadian beban tinggi didefinisikan sebagai interval berurutan di atas ambang; satu interval tunggal juga dihitung sebagai satu kejadian.</p></div>')
bm = mon.set_index("month")
sec23 = mk(
    '<h3 id="sec23">2.3 Biaya: berapa yang dibayar <span class="qlist">Q6, Q7</span></h3><div class="card">',
    Q(6, f"Biaya energi setahun Rp{juta(kpi.cost, 0)} juta (estimated), rata-rata Rp{juta(mon.cost.mean(), 0)} juta per bulan; tertinggi {MN(mon.loc[mon.cost.idxmax(), 'month'])} (Rp{juta(mon.cost.max(), 0)} juta). "
         f"Blok peak (jam {I(PEAK_START)} sampai {I(PEAK_END)}) menyumbang {P(kpi.peak_cost_share, 1)} biaya, dengan {P(kpi.peak_kwh / kpi.total_kwh, 1)} energi. "
         f"Semua angka biaya memakai tarif asumsi Rp{I(RATE_PEAK)} dan Rp{I(RATE_OFF)} per kWh; tarif disimpan di <code>dim_tariff</code> dan terbukti mengubah biaya sesuai hitungan manual (Tabel 2.6c).", warn=True),
    Q(7, f"Hari {DAYID[dow.loc[dow.avg_cost_per_day.idxmax(), 'day_of_week']]} paling mahal (Rp{juta(dow.avg_cost_per_day.max(), 2)} juta per hari) dan hari {DAYID[dow.loc[dow.avg_cost_per_day.idxmin(), 'day_of_week']]} paling murah (Rp{juta(dow.avg_cost_per_day.min(), 2)} juta). "
         "Hari kerja berkisar dekat satu sama lain; akhir pekan jauh lebih murah."),
    '<h4>Grafik 2.3a. Biaya per bulan (juta Rp, estimated): jam peak vs off-peak</h4>',
    gbars([MN(m) for m in mon.month], [("Peak", HI, list(mon.peak_cost / 1e6)), ("Off-peak", BLUE, list(mon.offpeak_cost / 1e6))], lambda v: D(v, 0), "Biaya per bulan (juta Rp)", rot=0),
    legend([(HI, "Peak 17-22"), (BLUE, "Off-peak")]),
    '<h4>Grafik 2.3b. Biaya rata-rata per hari dalam minggu (juta Rp, estimated)</h4>',
    bars([(DAYID[d][:3], dowi.loc[d, "avg_cost_per_day"] / 1e6, BLUE if d not in ("Saturday", "Sunday") else HI, f"{DAYID[d]}: Rp{juta(dowi.loc[d, 'avg_cost_per_day'], 2)} juta per hari, {I(dowi.loc[d, 'n_days'])} hari") for d in ord_dow],
         lambda v: D(v, 1), "Biaya rata-rata per hari", rot=0, small=True), '</div>')
pfs = pfh.sort_values("hour")
sec24 = mk(
    '<h3 id="sec24">2.4 Kualitas daya dan emisi <span class="qlist">Q8, Q9</span></h3><div class="card">',
    Q(8, f"Power factor rendah (lag PF di bawah {D(PF_LIMIT, 0)}) terjadi pada {P(ev.pf_low_all, 1)} interval. Hampir seluruhnya pada beban Light: {P(ev.pf_low_light, 1)} interval Light, dibandingkan {P(ev.pf_low_medium, 1)} (Medium) dan {P(ev.pf_low_max, 1)} (Maximum). "
         f"Per jam, porsinya di atas {P(0.9, 0)} pada jam {I(pfs[pfs.porsi_rendah > 0.9].hour.min())} sampai {I(pfs[pfs.porsi_rendah > 0.9].hour.max())} dan di bawah {P(0.1, 0)} pada sebagian besar jam siang. Hipotesis 4 terbukti; penyebab fisik belum diketahui (hanya pola)."),
    Q(9, f"Emisi setahun {D(kpi.co2_t, 0)} tCO2. Bulan tertinggi {MN(mon.loc[mon.co2_t.idxmax(), 'month'])} ({D(mon.co2_t.max(), 1)} tCO2), terendah {MN(mon.loc[mon.co2_t.idxmin(), 'month'])} ({D(mon.co2_t.min(), 1)} tCO2). Pola mengikuti energi bulanan; CO2 sumber dibulatkan 0,01 t per interval."),
    '<h4>Grafik 2.4a. Porsi interval dengan power factor rendah per jam</h4>',
    bars([(f"{int(r.hour):02d}", r.porsi_rendah, BLUE if r.porsi_rendah < 0.5 else HI, f"Jam {int(r.hour)}: {I(r.n_low)} dari {I(r.n_intervals)} interval ({P(r.porsi_rendah, 1)})") for r in pfs.rename(columns={"n_low_pf": "n_low"}).itertuples()],
         lambda v: P(v, 0), "Porsi PF rendah per jam", rot=0, small=True),
    '<h4>Grafik 2.4b. Emisi CO2 per bulan (tCO2)</h4>',
    bars([(MN(r.month), r.co2_t, BLUE, f"{MN(r.month)}: {D(r.co2_t, 1)} tCO2") for r in mon.itertuples()], lambda v: D(v, 0), "Emisi CO2 per bulan", rot=0, small=True), '</div>')
sec25 = mk(
    '<h3 id="sec25">2.5 Dampak: jika jadwal beban diubah <span class="qlist">Q10, Q11, Q12</span></h3><div class="card">',
    Q(10, f"Memindahkan {P(s10.pct, 0)} kWh blok peak ({D(s10.kwh_dipindah_per_bulan, 0)} kWh per bulan) ke jam off-peak menghemat sekitar Rp{juta(s10.penghematan_per_bulan, 2)} juta per bulan (Rp{juta(s10.penghematan_setahun, 1)} juta per tahun, {P(s10.penghematan_porsi_biaya, 1)} biaya). "
          f"Pada {P(s20.pct, 0)}: Rp{juta(s20.penghematan_per_bulan, 2)} juta per bulan; {P(s30.pct, 0)}: Rp{juta(s30.penghematan_per_bulan, 2)} juta; batas atas {P(MAX_SHIFT, 0)}: Rp{juta(s40.penghematan_per_bulan, 2)} juta. "
          f"Rumus: kWh dipindah × (Rp{I(RATE_PEAK)} − Rp{I(RATE_OFF)}). Angka berlabel estimated dan adalah batas atas, karena kelayakan operasional tiap beban tidak diketahui dan tarif adalah asumsi.", warn=True),
    Q(11, f"Beban puncak tahunan ({D(s10.peak_kw_sebelum, 1)} kW) tidak berubah pada semua skenario, karena puncak itu terjadi di luar blok peak. Puncak di dalam blok peak turun dari {D(s10.peak_blok_peak_kw_sebelum, 0)} kW menjadi {D(s10.peak_blok_peak_kw_sesudah, 0)} kW ({P(s10.pct, 0)}) hingga {D(s40.peak_blok_peak_kw_sesudah, 0)} kW ({P(s40.pct, 0)}). "
          f"Jam tujuan paling tinggi {D(s10.maks_kw_jam_tujuan_sesudah, 0)} kW ({P(s10.pct, 0)}) sampai {D(s40.maks_kw_jam_tujuan_sesudah, 0)} kW ({P(s40.pct, 0)}), jauh di bawah puncak tahunan, jadi tidak muncul puncak tahunan baru. "
          f"Namun pada {I(s10.hari_puncak_baru)} hari ({P(s10.pct, 0)}) sampai {I(s40.hari_puncak_baru)} hari ({P(s40.pct, 0)}) jam tujuan melampaui puncak harian lama, sehingga puncak harian bergeser. Hipotesis 5 benar sebagian.", warn=True),
    Q(12, f"Tujuh jam off-peak dengan beban rata-rata terendah adalah jam {', '.join(I(h) for h in hrs_dest[:-1])} dan {I(hrs_dest[-1])} (rata-rata {D(dest_sel.kwh_rata2.min(), 1)} sampai {D(dest_sel.kwh_rata2.max(), 1)} kWh per jam, tarif Rp{I(RATE_OFF)}). Jam tersebut dipakai sebagai tujuan di semua skenario; beban dibagi rata di antara tujuh jam itu pada hari yang sama."),
    '<h4>Tabel 2.5a. Skenario pemindahan beban (estimated, tarif asumsi)</h4>',
    table(["Porsi blok peak dipindah", "kWh dipindah per bulan", "Penghematan per bulan (juta Rp)", "Per tahun (juta Rp)", "Puncak blok peak (kW)", "Hari puncak harian bergeser"],
          [[P(r.pct, 0) + (" (batas atas)" if abs(r.pct - MAX_SHIFT) < 1e-9 else ""), D(r.kwh_dipindah_per_bulan, 0), D(r.penghematan_per_bulan / 1e6, 2), D(r.penghematan_setahun / 1e6, 1), D(r.peak_blok_peak_kw_sesudah, 0), I(r.hari_puncak_baru)] for r in sc.itertuples()]),
    '<h4>Grafik 2.5b. Beban puncak sebelum dan sesudah (kW)</h4>',
    gbars([P(p, 0) for p in sc.pct], [("Puncak blok peak sebelum", GREY, list(sc.peak_blok_peak_kw_sebelum)), ("Puncak blok peak sesudah", BLUE, list(sc.peak_blok_peak_kw_sesudah)), ("Puncak jam tujuan sesudah", HI, list(sc.maks_kw_jam_tujuan_sesudah))],
          lambda v: D(v, 0), "Beban puncak (kW)", rot=0),
    legend([(GREY, "Puncak blok peak, sebelum"), (BLUE, "Puncak blok peak, sesudah"), (HI, "Puncak jam tujuan, sesudah")]),
    '<h4>Tabel 2.5c. Beban rata-rata per jam off-peak dan jam tujuan</h4>',
    table(["Jam", "Blok", "kWh rata-rata per jam", "Tarif (Rp/kWh, asumsi)", "Jam tujuan"],
          [[I(r.hour), r.blok, D(r.kwh_rata2, 1), I(r.tarif), OK("Tujuan") if r.dipilih_tujuan else ""] for r in dest.itertuples() if r.blok == "Off-peak"]), '</div>')
sens_a, sens_b = sens.iloc[0], sens.iloc[1]
sec26 = mk(
    '<h3 id="sec26">2.6 Validitas: apakah datanya bisa dipercaya <span class="qlist">Q13, Q14</span></h3><div class="card">',
    Q(13, f"Tidak ada interval hilang, ganda, atau negatif. Masalahnya ada di label waktu: {I(dq['baris_00_00_salah_tanggal'])} baris berlabel 00:00 bertanggal sama dengan awal hari. Setelah tanggalnya digeser, {I(dq['jumlah_hari'])} hari berisi tepat 96 interval dan semua selisih 15 menit. "
          f"Hasil berubah jika koreksi tidak dilakukan: bila label dibaca apa adanya sebagai awal interval, {I(sens_b.jam_blok_peak_beda)} interval pindah blok tarif dan biaya setahun bergeser Rp{juta(sens_b.selisih_biaya_vs_A, 1)} juta ({P(sens_b.selisih_biaya_vs_A / sens_a.biaya_setahun, 1)}); jam tersibuk tetap jam {I(sens_a.jam_puncak)}."),
    Q(14, f"Ya. {I(cc_n)} pemeriksaan ({I(cc_v)} nilai) KPI total, bulanan, harian, profil jam, biaya per hari dalam minggu, dan porsi PF rendah dari SQL sama dengan hitungan pandas pada data bersih (selisih terbesar di bawah 1E-6). "
          "Rancangan menyebut Excel (opsional) dengan PivotTable; sesuai catatan rancangan, cek silang dikerjakan dengan pandas, jadi cek silang ke Excel sendiri belum dilakukan.", warn=True),
    '<h4>Tabel 2.6a. Tiga cara membaca label waktu</h4>',
    table(["Cara membaca", "Jam tersibuk", "Biaya setahun (juta Rp)", "Selisih vs dipakai (juta Rp)", "Interval beda blok tarif"],
          [[r.cara, I(r.jam_puncak), D(r.biaya_setahun / 1e6, 1), D(r.selisih_biaya_vs_A / 1e6, 1), I(r.jam_blok_peak_beda)] for r in sens.itertuples()]),
    '<p>Cara C (akhir interval tanpa koreksi 00:00) menghasilkan jam yang sama dengan cara A, tetapi tanggal 365 interval salah; pengaruhnya ada pada agregasi harian, bukan jam.</p>',
    '<h4>Tabel 2.6b. Uji perubahan tarif di <code>dim_tariff</code></h4>',
    table(["Tarif peak", "Tarif off-peak", "Biaya dari view (juta Rp)", "Hitung manual (juta Rp)", "Selisih", "Hemat 10% (juta Rp)"],
          [[I(r.tarif_peak), I(r.tarif_offpeak), D(r.biaya_view / 1e6, 1), D(r.biaya_hitung_manual / 1e6, 1), I(r.selisih), D(r.penghematan_10persen / 1e6, 1)] for r in tt.itertuples()]),
    '<p>Mengganti tarif di satu tabel mengubah semua biaya sesuai hitungan manual; tarif sama rata membuat penghematan 0.</p>',
    '<h4>Tabel 2.6c. Verdict lima hipotesis</h4>',
    table(["No", "Hipotesis", "Verdict", "Bukti"], [[r.id[1:], r.hipotesis, (OK if r.verdict == "Terbukti" else PART)(r.verdict), cs(r.bukti)] for r in hyp.itertuples()]), '</div>')
qn_all = (sec21 + sec22 + sec23 + sec24 + sec25 + sec26)
SEC = {1: "21", 2: "21", 3: "21", 4: "22", 5: "22", 6: "23", 7: "23", 8: "24", 9: "24", 10: "25", 11: "25", 12: "25", 13: "26", 14: "26"}
rp2_body = qn_all
qn_uniq = sorted(set(int(x) for x in re.findall(r'<span class="qn">Q(\d+)</span>', rp2_body)))
assert qn_uniq == list(range(1, 15)), qn_uniq
nw = len(WARN)
wtxt = ", ".join(f"Q{n}" for n in sorted(WARN))
chips = '<div class="qchips">' + "".join(f'<a class="qc{" w" if n in WARN else ""}" href="#sec{SEC[n]}" title="{esc(QT[n])}">Q{n}</a>' for n in range(1, 15)) + "</div>"
rp2 = mk(f'<div class="card"><p><b>Jawaban singkat:</b> semua {len(QT)} pertanyaan terjawab ({npr["Utama"]} Utama, {npr["Pendukung"]} Pendukung, {npr["Tambahan"]} Tambahan). '
         f'{nw} jawaban dengan catatan (kuning): {wtxt}. Klik nomor pertanyaan untuk melompat ke pembahasannya. Tarif adalah asumsi dan penghematan adalah batas atas.</p>',
         chips, '<p class="report-note">Q hijau = terjawab, Q kuning = terjawab dengan catatan. Pembahasan dikelompokkan per tema (2.1 sampai 2.6).</p></div>', rp2_body)

# ---------------------------------------------------------------- 3-5. dataset, tools, alur
CODE_REL = "project/code/"
allcode = list((REPO / CODE_REL).rglob("*.py"))
npy, loc = len(allcode), sum(len(p.read_text(encoding="utf-8").splitlines()) for p in allcode)
nsql = len(list((REPO / CODE_REL).rglob("*.sql")))
hv = hyp.set_index("id")
rp3 = mk(f'<div class="card"><p><b>Jawaban singkat:</b> dataset sesuai rancangan (UCI 851, {I(dbc["readings"])} baris, 11 kolom, 1 tahun) dengan satu temuan penting: label 00:00 salah tanggal. '
         'Empat hipotesis terbukti dan satu terbukti sebagian. Lisensi dataset belum diverifikasi.</p></div>',
         table(["Aspek", "Rancangan", "Realisasi", "Verdict"], [
             ["Sumber", f"UCI dataset 851, versi 1, akses {cs(ACCESS_DATE)}", "CSV dilampirkan manual karena unduhan dari lingkungan kerja diblokir; isi file dicocokkan dengan ukuran dan kolom rancangan", PART("Sesuai + penyesuaian")],
             ["Ukuran", "±35.040 baris, 11 kolom, ±1 tahun", f"{I(dq['baris'])} baris, {I(dq['kolom'])} kolom, {I(dq['jumlah_hari'])} hari", OK("Sesuai")],
             ["Kualitas label waktu", "Tidak disebut", f"{I(dq['baris_00_00_salah_tanggal'])} baris 00:00 salah tanggal; diperbaiki dan dicatat di log (L1)", PART("Temuan baru")],
             ["Lisensi dan sitasi", "Dicek di halaman sumber sebelum dipublikasikan", "Belum diverifikasi (halaman UCI tidak bisa dibuka dari lingkungan kerja); dicatat di <code>project/data/README.md</code>", NO("Belum selesai")],
             ["Tabel", "readings, dim_time, dim_tariff, daily_summary", f"Keempatnya dengan constraint; {I(dbc['readings'])}, {I(dbc['dim_time'])}, {I(dbc['dim_tariff'])}, {I(dbc['daily_summary'])} baris", OK("Sesuai")],
             ["Tarif", f"Peak Rp{I(RATE_PEAK)}, off-peak Rp{I(RATE_OFF)}, jam {I(PEAK_START)} sampai {I(PEAK_END)} (asumsi)", "Dipakai, tersimpan di <code>dim_tariff</code>; perubahan tarif terbukti mengubah biaya (Tabel 2.6b)", OK("Sesuai")],
             ["Hipotesis 1: pemakaian tertinggi siang, terendah malam", "Belum terbukti", cs(hv.loc["H1", "bukti"]), OK("Terbukti")],
             ["Hipotesis 2: akhir pekan jauh lebih rendah", "Belum terbukti", cs(hv.loc["H2", "bukti"]), OK("Terbukti")],
             ["Hipotesis 3: beban Maximum terkumpul di jam tertentu", "Belum terbukti", cs(hv.loc["H3", "bukti"]), OK("Terbukti")],
             ["Hipotesis 4: PF rendah lebih sering saat beban ringan", "Belum terbukti", cs(hv.loc["H4", "bukti"]), OK("Terbukti")],
             ["Hipotesis 5: sebagian beban peak bisa dipindah tanpa puncak baru", "Belum terbukti", cs(hv.loc["H5", "bukti"]), PART("Sebagian")]]))
rp4 = mk(f'<div class="card"><p><b>Jawaban singkat:</b> semua tools rancangan dipakai kecuali Excel (opsional, diganti pandas). Streamlit dibuat dan diuji lokal tetapi belum di-deploy.</p></div>',
         table(["Tool", "Rancangan", "Realisasi", "Verdict"], [
             ["Python (pandas)", "Baca CSV, cek interval, cleaning, pecah tabel, skenario", f"{I(npy)} skrip dan modul, {I(loc)} baris; satu urutan skrip bisa dijalankan ulang dari CSV mentah", OK("Sesuai")],
             ["DuckDB + SQL", "Profil beban, biaya per blok tarif, ringkasan harian sebagai view", f"<code>energy.duckdb</code> dengan constraint; {I(nsql)} file SQL; 7 view KPI", OK("Sesuai")],
             ["Excel (opsional)", "Cek silang PivotTable (Q14)", f"Diganti cek silang pandas ({I(cc_n)} pemeriksaan); rancangan mengizinkan penggantian", PART("Diganti pandas")],
             ["Streamlit + Plotly", "Dashboard 4 halaman, filter, slider skenario, publikasi gratis", "<code>streamlit/app.py</code> 4 halaman (Ringkasan, Profil beban, Biaya dan tarif, Skenario hemat), diuji dengan <code>AppTest</code>; belum di-deploy", PART("Sebagian")],
             ["GitHub", "Kode, query, README", "Struktur dan README siap di branch <code>project-6-build</code>, belum digabung ke <code>main</code>", PART("Sebagian")],
             ["Markdown", "README", "README dan dokumen definisi dibuat dari CSV hasil", OK("Sesuai")],
             ["matplotlib dan nbformat", "Tidak ada di rancangan", "Infografis dan notebook otomatis", PART("Tambahan")]]))
steps = [("1", "Menyepakati definisi KPI dan tarif", "<code>project/docs/definitions.md</code>", PART("Sesuai + penyesuaian"), "Tarif dan jam peak adalah asumsi rancangan; belum disepakati dengan tim utilitas."),
         ("2", "Merancang struktur tabel", "<code>01_schema.sql</code>, <code>data_dictionary.md</code>", OK("Sesuai"), "Ditambah constraint (PK, FK, CHECK)."),
         ("3", "Mengunduh dan memeriksa data", "<code>01_load_profile.py</code>", PART("Sesuai + penyesuaian"), "CSV dilampirkan manual; skrip berhenti dengan pesan jelas jika file tidak ada."),
         ("4", "Memeriksa interval dan membersihkan data", "<code>01_load_profile.py</code>", PART("Sesuai + temuan"), "365 baris 00:00 salah tanggal; log L1 sampai L5."),
         ("5", "Memasukkan data ke database", "<code>02_build_db.py</code>, <code>02_load.sql</code>", PART("Sesuai + tambahan"), "Ditambah uji penolakan dan pemeriksaan konsistensi."),
         ("6", "Menulis query KPI dan profil beban", "<code>03_views.sql</code>, <code>03_run_queries.py</code>", OK("Sesuai"), ""),
         ("7", "Cek silang", "<code>04_crosscheck.py</code>", PART("Sesuai + penyesuaian"), "Dengan pandas, bukan Excel."),
         ("8", "Menganalisis beban puncak dan biaya", "<code>05_analysis.py</code>", OK("Sesuai"), ""),
         ("9", "Menghitung skenario pemindahan beban", "<code>06_scenarios.py</code>", OK("Sesuai"), "10, 20, 30 persen, ditambah batas atas 40 persen."),
         ("10", "Menguji kewajaran temuan", "<code>07_validate_sensitivity.py</code>", PART("Sesuai + tambahan"), "Ditambah sensitivitas label waktu dan uji tarif."),
         ("11", "Membuat dashboard", "<code>08_build_dashboard_data.py</code>, <code>streamlit/app.py</code>", PART("Sebagian"), "Belum di-deploy ke Streamlit Community Cloud."),
         ("12", "Menulis README dan finalisasi", "<code>11_build_readme.py</code>, halaman ini", PART("Sebagian"), "Siap; digabung ke main setelah ditinjau.")]
renames = [("docs/kpi_definitions.md", "project/docs/definitions.md"), ("docs/data_dictionary.md", "project/docs/data_dictionary.md"), ("data/README.md", "project/data/README.md"),
           ("data/raw/steel_energy.csv", "project/data/raw/Steel_industry_data.csv (tidak di-commit)"), ("scripts/clean_load.py", CODE_REL + "1-data-preparation/python/01_load_profile.py, " + CODE_REL + "1-data-preparation/python/02_build_db.py"),
           ("outputs/cleaning_log.csv", "project/results/1-data-preparation/cleaning_log.csv"), ("sql/", CODE_REL + "1-data-preparation/sql/01_schema.sql, " + CODE_REL + "2-analysis/sql/03_views.sql"),
           ("energy.duckdb", "project/energy.duckdb (tidak di-commit)"), ("notebooks/analysis.ipynb", "project/results/3-presentation/analysis.ipynb"), ("outputs/scenarios.csv", "project/results/2-analysis/scenarios.csv"),
           ("outputs/crosscheck.xlsx", "project/results/2-analysis/crosscheck_pandas.csv"), ("dashboard/app.py", CODE_REL + "3-presentation/streamlit/app.py"),
           ("outputs/one_sheet.pdf / .png", "project/results/3-presentation/infographic.pdf, project/results/3-presentation/infographic.png"), ("requirements.txt", "project/requirements.txt")]
for a, b in renames:
    for part in b.split(", "):
        part = part.split(" (")[0]
        if "*" in part or "tidak di-commit" in b:
            continue
        assert (REPO / part).exists(), part
rp5 = mk('<div class="card"><p><b>Jawaban singkat:</b> 12 langkah dijalankan sesuai urutan. Nama dan lokasi file berubah mengikuti struktur repo standar, cek silang memakai pandas, dan dua langkah (11 dan 12) belum sepenuhnya selesai.</p></div>',
         table(["Langkah", "Rancangan", "Realisasi", "Verdict", "Catatan"], [[a, b, c, d, e] for a, b, c, d, e in steps]),
         '<div class="card"><h4>Penyesuaian dan improvisasi yang tidak ada di rancangan</h4><ul class="tight">',
         '<li>Label waktu CSV dibaca sebagai akhir interval karena 365 baris 00:00 bertanggal sama dengan awal hari; jam sebuah interval diambil dari awalnya (label dikurangi 15 menit). Sensitivitasnya ada di Tabel 2.6a.</li>',
         f'<li>Jam tujuan pemindahan dipilih dari tujuh jam off-peak berbeban terendah dan beban dibagi rata; batas atas {P(MAX_SHIFT, 0)} diambil dari catatan rancangan.</li>',
         '<li>Cek silang memakai pandas (rancangan mengizinkan pengganti Excel).</li>',
         '<li>Tarif dikunci ke satu tabel dan diuji dengan mengubah tarif di salinan database.</li>',
         '<li>Notebook, README, infografis, dan angka halaman ini dibuat otomatis dari hasil, dan angka halaman ini diaudit terhadap file hasil.</li></ul></div>',
         '<div class="card"><h4>Perubahan nama dan lokasi file terhadap rancangan</h4>',
         table(["Rancangan", "Realisasi"], [[f"<code>{a}</code>", ", ".join(f"<code>{x}</code>" if "(" not in x else x for x in b.split(", "))] for a, b in renames]) + '</div>')

# ---------------------------------------------------------------- 6. output
chk = lambda rel: (REPO / rel).exists()
outs = [("Dashboard interaktif", "Utama", PART("Sebagian"), "<code>streamlit/app.py</code> (4 halaman) diuji lokal dengan AppTest. Link publik belum ada"),
        ("One-sheet infografik", "Utama", OK("Tercapai"), "<code>infographic.png</code> dan <code>infographic.pdf</code>"),
        ("Database & query SQL", "Utama", OK("Tercapai"), f"<code>energy.duckdb</code> (dibuat ulang, tidak di-commit) dan {I(nsql)} file SQL"),
        ("Skrip cleaning & pemuat data", "Utama", OK("Tercapai"), "<code>01_load_profile.py</code> dan <code>02_build_db.py</code>, dengan log cleaning dan kamus data"),
        ("Notebook analisis", "Utama", OK("Tercapai"), "<code>analysis.ipynb</code> dieksekusi tanpa error, mencakup Q1 sampai Q14"),
        ("Laporan temuan & rekomendasi", "Utama", OK("Tercapai"), "<code>README.md</code> dan halaman ini"),
        ("Repositori GitHub", "Utama", PART("Sebagian"), "Struktur dan cara menjalankan ulang siap; berada di branch <code>project-6-build</code>, belum digabung ke <code>main</code>"),
        ("Slide presentasi", "Opsional", NO("Tidak dibuat"), "Opsional, tidak dibuat")]
nU = [o for o in outs if o[1] == "Utama"]
cnt = lambda s: sum(1 for o in nU if s in o[2])
docs = [("index.html", "Halaman rancangan", "index.html"), ("docs/kpi_definitions.md", "Definisi KPI, blok jam, tarif", "project/docs/definitions.md"), ("docs/data_dictionary.md", "Kamus data 4 tabel", "project/docs/data_dictionary.md"),
        ("data/README.md", "Sumber, lisensi, cara mengunduh", "project/data/README.md"), ("data/raw/steel_energy.csv", "Data mentah (tidak di-commit)", "project/data/raw"),
        ("scripts/clean_load.py", "Cek interval, cleaning, pemuat DuckDB", "project/code/1-data-preparation/python/01_load_profile.py"), ("outputs/cleaning_log.csv", "Catatan koreksi", "project/results/1-data-preparation/cleaning_log.csv"),
        ("energy.duckdb", "File database (tidak di-commit)", "project/energy.duckdb"), ("requirements.txt", "Paket Python", "project/requirements.txt"), ("sql/", "Query dan view KPI", "project/code/2-analysis/sql/03_views.sql"),
        ("notebooks/analysis.ipynb", "Analisis Q1 sampai Q14", "project/results/3-presentation/analysis.ipynb"), ("outputs/crosscheck.xlsx", "Cek silang (opsional)", "project/results/2-analysis/crosscheck_pandas.csv"),
        ("outputs/scenarios.csv", "Skenario pemindahan beban", "project/results/2-analysis/scenarios.csv"), ("dashboard/app.py", "Dashboard Streamlit", "project/code/3-presentation/streamlit/app.py"),
        ("outputs/one_sheet.pdf / .png", "One-sheet infografik", "project/results/3-presentation/infographic.pdf"), ("README.md", "Laporan temuan", "README.md"), ("slides/", "Slide (opsional)", "slides")]
stat_doc = lambda rel: PART("Tidak di-commit") if ("duckdb" in rel or "raw" in rel) else (OK("Ada") if chk(rel) else NO("Belum ada"))
rp6 = mk(f'<div class="card"><p><b>Jawaban singkat:</b> {I(cnt("Tercapai"))} dari {I(len(nU))} output Utama tercapai penuh dan {I(cnt("Sebagian"))} sebagian (dashboard belum punya link publik, repositori belum digabung ke main). Slide Opsional tidak dibuat.</p></div>',
         table(["Output", "Label", "Status", "Bukti"], [[f"<b>{a}</b>", b, c, d] for a, b, c, d in outs]),
         '<div class="card"><h4>Daftar dokumen pada rancangan vs repositori</h4>',
         table(["Dokumen (rancangan)", "Isi", "Lokasi sekarang", "Status"], [[f"<code>{a}</code>", b, f"<code>{c}</code>", stat_doc(c)] for a, b, c in docs]),
         '<p>Data mentah, data bersih, dan <code>energy.duckdb</code> tidak di-commit karena bisa dibuat ulang oleh skrip.</p></div>')

# ---------------------------------------------------------------- 7. kesimpulan
crit = [("1. Kesembilan pertanyaan Utama terjawab dengan angka", OK("Tercapai"), "Q1, Q2, Q4, Q5, Q6, Q10, Q11, Q13, Q14 terjawab (bagian 2); empat dengan catatan"),
        ("2. Angka KPI dari SQL sama dengan hitungan Excel atau pandas", OK("Tercapai"), f"{I(cc_n)} pemeriksaan PASS dengan pandas (Excel tidak dipakai)"),
        ("3. Total kWh setelah cleaning cocok dengan data mentah, setiap perubahan tercatat", OK("Tercapai"), f"{I(db_kwh)} kWh di database = {I(dq['total_kwh_mentah'])} kWh mentah; {I(dq['baris_00_00_salah_tanggal'])} perubahan tanggal tercatat di <code>fix_flag</code> dan log"),
        ("4. Orang awam membuka dashboard dan menyebut jam puncak serta porsi biaya peak dalam &lt; 1 menit", PART("Belum diuji"), "Dashboard dibuat tetapi belum di-deploy dan belum diuji ke pembaca sebenarnya"),
        ("5. Tarif diganti di satu tempat dan semua biaya ikut berubah", OK("Tercapai"), "Tabel 2.6b: perubahan <code>dim_tariff</code> sama dengan hitungan manual; dashboard punya isian tarif"),
        ("6. Checklist standar (pertanyaan bisnis, cleaning, SQL, dashboard ter-deploy, README)", PART("Sebagian"), "Semua ada kecuali dashboard ter-deploy")]
ncr = sum(1 for c in crit if ">Tercapai<" in c[1])
rp7 = mk(
    '<div class="card"><h4>7.1 Hasil analisis: jawaban atas pertanyaan utama</h4>',
    '<p><i>Kapan beban puncak terjadi, berapa biayanya, dan berapa yang bisa dihemat jika sebagian beban dipindah ke jam yang lebih murah?</i></p><ul class="tight">',
    f'<li><b>Kapan:</b> beban tertinggi di jam {I(pk_h)} pada hari kerja (dan terendah jam {I(mn_h)}); beban Maximum terkumpul di {I(n80)} jam. Akhir pekan hanya {P(ev.weekend_ratio, 0)} dari hari kerja.</li>',
    f'<li><b>Berapa biayanya (estimated):</b> Rp{juta(kpi.cost, 0)} juta setahun dengan tarif asumsi, {P(kpi.peak_cost_share, 0)} di blok peak. Blok tarif peak (jam {I(PEAK_START)} sampai {I(PEAK_END)}) bukan jam beban tertinggi, jadi jam mahal tidak identik dengan jam puncak.</li>',
    f'<li><b>Berapa yang bisa dihemat (estimated, batas atas):</b> Rp{juta(s10.penghematan_per_bulan, 2)} juta per bulan pada pemindahan {P(s10.pct, 0)} sampai Rp{juta(s40.penghematan_per_bulan, 2)} juta pada {P(s40.pct, 0)}. Puncak tahunan tidak berubah.</li>',
    f'<li><b>Power factor:</b> rendah hampir selalu pada beban ringan ({P(ev.pf_low_light, 0)} interval Light), bukan pada beban tinggi.</li></ul></div>',
    '<div class="card"><h4>7.2 Impact</h4><ul class="tight">',
    f'<li><b>Nilai praktis (estimated):</b> memindahkan sebagian beban dari jam {I(PEAK_START)} sampai {I(PEAK_END)} menghemat sekitar Rp{juta(s10.penghematan_setahun, 1)} juta per tahun pada {P(s10.pct, 0)} (batas atas, tarif asumsi), tanpa menaikkan puncak tahunan.</li>',
    '<li><b>Nilai analitis:</b> temuan label 00:00 salah tanggal dan sensitivitasnya (Tabel 2.6a) menunjukkan cara memeriksa data time series sebelum menghitung biaya.</li>',
    '<li><b>Nilai portofolio:</b> pipeline lengkap: data publik berversi, cleaning bertanda, DuckDB dengan constraint dan view KPI, cek silang, skenario, dashboard, infografis, dan notebook.</li>',
    '<li><b>Belum terukur:</b> tarif kontrak sebenarnya, beban yang bisa digeser, dan penerimaan tim operasi.</li></ul></div>')
rp7 += ('<div class="card"><h4>7.3 Success criteria</h4>' + table(["Kriteria (Design Project, bagian 8)", "Status", "Bukti"], [[a, b, c] for a, b, c in crit])
        + f'<p><b>Hasil:</b> {I(ncr)} dari {I(len(crit))} kriteria tercapai, {I(len(crit) - ncr)} sebagian atau belum diuji.</p></div>')
rp7 += mk('<div class="card"><h4>7.4 Rekomendasi</h4><ul class="tight">',
          f'<li>Mulai dengan memindahkan {P(s10.pct, 0)} beban blok peak yang paling mudah ditunda (misalnya proses tidak kritis) ke jam {I(hrs_dest[0])} sampai {I(hrs_dest[-1])}.</li>',
          f'<li>Tinjau jam beban Maximum (jam {I(min(hrs80))} sampai {I(max(hrs80))}) untuk penjadwalan mesin berat, karena itu penentu beban puncak, bukan blok tarif peak.</li>',
          '<li>Pantau power factor pada jam beban ringan dan periksa penyebabnya di lapangan sebelum menyimpulkan.</li>',
          '<li>Ganti tarif asumsi dengan tarif kontrak di <code>dim_tariff</code> atau di dashboard sebelum angka dipakai untuk keputusan.</li></ul></div>')
rp7 += mk('<div class="card"><h4>7.5 Saran perbaikan</h4><ul class="tight">',
          '<li>Verifikasi lisensi dan cara sitasi dataset UCI dari halaman sumber sebelum dipublikasikan.</li>',
          '<li>Ganti tarif asumsi dengan tarif kontrak dan tambahkan biaya beban (kVA) dan denda kVArh.</li>',
          '<li>Dapatkan daftar beban yang bisa digeser dari tim operasi supaya skenario tidak lagi batas atas.</li>',
          '<li>Deploy dashboard ke Streamlit Community Cloud dan uji ke satu pembaca awam untuk mengisi kriteria 4 dan 6.</li></ul></div>')
rp7 += mk('<div class="card"><h4>7.6 Batasan</h4><ul class="tight">',
          '<li>Satu pabrik dan satu tahun; pola dan tarif di pabrik lain berbeda.</li>',
          f'<li>Tarif (Rp{I(RATE_PEAK)} dan Rp{I(RATE_OFF)} per kWh, jam {I(PEAK_START)} sampai {I(PEAK_END)}) adalah asumsi; biaya hanya komponen energi (kWh).</li>',
          '<li>Data tidak menyebut mesin mana yang menyala, jadi penghematan adalah batas atas dan kelayakan pemindahan belum diuji.</li>',
          '<li>Pola power factor rendah belum tentu penyebabnya; label waktu dibaca sebagai akhir interval berdasarkan bukti dari data, bukan dokumentasi sumber.</li>',
          '<li>Lisensi dataset belum diverifikasi. Dashboard belum di-deploy dan kriteria 4 dan 6 belum terpenuhi. Slide presentasi (Opsional) tidak dibuat.</li></ul></div>')

evq = [("1", "rp1", "Data yang didapat", OK("Didapat"), f"{I(dbc['readings'])} interval, {I(dbc['daily_summary'])} hari, 4 tabel, {I(len(resfiles))} CSV hasil"),
       ("2", "rp2", "Business question terjawab?", OK(f"{len(QT)} dari {len(QT)}"), f"Semua terjawab ({npr['Utama']} Utama, {npr['Pendukung']} Pendukung, {npr['Tambahan']} Tambahan); {nw} dengan catatan ({wtxt})"),
       ("3", "rp3", "Dataset sesuai?", PART("Sesuai + temuan"), "Dataset sesuai; label 00:00 diperbaiki; empat hipotesis terbukti, satu sebagian"),
       ("4", "rp4", "Tools sesuai?", PART("Sesuai + penyesuaian"), "Excel diganti pandas; Streamlit belum di-deploy"),
       ("5", "rp5", "Alur sesuai?", PART("Sesuai + penyesuaian"), "12 langkah dijalankan; sensitivitas dan uji tarif ditambahkan"),
       ("6", "rp6", "Output tercapai?", PART(f"{cnt('Tercapai')} penuh, {cnt('Sebagian')} sebagian"), f"{cnt('Tercapai')} dari {len(nU)} output Utama penuh"),
       ("7", "rp7", "Kesimpulan", OK("Tersedia"), f"Hasil analisis, Impact, {len(crit)} kriteria sukses, rekomendasi, saran perbaikan, batasan")]
evq_html = '<div class="scroll"><table class="evq"><tr><th>No</th><th>Pertanyaan evaluasi</th><th>Verdict</th><th>Ringkasan</th></tr>' + "".join(
    f'<tr><td><span class="en">{n}</span></td><td><a href="#{h}">{t}</a></td><td>{v}</td><td>{s}</td></tr>' for n, h, t, v, s in evq) + "</table></div>"
H = lambda i, t, sm, body: f'\n<h2 id="rp{i}">{i}. {t}<small>{sm}</small></h2>\n{body}\n'
report = mk(
    '<div class="pane" id="report" data-tab="report" hidden>\n',
    '<div class="callout g"><h4>Report Project versi 2: evaluasi hasil terhadap Design Project</h4><p>Halaman ini disusun sebagai 7 jawaban atas pertanyaan evaluasi. Tabel dan grafik dibuat otomatis dari hasil query SQL (DuckDB) dan analisis pada data UCI. '
    f'Hasil SQL dicek silang dengan pandas ({I(cc_n)} pemeriksaan). Angka pada teks diaudit terhadap file di <code>project/results/</code>: @@AUDIT@@ angka diperiksa tanpa selisih. '
    'Biaya dan penghematan memakai tarif asumsi. Rancangan lengkap ada di tab <a href="#design">Design Project</a>.</p></div>\n',
    evq_html,
    H(1, "Data yang berhasil didapatkan", "Isi data mentah, tabel di database, dan data hasil analisis", rp1),
    H(2, "Apakah business question terjawab?", f"{len(QT)} pertanyaan pada Design Project, dijawab dengan data", rp2),
    H(3, "Apakah dataset sesuai dengan Design Project?", "Perbandingan rancangan dengan realisasi", rp3),
    H(4, "Apakah tools yang digunakan sesuai?", "Perbandingan rancangan dengan eksekusi", rp4),
    H(5, "Apakah alur pengerjaan sesuai dengan Design Project?", f"{len(steps)} langkah rancangan vs yang dijalankan", rp5),
    H(6, "Apakah project output tercapai?", "Output pada Design Project, bagian 7", rp6),
    H(7, "Kesimpulan", "Hasil analisis, Impact, success criteria, rekomendasi, saran perbaikan, dan batasan", rp7),
    '</div>\n')

# ---------------------------------------------------------------- audit angka
STATIC = {str(i) for i in range(0, 21)} | {f"{i:02d}" for i in range(0, 13)} | {"30", "100", "50", "25", "24", "96", "90", "85", "2018", "2026", "1E-6", "0,01", "95", "40", "60", "12", "22", "17", "10", "15", "31", "365", "1.650", "1.100",
                                                                                   "35.040", "851", "0,85", "00:00", "24:00", "23:45", "00:15", "11", "7"}
STATIC |= {f"{a}.{b}" for a in range(1, 10) for b in range(1, 10)}
n_tok, bad = audit(report, STATIC)
manual = [("seluruh CSV hasil terdokumentasi", not miss), ("crosscheck semua PASS", (cc.status == "PASS").all()), ("semua uji constraint ditolak", (ctest.outcome == "ditolak").all()),
          ("semua pemeriksaan konsistensi 0 pelanggaran", (cons.violations == 0).all()), ("jumlah pertanyaan = 14 (9 Utama, 4 Pendukung, 1 Tambahan)", len(QT) == 14 and npr == {"Utama": 9, "Pendukung": 4, "Tambahan": 1}),
          ("catatan hanya Q6, Q10, Q11, Q14", WARN == {6, 10, 11, 14}), ("langkah rancangan = 12", len(steps) == 12), ("jumlah pertanyaan unik pada bagian 2 = 14", qn_uniq == list(range(1, 15))),
          ("total kWh database = mentah", abs(db_kwh - float(dq["total_kwh_mentah"])) < 0.01), ("penghematan naik menurut porsi", (sc.penghematan_setahun.diff().dropna() > 0).all()),
          ("puncak tahunan sama di semua skenario", sc.peak_kw_sebelum.eq(sc.peak_kw_sesudah).all()), ("uji tarif: selisih view vs manual di bawah 1", (tt.selisih.abs() < 1).all())]
assert all(v for _, v in manual), [k for k, v in manual if not v]
if bad:
    print("TOKEN TIDAK TERDAFTAR:", bad)
    sys.exit(1)
report = report.replace("@@AUDIT@@", I(n_tok) + f" (ditambah {I(len(manual))} klaim manual)")

# ---------------------------------------------------------------- rakit halaman
v1 = (HERE / "page_v1.html").read_text(encoding="utf-8")
a = v1.index('<div class="pane" id="report"')
b = v1.index("</main>")
design_pane = v1[v1.index('<div class="pane" id="design"'):a]
nav_old = re.search(r'<nav aria-label="Project navigation">.*?</nav>', v1, re.S).group(0)
btn = lambda t: re.search(rf'<button type="button" class="tab[^"]*" data-t="{t}".*?</button>', nav_old, re.S).group(0)
design_links = re.search(r'<div class="links" data-tab="design">.*?</div>', nav_old, re.S).group(0)
report_links = ('<div class="links" data-tab="report" hidden>' + "".join(f'<a href="#rp{i}">{t}</a>' for i, t in
               enumerate(["Data", "Business Questions", "Dataset", "Tools", "Alur Kerja", "Project Output", "Kesimpulan"], 1)) + "</div>")
nav_new = f'<nav aria-label="Project navigation">{btn("design")}{btn("report")}{design_links}{report_links}</nav>'
css = (HERE / "report.css").read_text(encoding="utf-8")
html = v1[:a] + report + v1[b:]
html = html.replace(nav_old, nav_new)
i = html.rindex("</style>")
html = html[:i] + css + html[i:]
out = REPO / "design-and-report" / "index.html"
out.write_text(html, encoding="utf-8")
assert design_pane == html[html.index('<div class="pane" id="design"'):html.index('<div class="pane" id="report"')], "pane Design berubah"
print(f"index.html {len(html) / 1024:.0f} KB; {n_tok} angka diaudit; {len(manual)} klaim manual; pane Design identik")
