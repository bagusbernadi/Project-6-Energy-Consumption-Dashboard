[← Back to portfolio](https://bagusbernadi.github.io/)

# Project 6: Energy Consumption Dashboard

**Status: Design (rancangan).** Halaman rancangan ada di [`index.html`](index.html). Analisis, dashboard, dan angka hasil belum dikerjakan, sehingga bagian Analysis, Recommendation, dan Impact di bawah masih kosong.

**Tujuan:** membangun dashboard pemakaian listrik pabrik yang menunjukkan kapan beban puncak terjadi, berapa biaya yang ditimbulkannya, dan beban mana yang bisa dipindah ke jam yang lebih murah, sehingga jadwal operasi dapat disusun untuk menekan biaya energi.

| | |
|---|---|
| Kategori | Industri & energi (Tech / Energi) |
| Tingkat | Mudah |
| Data | Dataset publik UCI Steel Industry Energy Consumption |
| Tools | DuckDB + SQL, Python (pandas), Streamlit + Plotly. Excel opsional |

## 1. Problem

**Pertanyaan utama:** Kapan beban puncak terjadi, berapa biayanya, dan berapa yang bisa dihemat jika sebagian beban dipindah ke jam yang lebih murah?

Rancangan memecahnya menjadi 14 pertanyaan (9 Utama, 4 Pendukung, 1 Tambahan) dalam tema pola waktu, beban puncak, biaya, kualitas daya dan emisi, dampak, serta validitas data. Daftar lengkap ada di bagian 2 halaman rancangan.

## 2. Data

- Sumber data: [here](https://archive.ics.uci.edu/dataset/851/steel+industry+energy+consumption) (Versi: 1, Tanggal akses: 23 Oktober 2026)
- Sumber: pabrik baja DAEWOO Steel, Gwangyang, Korea Selatan (UCI Machine Learning Repository).
- Ukuran (perkiraan, **belum diverifikasi**): ±35.040 baris per 15 menit, 11 kolom, ±1 tahun.
- Biaya dihitung dengan tarif contoh berlabel asumsi: off-peak Rp1.100/kWh, peak 17.00–22.00 Rp1.650/kWh.
- Rencana tabel: `readings`, `dim_time`, `dim_tariff`, `daily_summary`.
- Lisensi dan sitasi: dicek di halaman sumber sebelum project dipublikasikan.
- Data mentah tidak di-commit ke repository.

## 3. Analysis

Belum dikerjakan. Rencana langkah (12 langkah, tahap A sampai D) ada di bagian 6 halaman rancangan. Semua angka nanti dihitung dari data dengan SQL dan dicek silang.

Hipotesis yang akan diuji (belum terbukti):
1. Pemakaian tertinggi di jam kerja siang, terendah malam hari.
2. Pemakaian akhir pekan jauh lebih rendah.
3. Beban Maximum terkumpul di beberapa jam tertentu.
4. Power factor rendah lebih sering saat beban ringan.
5. Sebagian beban jam peak bisa dipindah tanpa puncak baru.

## 4. Recommendation

Belum dikerjakan. Output yang direncanakan: jadwal pemindahan beban dari jam peak ke jam off-peak.

## 5. Impact

Belum dikerjakan. Rumus yang akan dipakai (semua hasil diberi label `estimated`):

```
Penghematan per bulan = kWh dipindah × (tarif peak − tarif off-peak)
```

## Batasan yang sudah diketahui

- Data tidak menyebut mesin mana yang menyala, jadi penghematan adalah batas atas.
- Tarif adalah asumsi, bukan tarif resmi.
- Satu pabrik dan satu tahun data.

## Struktur repository

```
index.html   Halaman rancangan project (bisa dibuka di browser atau lewat GitHub Pages)
README.md    Dokumen ini
```

Folder `docs/`, `data/`, `scripts/`, `sql/`, `notebooks/`, `dashboard/`, dan `outputs/` ditambahkan saat pengerjaan dimulai.
