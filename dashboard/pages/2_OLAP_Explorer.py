"""
Page 2: OLAP Explorer & Multidimensional Data Cube Analysis.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from dashboard.utils import load_fact_data

st.title("🧊 OLAP Data Cube Explorer")
st.markdown("""
Perform online analytical operations (**Roll-Up, Drill-Down, Slice, Dice, and Pivot**) over the multidimensional Star Schema.
""")

df = load_fact_data()

tabs = st.tabs(["Roll-Up", "Drill-Down", "Slice", "Dice", "Pivot Table / Cube"])

# -------------------------------------------------------------
# TAB 1: ROLL-UP
# -------------------------------------------------------------
with tabs[0]:
    st.subheader("Climbing Up the Hierarchy: Roll-Up")
    st.info("Aggregates granular readings upward: Day/Month ➡️ Quarter ➡️ Year.")
    rollup_group = st.selectbox("Roll-up Level", ["Year", "Quarter", "Month"], index=1)

    if rollup_group == "Year":
        grp_cols = ["year_number"]
    elif rollup_group == "Quarter":
        grp_cols = ["year_number", "quarter_name"]
    else:
        grp_cols = ["year_number", "quarter_name", "month_name"]

    res_rollup = df.groupby(grp_cols).agg(
        Total_Energy_kWh=("energy_kwh", "sum"),
        Average_Hourly_kWh=("energy_kwh", "mean"),
        Peak_Demand_kW=("peak_demand_kw", "max"),
        Record_Count=("fact_id", "count")
    ).reset_index().round(2)

    st.dataframe(res_rollup, use_container_width=True)

    fig = px.bar(res_rollup, x=grp_cols[-1], y="Total_Energy_kWh",
                 color=grp_cols[0], barmode="group",
                 title=f"Roll-Up Aggregation by {rollup_group}")
    st.plotly_chart(fig, use_container_width=True)

# -------------------------------------------------------------
# TAB 2: DRILL-DOWN
# -------------------------------------------------------------
with tabs[1]:
    st.subheader("Stepping Down the Hierarchy: Drill-Down")
    st.info("Navigates from high-level yearly summaries down into detailed city and consumer distributions.")
    selected_year = st.selectbox("Select Year to Drill Into", sorted(df["year_number"].unique()), index=0)

    drill_df = df[df["year_number"] == selected_year]
    drill_summary = drill_df.groupby(["city", "consumer_type"]).agg(
        Total_Energy_kWh=("energy_kwh", "sum"),
        Avg_Voltage_V=("voltage_v", "mean"),
        Total_Carbon_kg=("carbon_emissions_kg", "sum")
    ).reset_index().round(2)

    st.dataframe(drill_summary, use_container_width=True)

    fig_drill = px.sunburst(drill_summary, path=["city", "consumer_type"], values="Total_Energy_kWh",
                            title=f"Drill-Down Breakdown for Year {selected_year}",
                            color="Total_Energy_kWh", color_continuous_scale="Blues")
    st.plotly_chart(fig_drill, use_container_width=True)

# -------------------------------------------------------------
# TAB 3: SLICE
# -------------------------------------------------------------
with tabs[2]:
    st.subheader("Fixing One Dimension: Slice")
    st.info("Cuts a 2D slice through the cube by fixing exactly ONE dimension.")
    slice_dim = st.radio("Slice by Dimension:", ["Consumer Type", "City", "Season"], horizontal=True)

    if slice_dim == "Consumer Type":
        val = st.selectbox("Select Consumer Type", sorted(df["consumer_type"].unique()))
        slice_res = df[df["consumer_type"] == val].groupby(["season", "period_of_day"]).agg(
            Total_Energy_kWh=("energy_kwh", "sum"),
            Avg_Energy_kWh=("energy_kwh", "mean")
        ).reset_index().round(2)
    elif slice_dim == "City":
        val = st.selectbox("Select City", sorted(df["city"].unique()))
        slice_res = df[df["city"] == val].groupby(["consumer_type", "season"]).agg(
            Total_Energy_kWh=("energy_kwh", "sum"),
            Avg_Energy_kWh=("energy_kwh", "mean")
        ).reset_index().round(2)
    else:
        val = st.selectbox("Select Season", sorted(df["season"].unique()))
        slice_res = df[df["season"] == val].groupby(["city", "period_of_day"]).agg(
            Total_Energy_kWh=("energy_kwh", "sum"),
            Avg_Energy_kWh=("energy_kwh", "mean")
        ).reset_index().round(2)

    st.dataframe(slice_res, use_container_width=True)

# -------------------------------------------------------------
# TAB 4: DICE
# -------------------------------------------------------------
with tabs[3]:
    st.subheader("Multi-Dimensional Filtering: Dice")
    st.info("Extracts a sub-cube by constraining multiple dimensions simultaneously.")

    c1, c2, c3 = st.columns(3)
    with c1:
        dice_cities = st.multiselect("Select Cities", sorted(df["city"].unique()), default=["Noida", "Delhi"])
    with c2:
        dice_types = st.multiselect("Select Consumer Types", sorted(df["consumer_type"].unique()), default=["Residential"])
    with c3:
        dice_seasons = st.multiselect("Select Seasons", sorted(df["season"].unique()), default=["Summer"])

    dice_data = df[
        (df["city"].isin(dice_cities)) &
        (df["consumer_type"].isin(dice_types)) &
        (df["season"].isin(dice_seasons))
    ]

    st.write(f"**Sub-Cube Records Found:** {len(dice_data):,}")
    if len(dice_data) > 0:
        dice_summary = dice_data.groupby(["city", "consumer_type", "season", "period_of_day"]).agg(
            Total_kWh=("energy_kwh", "sum"),
            Avg_kWh=("energy_kwh", "mean")
        ).reset_index().round(2)
        st.dataframe(dice_summary, use_container_width=True)

# -------------------------------------------------------------
# TAB 5: PIVOT / CUBE VIEW
# -------------------------------------------------------------
with tabs[4]:
    st.subheader("Cross-Tabulation Matrix (City vs Consumer Sector)")
    pivot_df = pd.pivot_table(
        df,
        values="energy_kwh",
        index="city",
        columns="consumer_type",
        aggfunc="sum",
        margins=True,
        margins_name="Total_Grid"
    ).round(2)
    st.dataframe(pivot_df, use_container_width=True)

    fig_heat = px.imshow(pivot_df.drop(index="Total_Grid", columns="Total_Grid", errors="ignore"),
                         labels=dict(x="Consumer Sector", y="City", color="Total kWh"),
                         color_continuous_scale="Viridis", text_auto=".1f",
                         title="Energy Matrix Heatmap")
    st.plotly_chart(fig_heat, use_container_width=True)

