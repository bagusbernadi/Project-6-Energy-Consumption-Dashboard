"""Membangun energy.duckdb dari data bersih, menguji constraint, dan memeriksa konsistensi antar tabel."""
import sys
from pathlib import Path

import duckdb
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import common as C  # noqa: E402

C.chdir_root()
if C.DB_PATH.exists():
    C.DB_PATH.unlink()
con = duckdb.connect(str(C.DB_PATH))
con.execute((C.SQL_PREP / "01_schema.sql").read_text())
load = (C.SQL_PREP / "02_load.sql").read_text()
for k, v in {"$peak_start": C.PEAK_START, "$peak_end": C.PEAK_END, "$rate_peak": C.RATE_PEAK, "$rate_off": C.RATE_OFF}.items():
    load = load.replace(k, str(v))
con.execute(load)
con.execute((C.SQL_ANALYSIS / "03_views.sql").read_text())
con.execute("INSERT INTO daily_summary SELECT * FROM v_daily")

# uji constraint: baris salah harus ditolak
tests = [("ts ganda", "INSERT INTO readings SELECT 99999, ts, 1, 1, 1, 90, 100, 0, 'Light_Load', 'ok' FROM readings LIMIT 1"),
         ("kWh negatif", "INSERT INTO readings VALUES (99998, '2030-01-01 00:15', -1, 0, 0, 90, 100, 0, 'Light_Load', 'ok')"),
         ("power factor di atas 100", "INSERT INTO readings VALUES (99997, '2030-01-01 00:30', 1, 0, 0, 120, 100, 0, 'Light_Load', 'ok')"),
         ("Load_Type tidak dikenal", "INSERT INTO readings VALUES (99996, '2030-01-01 00:45', 1, 0, 0, 90, 100, 0, 'Heavy', 'ok')"),
         ("fix_flag tidak dikenal", "INSERT INTO readings VALUES (99995, '2030-01-01 01:00', 1, 0, 0, 90, 100, 0, 'Light_Load', 'x')"),
         ("dim_time tanpa readings", "INSERT INTO dim_time VALUES ('2031-01-01 00:00', '2030-12-31 23:45', '2030-12-31', 23, 85500, 'Tuesday', 'Weekday', 12)"),
         ("jam di luar 0-23", "INSERT INTO dim_time SELECT ts, ts_start, date, 25, nsm, day_of_week, week_status, month FROM dim_time LIMIT 1"),
         ("tarif nol", "INSERT INTO dim_tariff VALUES ('X', 0, 1, FALSE, 0)"),
         ("blok tarif ganda", "INSERT INTO dim_tariff VALUES ('Peak', 0, 1, TRUE, 1)"),
         ("tanggal ganda di daily_summary", "INSERT INTO daily_summary SELECT * FROM daily_summary LIMIT 1")]
rows = []
for name, sql in tests:
    try:
        con.execute(sql)
        rows.append((name, "DITERIMA"))
    except Exception:
        rows.append((name, "ditolak"))
pd.DataFrame(rows, columns=["test", "outcome"]).to_csv(C.RES_PREP / "constraint_tests.csv", index=False)
assert all(o == "ditolak" for _, o in rows), rows

checks = {
    "readings = 35.040 baris": "SELECT abs(count(*) - 35040) FROM readings",
    "dim_time satu baris per readings": "SELECT count(*) FROM readings r LEFT JOIN dim_time t USING (ts) WHERE t.ts IS NULL",
    "setiap interval masuk tepat satu blok tarif": "SELECT abs(count(*) - 35040) FROM v_interval",
    "setiap hari tepat 96 interval": "SELECT count(*) FROM (SELECT date FROM v_interval GROUP BY date HAVING count(*) <> 96)",
    "jumlah hari 365": "SELECT abs(count(*) - 365) FROM daily_summary",
    "total kWh harian = total kWh readings": "SELECT abs((SELECT sum(total_kwh) FROM daily_summary) - (SELECT sum(usage_kwh) FROM readings))",
    "biaya = kWh x tarif blok": "SELECT abs((SELECT sum(cost) FROM daily_summary) - (SELECT sum(usage_kwh * rate_per_kwh) FROM v_interval))",
    "peak_cost_share antara 0 dan 1": "SELECT count(*) FROM daily_summary WHERE peak_cost_share NOT BETWEEN 0 AND 1",
    "ts menaik terhadap row_id": "SELECT count(*) FROM (SELECT ts > lag(ts) OVER (ORDER BY row_id) AS ok FROM readings) WHERE ok = FALSE",
}
res = [(k, round(float(con.execute(q).fetchone()[0]), 6)) for k, q in checks.items()]
pd.DataFrame(res, columns=["pemeriksaan", "violations"]).to_csv(C.RES_PREP / "consistency_checks.csv", index=False)
assert all(v < 1e-6 for _, v in res), res
rowsn = [(t, con.execute(f"SELECT count(*) FROM {t}").fetchone()[0]) for t in ("readings", "dim_time", "dim_tariff", "daily_summary")]
pd.DataFrame(rowsn, columns=["tabel", "baris"]).to_csv(C.RES_PREP / "table_rows.csv", index=False)
print(rowsn, "constraint 10/10 ditolak,", len(res), "pemeriksaan konsistensi 0 pelanggaran")
con.close()
