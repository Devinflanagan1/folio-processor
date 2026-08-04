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
st.info("Add your charge items below. Click 'Add Another Charge' to log additional lines safely without losing data.")

# Initialize secure session state list for charges
if "charge_list" not in st.session_state:
    st.session_state.charge_list = [
        {"date": arrival_date, "category": "Field Notes (Breakfast)", "amount": 0.0}
    ]

# Button to add a new row safely
if st.button("➕ Add Another Charge"):
    last_date = st.session_state.charge_list[-1]["date"] if st.session_state.charge_list else arrival_date
    st.session_state.charge_list.append(
        {"date": last_date, "category": "Field Notes (Breakfast)", "amount": 0.0}
    )

# Render inputs safely in standard form elements that never wipe on click
updated_charges = []
for i, item in enumerate(st.session_state.charge_list):
    cols = st.columns([2, 3, 2, 1])
    with cols[0]:
        c_date = st.date_input(f"Date {i}", value=item["date"], key=f"date_{i}", label_visibility="collapsed")
    with cols[1]:
        c_cat = st.selectbox(f"Category {i}", options=["Field Notes (Breakfast)", "Other Property Charge"], index=0 if item["category"] == "Field Notes (Breakfast)" else 1, key=f"cat_{i}", label_visibility="collapsed")
    with cols[2]:
        c_amt = st.number_input(f"Amount {i}", value=float(item["amount"]), min_value=0.0, step=0.01, format="%.2f", key=f"amt_{i}", label_visibility="collapsed")
    with cols[3]:
        if st.button("🗑️", key=f"del_{i}"):
            st.session_state.charge_list.pop(i)
            st.rerun()
            
    updated_charges.append({"date": c_date, "category": c_cat, "amount": c_amt})

st.session_state.charge_list = updated_charges

st.markdown("---")

# 2. Calculation Logic
if st.button("Calculate Credits", type="primary"):
    calc_df = pd.DataFrame(st.session_state.charge_list)
    
    if calc_df.empty:
        st.warning("Please add at least one charge.")
    else:
        total_breakfast_credit = 0.0
        total_breakfast_overage = 0.0
        breakdown = []
        
        # --- BREAKFAST CREDIT ($60/day non-rolling for stayed nights ONLY) ---
        breakfast_df = calc_df[calc_df["category"] == "Field Notes (Breakfast)"]
        
        arrival_breakfast_charges = breakfast_df[breakfast_df["date"] == arrival_date]["amount"].sum()
        
        valid_breakfast_df = breakfast_df[breakfast_df["date"] > arrival_date]
        daily_breakfast = valid_breakfast_df.groupby("date")["amount"].sum().reset_index()
        
        current_date = arrival_date + timedelta(days=1)
        while current_date <= departure_date:
            day_charge = daily_breakfast[daily_breakfast["date"] == current_date]["amount"].sum() if current_date in daily_breakfast["date"].values else 0.0
            
            eligible_credit = min(day_charge, 60.0)
            day_overage = max(0.0, day_charge - 60.0)
            
            total_breakfast_credit += eligible_credit
            total_breakfast_overage += day_overage
            
            breakdown.append({
                "Date": current_date.strftime("%Y-%m-%d"),
                "Breakfast Charged": f"${day_charge:.2f}",
                "Breakfast Credit Applied": f"${eligible_credit:.2f}",
                "Uncovered Overage": f"${day_overage:.2f}"
            })
            current_date += timedelta(days=1)
            
        # --- PROPERTY CREDIT ($100 Pool) ---
        other_df = calc_df[calc_df["category"] == "Other Property Charge"]
        total_other_charges = other_df["amount"].sum() + arrival_breakfast_charges
        
        prop_credit_applied_to_other = min(total_other_charges, 100.0)
        remaining_prop_credit = 100.0 - prop_credit_applied_to_other
        
        prop_credit_applied_to_overage = min(total_breakfast_overage, remaining_prop_credit)
        final_remaining_prop_credit = remaining_prop_credit - prop_credit_applied_to_overage
        
        total_property_credit_to_post = prop_credit_applied_to_other + prop_credit_applied_to_overage
        total_credit_to_post = total_breakfast_credit + total_property_credit_to_post
        
        # 3. Display Results
        st.success(f"### Total Credit to Post: **${total_credit_to_post:.2f}**")
        
        col_a, col_b = st.columns(2)
        with col_a:
            st.metric("Breakfast Credit to Post", f"${total_breakfast_credit:.2f}")
        with col_b:
            st.metric(
                "Property Credit to Post", 
                f"${total_property_credit_to_post:.2f}", 
                help=f"${prop_credit_applied_to_other:.2f} to property/arrival charges, ${prop_credit_applied_to_overage:.2f} to breakfast overage."
            )
            
        if arrival_breakfast_charges > 0:
            st.info(f"Note: **${arrival_breakfast_charges:.2f}** in Field Notes charges logged on the arrival date were automatically routed to the $100 property credit pool.")
            
        if final_remaining_prop_credit > 0:
            st.info(f"Guest left **${final_remaining_prop_credit:.2f}** of their $100 property credit unused.")
            
        st.markdown("#### Daily Breakfast Breakdown (Stayed Nights)")
        st.dataframe(pd.DataFrame(breakdown), use_container_width=True)
