import streamlit as st
import pandas as pd
import plotly.express as px
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
import io

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Factory Optimization", layout="wide")

# ---------------- LOAD DATA ----------------
@st.cache_data
def load_data():
    final_sim = pd.read_csv("final_simulation.csv")
    rec = pd.read_csv("recommendations.csv")
    return final_sim, rec

final_sim, rec = load_data()

# ---------------- SIDEBAR ----------------
st.sidebar.title("⚙️ Controls")

region = st.sidebar.selectbox("Region", final_sim["Region"].dropna().unique())
ship_mode = st.sidebar.selectbox("Ship Mode", final_sim["Ship Mode"].dropna().unique())
priority = st.sidebar.slider("Speed vs Profit Priority (%)", 0, 100, 50)

# Apply filters
filtered_sim = final_sim[
    (final_sim["Region"] == region) &
    (final_sim["Ship Mode"] == ship_mode)
]

# ---------------- HEADER ----------------
st.title("🏭 Factory Optimization Dashboard")
st.markdown("---")

# ---------------- KPI CARDS ----------------
avg_improvement = round(filtered_sim["Improvement"].mean(), 2)
avg_profit = round(filtered_sim["Profit_Impact"].mean(), 2)
top_factory = filtered_sim.groupby("Factory")["Profit_Impact"].mean().idxmax()
products = filtered_sim["Product Name"].nunique()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Avg Improvement", avg_improvement)
c2.metric("Avg Profit Impact", avg_profit)
c3.metric("Top Factory", top_factory)
c4.metric("Products", products)

st.markdown("---")

# ---------------- OPTIMIZATION ----------------
st.subheader("🎯 Optimization Simulator")

# ✅ FILTER recommendations also using sidebar filters
filtered_rec = rec[
    (rec["Region"] == region) &
    (rec["Ship Mode"] == ship_mode)
]

# ✅ Product dropdown depends on filtered data
products = filtered_rec["Product Name"].unique()

if len(products) == 0:
    st.warning("No data available for selected filters")
    st.stop()

product = st.selectbox("Select Product", products)

# ✅ Now filter based on selected product
df = filtered_rec[filtered_rec["Product Name"] == product].copy()

# 🧠 SAFE NORMALIZATION
def safe_norm(col):
    if col.max() == 0:
        return col
    return col / col.max()

df["Improvement_norm"] = safe_norm(df["Improvement"])
df["Profit_Impact_norm"] = safe_norm(df["Profit_Impact"])
df["Risk_norm"] = safe_norm(df["Risk"])

# 🧠 DYNAMIC SCORE (balanced properly)
df["Dynamic_Score"] = (
    (priority / 100) * df["Improvement_norm"] +
    ((100 - priority) / 100) * df["Profit_Impact_norm"] -
    (0.3 * df["Risk_norm"])   # reduced risk penalty so variation appears
)

# 🎯 Best factory per product + filters
best = df.sort_values("Dynamic_Score", ascending=False).iloc[0]

# ---------------- RESULT ----------------
st.markdown(f"""
<div style="background:#f1f5f9;padding:15px;border-radius:10px;color:black">
🏆 <b>Recommended Factory:</b> {best['Factory']}<br>
Score: {round(best['Dynamic_Score'],2)}
</div>
""", unsafe_allow_html=True)

# ---------------- INSIGHT ----------------
if best["Improvement"] < 0.05:
    insight = "⚠️ No strong improvement opportunity"
elif best["Risk"] > 0.7:
    insight = "⚠️ High risk involved"
else:
    insight = "🟢 Strong improvement opportunity"

st.success(insight)

# ---------------- EXPLANATION ----------------
st.subheader("💡 Decision Explanation")
st.markdown(f"""
- Improvement: {round(best['Improvement'],2)}
- Profit Impact: {round(best['Profit_Impact'],2)}
- Risk Level: {round(best['Risk'],2)}
- Priority Weight: {priority}%
""")
# ---------------- PDF ----------------
def create_pdf():
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()

    content = []
    content.append(Paragraph("Factory Optimization Report", styles["Title"]))
    content.append(Paragraph(f"Recommended Factory: {best['Factory']}", styles["Normal"]))
    content.append(Paragraph(f"Score: {round(best['Dynamic_Score'],2)}", styles["Normal"]))
    content.append(Paragraph(f"Improvement: {round(best['Improvement'],2)}", styles["Normal"]))
    content.append(Paragraph(f"Profit Impact: {round(best['Profit_Impact'],2)}", styles["Normal"]))
    content.append(Paragraph(f"Risk: {round(best['Risk'],2)}", styles["Normal"]))

    doc.build(content)
    buffer.seek(0)
    return buffer

pdf = create_pdf()

st.download_button(
    label="📄 Download Report",
    data=pdf,
    file_name="factory_report.pdf",
    mime="application/pdf"
)

st.markdown("---")

# ---------------- TOP PRODUCTS ----------------
st.subheader("🏆 Top Performing Products")

top_rec = rec.sort_values("Profit_Impact", ascending=False).head(6)

fig = px.bar(
    top_rec,
    x="Profit_Impact",
    y="Product Name",
    color="Factory",
    orientation="h"
)

st.plotly_chart(fig, use_container_width=True)

# ---------------- FACTORY PERFORMANCE ----------------
st.subheader("📊 Factory Performance")

perf = rec.groupby("Factory")[["Improvement", "Profit_Impact"]].mean().reset_index()

fig1 = px.bar(perf, x="Factory", y="Improvement", color="Factory")
fig2 = px.bar(perf, x="Factory", y="Profit_Impact", color="Factory")

c1, c2 = st.columns(2)
c1.plotly_chart(fig1, use_container_width=True)
c2.plotly_chart(fig2, use_container_width=True)

st.markdown("---")

# ---------------- RISK ----------------
st.subheader("⚠️ Risk Analysis")

risk = rec.groupby("Factory")[["Risk", "Profit_Impact"]].mean().reset_index()

c1, c2 = st.columns(2)

with c1:
    st.markdown("### 🔴 High Risk")
    st.dataframe(risk[risk["Risk"] > 0.7])

with c2:
    st.markdown("### 🟡 Low Profit")
    st.dataframe(risk[risk["Profit_Impact"] < 5])

st.markdown("---")

# ---------------- LINE CHART ----------------
st.subheader("📉 Lead Time vs Improvement")

sim = rec.groupby("Factory")[["Improvement", "Profit_Impact"]].mean().reset_index()
sim["Optimized_Lead_Time"] = sim["Improvement"] * 0.5

lead = sim.melt(id_vars="Factory", value_vars=["Improvement", "Optimized_Lead_Time"])

fig = px.line(
    lead,
    x="Factory",
    y="value",
    color="variable",
    markers=True
)

st.plotly_chart(fig, use_container_width=True)

# ---------------- FINAL INSIGHTS ----------------
st.subheader("🧠 Key Insights")

st.markdown(f"""
<div style="background:#f1f5f9;padding:15px;border-radius:10px;color:black">
• Recommended Factory: {best['Factory']} <br>
• Priority Weight: {priority}% <br>
• Insight: {insight}
</div>
""", unsafe_allow_html=True)
