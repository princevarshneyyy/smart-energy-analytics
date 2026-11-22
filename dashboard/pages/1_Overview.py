"""
Page 1: Overview & Grid Performance KPIs.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from dashboard.utils import load_fact_data, render_kpi_card

st.title("📊 Energy Consumption Overview & Grid Trends")

df = load_fact_data()

# -------------------------------------------------------------
# SIDEBAR FILTERS
# -------------------------------------------------------------
st.sidebar.header("Global Filters")
cities = ["All"] + sorted(df["city"].unique().tolist())
selected_city = st.sidebar.selectbox("Filter by City", cities)

consumer_types = ["All"] + sorted(df["consumer_type"].unique().tolist())
selected_type = st.sidebar.selectbox("Filter by Consumer Type", consumer_types)

# Apply filters
filtered_df = df.copy()
if selected_city != "All":
    filtered_df = filtered_df[filtered_df["city"] == selected_city]
if selected_type != "All":
    filtered_df = filtered_df[filtered_df["consumer_type"] == selected_type]

# -------------------------------------------------------------
# KPI METRICS ROW
# -------------------------------------------------------------
total_consumption = filtered_df["energy_kwh"].sum()
avg_hourly = filtered_df["energy_kwh"].mean()
peak_kw = filtered_df["peak_demand_kw"].max()
carbon_total = filtered_df["carbon_emissions_kg"].sum()

col1, col2, col3, col4 = st.columns(4)
with col1:
    render_kpi_card("Total Consumption", f"{total_consumption:,.1f} kWh", "Cumulative energy registered")
with col2:
    render_kpi_card("Average Hourly Load", f"{avg_hourly:.2f} kWh", "Mean active power per hour")
with col3:
    render_kpi_card("Peak Demand Recorded", f"{peak_kw:.1f} kW", "Maximum instantaneous load")
with col4:
    render_kpi_card("Total Carbon Footprint", f"{carbon_total / 1000:,.2f} Tons", "Estimated CO2 emissions (@0.82 kg/kWh)")

st.divider()

# -------------------------------------------------------------
# TIME SERIES TRENDS (Daily / Monthly)
# -------------------------------------------------------------
st.subheader("📈 Temporal Consumption Trends")
trend_granularity = st.radio("Trend Aggregation", ["Daily", "Monthly"], horizontal=True)

if trend_granularity == "Daily":
    trend_df = filtered_df.groupby("full_date")["energy_kwh"].sum().reset_index()
    fig = px.line(trend_df, x="full_date", y="energy_kwh",
                  title="Daily Total Energy Consumption (kWh)",
                  labels={"full_date": "Date", "energy_kwh": "Total kWh"},
                  color_discrete_sequence=["#1f77b4"])
else:
    trend_df = filtered_df.groupby(["year_number", "month_name", "month_number"])["energy_kwh"].sum().reset_index()
    trend_df = trend_df.sort_values(by=["year_number", "month_number"])
    trend_df["period"] = trend_df["month_name"] + " " + trend_df["year_number"].astype(str)
    fig = px.bar(trend_df, x="period", y="energy_kwh",
                 title="Monthly Energy Consumption (kWh)",
                 labels={"period": "Month", "energy_kwh": "Total kWh"},
                 color="energy_kwh", color_continuous_scale="Blues")

fig.update_layout(template="plotly_white", hovermode="x unified")
st.plotly_chart(fig, use_container_width=True)

# -------------------------------------------------------------
# BREAKDOWNS: City and Consumer Type
# -------------------------------------------------------------
col_a, col_b = st.columns(2)

with col_a:
    st.subheader("🏙️ Consumption by City")
    city_df = filtered_df.groupby("city")["energy_kwh"].sum().reset_index()
    fig_city = px.pie(city_df, values="energy_kwh", names="city",
                      title="Energy Distribution Across Cities",
                      hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
    st.plotly_chart(fig_city, use_container_width=True)

with col_b:
    st.subheader("🏭 Consumption by Consumer Sector")
    sector_df = filtered_df.groupby("consumer_type")["energy_kwh"].sum().reset_index()
    fig_sector = px.bar(sector_df, x="consumer_type", y="energy_kwh",
                        color="consumer_type",
                        title="Sectoral Load Distribution",
                        labels={"consumer_type": "Sector", "energy_kwh": "Total kWh"})
    fig_sector.update_layout(template="plotly_white")
    st.plotly_chart(fig_sector, use_container_width=True)

