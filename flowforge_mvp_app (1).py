
import streamlit as st
import pandas as pd

st.set_page_config(page_title="FlowForge MVP", layout="wide")

st.title("📦 FlowForge MVP – Dynamic Labor Allocation & Pick Priority Engine")

uploaded_file = st.file_uploader("Upload the FlowForge Excel File", type=["xlsx"])

if uploaded_file:
    st.success("File uploaded successfully!")

    # Read the Excel file
    order_backlog = pd.read_excel(uploaded_file, sheet_name="Order_Backlog")
    zone_activity = pd.read_excel(uploaded_file, sheet_name="Zone_Activity")
    labor_roster = pd.read_excel(uploaded_file, sheet_name="Labor_Roster")

    # Display key metrics
    st.subheader("📊 Summary Stats")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Orders", len(order_backlog))
    col2.metric("Zones", order_backlog['Zone'].nunique())
    col3.metric("Active Associates", labor_roster[labor_roster['Availability'] == "Available"].shape[0])

    st.markdown("---")

    # Display zone activity
    st.subheader("📍 Zone Activity Overview")
    st.dataframe(zone_activity)

    st.markdown("---")

    # Display current labor roster
    st.subheader("🧍 Labor Roster (Available Only)")
    available_labor = labor_roster[labor_roster["Availability"] == "Available"]
    st.dataframe(available_labor)

    st.markdown("---")

    # Simple rule-based picker assignment (example logic)
    st.subheader("⚙️ Suggested Picker Assignments (Example Logic)")
    sample_assignments = available_labor.copy()
    sample_assignments["Suggested_Zone"] = sample_assignments["Assigned_Zone"].apply(
        lambda z: z if z != "Unassigned" else zone_activity.sort_values("Total_Orders", ascending=False).iloc[0]["Zone"]
    )
    st.dataframe(sample_assignments[["PickerID", "Skill_Level", "Primary_Task", "Suggested_Zone"]])

else:
    st.info("Please upload a valid FlowForge Excel file to begin.")
