import streamlit as st
import pandas as pd

st.set_page_config(page_title="Factory Optimization", layout="wide")

# ---------------- LOAD DATA ----------------
@st.cache_data
def load_data():
    sim = pd.read_csv("final_simulation.csv")
    rec = pd.read_csv("recommendations.csv")
    
    # Clean column names
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

# ---------------- FILTER SIM DATA ----------------
filtered_sim = sim_df[
    (sim_df["Region"] == region) &
    (sim_df["Ship Mode"] == ship_mode)
]

# ---------------- GET PRODUCTS ----------------
products = sorted(filtered_sim["Product Name"].dropna().unique())

st.title("🏭 Factory Optimization Dashboard")

# ---------------- METRICS ----------------
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

# ---------------- OPTIMIZER ----------------
st.subheader("🎯 Optimization Simulator")

if len(products) == 0:
    st.warning("No data available for selected filters")
    st.stop()

product = st.selectbox("Select Product", products)

# ---------------- FILTER RECOMMENDATIONS ----------------
rec_filtered = rec_df[rec_df["Product Name"] == product].copy()

if len(rec_filtered) == 0:
    st.warning("No recommendation data available for this product")
    st.stop()

# ---------------- SCORE CALCULATION ----------------
rec_filtered["Final_Score"] = (
    (priority / 100) * rec_filtered["Improvement_norm"] +
    ((100 - priority) / 100) * rec_filtered["Profit_Impact_norm"] -
    (0.3 * rec_filtered["Risk_norm"])
)

best = rec_filtered.sort_values("Final_Score", ascending=False).iloc[0]

# ---------------- OUTPUT ----------------
st.markdown(
    f"""
    <div style="background:#f1f5f9;padding:15px;border-radius:10px">
    🏆 <b>Recommended Factory:</b> {best['Factory']}<br>
    Score: {round(best['Final_Score'], 3)}
    </div>
    """,
    unsafe_allow_html=True
)

# ---------------- RISK ----------------
if best["Risk"] > 1:
    st.error("⚠️ High risk involved")
elif best["Improvement"] < 0.3:
    st.warning("⚠️ Low improvement potential")
else:
    st.success("🟢 Good optimization opportunity")

# ---------------- EXPLANATION ----------------
st.subheader("💡 Decision Explanation")

st.write(f"Improvement: {round(best['Improvement'], 2)}")
st.write(f"Profit Impact: {round(best['Profit_Impact'], 2)}")
st.write(f"Risk: {round(best['Risk'], 2)}")
st.write(f"Priority Weight: {priority}%")
