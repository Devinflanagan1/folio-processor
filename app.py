import streamlit as st
import pandas as pd
from datetime import timedelta

st.set_page_config(page_title="THC Credit Calculator", layout="centered")
st.markdown("### THC Credit Calculator (Breakfast & Property)")

# 1. Date Inputs
col1, col2 = st.columns(2)
with col1:
    arrival_date = st.date_input("Arrival Date")
with col2:
    departure_date = st.date_input("Departure Date")

st.markdown("---")
st.markdown("#### Enter Charges")
st.info("Log all eligible charges below. Use the 'Category' dropdown to sort them.")

# 2. Setup Data Editor for Charges
if "charge_data" not in st.session_state:
    st.session_state.charge_data = pd.DataFrame([
        {"Date": arrival_date, "Category": "Field Notes (Breakfast)", "Amount": 0.0}
    ])

edited_df = st.data_editor(
    st.session_state.charge_data,
    num_rows="dynamic",
    column_config={
        "Date": st.column_config.DateColumn("Charge Date", default=arrival_date),
        "Category": st.column_config.SelectboxColumn(
            "Category",
            help="Select the type of charge",
            options=["Field Notes (Breakfast)", "Other Property Charge"],
            required=True
        ),
        "Amount": st.column_config.NumberColumn("Amount ($)", min_value=0.0, format="$%.2f")
    },
    use_container_width=True,
    key="charge_editor"
)

# 3. Calculation Logic
if st.button("Calculate Credits", type="primary"):
    edited_df["Date"] = pd.to_datetime(edited_df["Date"]).dt.date
    
    total_breakfast_credit = 0.0
    total_breakfast_overage = 0.0
    breakdown = []
    
    # --- BREAKFAST CREDIT ($60/day non-rolling) ---
    breakfast_df = edited_df[edited_df["Category"] == "Field Notes (Breakfast)"]
    daily_breakfast = breakfast_df.groupby("Date")["Amount"].sum().reset_index()
    
    current_date = arrival_date
    while current_date < departure_date:
        # Get total breakfast charges for the current date
        day_charge = daily_breakfast[daily_breakfast["Date"] == current_date]["Amount"].sum() if current_date in daily_breakfast["Date"].values else 0.0
        
        # Cap the credit at $60 per day
        eligible_credit = min(day_charge, 60.0)
        day_overage = max(0.0, day_charge - 60.0)
        
        total_breakfast_credit += eligible_credit
        total_breakfast_overage += day_overage
        
        breakdown.append({
            "Date": current_date.strftime("%Y-%m-%d"),
            "Breakfast Charged": f"${day_charge:.2f}",
            "Breakfast Credit Applied": f"${eligible_credit:.2f}",
            "Uncovered Overage": day_overage # Stored as float for math, formatted later
        })
        current_date += timedelta(days=1)
        
    # --- PROPERTY CREDIT ($100 Pool) ---
    other_df = edited_df[edited_df["Category"] == "Other Property Charge"]
    total_other_charges = other_df["Amount"].sum()
    
    # Step A: Apply $100 credit to 'Other' charges first
    prop_credit_applied_to_other = min(total_other_charges, 100.0)
    remaining_prop_credit = 100.0 - prop_credit_applied_to_other
    
    # Step B: Apply remaining property credit to any breakfast overages
    prop_credit_applied_to_overage = min(total_breakfast_overage, remaining_prop_credit)
    final_remaining_prop_credit = remaining_prop_credit - prop_credit_applied_to_overage
    
    total_property_credit_to_post = prop_credit_applied_to_other + prop_credit_applied_to_overage
    total_credit_to_post = total_breakfast_credit + total_property_credit_to_post
    
    # Format overage column for display
    for day in breakdown:
        day["Uncovered Overage"] = f"${day['Uncovered Overage']:.2f}"
        
    # 4. Display Results
    st.markdown("---")
    st.success(f"### Total Credit to Post: **${total_credit_to_post:.2f}**")
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.metric("Breakfast Credit to Post", f"${total_breakfast_credit:.2f}")
    with col_b:
        st.metric(
            "Property Credit to Post", 
            f"${total_property_credit_to_post:.2f}", 
            help=f"${prop_credit_applied_to_other:.2f} to property charges, ${prop_credit_applied_to_overage:.2f} to breakfast overage."
        )
        
    if final_remaining_prop_credit > 0:
        st.info(f"Guest left **${final_remaining_prop_credit:.2f}** of their $100 property credit unused.")
        
    st.markdown("#### Daily Breakfast Breakdown")
    st.dataframe(pd.DataFrame(breakdown), use_container_width=True)
