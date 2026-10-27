"""Pengaturan bersama untuk semua skrip. Semua jalur relatif terhadap folder project/."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent          # folder project/
DATA = ROOT / "data"
RAW_DIR = DATA / "raw"                                 # CSV asli UCI (tidak di-commit)
CLEAN_DIR = DATA / "clean"                             # data bersih (tidak di-commit)
RAW_CSV = RAW_DIR / "Steel_industry_data.csv"
CLEAN_CSV = CLEAN_DIR / "readings_clean.csv"
DB_PATH = ROOT / "energy.duckdb"
CODE = ROOT / "code"
SQL_PREP = CODE / "1-data-preparation" / "sql"
SQL_ANALYSIS = CODE / "2-analysis" / "sql"
RES_PREP = ROOT / "results" / "1-data-preparation"
RES_ANALYSIS = ROOT / "results" / "2-analysis"
RES_PRESENT = ROOT / "results" / "3-presentation"
DOCS_DIR = ROOT / "docs"
for _d in (RAW_DIR, CLEAN_DIR, RES_PREP, RES_ANALYSIS, RES_PRESENT):   # dibuat otomatis pada repo bersih
    _d.mkdir(parents=True, exist_ok=True)

# Sumber data (UCI, dataset 851)
DATA_VERSION = "1"
ACCESS_DATE = "23 Oktober 2026"                        # tanggal akses dari halaman rancangan
SOURCE_URL = "https://archive.ics.uci.edu/dataset/851/steel+industry+energy+consumption"

# Definisi (lihat docs/definitions.md)
INTERVAL_MIN = 15
PER_DAY = 96
PEAK_START, PEAK_END = 17, 22                          # blok peak: jam 17:00 sampai 21:59
RATE_OFF, RATE_PEAK = 1100, 1650                       # Rp per kWh, ASUMSI (bukan tarif resmi)
PF_LIMIT = 85.0                                        # power factor rendah jika di bawah 85 (persen)
HIGH_Q = 0.90                                          # ambang beban tinggi = persentil 90 kWh per interval
SHIFT_PCTS = [0.10, 0.20, 0.30]                        # skenario pemindahan beban peak
MAX_SHIFT = 0.40                                       # batas atas yang dianggap bisa dipindah (asumsi)
N_DEST_HOURS = 7                                       # jumlah jam tujuan pemindahan beban
SEED = 20261025


def result(name):
    for d in (RES_PREP, RES_ANALYSIS, RES_PRESENT):
        p = d / name
        if p.exists():
            return p
    raise FileNotFoundError(name)


def chdir_root():
    os.chdir(ROOT)
