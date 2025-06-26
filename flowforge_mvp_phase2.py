
import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="FlowForge MVP", layout="wide")
st.title("📦 FlowForge MVP – Dynamic Labor Allocation & Alerts Engine")

uploaded_file = st.file_uploader("Upload the FlowForge Excel File", type=["xlsx"])

if uploaded_file:
    st.success("File uploaded successfully!")

    # Read Excel sheets
    order_backlog = pd.read_excel(uploaded_file, sheet_name="Order_Backlog")
    zone_activity = pd.read_excel(uploaded_file, sheet_name="Zone_Activity")
    labor_roster = pd.read_excel(uploaded_file, sheet_name="Labor_Roster")

    # Process Due_Time and add Hours_Until_Due
    order_backlog["Due_Time"] = pd.to_datetime(order_backlog["Due_Time"])
    order_backlog["Hours_Until_Due"] = (order_backlog["Due_Time"] - datetime.now()).dt.total_seconds() / 3600

    # Add Priority Score
    def calculate_score(row):
        score = 0
        if row["Priority"] == "High":
            score += 3
        elif row["Priority"] == "Medium":
            score += 2
        else:
            score += 1
        if row["Hours_Until_Due"] < 4:
            score += 2
        if row["SKU_Count"] > 10:
            score += 1
        return score

    order_backlog["Priority_Score"] = order_backlog.apply(calculate_score, axis=1)

    # === Sidebar Filters ===
    st.sidebar.header("🔍 Filters")
    selected_zones = st.sidebar.multiselect("Filter by Zone", options=order_backlog["Zone"].unique(), default=order_backlog["Zone"].unique())
    selected_tasks = st.sidebar.multiselect("Filter by Task", options=order_backlog["Task"].unique(), default=order_backlog["Task"].unique())
    selected_priorities = st.sidebar.multiselect("Filter by Priority", options=order_backlog["Priority"].unique(), default=order_backlog["Priority"].unique())
    selected_skills = st.sidebar.multiselect("Filter Pickers by Skill Level", options=labor_roster["Skill_Level"].unique(), default=labor_roster["Skill_Level"].unique())

    # Apply filters
    filtered_orders = order_backlog[
        (order_backlog["Zone"].isin(selected_zones)) &
        (order_backlog["Task"].isin(selected_tasks)) &
        (order_backlog["Priority"].isin(selected_priorities))
    ]

    filtered_pickers = labor_roster[
        (labor_roster["Skill_Level"].isin(selected_skills))
    ]

    # === Alerts ===
    st.subheader("🚨 Real-Time Operational Alerts")

    alerts = []

    # Zone overload check
    for _, row in zone_activity.iterrows():
        if row["Active_Pickers"] > 0:
            orders_in_zone = filtered_orders[filtered_orders["Zone"] == row["Zone"]].shape[0]
            ratio = orders_in_zone / row["Active_Pickers"]
            if ratio > 10:
                alerts.append(f"⚠️ Zone {row['Zone']} is overloaded: {orders_in_zone} orders / {row['Active_Pickers']} pickers")

    # Idle workers
    idle = labor_roster[(labor_roster["Availability"] != "Available") | (labor_roster["Assigned_Zone"] == "Unassigned")]
    if not idle.empty:
        alerts.append(f"🟡 {idle.shape[0]} pickers are currently unassigned or unavailable")

    # SLA risks
    urgent_orders = filtered_orders[(filtered_orders["Priority"] == "High") & (filtered_orders["Hours_Until_Due"] < 2)]
    if not urgent_orders.empty:
        alerts.append(f"🚨 {urgent_orders.shape[0]} high-priority orders are at SLA risk (< 2 hrs left)")

    if alerts:
        for a in alerts:
            st.warning(a)
    else:
        st.success("✅ No critical alerts at the moment.")

    # === Data Tables ===
    st.subheader("🔥 Filtered Priority Orders")
    st.dataframe(filtered_orders.sort_values(by="Priority_Score", ascending=False)[["OrderID", "Zone", "Task", "Priority", "Hours_Until_Due", "SKU_Count", "Priority_Score"]])

    st.subheader("🧍 Filtered Picker Pool")
    st.dataframe(filtered_pickers[["PickerID", "Skill_Level", "Assigned_Zone", "Availability", "Primary_Task"]])

else:
    st.info("Please upload a valid FlowForge Excel file to begin.")
