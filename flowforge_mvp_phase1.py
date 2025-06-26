
import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="FlowForge MVP", layout="wide")
st.title("📦 FlowForge MVP – Dynamic Labor Allocation & Priority Engine")

uploaded_file = st.file_uploader("Upload the FlowForge Excel File", type=["xlsx"])

if uploaded_file:
    st.success("File uploaded successfully!")

    # Read the Excel file
    order_backlog = pd.read_excel(uploaded_file, sheet_name="Order_Backlog")
    zone_activity = pd.read_excel(uploaded_file, sheet_name="Zone_Activity")
    labor_roster = pd.read_excel(uploaded_file, sheet_name="Labor_Roster")

    # Convert due times
    order_backlog["Due_Time"] = pd.to_datetime(order_backlog["Due_Time"])
    order_backlog["Hours_Until_Due"] = (order_backlog["Due_Time"] - datetime.now()).dt.total_seconds() / 3600

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
    top_orders = order_backlog.sort_values(by="Priority_Score", ascending=False)

    st.subheader("🔥 Top Priority Orders")
    st.dataframe(top_orders[["OrderID", "Zone", "Task", "Priority", "Hours_Until_Due", "SKU_Count", "Priority_Score"]].head(20))

    st.markdown("---")

    # Available pickers
    available_pickers = labor_roster[labor_roster["Availability"] == "Available"].copy()

    # Assign pickers to top zones
    zone_demand = top_orders["Zone"].value_counts().reset_index()
    zone_demand.columns = ["Zone", "Demand"]

    picker_assignments = []
    for _, picker in available_pickers.iterrows():
        assigned_zone = picker["Assigned_Zone"]
        if assigned_zone == "Unassigned":
            top_zone = zone_demand.sort_values(by="Demand", ascending=False)["Zone"].iloc[0]
            picker_assignments.append((picker["PickerID"], picker["Primary_Task"], top_zone))
        else:
            picker_assignments.append((picker["PickerID"], picker["Primary_Task"], assigned_zone))

    assignment_df = pd.DataFrame(picker_assignments, columns=["PickerID", "Primary_Task", "Assigned_Zone"])

    st.subheader("🤖 Dynamic Picker Assignments (Rule-Based)")
    st.dataframe(assignment_df)

else:
    st.info("Please upload a valid FlowForge Excel file to begin.")
