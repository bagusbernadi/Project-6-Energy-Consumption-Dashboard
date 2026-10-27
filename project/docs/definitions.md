# Definisi (Project 6)

| Istilah | Definisi |
|---|---|
| Interval | 15 menit; label `date` di CSV = akhir interval. Interval dimulai 15 menit sebelum label (`ts_start`) |
| Koreksi 00:00 | 365 baris berlabel 00:00 adalah akhir hari (24:00); tanggal digeser +1 hari (L1) |
| Jam | Jam mulai interval (0 sampai 23); satu jam = 4 interval |
| Beban (kW) | kWh interval x 4 |
| Beban puncak | Maksimum beban interval pada periode tertentu |
| Load factor | Beban rata-rata / beban puncak (harian: kWh / 24 / puncak kW) |
| Blok peak | Jam 17:00 sampai 21:59 (ASUMSI), tarif Rp1.650/kWh; off-peak Rp1.100/kWh (ASUMSI) |
| Biaya | kWh x tarif blok (estimated, bukan tagihan) |
| PF rendah | `lag_pf` kurang dari 85 persen |
| Beban tinggi | Interval di atas persentil 90 kWh per interval; kejadian = interval berurutan di atas ambang |
| Skenario pemindahan | Sebagian kWh blok peak (10/20/30%, batas atas 40%) dipindah ke 7 jam off-peak berbeban terendah pada hari yang sama; hemat = kWh dipindah x (1.650 - 1.100). Batas atas karena kelayakan operasional tidak diuji |
