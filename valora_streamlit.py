import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# --- APP TITLE ---
st.set_page_config(page_title="Valora AI Real Estate Advisor", layout="wide")
st.title("🏡 Valora: AI Real Estate Investment Advisor")

# --- SIDEBAR INPUTS ---
st.sidebar.header("Property Inputs")
address = st.sidebar.text_input("Property Address", "879 Reflection Cove Rd E, Jacksonville, FL")
asking_price = st.sidebar.number_input("Asking Price ($)", min_value=50000, max_value=5000000, value=300000, step=5000)
beds = st.sidebar.number_input("Beds", min_value=0, max_value=20, value=3)
baths = st.sidebar.number_input("Baths", min_value=0, max_value=20, value=2)
sqft = st.sidebar.number_input("Square Feet", min_value=100, max_value=20000, value=1800)
condition = st.sidebar.selectbox("Condition", ["Poor", "Fair", "Good", "Excellent"])
occupancy = st.sidebar.selectbox("Occupancy", ["Vacant", "Tenant Occupied", "Owner Occupied"])
seller_motivation = st.sidebar.text_input("Seller Motivation (if known)")

repair = st.sidebar.number_input("Estimated Repair Cost ($)", min_value=0, max_value=500000, value=20000, step=1000)
years = st.sidebar.slider("Holding Period (Years)", 1, 10, 5)
strategy = st.sidebar.selectbox("Investment Strategy", ["Buy & Hold", "Fix & Flip", "Rental"])

# --- DATA CALCULATIONS ---
# Appreciation assumptions
appreciation_rate = 0.035  # 3.5% yearly
future_value = asking_price * (1 + appreciation_rate) ** years

# ROI calculations
if strategy == "Fix & Flip":
    roi = (future_value - (asking_price + repair)) / (asking_price + repair)
elif strategy == "Rental":
    rent = asking_price * 0.008  # approx 0.8% monthly rent
    expenses = asking_price * 0.01  # yearly expenses 1%
    cash_flow = (rent*12 - expenses) * years
    roi = (future_value + cash_flow - (asking_price + repair)) / (asking_price + repair)
else:  # Buy & Hold
    roi = (future_value - asking_price) / asking_price

# --- DASHBOARD METRICS ---
st.subheader(f"📍 {address}")
col1, col2, col3 = st.columns(3)

col1.metric("Predicted Value ($)", f"{future_value:,.0f}")
col2.metric("ROI (%)", f"{roi*100:.2f}%")
if strategy == "Rental":
    col3.metric("Cash Flow ($)", f"{cash_flow:,.0f}")
else:
    col3.metric("Repair Cost ($)", f"{repair:,.0f}")

# --- PROPERTY DETAILS ---
st.subheader("🏠 Property Details")
st.write(f"- Beds/Baths/SqFt: {beds}/{baths}/{sqft}")
st.write(f"- Condition: {condition}")
st.write(f"- Occupancy: {occupancy}")
st.write(f"- Seller Motivation: {seller_motivation}")

# --- GRAPHS ---
st.subheader("📈 Property Value Over Time")
years_list = list(range(1, years+1))
value_list = [asking_price * (1 + appreciation_rate) ** y for y in years_list]
fig1 = px.line(x=years_list, y=value_list, labels={'x':'Year', 'y':'Value ($)'}, title="Projected Property Value")
st.plotly_chart(fig1, use_container_width=True)

if strategy == "Fix & Flip":
    roi_compare = pd.DataFrame({
        "Strategy": ["Fix & Flip", "Buy & Hold", "Rental"],
        "ROI": [
            (future_value - (asking_price + repair)) / (asking_price + repair),
            (future_value - asking_price)/asking_price,
            ((future_value + (asking_price*0.008*12*years) - (asking_price + repair)) / (asking_price + repair))
        ]
    })
    st.subheader("📊 ROI Comparison by Strategy")
    fig2 = px.bar(roi_compare, x="Strategy", y="ROI", text="ROI", labels={"ROI":"ROI (%)"})
    fig2.update_traces(texttemplate='%{text:.2%}', textposition='outside')
    st.plotly_chart(fig2, use_container_width=True)

# --- DEAL INSIGHTS ---
st.subheader("💡 Deal Insights & Strategy Tips")
if strategy == "Fix & Flip":
    st.write(f"- Consider negotiating repair costs to improve ROI.\n- Target resale in {years} years to maximize appreciation.\n- Comparable properties should guide offer price.")
elif strategy == "Rental":
    st.write(f"- Monthly rent estimated at ${rent:,.0f}.\n- ROI includes cash flow over {years} years.\n- Keep property well-maintained to reduce vacancies.")
else:
    st.write(f"- Buy & Hold strategy relies mainly on property appreciation.\n- Consider long-term market trends.\n- Minimal repairs assumed.")

st.write("---")
st.caption("Valora Demo: Powered by AI Insights for Real Estate Investment")
