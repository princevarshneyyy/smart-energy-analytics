"""
Step 5: OLAP Operations (Roll-up, Drill-down, Slice, Dice, Pivot/Cube).

Purpose:
  1. Executes both Pandas-based and SQL-based OLAP operations over the data warehouse.
  2. Implements the 5 core OLAP operations:
     - ROLL-UP: Hierarchical aggregation (Hour -> Day -> Month -> Quarter -> Year).
     - DRILL-DOWN: Detail navigation (Yearly total -> City -> Consumer category).
     - SLICE: 2D rectangular slice fixing 1 dimension (e.g., Commercial Consumers only).
     - DICE: Multi-dimensional sub-cube filter (Residential + Noida/Delhi + Summer + Peak Hours).
     - PIVOT / CUBE: Cross-tabulation matrix of consumption across Cities vs Consumer Sectors.
  3. Prints clear educational explanations alongside each operation's output.
  4. Saves resulting tabular summaries to outputs/tables/ and figures to outputs/figures/.

Inputs:
  - Database Fact & Dimension tables / data/processed/featured_energy_data.csv
Outputs:
  - outputs/tables/olap_rollup.csv, olap_drilldown.csv, olap_slice.csv, olap_dice.csv, olap_pivot_cube.csv
  - outputs/figures/olap_cube_heatmap.png

Course: Data Mining and Warehousing Lab (24B15CS313), JIIT Noida.
"""

import sys
import logging
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sqlalchemy import text

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

import config
from src.db_connection import get_db_engine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("05_OLAP")


def perform_olap_operations():
    """Executes pure-SQL and Pandas OLAP operations with descriptive commentary."""
    engine, dialect = get_db_engine()
    logger.info("Loading joined star schema data for OLAP execution...")

    # Load complete joined view
    query = """
    SELECT 
        f.fact_id, f.energy_kwh, f.voltage_v, f.peak_demand_kw, f.carbon_emissions_kg,
        d.full_date, d.day_of_month, d.month_name, d.month_number, d.quarter_name, d.year_number, d.day_name, d.is_weekend, d.season,
        t.hour_of_day, t.time_label, t.period_of_day, t.is_peak_hour,
        c.consumer_id, c.consumer_name, c.consumer_type, c.tariff_category,
        l.city, l.state, l.region
    FROM Fact_Energy_Consumption f
    JOIN Dim_Date d ON f.date_key = d.date_key
    JOIN Dim_Time t ON f.time_key = t.time_key
    JOIN Dim_Consumer c ON f.consumer_key = c.consumer_key
    JOIN Dim_Location l ON f.location_key = l.location_key;
    """
    with engine.connect() as conn:
        df = pd.read_sql(text(query), conn)

    print("\n" + "=" * 80)
    print("                     ONLINE ANALYTICAL PROCESSING (OLAP) REPORT")
    print("=" * 80)

    # -------------------------------------------------------------
    # 1. ROLL-UP (Aggregation to higher dimensional levels)
    # -------------------------------------------------------------
    print("\n[OPERATION 1: ROLL-UP]")
    print("Explanation: Climbing UP the concept hierarchy from individual readings -> Month -> Quarter -> Year.")
    rollup_df = df.groupby(["year_number", "quarter_name", "month_name"]).agg(
        total_energy_kwh=("energy_kwh", "sum"),
        avg_hourly_kwh=("energy_kwh", "mean"),
        max_peak_demand=("peak_demand_kw", "max"),
        reading_count=("fact_id", "count")
    ).reset_index()
    rollup_df["total_energy_kwh"] = rollup_df["total_energy_kwh"].round(2)
    rollup_df["avg_hourly_kwh"] = rollup_df["avg_hourly_kwh"].round(3)
    print(rollup_df.head(10).to_string(index=False))
    rollup_df.to_csv(config.TABLES_DIR / "olap_rollup.csv", index=False)

    # -------------------------------------------------------------
    # 2. DRILL-DOWN (Navigating from high-level summary to granular details)
    # -------------------------------------------------------------
    print("\n" + "-" * 80)
    print("[OPERATION 2: DRILL-DOWN]")
    print("Explanation: Stepping DOWN the hierarchy into a specific Year (2023) -> City -> Consumer Type.")
    drilldown_df = df[df["year_number"] == 2023].groupby(["year_number", "city", "consumer_type"]).agg(
        total_energy_kwh=("energy_kwh", "sum"),
        avg_voltage=("voltage_v", "mean"),
        carbon_emissions_kg=("carbon_emissions_kg", "sum")
    ).reset_index().sort_values(by="total_energy_kwh", ascending=False)
    drilldown_df["total_energy_kwh"] = drilldown_df["total_energy_kwh"].round(2)
    drilldown_df["avg_voltage"] = drilldown_df["avg_voltage"].round(1)
    drilldown_df["carbon_emissions_kg"] = drilldown_df["carbon_emissions_kg"].round(2)
    print(drilldown_df.head(12).to_string(index=False))
    drilldown_df.to_csv(config.TABLES_DIR / "olap_drilldown.csv", index=False)

    # -------------------------------------------------------------
    # 3. SLICE (Fixing ONE dimension value)
    # -------------------------------------------------------------
    print("\n" + "-" * 80)
    print("[OPERATION 3: SLICE]")
    print("Explanation: Slicing the cube by fixing ONE dimension: Consumer Type = 'Commercial'.")
    slice_df = df[df["consumer_type"] == "Commercial"].groupby(["season", "period_of_day"]).agg(
        total_energy_kwh=("energy_kwh", "sum"),
        avg_hourly_kwh=("energy_kwh", "mean"),
        records=("fact_id", "count")
    ).reset_index()
    slice_df["total_energy_kwh"] = slice_df["total_energy_kwh"].round(2)
    slice_df["avg_hourly_kwh"] = slice_df["avg_hourly_kwh"].round(3)
    print(slice_df.to_string(index=False))
    slice_df.to_csv(config.TABLES_DIR / "olap_slice.csv", index=False)

    # -------------------------------------------------------------
    # 4. DICE (Multi-dimensional sub-cube extraction)
    # -------------------------------------------------------------
    print("\n" + "-" * 80)
    print("[OPERATION 4: DICE]")
    print("Explanation: Extracting a sub-cube with multiple criteria:")
    print("  Criteria: City IN ('Noida', 'Delhi') AND Type == 'Residential' AND Season == 'Summer' AND is_peak_hour == 1")
    dice_df = df[
        (df["city"].isin(["Noida", "Delhi"])) &
        (df["consumer_type"] == "Residential") &
        (df["season"] == "Summer") &
        (df["is_peak_hour"] == 1)
    ].groupby(["city", "month_name", "time_label"]).agg(
        total_energy_kwh=("energy_kwh", "sum"),
        avg_hourly_kwh=("energy_kwh", "mean"),
        consumer_count=("consumer_id", "nunique")
    ).reset_index().sort_values(by="total_energy_kwh", ascending=False)
    dice_df["total_energy_kwh"] = dice_df["total_energy_kwh"].round(2)
    dice_df["avg_hourly_kwh"] = dice_df["avg_hourly_kwh"].round(3)
    print(dice_df.head(10).to_string(index=False))
    dice_df.to_csv(config.TABLES_DIR / "olap_dice.csv", index=False)

    # -------------------------------------------------------------
    # 5. PIVOT / CUBE (Multi-way cross tabulation)
    # -------------------------------------------------------------
    print("\n" + "-" * 80)
    print("[OPERATION 5: PIVOT / CUBE VIEW]")
    print("Explanation: Cross-tabulation matrix showing Total Energy (kWh) by City vs Consumer Type.")
    pivot_df = pd.pivot_table(
        df,
        values="energy_kwh",
        index="city",
        columns="consumer_type",
        aggfunc="sum",
        margins=True,
        margins_name="Total_All_Sectors"
    ).round(2)
    print(pivot_df.to_string())
    pivot_df.to_csv(config.TABLES_DIR / "olap_pivot_cube.csv")

    # Generate Heatmap figure for visual lab presentation
    plt.figure(figsize=(10, 6))
    plot_data = pivot_df.drop(index="Total_All_Sectors", columns="Total_All_Sectors", errors="ignore")
    sns.heatmap(plot_data, annot=True, fmt=".1f", cmap="YlGnBu", cbar_kws={'label': 'Total Energy Consumption (kWh)'})
    plt.title("OLAP Data Cube Slice: Total Energy Consumption (City vs Consumer Type)", fontsize=13, fontweight='bold', pad=12)
    plt.xlabel("Consumer Type", fontweight='bold')
    plt.ylabel("City", fontweight='bold')
    plt.tight_layout()
    fig_path = config.FIGURES_DIR / "olap_cube_heatmap.png"
    plt.savefig(fig_path, dpi=300)
    plt.close()
    logger.info("Saved OLAP heatmap to: %s", fig_path)

    print("=" * 80 + "\n")


def run_olap():
    """Main execution entrypoint for Step 5."""
    logger.info("=== STEP 5: STARTING OLAP OPERATIONS ===")
    perform_olap_operations()
    logger.info("=== STEP 5 COMPLETE ===")


if __name__ == "__main__":
    run_olap()

