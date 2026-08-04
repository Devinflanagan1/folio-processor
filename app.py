import streamlit as st
import pandas as pd
from datetime import date, timedelta

st.set_page_config(page_title="THC Breakfast Credit Calculator", layout="wide")
st.markdown("### THC Daily Breakfast Credit Calculator ($60/Night Non-Rolling)")

# 1. Stay Date Selection
col1, col2 = st.columns(2)
with col1:
    arrival_date = st.date_input("Arrival Date", value=date.today())
with col2:
    departure_date = st.date_input("Departure Date", value=date.today() + timedelta(days=2))

nights = (departure_date - arrival_date).days

if nights <= 0:
    st.error("Departure date must be after arrival date.")
else:
    st.markdown(f"**Total Nights:** {nights} | **Max Potential Credit:** ${nights * 60:,.2f}")
    st.markdown("---")
    
    # 2. Pre-populate rows for each stay date
    stay_dates = [arrival_date + timedelta(days=i) for i in range(nights + 1)]
    default_data = [{"Date": d, "Charge Description": "Field Notes", "Amount ($)": 0.0} for d in stay_dates]
    
    df_initial = pd.DataFrame(default_data)
    
    st.markdown("#### Enter Field Notes Charges")
    st.caption("Enter amounts below. You can add extra rows if there are multiple charges on the same day.")
    
    edited_df = st.data_editor(
        df_initial,
        num_rows="dynamic",
        use_container_width=True,
        key="thc_editor"
    )
    
    # 3. Calculation & Non-Rolling Cap Logic
    edited_df["Amount ($)"] = pd.to_numeric(edited_df["Amount ($)"], errors="coerce").fillna(0.0)
    
    # Group by date to total multiple charges on the same day
    daily_summary = edited_df.groupby("Date")["Amount ($)"].sum().reset_index()
    daily_summary.rename(columns={"Amount ($)": "Total Charged ($)"}, inplace=True)
    
    # Apply the use-it-or-lose-it $60 daily cap
    daily_summary["Credit to Post ($)"] = daily_summary["Total Charged ($)"].apply(lambda x: min(x, 60.0))
    daily_summary["Guest Responsibility ($)"] = daily_summary["Total Charged ($)"] - daily_summary["Credit to Post ($)"]
    
    total_credit = daily_summary["Credit to Post ($)"].sum()
    total_charged = daily_summary["Total Charged ($)"].sum()
    
    st.markdown("---")
    st.markdown("#### Daily Breakdown & Posting Summary")
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Field Notes Charged", f"${total_charged:,.2f}")
    m2.metric("Total Breakfast Credit to Post", f"${total_credit:,.2f}")
    m3.metric("Remaining Guest Charge", f"${(total_charged - total_credit):,.2f}")
    
    st.dataframe(daily_summary, use_container_width=True, hide_index=True)
