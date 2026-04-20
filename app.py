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
    return pd.read_csv("final_simulation.csv"), pd.read_csv("recommendations.csv")

final_sim, rec = load_data()

# ---------------- SIDEBAR ----------------
st.sidebar.title("⚙️ Controls")

region = st.sidebar.selectbox("Region", final_sim["Region"].dropna().unique())
ship_mode = st.sidebar.selectbox("Ship Mode", final_sim["Ship Mode"].dropna().unique())
priority = st.sidebar.slider("Speed vs Profit", 0, 100, 50)

# Apply filters ONLY on final_sim
final_sim = final_sim[
    (final_sim["Region"] == region) &
    (final_sim["Ship Mode"] == ship_mode)
]

# ---------------- HEADER ----------------
st.title("🏭 Factory Optimization Dashboard")
st.markdown("---")

# ---------------- KPI CARDS ----------------
avg_improvement = round(rec["Improvement"].mean(), 2)
avg_profit = round(rec["Profit_Impact"].mean(), 2)
top_factory = rec.groupby("Factory")["Score"].mean().idxmax()
products = rec["Product Name"].nunique()

c1, c2, c3, c4 = st.columns(4)

c1.metric("Avg Improvement", avg_improvement)
c2.metric("Avg Profit Impact", avg_profit)
c3.metric("Top Factory", top_factory)
c4.metric("Products", products)

st.markdown("---")

# ---------------- OPTIMIZATION ----------------
st.subheader("🎯 Optimization Simulator")

product = st.selectbox("Select Product", rec["Product Name"].unique())
df = rec[rec["Product Name"] == product].copy()

df["Dynamic_Score"] = (
    (priority/100)*df["Improvement_norm"] +
    ((100-priority)/100)*df["Profit_Impact_norm"] -
    df["Risk_norm"]
)

best = df.sort_values("Dynamic_Score", ascending=False).iloc[0]

# ---------------- DECISION INTELLIGENCE ----------------
st.markdown(f"""
<div style="background:#1f6f4a;padding:15px;border-radius:10px">
🏆 <b>Recommended Factory: {best['Factory']}</b><br>
Score: {round(best['Dynamic_Score'],2)}
</div>
""", unsafe_allow_html=True)

# Decision logic
if best["Improvement"] < 0.05:
    decision = "MAINTAIN"
    insight = "⚠️ No strong improvement opportunity"
elif best["Risk"] > 0.7:
    decision = "CAUTION"
    insight = "⚠️ High risk involved"
else:
    decision = "OPTIMIZE"
    insight = "🟢 Strong improvement opportunity"

st.success(f"{insight}")

# ---------------- EXPLANATION ----------------
st.subheader("💡 Decision Explanation")

st.markdown(f"""
- Improvement: {round(best['Improvement'],2)}
- Profit Impact: {round(best['Profit_Impact'],2)}
- Risk Level: {round(best['Risk'],2)}
- Priority Weight: {priority}%
""")

# ---------------- PDF DOWNLOAD ----------------
def create_pdf():
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()

    content = []

    content.append(Paragraph("Factory Optimization Report", styles["Title"]))
    content.append(Paragraph(f"Recommended Factory: {best['Factory']}", styles["Normal"]))
    content.append(Paragraph(f"Decision: {decision}", styles["Normal"]))
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

top_rec = rec.sort_values("Score", ascending=False).head(6)

fig = px.bar(
    top_rec,
    x="Score",
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

# ---------------- STRATEGY ----------------
st.subheader("📈 Strategy Overview")

sim = rec.groupby("Factory")[["Improvement", "Profit_Impact", "Score"]].mean().reset_index()
sim["Optimized_Lead_Time"] = sim["Improvement"] * 0.5

st.dataframe(sim)

# ---------------- LINE CHART ----------------
st.subheader("📉 Lead Time vs Improvement")

lead = sim.melt(id_vars="Factory", value_vars=["Improvement", "Optimized_Lead_Time"])

fig = px.line(
    lead,
    x="Factory",
    y="value",
    color="variable",
    markers=True
)

st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ---------------- FINAL INSIGHTS ----------------
st.subheader("🧠 Key Insights")

st.markdown(f"""
<div style="background:#1f6f4a;padding:15px;border-radius:10px">
• Decision Type: {decision} <br>
• Recommended Factory: {best['Factory']} <br>
• Priority Weight: {priority}% <br>
• Insight: {insight}
</div>
""", unsafe_allow_html=True)