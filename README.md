[← Back to portfolio](https://bagusbernadi.github.io/)

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

- 35.040 interval 15 menit, 1 tahun (2018), satu pabrik baja (DAEWOO Steel, Gwangyang). Sumber: [UCI 851](https://archive.ics.uci.edu/dataset/851/steel+industry+energy+consumption), tanggal akses 23 Oktober 2026. Data tidak di-commit (lihat `project/data/README.md`).
- Ditemukan 365 baris berlabel 00:00 yang sebenarnya akhir hari (bertanggal sama dengan awal hari); tanggalnya digeser +1 hari, setelah itu 365 hari lengkap 96 interval, tanpa duplikat.

## 3. Analysis

- Energi 960 MWh setahun, beban puncak 629 kW, load factor 0,17.
- Jam tersibuk jam 9; akhir pekan hanya 35% dari hari kerja. Porsi PF rendah: Light 77%, Medium 10%, Maximum 14% (hipotesis PF rendah saat beban ringan terbukti).
- Blok tarif peak (17-22) bukan jam beban tertinggi; porsinya 32% dari biaya (tarif asumsi Rp1.650 dan Rp1.100 per kWh).
- 983 kejadian beban tinggi (di atas P90), durasi median 0,5 jam.
- Skenario pemindahan 10%: hemat Rp12,5 juta per tahun (estimated); 40% (batas atas): Rp50,1 juta. Puncak tahunan tidak berubah.
- Validasi: 10 uji constraint, 9 pemeriksaan konsistensi, 21 pemeriksaan SQL vs pandas (2.017 nilai) lulus.

## 4. Recommendation

Mulai dari pemindahan beban peak yang paling mudah (10%), pantau power factor di jam beban ringan, dan ganti tarif asumsi dengan tarif kontrak sebelum menghitung ulang di dashboard.

## 5. Impact

Estimated: Rp1,0 juta per bulan pada skenario 10% (batas atas, tarif asumsi).

## Batasan

- Satu pabrik, satu tahun; tarif adalah asumsi; penghematan adalah batas atas (kelayakan operasional tidak diuji).
- Lisensi dataset belum diverifikasi. Dashboard belum di-deploy.

## Menjalankan

```
pip install -r project/requirements.txt
cd project/code/1-data-preparation/python && python 01_load_profile.py && python 02_build_db.py
cd ../../2-analysis/python && for s in 03 04 05 06 07; do python ${s}_*.py; done
cd ../../3-presentation/python && for s in 08 09 10 11; do python ${s}_*.py; done
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
