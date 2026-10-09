from src.quantum_optimizer import solve_qaoa_demo
import streamlit as st
import pandas as pd

from src.water_rescue import demo_fields, recommend_transfers, audit_allocation, build_simulated_control_plan
from src.qubo_demo import solve_qubo_demo
from src.optimization_benchmark import run_optimization_comparison
from src.quantum_allocation import run_scenario, hardware_status

st.set_page_config(
    page_title="Water Rescue Exchange",
    page_icon="💧",
    layout="wide",
)

st.title("💧 Water Rescue Exchange")
st.caption("Deadline-aware irrigation water reallocation")

st.warning(
    "Hackathon prototype: uses editable demo data. "
    "No live sensors or real irrigation gate controls are connected."
)

st.markdown(
    """
    **Goal:** Identify fields with water they can spare and recommend transfers
    to fields with unmet demand, while considering deadlines and authorization.
    """
)

# ---------------- SIDEBAR ----------------

with st.sidebar:
    st.header("⚙️ Demo settings")
    route_capacity = st.number_input(
        "Maximum transfer per route (litres)",
        min_value=1,
        max_value=10000,
        value=20,
        step=1,
    )
    st.caption("Simplified route limit; not a hydraulic canal simulation.")

# ---------------- FIELD DATA ----------------

st.header("1. 🌾 Field data")

initial = pd.DataFrame(demo_fields())

edited = st.data_editor(
    initial,
    use_container_width=True,
    hide_index=True,
    num_rows="fixed",
    column_config={
        "field": st.column_config.TextColumn("Field", disabled=True),
        "surplus_l": st.column_config.NumberColumn("Safe surplus (L)", min_value=0, step=1),
        "need_l": st.column_config.NumberColumn("Unmet need (L)", min_value=0, step=1),
        "urgency": st.column_config.NumberColumn("Urgency (1–10)", min_value=1, max_value=10, step=1),
        "travel_min": st.column_config.NumberColumn("Travel time (min)", min_value=0, step=1),
        "deadline_min": st.column_config.NumberColumn("Deadline (min)", min_value=0, step=1),
        "authorized": st.column_config.CheckboxColumn("Transfer authorized"),
    },
)

col1, col2, col3 = st.columns(3)
col1.metric("Total safe surplus", f"{edited['surplus_l'].sum():g} L")
col2.metric("Total unmet need", f"{edited['need_l'].sum():g} L")
col3.metric("Authorized fields", int(edited["authorized"].sum()))

# ---------------- CLASSICAL ALLOCATION ----------------

st.header("2. 💧 Water transfer recommendations")

if st.button("Find feasible transfers", type="primary", use_container_width=True):
    try:
        recommendations, rejected = recommend_transfers(
            edited.to_dict(orient="records"),
            route_capacity_l=float(route_capacity),
        )
        st.session_state["recommendations"] = recommendations
        st.session_state["rejected"] = rejected
    except Exception as e:
        st.error(f"Transfer calculation failed: {e}")

if "recommendations" in st.session_state:
    recs = st.session_state["recommendations"]
    rejected = st.session_state.get("rejected", [])
    if recs:
        result_df = pd.DataFrame(recs)
        c1, c2, c3 = st.columns(3)
        c1.metric("Recommended water", f"{result_df['quantity_l'].sum():g} L")
        c2.metric("Transfers proposed", len(result_df))
        c3.metric("Recipients helped", result_df["recipient"].nunique())
        st.dataframe(result_df, use_container_width=True, hide_index=True)
        st.download_button(
            "⬇️ Download transfer report (CSV)",
            data=result_df.to_csv(index=False).encode("utf-8"),
            file_name="water_transfer_recommendations.csv",
            mime="text/csv",
        )
    else:
        st.info("No feasible transfers found for the current inputs.")
    with st.expander("Why some transfers were rejected"):
        if rejected:
            st.dataframe(pd.DataFrame(rejected), use_container_width=True, hide_index=True)
        else:
            st.write("No candidate transfers were rejected.")

# ---------------- QUBO DEMO ----------------

st.divider()
st.header("3. 🧮 QUBO water allocation demo")
st.markdown(
    """
    QUBO means **Quadratic Unconstrained Binary Optimization**.
    The demo represents candidate transfers using binary choices and scores
    combinations with an energy function.
    """
)
st.info("This section solves a simplified QUBO using classical computation. The separate QAOA section demonstrates a quantum optimization algorithm on a simulator. Neither section uses a physical quantum computer.")
st.caption(
    "The QUBO demo uses the currently edited fields, but its simplified model "
    "does not replace all the feasibility checks in the main allocator."
)

if st.button("Run QUBO Demo", use_container_width=True):
    try:
        qubo_fields = [
            {
                "name": str(row["field"]),
                "available_water": float(row["surplus_l"]) + float(row["need_l"]),
                "water_need": float(row["need_l"]),
                "deadline_hours": max(float(row["deadline_min"]) / 60.0, 1.0 / 60.0),
            }
            for row in edited.to_dict(orient="records")
            if bool(row["authorized"])
        ]
        result = solve_qubo_demo(qubo_fields)
        st.write("**Solver method:**", result["method"])
        st.write("**Status:**", result["status"])
        st.write("**QUBO variables:**", result["qubo_variables"])
        st.write("**Best energy:**", result["best_energy"])
        if result["transfers"]:
            qubo_df = pd.DataFrame(result["transfers"])
            st.subheader("QUBO candidate transfers")
            st.dataframe(qubo_df, use_container_width=True, hide_index=True)
            st.download_button(
                "⬇️ Download QUBO report (CSV)",
                data=qubo_df.to_csv(index=False).encode("utf-8"),
                file_name="qubo_water_allocation_demo.csv",
                mime="text/csv",
            )
        else:
            st.info("No eligible QUBO transfer options found.")
        st.caption("These are educational classical-search results, not quantum-computer results.")
    except Exception as e:
        st.error(f"QUBO demo failed: {e}")

# ---------------- CLASSICAL VS QAOA BENCHMARK ----------------

st.divider()
st.header("4. 📊 Compare QAOA with classical baselines")
st.markdown(
    "This benchmark compares greedy selection, exact classical search, and the QAOA "
    "statevector simulation on the same small illustrative transfer problem. It is a "
    "separate benchmark instance, not the editable field table above."
)

if st.button("Run optimization comparison", use_container_width=True):
    try:
        with st.spinner("Running classical baselines and QAOA simulation..."):
            comparison = run_optimization_comparison()
        comparison_df = pd.DataFrame(comparison["results"])
        st.dataframe(comparison_df, use_container_width=True, hide_index=True)
        st.caption(comparison["note"])
        st.download_button(
            "⬇️ Download optimization comparison (CSV)",
            data=comparison_df.to_csv(index=False).encode("utf-8"),
            file_name="optimization_comparison.csv",
            mime="text/csv",
        )
    except Exception as e:
        st.error(f"Optimization comparison failed: {e}")

# ---------------- FAIRNESS-AWARE QUANTUM SCENARIO LAB ----------------

st.divider()
st.header("5. ⚛️ Quantum allocation + fairness + drought lab")
st.markdown(
    "Reuses the project's QAOA/statevector approach for a small scenario built from the edited fields. "
    "A classical exact-search baseline is run on the same candidate options, and selected transfers "
    "are independently checked against hard capacity/need constraints."
)
drought = st.slider(
    "Drought stress: available surplus (%)",
    min_value=50, max_value=100, value=100, step=10,
    help="Lower surplus and raise unmet demand in this illustrative stress test."
)
use_hardware_check = st.checkbox("Check optional IBM Quantum hardware account", value=False)
st.caption("Hardware check only: this prototype does not submit jobs to a physical quantum backend.")
if st.button("Run quantum + fairness + drought scenario", use_container_width=True):
    try:
        with st.spinner("Comparing exact classical search and QAOA simulator..."):
            scenario = run_scenario(
                edited.to_dict(orient="records"),
                float(route_capacity),
                drought_factor=drought / 100.0,
                try_hardware=use_hardware_check,
            )
        st.subheader("Scenario parameters")
        st.json(scenario["scenario"])
        left, right = st.columns(2)
        with left:
            st.markdown("**Classical baseline**")
            st.metric("Objective (lower is better)", scenario["classical"]["objective"])
            st.metric("Feasible", str(scenario["classical"]["feasible"]))
            st.metric("Fairness gap", scenario["classical"]["fairness_gap"])
            st.caption(f"Runtime: {scenario['classical']['runtime_s']} s")
            st.dataframe(pd.DataFrame(scenario["classical"]["transfers"]), use_container_width=True, hide_index=True)
        with right:
            st.markdown("**QAOA simulator**")
            st.metric("Objective (lower is better)", scenario["qaoa"]["objective"])
            st.metric("Independent feasibility audit", str(scenario["qaoa"]["feasible"]))
            st.metric("Fairness gap", scenario["qaoa"]["fairness_gap"])
            st.caption(f"Runtime: {scenario['qaoa']['runtime_s']} s")
            st.dataframe(pd.DataFrame(scenario["qaoa"]["transfers"]), use_container_width=True, hide_index=True)
        if use_hardware_check:
            st.info(scenario["hardware"]["message"])
        st.warning(scenario["note"])
        rows = []
        for method in ("classical", "qaoa"):
            item = scenario[method]
            rows.append({
                "Method": item["method"], "Objective": item["objective"],
                "Feasible": item["feasible"], "Fairness gap": item["fairness_gap"],
                "Runtime (s)": item["runtime_s"],
                "Transfers": "; ".join(x["route"] for x in item["transfers"]),
            })
        scenario_df = pd.DataFrame(rows)
        st.download_button(
            "⬇️ Download quantum scenario comparison (CSV)",
            data=scenario_df.to_csv(index=False).encode("utf-8"),
            file_name="quantum_drought_fairness_comparison.csv",
            mime="text/csv",
        )
    except Exception as e:
        st.error(f"Quantum scenario lab failed: {e}")

# ---------------- PROJECT LIMITATIONS ----------------

st.divider()
st.header("6. ℹ️ What this prototype does")
st.markdown(
    """
    **Included**
    - Editable demo field data
    - Basic feasible-transfer recommendations
    - Simplified route capacity and deadline checks
    - Transfer authorization input
    - CSV export
    - Educational QUBO model with classical exhaustive search
    - Small benchmark comparing greedy, exact classical search, and QAOA simulation

    **Not yet implemented**
    - Live sensor readings
    - Real canal hydraulics and water-rights validation
    - Production-grade fairness and safety constraints
    - Physical quantum hardware integration
    - Automatic pump or irrigation-gate control
    """
)
# ---------------- FAIRNESS, SAFETY & SIMULATED CONTROL ----------------

st.divider()
st.header("7. 🛡️ Fairness & safety review")
st.warning(
    "These are prototype checks, not production-grade safety controls. "
    "Review results with water-management experts before any real-world use."
)

if "recommendations" in st.session_state:
    audit = audit_allocation(edited.to_dict(orient="records"), st.session_state["recommendations"])
    if audit["checks_passed"]:
        st.success("The selected recommendations passed the implemented prototype audit.")
    else:
        st.error("The prototype audit found issues that need review.")
        st.write(audit["violations"])
    st.metric("Recipient satisfaction gap", audit["fairness_gap"])
    st.caption(
        "Fairness gap is the difference between the highest and lowest capped "
        "need-satisfaction ratios among recipients with nonzero need. It is a simple indicator, "
        "not a complete fairness measure."
    )
    satisfaction_rows = []
    for row in edited.to_dict(orient="records"):
        need = float(row["need_l"])
        delivered = audit["delivered_l"].get(row["field"], 0.0)
        satisfaction_rows.append({
            "Field": row["field"],
            "Need (L)": need,
            "Recommended (L)": delivered,
            "Need satisfied (%)": round(min(100.0, delivered / need * 100), 1) if need > 0 else None,
        })
    st.dataframe(pd.DataFrame(satisfaction_rows), use_container_width=True, hide_index=True)

    st.subheader("🚰 Simulated pump / irrigation-gate control preview")
    st.info(
        "Preview only: this app is not connected to pumps, gates, PLCs, or IoT devices. "
        "No physical command will be sent."
    )
    plan = build_simulated_control_plan(st.session_state["recommendations"])
    if plan:
        st.dataframe(pd.DataFrame(plan), use_container_width=True, hide_index=True)
        st.download_button(
            "⬇️ Download simulated control plan (CSV)",
            data=pd.DataFrame(plan).to_csv(index=False).encode("utf-8"),
            file_name="simulated_control_plan.csv",
            mime="text/csv",
        )
    else:
        st.info("No transfer recommendations are available to preview.")
else:
    st.info("Run 'Find feasible transfers' first to see the fairness review and simulated control preview.")

st.caption("Water Rescue Exchange | Hackathon prototype | Simulated data")


# ---------------- SEVEN-DAY WATER AVAILABILITY PREDICTION ----------------

st.divider()
st.header("8. 🔮 Water availability prediction — next 7 days")
st.markdown(
    "Enter your reservoir/field estimates manually and optionally use the Open-Meteo "
    "daily rainfall forecast. The forecast is a transparent water-balance estimate, "
    "not a trained machine-learning model or a guaranteed supply prediction."
)

from src.water_prediction import fetch_rainfall_forecast, build_seven_day_forecast

with st.expander("How this estimate works", expanded=False):
    st.write(
        "Each day: previous storage + estimated base inflow + rainfall × capture factor − "
        "expected demand. Storage is capped at the entered capacity. The rainfall capture "
        "factor is a user-entered estimate in litres per millimetre; calibrate it for your "
        "catchment/reservoir. This simplified model does not simulate evaporation, releases, "
        "groundwater, canal losses, or complex hydrology."
    )

p1, p2, p3 = st.columns(3)
with p1:
    current_storage = st.number_input("Current stored water (L)", min_value=0.0, value=50000.0, step=1000.0, key="pred_storage")
    storage_capacity = st.number_input("Total storage capacity (L)", min_value=1.0, value=100000.0, step=1000.0, key="pred_capacity")
with p2:
    base_inflow = st.number_input("Expected base inflow per day (L)", min_value=0.0, value=5000.0, step=500.0, key="pred_inflow")
    daily_demand = st.number_input("Expected water use per day (L)", min_value=0.0, value=7000.0, step=500.0, key="pred_demand")
with p3:
    capture_factor = st.number_input(
        "Rain capture factor (L per mm)",
        min_value=0.0, value=100.0, step=10.0, key="pred_capture",
        help="Estimate how many litres enter storage per 1 mm of rainfall. Use 0 if rainfall does not add measurable storage."
    )
    rain_source = st.radio("Rainfall input", ["Live weather forecast", "Enter rainfall manually"], key="pred_rain_source")

if rain_source == "Live weather forecast":
    wx1, wx2 = st.columns(2)
    with wx1:
        latitude = st.number_input("Location latitude", min_value=-90.0, max_value=90.0, value=17.3850, format="%.4f", key="pred_lat")
    with wx2:
        longitude = st.number_input("Location longitude", min_value=-180.0, max_value=180.0, value=78.4867, format="%.4f", key="pred_lon")
    st.caption("Default coordinates are Hyderabad. Change them to your reservoir/field location.")
    if st.button("Fetch 7-day rainfall forecast", key="fetch_rain_btn"):
        try:
            with st.spinner("Fetching daily rainfall forecast..."):
                weather_df = fetch_rainfall_forecast(latitude, longitude)
            st.session_state["prediction_rainfall"] = weather_df
            st.session_state["prediction_rain_source_label"] = "Open-Meteo live weather forecast"
        except Exception as e:
            st.error(f"Weather data could not be fetched: {e}")
            st.info("Switch to 'Enter rainfall manually' to continue without the weather service.")
    if "prediction_rainfall" in st.session_state:
        rainfall_df = st.session_state["prediction_rainfall"].copy()
        st.caption("Rainfall source: Open-Meteo. Forecast can change and may not represent local microclimates.")
        st.dataframe(rainfall_df, use_container_width=True, hide_index=True)
        rainfall_values = rainfall_df["Forecast rainfall (mm)"].astype(float).tolist()
    else:
        rainfall_values = None
        st.info("Click 'Fetch 7-day rainfall forecast' before calculating, or choose manual rainfall input.")
else:
    st.caption("Enter expected daily rainfall in millimetres for each of the next seven days.")
    manual_rain = []
    rain_cols = st.columns(7)
    for day_idx, rain_col in enumerate(rain_cols, start=1):
        with rain_col:
            manual_rain.append(
                st.number_input(f"Day {day_idx} (mm)", min_value=0.0, value=0.0, step=1.0, key=f"pred_manual_rain_{day_idx}")
            )
    rainfall_values = manual_rain

if st.button("Calculate 7-day water availability", type="primary", key="calc_water_prediction"):
    try:
        if rainfall_values is None:
            st.error("Fetch weather rainfall data first, or switch to manual rainfall input.")
        else:
            forecast_df = build_seven_day_forecast(
                current_storage_l=float(current_storage),
                storage_capacity_l=float(storage_capacity),
                daily_base_inflow_l=float(base_inflow),
                daily_demand_l=float(daily_demand),
                rainfall_mm=[float(x) for x in rainfall_values],
                rainfall_capture_l_per_mm=float(capture_factor),
            )
            st.session_state["water_availability_forecast"] = forecast_df
    except Exception as e:
        st.error(f"Could not calculate forecast: {e}")

if "water_availability_forecast" in st.session_state:
    forecast_df = st.session_state["water_availability_forecast"]
    final_storage = float(forecast_df.iloc[-1]["Forecast storage (L)"])
    min_storage_pct = float(forecast_df["Storage available (%)"].min())
    total_unmet = float(forecast_df["Estimated unmet demand (L)"].sum())
    m1, m2, m3 = st.columns(3)
    m1.metric("Storage after 7 days", f"{final_storage:,.0f} L")
    m2.metric("Lowest forecast storage", f"{min_storage_pct:.1f}%")
    m3.metric("Estimated unmet demand", f"{total_unmet:,.0f} L")
    if min_storage_pct < 20 or total_unmet > 0:
        st.warning("Shortage risk: forecast storage becomes low or demand may not be fully met. Review inputs and plan with local water managers.")
    else:
        st.success("The simple model does not indicate a shortage under the entered assumptions.")
    chart_df = forecast_df.set_index("Date")[["Forecast storage (L)"]]
    st.line_chart(chart_df)
    st.dataframe(forecast_df, use_container_width=True, hide_index=True)
    st.download_button(
        "⬇️ Download 7-day water availability forecast (CSV)",
        data=forecast_df.to_csv(index=False).encode("utf-8"),
        file_name="water_availability_7_day_forecast.csv",
        mime="text/csv",
        key="download_water_prediction",
    )

