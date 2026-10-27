"""Dashboard Streamlit: ringkasan, profil beban, biaya dan tarif (bisa diubah), skenario pemindahan beban.
Hanya membaca CSV di results/ (streamlit run app.py)."""
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

RES = Path(__file__).resolve().parents[3] / "results"
P, A_ = RES / "3-presentation", RES / "2-analysis"
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
st.set_page_config(page_title="Energy Consumption Dashboard", layout="wide")


@st.cache_data
def load():
    r = lambda n, **k: pd.read_csv(P / n, **k)
    return (r("dash_heatmap.csv"), r("dash_hour.csv"), r("dash_daily.csv", parse_dates=["date"]), r("dash_monthly.csv"), r("dash_scenarios.csv"),
            r("dash_pf.csv"), r("dash_loadtype.csv"), pd.read_csv(A_ / "kpi_year.csv").iloc[0], pd.read_csv(A_ / "hypotheses.csv"))


hm, hour, daily, mon, sc, pf, lt, kpi, hyp = load()
page = st.sidebar.radio("Halaman", ["Ringkasan", "Profil beban", "Biaya dan tarif", "Skenario hemat"])
st.title("Project 6: Energy Consumption Dashboard")
st.caption("Data UCI Steel Industry Energy Consumption (DAEWOO Steel), 2018, interval 15 menit. Tarif adalah asumsi, bukan tagihan nyata.")

if page == "Ringkasan":
    c = st.columns(4)
    c[0].metric("Energi setahun (MWh)", f"{kpi.total_kwh / 1000:,.0f}")
    c[1].metric("Beban puncak (kW)", f"{kpi.peak_kw:,.0f}")
    c[2].metric("Load factor", f"{kpi.load_factor:.2f}")
    c[3].metric("Porsi biaya jam peak", f"{kpi.peak_cost_share:.0%}")
    st.subheader("Hipotesis")
    st.dataframe(hyp.rename(columns={"hipotesis": "hipotesis", "bukti": "bukti"}), hide_index=True)
    fig = px.line(daily, x="date", y=["total_kwh", "ma7_kwh"], labels={"value": "kWh per hari", "date": ""})
    fig.update_layout(height=320, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", title=None))
    st.plotly_chart(fig, width="stretch")

elif page == "Profil beban":
    h = hm.pivot(index="day_of_week", columns="hour", values="kwh_per_jam").reindex(DAYS)
    fig = px.imshow(h, aspect="auto", color_continuous_scale="Blues", labels=dict(x="jam", y="", color="kWh/jam"))
    fig.update_layout(height=360, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, width="stretch")
    st.caption("Rata-rata kWh per jam. Jam = jam mulai interval.")
    q = hour.groupby("hour", as_index=False).avg_kwh_per_hour.mean()
    st.bar_chart(q, x="hour", y="avg_kwh_per_hour")
    st.subheader("Power factor rendah (lag PF < 85) per jam")
    st.line_chart(pf, x="hour", y="porsi_rendah")

elif page == "Biaya dan tarif":
    c = st.columns(2)
    rp = c[0].number_input("Tarif jam peak 17-22 (Rp/kWh)", 500, 5000, 1650, 50)
    ro = c[1].number_input("Tarif off-peak (Rp/kWh)", 500, 5000, 1100, 50)
    m = mon.assign(biaya=lambda x: x.peak_kwh * rp + (x.total_kwh - x.peak_kwh) * ro)
    st.metric("Biaya setahun (estimated, juta Rp)", f"{m.biaya.sum() / 1e6:,.0f}")
    st.bar_chart(m, x="month", y="biaya")
    st.caption("Biaya dihitung ulang dari kWh bulanan per blok tarif; angka di Report memakai tarif asumsi 1.650 dan 1.100.")

else:
    pct = st.select_slider("Porsi kWh jam peak yang dipindah", [0.1, 0.2, 0.3, 0.4], value=0.1, format_func=lambda v: f"{v:.0%}")
    rp = st.number_input("Tarif peak", 500, 5000, 1650, 50)
    ro = st.number_input("Tarif off-peak", 500, 5000, 1100, 50)
    r = sc[(sc.pct - pct).abs() < 1e-9].iloc[0]
    sav = r.kwh_dipindah_setahun * (rp - ro)
    c = st.columns(3)
    c[0].metric("kWh dipindah per bulan", f"{r.kwh_dipindah_per_bulan:,.0f}")
    c[1].metric("Penghematan per bulan (estimated, Rp)", f"{sav / 12:,.0f}")
    c[2].metric("Hari jam tujuan melampaui puncak lama", f"{int(r.hari_puncak_baru)}")
    st.info("Batas atas: asumsi semua beban peak bisa digeser dan jam tujuan tersedia. Puncak tahunan (kW) tidak berubah karena terjadi di luar blok peak.")
