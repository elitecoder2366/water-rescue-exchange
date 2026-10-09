from src.qubo_demo import solve_qubo_demo
import streamlit as st
import pandas as pd
from src.water_rescue import demo_fields, recommend_transfers

st.set_page_config(page_title="Water Rescue Exchange", page_icon="💧", layout="wide")

st.title("💧 Water Rescue Exchange")
st.caption("A small prototype for deadline-aware irrigation water reallocation")

st.warning(
    "Prototype mode: all values are editable demo data. This app is not connected to live sensors "
    "and does not control real irrigation gates."
)

st.markdown(
    """
    **The idea:** if one field has water it can safely spare, the system looks for another field
    with an unmet need and checks whether the water could arrive before the recipient's deadline.
    """
)

with st.sidebar:
    st.header("Demo settings")
    route_capacity = st.number_input(
        "Maximum transfer per route (litres)", min_value=1, max_value=10000, value=20, step=1
    )
    st.caption("This is a simplified per-transfer limit, not a hydraulic canal model.")

st.subheader("1. Field data")
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

if st.button("Find feasible transfers", type="primary", use_container_width=True):
    recommendations, rejected = recommend_transfers(
        edited.to_dict(orient="records"),
        route_capacity_l=float(route_capacity),
    )
    st.session_state["recommendations"] = recommendations
    st.session_state["rejected"] = rejected

if "recommendations" in st.session_state:
    recs = st.session_state["recommendations"]
    rejected = st.session_state["rejected"]
    st.subheader("2. Recommendations")
    if recs:
        result = pd.DataFrame(recs)
        c1, c2, c3 = st.columns(3)
        c1.metric("Recommended water", f"{result['quantity_l'].sum():g} L")
        c2.metric("Transfers proposed", len(result))
        c3.metric("Recipients helped", result["recipient"].nunique())
        st.dataframe(result, use_container_width=True, hide_index=True)
    else:
        st.info("No feasible transfers were found for the current inputs.")

    with st.expander("Why some transfers were rejected"):
        if rejected:
            st.dataframe(pd.DataFrame(rejected), use_container_width=True, hide_index=True)
        else:
            st.write("No candidate transfer was rejected by the basic checks.")

st.subheader("3. What this prototype checks")
st.markdown(
    """
    - Donor surplus and recipient unmet need
    - A simplified transfer-volume limit
    - Recipient deadline versus travel time
    - Explicit transfer authorization
    - A basic urgency-first allocation rule

    **Not implemented yet:** live sensor readings, real canal hydraulics, legal water-rights
    integration, crop-specific water-stress models, quantum optimization, or automatic gate control.
    """
)

st.caption("Water Rescue Exchange · Hackathon prototype · Simulated data only")
