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
