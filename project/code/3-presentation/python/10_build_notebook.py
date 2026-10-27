"""Membuat dan menjalankan results/3-presentation/analysis.ipynb (Q1-Q14). Notebook hanya membaca CSV hasil."""
import sys
from pathlib import Path

import nbformat as nbf
from nbclient import NotebookClient

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import common as C  # noqa: E402

nb = nbf.v4.new_notebook()
M = lambda t: nb.cells.append(nbf.v4.new_markdown_cell(t))
K = lambda t: nb.cells.append(nbf.v4.new_code_cell(t.strip()))
M("# Project 6: Energy Consumption Dashboard\nNotebook membaca CSV hasil (`results/`), tidak menghitung ulang. Urutan mengikuti 14 pertanyaan pada Design Project. Tarif Rp1.650/Rp1.100 per kWh adalah asumsi.")
K("""
import pandas as pd, matplotlib.pyplot as plt
pd.set_option("display.width", 170); pd.set_option("display.max_columns", 30)
R1, R2 = "../1-data-preparation/", "../2-analysis/"
rd = lambda p: pd.read_csv(p)
""")
S = [("Q1-Q2. Profil beban per jam, hari kerja vs akhir pekan", """
h = rd(R2+"hour_profile.csv").pivot(index="hour", columns="week_status", values="avg_kwh_per_hour"); h.plot(figsize=(8,3.5)); plt.ylabel("kWh per jam"); plt.show()
print(rd(R2+"weekday_weekend.csv").round(2).to_string(index=False))"""),
("Q3. Tren bulanan", "print(rd(R2+'monthly.csv').round(0).to_string(index=False))"),
("Q4. Load_Type per jam", "print(rd(R2+'loadtype_summary.csv').round(3).to_string(index=False)); print(rd(R2+'maximum_by_hour.csv').round(3).to_string(index=False))"),
("Q5. Kejadian beban tinggi (di atas P90)", "print(rd(R2+'high_load_summary.csv').T.to_string(header=False)); print(rd(R2+'high_load_events.csv').head(10).to_string(index=False))"),
("Q6-Q7. Biaya per bulan dan per hari dalam seminggu", "print(rd(R2+'dow_cost.csv').round(0).to_string(index=False)); print(rd(R2+'kpi_year.csv').T.to_string(header=False))"),
("Q8-Q9. Power factor rendah", "print(rd(R2+'pf_by_load.csv').round(3).to_string(index=False)); print(rd(R2+'pf_hour.csv').round(3).T.to_string(header=False))"),
("Q10-Q12. Skenario pemindahan beban (estimated)", "print(rd(R2+'dest_hours.csv').round(1).to_string(index=False)); print(rd(R2+'scenarios.csv').round(1).T.to_string(header=False))"),
("Q13. Sensitivitas label waktu dan uji tarif", "print(rd(R2+'sensitivity_label.csv').round(1).to_string(index=False)); print(rd(R2+'tariff_test.csv').round(0).to_string(index=False)); print(rd(R1+'data_quality.csv').to_string(index=False))"),
("Q14. Validasi: constraint, konsistensi, SQL vs pandas", "print(rd(R1+'constraint_tests.csv').to_string(index=False)); print(rd(R1+'consistency_checks.csv').to_string(index=False)); c=rd(R2+'crosscheck_pandas.csv'); print(c.status.value_counts().to_string())"),
("Hipotesis", "print(rd(R2+'hypotheses.csv').to_string(index=False))")]
for t, c in S:
    M("## " + t); K(c)
nb.metadata["kernelspec"] = {"display_name": "Python 3", "language": "python", "name": "python3"}
NotebookClient(nb, timeout=300, kernel_name="python3", resources={"metadata": {"path": str(C.RES_PRESENT)}}).execute()
errs = [o for c in nb.cells if c.cell_type == "code" for o in c.outputs if o.output_type == "error"]
assert not errs, errs
nbf.write(nb, C.RES_PRESENT / "analysis.ipynb")
print("notebook:", len(nb.cells), "sel, 0 error")
