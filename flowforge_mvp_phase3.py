
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="FlowForge MVP", layout="wide")
st.title("📦 FlowForge MVP – Simulated Shift & SLA Monitor")

uploaded_file = st.file_uploader("Upload the FlowForge Excel File", type=["xlsx"])

if uploaded_file:
    st.success("File uploaded successfully!")

    # Load data
    order_backlog = pd.read_excel(uploaded_file, sheet_name="Order_Backlog")
    zone_activity = pd.read_excel(uploaded_file, sheet_name="Zone_Activity")
    labor_roster = pd.read_excel(uploaded_file, sheet_name="Labor_Roster")

    # Convert date fields
    order_backlog["Due_Time"] = pd.to_datetime(order_backlog["Due_Time"])
    labor_roster["Shift_Start"] = pd.to_datetime(labor_roster["Shift_Start"])

    # Simulated time control
    st.sidebar.header("⏱️ Simulated Clock")
    simulated_hour = st.sidebar.slider("Current Hour", 8, 20, 10)
    simulated_time = datetime.now().replace(hour=simulated_hour, minute=0, second=0, microsecond=0)
    st.sidebar.write(f"🕒 Simulated Time: {simulated_time.strftime('%H:%M')}")

    # Update Hours_Until_Due
    order_backlog["Hours_Until_Due"] = (order_backlog["Due_Time"] - simulated_time).dt.total_seconds() / 3600

    # Update Picker Availability
    labor_roster["Shift_Status"] = labor_roster["Shift_Start"].apply(
        lambda t: "Available" if t.hour <= simulated_hour < t.hour + 8 else "Off-shift"
    )

    # Priority scoring
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

    # Alerts
    st.subheader("🚨 Shift-Based Operational Alerts")
    alerts = []

    # SLA risk
    urgent_orders = order_backlog[(order_backlog["Priority"] == "High") & (order_backlog["Hours_Until_Due"] < 2)]
    if not urgent_orders.empty:
        alerts.append(f"🚨 {urgent_orders.shape[0]} high-priority orders are at SLA risk (< 2 hrs left)")

    # Off-shift or unassigned workers
    off_shift = labor_roster[labor_roster["Shift_Status"] == "Off-shift"]
    if not off_shift.empty:
        alerts.append(f"🛌 {off_shift.shape[0]} workers are currently off-shift")

    # Zone overload check
    for _, row in zone_activity.iterrows():
        zone_orders = order_backlog[order_backlog["Zone"] == row["Zone"]].shape[0]
        if row["Active_Pickers"] > 0:
            ratio = zone_orders / row["Active_Pickers"]
            if ratio > 10:
                alerts.append(f"⚠️ Zone {row['Zone']} is overloaded: {zone_orders} orders / {row['Active_Pickers']} pickers")

    if alerts:
        for alert in alerts:
            st.warning(alert)
    else:
        st.success("✅ No major alerts at this simulated hour.")

    st.markdown("---")
    st.subheader("📦 Orders Near SLA Threshold")
    st.dataframe(urgent_orders[["OrderID", "Zone", "Task", "Priority", "Hours_Until_Due", "Priority_Score"]])

    st.markdown("---")
    st.subheader("👷 Picker Shift Planner")
    st.dataframe(labor_roster[["PickerID", "Skill_Level", "Shift_Start", "Shift_Status", "Assigned_Zone", "Primary_Task"]])

else:
    st.info("Please upload a valid FlowForge Excel file to begin.")
