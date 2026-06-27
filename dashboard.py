"""AeroGrid Turbine Telemetry — interactive dashboard.

A Streamlit UI built on top of the SAME anomaly-detection logic as main.py
(`compute_metrics` is imported, not re-implemented). Anyone can see at a glance
which turbines are healthy, drill into a single turbine's readings over time,
and experiment with the safety thresholds.

Run:
    pip install -r requirements-dashboard.txt
    streamlit run dashboard.py

Future: this reads a fixed CSV today. To go live, swap `load_data()` for a
reader that pulls from the streaming pipeline (see architecture.png) — nothing
else in this file needs to change.
"""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# Reuse the project's real, tested logic — the UI does not duplicate it.
from main import compute_metrics, DATA_FILE, TEMP_LIMIT, VIB_LIMIT

OK_BLUE, DANGER_RED, WARN_ORANGE, OK_GREEN = "#5DADE2", "#E74C3C", "#E67E22", "#2ECC71"

st.set_page_config(page_title="AeroGrid Turbine Dashboard", page_icon="🌀", layout="wide")


@st.cache_data
def load_data(path: str = DATA_FILE) -> pd.DataFrame:
    """Load the telemetry CSV and parse timestamps (cached, so reruns are instant).

    Swap the body of this function to read from a live stream to go real-time.
    """
    df = pd.read_csv(path)
    df["timestamp"] = pd.to_datetime(
        df["timestamp"], format="%m/%d/%Y %H:%M", errors="coerce"
    )
    return df


# ----------------------------------------------------------------- load data
try:
    df = load_data()
except FileNotFoundError:
    st.error(f"Could not find `{DATA_FILE}`. Put it next to dashboard.py and reload.")
    st.stop()

# ----------------------------------------------------------------- sidebar controls
st.sidebar.header("⚙️ Controls")
st.sidebar.caption("Drag the thresholds and watch the fleet status update instantly.")
temp_limit = st.sidebar.slider("Max mean temperature (°C)", 50.0, 100.0, float(TEMP_LIMIT), 0.5)
vib_limit = st.sidebar.slider("Max vibration spike (mm/s)", 5.0, 30.0, float(VIB_LIMIT), 0.5)
st.sidebar.divider()
st.sidebar.caption(f"Defaults are the brief's safety limits: {TEMP_LIMIT:.1f} °C and {VIB_LIMIT:.1f} mm/s.")

# ----------------------------------------------------------------- compute (reuses main.py)
metrics = compute_metrics(df).copy()
metrics["temp_fail"] = metrics["mean_temp"] > temp_limit
metrics["vib_fail"] = metrics["max_vib"] > vib_limit
metrics["failing"] = metrics["temp_fail"] | metrics["vib_fail"]


def status_label(row: pd.Series) -> str:
    if row["temp_fail"] and row["vib_fail"]:
        return "🔴 Temp + Vibration"
    if row["temp_fail"]:
        return "🔴 Overheating"
    if row["vib_fail"]:
        return "🟠 Vibration spike"
    return "✅ Healthy"


metrics["status"] = metrics.apply(status_label, axis=1)
n_total = len(metrics)
n_failing = int(metrics["failing"].sum())

# ----------------------------------------------------------------- header + KPIs
st.title(" AeroGrid Turbine Telemetry Dashboard")
st.markdown(
    "Health view of an offshore wind-turbine fleet. A turbine is flagged when its "
    f"**mean temperature exceeds {temp_limit:.1f} °C** *or* its **peak vibration exceeds "
    f"{vib_limit:.1f} mm/s**."
)

k1, k2, k3, k4 = st.columns(4)
k1.metric("Turbines", n_total)
k2.metric("✅ Healthy", n_total - n_failing)
k3.metric("⚠️ Need attention", n_failing)
k4.metric("Total readings", f"{len(df):,}")
st.divider()

# ----------------------------------------------------------------- fleet table + danger-zone scatter
left, right = st.columns([1.1, 1])

with left:
    st.subheader("Fleet status")
    table = metrics.reset_index()[["turbine_id", "status", "mean_temp", "max_vib"]].copy()
    table["mean_temp"] = table["mean_temp"].round(1)
    table["max_vib"] = table["max_vib"].round(1)
    table.columns = ["Turbine", "Status", "Mean temp (°C)", "Max vib (mm/s)"]
    st.dataframe(table, width="stretch", hide_index=True)
    if n_failing:
        st.warning("**Need urgent maintenance:** " + ", ".join(metrics[metrics["failing"]].index))
    else:
        st.success("All turbines within safe limits. 🎉")

with right:
    st.subheader("Danger zone")
    m = metrics.reset_index()
    fig = go.Figure(go.Scatter(
        x=m["mean_temp"], y=m["max_vib"], mode="markers+text",
        text=m["turbine_id"], textposition="top center",
        marker=dict(size=14, color=[DANGER_RED if f else OK_GREEN for f in m["failing"]]),
    ))
    fig.add_vline(x=temp_limit, line_dash="dash", line_color=DANGER_RED)
    fig.add_hline(y=vib_limit, line_dash="dash", line_color=DANGER_RED)
    fig.update_layout(
        height=380, margin=dict(l=10, r=10, t=10, b=10),
        xaxis_title="Mean temperature (°C)", yaxis_title="Max vibration (mm/s)",
    )
    st.plotly_chart(fig, width="stretch")
    st.caption("Top-right of the dashed lines = breaching a rule.")

st.divider()

# ----------------------------------------------------------------- per-turbine bars
st.subheader("Per-turbine metrics")
b1, b2 = st.columns(2)
m = metrics.reset_index()
with b1:
    fig = go.Figure(go.Bar(
        x=m["turbine_id"], y=m["mean_temp"],
        marker_color=[DANGER_RED if f else OK_BLUE for f in m["temp_fail"]],
    ))
    fig.add_hline(y=temp_limit, line_dash="dash", line_color=DANGER_RED,
                  annotation_text=f"{temp_limit:.0f} °C limit")
    fig.update_layout(height=320, margin=dict(l=10, r=10, t=30, b=10),
                      yaxis_title="Mean temperature (°C)")
    st.plotly_chart(fig, width="stretch")
with b2:
    fig = go.Figure(go.Bar(
        x=m["turbine_id"], y=m["max_vib"],
        marker_color=[WARN_ORANGE if f else OK_BLUE for f in m["vib_fail"]],
    ))
    fig.add_hline(y=vib_limit, line_dash="dash", line_color=WARN_ORANGE,
                  annotation_text=f"{vib_limit:.0f} mm/s limit")
    fig.update_layout(height=320, margin=dict(l=10, r=10, t=30, b=10),
                      yaxis_title="Max vibration (mm/s)")
    st.plotly_chart(fig, width="stretch")

st.divider()

# ----------------------------------------------------------------- single-turbine drill-down
st.subheader("🔍 Inspect a single turbine over time")
turbine = st.selectbox("Choose a turbine", sorted(df["turbine_id"].unique()))
tdf = df[df["turbine_id"] == turbine].sort_values("timestamp")

d1, d2, d3 = st.columns(3)
d1.metric("Mean temp (°C)", f"{tdf['temperature_c'].mean():.1f}")
d2.metric("Peak vibration (mm/s)", f"{tdf['vibration_mm_s'].max():.1f}")
d3.metric("Readings", f"{len(tdf):,}")

fig = go.Figure()
fig.add_trace(go.Scatter(x=tdf["timestamp"], y=tdf["temperature_c"],
                         name="Temperature (°C)", line=dict(color=DANGER_RED)))
fig.add_trace(go.Scatter(x=tdf["timestamp"], y=tdf["vibration_mm_s"],
                         name="Vibration (mm/s)", line=dict(color=WARN_ORANGE), yaxis="y2"))
fig.update_layout(
    height=380, margin=dict(l=10, r=10, t=30, b=10),
    yaxis=dict(title="Temperature (°C)"),
    yaxis2=dict(title="Vibration (mm/s)", overlaying="y", side="right"),
    legend=dict(orientation="h", y=1.15),
)
st.plotly_chart(fig, width="stretch")

# ----------------------------------------------------------------- fleet insights
st.divider()
st.subheader("📈 Fleet insights")
hottest = metrics["mean_temp"].idxmax()
shakiest = metrics["max_vib"].idxmax()
span = df["timestamp"].max() - df["timestamp"].min()
i1, i2, i3 = st.columns(3)
i1.info(f"**Hottest turbine:** {hottest} — {metrics.loc[hottest, 'mean_temp']:.1f} °C avg")
i2.info(f"**Shakiest turbine:** {shakiest} — peak {metrics.loc[shakiest, 'max_vib']:.1f} mm/s")
i3.info(f"**Data window:** {span} · {len(df):,} readings")

st.caption(
    "ℹ️ This dashboard reads a fixed CSV today. The architecture (architecture.png) is "
    "designed to feed it from a live stream — swap `load_data()` to go real-time."
)
