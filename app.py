import streamlit as st
import pandas as pd

st.set_page_config(page_title="Factory Optimization", layout="wide")

# ---------------- LOAD DATA ----------------
@st.cache_data
def load_data():
    sim = pd.read_csv("final_simulation.csv")
    rec = pd.read_csv("recommendations.csv")

    sim.columns = sim.columns.str.strip()
    rec.columns = rec.columns.str.strip()

    return sim, rec

sim_df, rec_df = load_data()

# ---------------- SIDEBAR ----------------
st.sidebar.header("⚙️ Controls")

region = st.sidebar.selectbox(
    "Region",
    sorted(sim_df["Region"].dropna().unique())
)

ship_mode = st.sidebar.selectbox(
    "Ship Mode",
    sorted(sim_df["Ship Mode"].dropna().unique())
)

priority = st.sidebar.slider(
    "Speed vs Profit Priority (%)",
    0, 100, 50
)

# ---------------- FILTER ----------------
filtered_sim = sim_df[
    (sim_df["Region"] == region) &
    (sim_df["Ship Mode"] == ship_mode)
]

products = sorted(filtered_sim["Product Name"].dropna().unique())

st.title("🏭 Factory Optimization Dashboard")

# ---------------- KPIs ----------------
col1, col2, col3, col4 = st.columns(4)

if len(filtered_sim) > 0:
    col1.metric("Avg Improvement", round(filtered_sim["Improvement"].mean(), 2))
    col2.metric("Avg Profit Impact", round(filtered_sim["Profit_Impact"].mean(), 2))
    col3.metric("Top Factory", filtered_sim["Factory"].mode()[0])
    col4.metric("Products", len(products))
else:
    col1.metric("Avg Improvement", 0)
    col2.metric("Avg Profit Impact", 0)
    col3.metric("Top Factory", "N/A")
    col4.metric("Products", 0)

# ---------------- SIMULATOR ----------------
st.subheader("🎯 Factory Optimization Simulator")

if len(products) == 0:
    st.warning("No data available")
    st.stop()

product = st.selectbox("Select Product", products)

rec_filtered = rec_df[rec_df["Product Name"] == product].copy()

if len(rec_filtered) == 0:
    st.warning("No recommendation data")
    st.stop()

# ---------------- SCORING ----------------
rec_filtered["Final_Score"] = (
    (priority / 100) * rec_filtered["Improvement_norm"] +
    ((100 - priority) / 100) * rec_filtered["Profit_Impact_norm"] -
    (0.3 * rec_filtered["Risk_norm"])
)

rec_filtered = rec_filtered.sort_values("Final_Score", ascending=False)

best = rec_filtered.iloc[0]

# ---------------- RESULT ----------------
st.success(f"🏆 Recommended Factory: {best['Factory']} (Score: {round(best['Final_Score'],3)})")

# ---------------- WHAT-IF SCENARIO ----------------
st.subheader("🔄 What-if Scenario Analysis")

colA, colB = st.columns(2)

with colA:
    st.markdown("### Current Scenario")
    st.write(f"Lead Time: {round(best['Lead_Time_Reduction_%'],2)}% reduction")
    st.write(f"Profit Impact: {round(best['Profit_Impact'],2)}")

with colB:
    st.markdown("### Alternative Factory")
    alt = rec_filtered.iloc[1] if len(rec_filtered) > 1 else best
    st.write(f"Factory: {alt['Factory']}")
    st.write(f"Lead Time: {round(alt['Lead_Time_Reduction_%'],2)}%")
    st.write(f"Profit Impact: {round(alt['Profit_Impact'],2)}")

# ---------------- RANKING TABLE ----------------
st.subheader("📊 Recommendation Dashboard (Ranked)")

st.dataframe(
    rec_filtered[
        ["Factory", "Improvement", "Profit_Impact", "Risk", "Final_Score", "Rank"]
    ],
    use_container_width=True
)

# ---------------- VISUALIZATION ----------------
st.subheader("📉 Lead Time Improvement View")

chart_data = rec_filtered[["Factory", "Lead_Time_Reduction_%"]].set_index("Factory")
st.bar_chart(chart_data)

# ---------------- RISK PANEL ----------------
st.subheader("⚠️ Risk & Impact Panel")

if best["Risk"] > 1:
    st.error("🚨 High Risk Reassignment")
elif best["Risk"] > 0.7:
    st.warning("⚠️ Moderate Risk")
else:
    st.success("🟢 Low Risk")

if best["Profit_Impact"] < 0:
    st.error("💸 Negative Profit Impact")

# ---------------- EXPLANATION ----------------
st.subheader("💡 Decision Explanation")

st.write(f"Improvement: {round(best['Improvement'],2)}")
st.write(f"Profit Impact: {round(best['Profit_Impact'],2)}")
st.write(f"Risk: {round(best['Risk'],2)}")
st.write(f"Priority Weight: {priority}%")
