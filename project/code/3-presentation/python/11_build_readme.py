"""Membuat README.md di root repo; semua angka dibaca dari CSV hasil."""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from common import ACCESS_DATE, RATE_OFF, RATE_PEAK, ROOT, result  # noqa: E402

R = lambda n: pd.read_csv(result(n))
f = lambda v, d=1: f"{v:.{d}f}".replace(".", ",")
pc = lambda v, d=0: f(v * 100, d) + "%"
n = lambda v: f"{int(round(float(v))):,}".replace(",", ".")
dq = R("data_quality.csv").set_index("ukuran").nilai
k, ev, sc, hl = R("kpi_year.csv").iloc[0], R("hypothesis_evidence.csv").iloc[0], R("scenarios.csv"), R("high_load_summary.csv").iloc[0]
cc, ct, cs = R("crosscheck_pandas.csv"), R("constraint_tests.csv"), R("consistency_checks.csv")
s10, s40 = sc.iloc[0], sc.iloc[-1]
juta = lambda v: f(v / 1e6, 1)

md = f"""[← Back to portfolio](https://bagusbernadi.github.io/)

# Project 6: Energy Consumption Dashboard

**Status: Selesai di branch `project-6-build` (menunggu review sebelum digabung ke `main`).**

Halaman rancangan dan Report: https://bagusbernadi.github.io/Project-6-Energy-Consumption-Dashboard/

| | |
|---|---|
| Kategori | Manufaktur (energi pabrik baja) |
| Data | Dataset publik UCI 851, Steel Industry Energy Consumption (lisensi belum diverifikasi) |
| Tools | SQL (DuckDB), Python (pandas, matplotlib), Jupyter, Streamlit + Plotly, GitHub |

## 1. Problem

Kapan pabrik memakai listrik paling banyak, berapa biayanya, dan apakah memindahkan sebagian beban dari jam tarif tinggi layak dipertimbangkan? Dipecah menjadi 14 pertanyaan (9 utama); jawabannya ada di tab Report.

## 2. Data

- {n(dq["baris"])} interval 15 menit, 1 tahun (2018), satu pabrik baja (DAEWOO Steel, Gwangyang). Sumber: [UCI 851]({'https://archive.ics.uci.edu/dataset/851/steel+industry+energy+consumption'}), tanggal akses {ACCESS_DATE}. Data tidak di-commit (lihat `project/data/README.md`).
- Ditemukan {n(dq["baris_00_00_salah_tanggal"])} baris berlabel 00:00 yang sebenarnya akhir hari (bertanggal sama dengan awal hari); tanggalnya digeser +1 hari, setelah itu {n(dq["jumlah_hari"])} hari lengkap 96 interval, tanpa duplikat.

## 3. Analysis

- Energi {f(k.total_kwh/1000, 0)} MWh setahun, beban puncak {f(k.peak_kw, 0)} kW, load factor {f(k.load_factor, 2)}.
- Jam tersibuk jam {n(ev.peak_hour)}; akhir pekan hanya {pc(ev.weekend_ratio)} dari hari kerja. Porsi PF rendah: Light {pc(ev.pf_low_light)}, Medium {pc(ev.pf_low_medium)}, Maximum {pc(ev.pf_low_max)} (hipotesis PF rendah saat beban ringan terbukti).
- Blok tarif peak (17-22) bukan jam beban tertinggi; porsinya {pc(k.peak_cost_share)} dari biaya (tarif asumsi Rp{n(RATE_PEAK)} dan Rp{n(RATE_OFF)} per kWh).
- {n(hl.n_kejadian)} kejadian beban tinggi (di atas P90), durasi median {f(hl.durasi_median_jam, 1)} jam.
- Skenario pemindahan 10%: hemat Rp{juta(s10.penghematan_setahun)} juta per tahun (estimated); 40% (batas atas): Rp{juta(s40.penghematan_setahun)} juta. Puncak tahunan tidak berubah.
- Validasi: {n(len(ct))} uji constraint, {n(len(cs))} pemeriksaan konsistensi, {n(len(cc))} pemeriksaan SQL vs pandas ({n(cc.jumlah_nilai.sum())} nilai) lulus.

## 4. Recommendation

Mulai dari pemindahan beban peak yang paling mudah (10%), pantau power factor di jam beban ringan, dan ganti tarif asumsi dengan tarif kontrak sebelum menghitung ulang di dashboard.

## 5. Impact

Estimated: Rp{juta(s10.penghematan_per_bulan)} juta per bulan pada skenario 10% (batas atas, tarif asumsi).

## Batasan

- Satu pabrik, satu tahun; tarif adalah asumsi; penghematan adalah batas atas (kelayakan operasional tidak diuji).
- Lisensi dataset belum diverifikasi. Dashboard belum di-deploy.

## Menjalankan

```
pip install -r project/requirements.txt
cd project/code/1-data-preparation/python && python 01_load_profile.py && python 02_build_db.py
cd ../../2-analysis/python && for s in 03 04 05 06 07; do python ${{s}}_*.py; done
cd ../../3-presentation/python && for s in 08 09 10 11; do python ${{s}}_*.py; done
streamlit run ../streamlit/app.py
python design-and-report/src/build_report.py   # dari root repo
```

## Struktur repository

```
index.html                 Pengalihan ke design-and-report/
design-and-report/         Halaman Design dan Report (src/ berisi generator)
project/
  code/1-data-preparation  Muat dan profil data, database (python, sql)
  code/2-analysis          View SQL, analisis, skenario, validasi
  code/3-presentation      Data dashboard, infografis, notebook, README, Streamlit
  results/                 CSV hasil per tahap, infografis, notebook
  docs/                    Definisi dan kamus data
  data/                    README sumber data (data mentah dan bersih tidak di-commit)
```
"""
(ROOT.parent / "README.md").write_text(md, encoding="utf-8")
print("README.md ditulis")
