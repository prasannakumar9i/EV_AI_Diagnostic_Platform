"""
dashboard/fleet_dashboard.py
EV Fleet Analytics Dashboard with Plotly visualisations.
Run: streamlit run fleet_dashboard.py
"""
import os
import sys

BASE = os.environ.get("EV_BASE", "/content/drive/MyDrive/EV_AI_Platform")

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(
    page_title = "EV Fleet Analytics",
    page_icon  = "EV",
    layout     = "wide",
)

st.markdown("""
<style>
    .kpi-card { background:#F0F6FF; border-radius:8px; padding:16px;
                text-align:center; border:1px solid #1F6FEB33; }
    .kpi-val  { font-size:2rem; font-weight:800; color:#1F6FEB; }
    .kpi-lbl  { font-size:0.85rem; color:#586069; }
    .title    { font-size:1.8rem; font-weight:800; color:#0D1117; }
</style>
""", unsafe_allow_html=True)


# ── Data ──────────────────────────────────────────────────────────────────────
@st.cache_data
def load_fleet_data(n: int = 60, seed: int = 42) -> pd.DataFrame:
    np.random.seed(seed)
    brands = ["Tesla", "Nissan", "Hyundai", "BMW", "Kia", "Volkswagen"]
    return pd.DataFrame({
        "vehicle_id":   [f"EV-{i:03d}" for i in range(n)],
        "brand":        np.random.choice(brands, n),
        "model":        np.random.choice(["Model 3", "Leaf", "IONIQ 5", "i4", "EV6"], n),
        "year":         np.random.randint(2019, 2025, n),
        "soh_pct":      np.random.normal(86, 9, n).clip(45, 100).round(1),
        "soc_pct":      np.random.normal(64, 22, n).clip(5, 100).round(1),
        "cycle_count":  np.random.randint(40, 1600, n),
        "battery_temp": np.random.normal(34, 10, n).clip(8, 78).round(1),
        "motor_temp":   np.random.normal(42, 12, n).clip(15, 110).round(1),
        "fault_count":  np.random.poisson(1.4, n),
        "range_km":     np.random.normal(310, 65, n).clip(80, 520).round(0),
        "energy_kwh":   np.random.normal(72, 12, n).clip(30, 100).round(1),
        "risk":         np.random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"],
                                          n, p=[0.58, 0.26, 0.11, 0.05]),
        "last_service": pd.date_range("2023-01-01", periods=n, freq="5D").strftime("%Y-%m-%d"),
    })


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## Fleet Analytics")
    brand_filter = st.multiselect("Filter by brand",
                                  ["Tesla","Nissan","Hyundai","BMW","Kia","Volkswagen"])
    risk_filter  = st.multiselect("Filter by risk",
                                  ["LOW","MEDIUM","HIGH","CRITICAL"])
    soh_min      = st.slider("Min SOH %", 0, 100, 0)
    st.markdown("---")
    n_vehicles = st.slider("Fleet size (demo)", 20, 100, 60)
    if st.button("Refresh Data"):
        st.cache_data.clear()


# ── Load & filter ─────────────────────────────────────────────────────────────
df = load_fleet_data(n_vehicles)
if brand_filter:
    df = df[df.brand.isin(brand_filter)]
if risk_filter:
    df = df[df.risk.isin(risk_filter)]
df = df[df.soh_pct >= soh_min]

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown('<p class="title">EV Fleet Analytics Dashboard</p>', unsafe_allow_html=True)
st.caption(f"Showing {len(df)} vehicles | Updated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}")
st.markdown("---")

# ── KPI row ───────────────────────────────────────────────────────────────────
k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("Fleet Size",       len(df))
k2.metric("Avg SOH",          f"{df.soh_pct.mean():.1f}%",
          delta=f"{df.soh_pct.mean()-80:.1f}% above threshold")
k3.metric("Avg SOC",          f"{df.soc_pct.mean():.0f}%")
k4.metric("Total Faults",     int(df.fault_count.sum()))
k5.metric("High Risk",        int(df.risk.isin(["HIGH","CRITICAL"]).sum()),
          delta_color="inverse")
k6.metric("Avg Range (km)",   f"{df.range_km.mean():.0f}")

st.markdown("---")

# ── Charts row 1 ─────────────────────────────────────────────────────────────
c1, c2 = st.columns(2)

with c1:
    fig = px.histogram(
        df, x="soh_pct", nbins=20, color="brand",
        title="Battery SOH Distribution by Brand",
        labels={"soh_pct": "State of Health (%)"},
        barmode="overlay",
    )
    fig.add_vline(x=80, line_dash="dash", line_color="red",
                  annotation_text="80% Service Threshold")
    fig.update_layout(height=360)
    st.plotly_chart(fig, use_container_width=True)

with c2:
    rc   = df.risk.value_counts()
    cols = {"LOW":"#2ecc71","MEDIUM":"#f39c12","HIGH":"#e74c3c","CRITICAL":"#8e44ad"}
    fig  = go.Figure(go.Pie(
        labels          = rc.index,
        values          = rc.values,
        hole            = 0.44,
        marker_colors   = [cols.get(r,"#999") for r in rc.index],
        textinfo        = "label+percent",
    ))
    fig.update_layout(title="Fleet Risk Distribution", height=360)
    st.plotly_chart(fig, use_container_width=True)

# ── Charts row 2 ─────────────────────────────────────────────────────────────
c3, c4 = st.columns(2)

with c3:
    fig = px.scatter(
        df, x="cycle_count", y="soh_pct",
        color="risk", size="fault_count",
        hover_name="vehicle_id",
        hover_data={"brand":True,"soc_pct":True,"cycle_count":True},
        title="SOH vs Charge Cycles",
        color_discrete_map={"LOW":"green","MEDIUM":"orange","HIGH":"red","CRITICAL":"purple"},
    )
    fig.add_hline(y=80, line_dash="dot", line_color="red")
    fig.update_layout(height=360)
    st.plotly_chart(fig, use_container_width=True)

with c4:
    fb  = df.groupby("brand")["fault_count"].sum().sort_values(ascending=False).reset_index()
    fig = px.bar(fb, x="brand", y="fault_count", color="brand",
                 title="Total Faults by Brand",
                 labels={"fault_count":"Faults"})
    fig.update_layout(showlegend=False, height=360)
    st.plotly_chart(fig, use_container_width=True)

# ── Temperature charts ────────────────────────────────────────────────────────
st.markdown("### Temperature Analysis")
c5, c6 = st.columns(2)

with c5:
    fig = px.box(df, x="brand", y="battery_temp", color="brand",
                 title="Battery Temperature Distribution by Brand",
                 labels={"battery_temp":"Battery Temp (°C)"})
    fig.add_hline(y=45, line_dash="dash", line_color="orange",
                  annotation_text="Warning threshold")
    fig.update_layout(showlegend=False, height=340)
    st.plotly_chart(fig, use_container_width=True)

with c6:
    fig = px.scatter(df, x="battery_temp", y="soh_pct",
                     color="brand", trendline="ols",
                     title="SOH vs Battery Temperature",
                     labels={"battery_temp":"Avg Battery Temp (°C)", "soh_pct":"SOH (%)"})
    fig.update_layout(height=340)
    st.plotly_chart(fig, use_container_width=True)

# ── Data table ────────────────────────────────────────────────────────────────
st.markdown("### Vehicle Fleet Table")
display_df = df[["vehicle_id","brand","model","year","soh_pct","soc_pct",
                 "cycle_count","fault_count","risk","range_km","last_service"]]
display_df = display_df.sort_values("risk", key=lambda x: x.map(
    {"CRITICAL":0,"HIGH":1,"MEDIUM":2,"LOW":3}))

st.dataframe(
    display_df.style.background_gradient(subset=["soh_pct"], cmap="RdYlGn"),
    use_container_width=True,
    height=400,
)

st.markdown("---")
st.caption("EV AI Diagnostic Platform — Personal Resume Project | "
           "Google Colab + Streamlit + Plotly + ML")
