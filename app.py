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

if "prev_arrival" not in st.session_state:
    st.session_state.prev_arrival = arrival_date
    
if st.session_state.prev_arrival != arrival_date:
    st.session_state.base_data = pd.DataFrame([
        {"Date": arrival_date, "Category": "Field Notes (Breakfast)", "Amount": "0.00"}
    ])
    st.session_state.last_date = arrival_date
    st.session_state.prev_arrival = arrival_date
    if "charge_editor" in st.session_state:
        del st.session_state["charge_editor"]

st.markdown("---")
st.markdown("#### Enter Charges")
st.info("Log all eligible charges below. Note: Charges on the Arrival Date automatically route to the Property Credit pool since arrival day does not include a breakfast credit night.")

# 2. Setup Data Editor
if "base_data" not in st.session_state:
    st.session_state.base_data = pd.DataFrame([
        {"Date": arrival_date, "Category": "Field Notes (Breakfast)", "Amount": "0.00"}
    ])

if "last_date" not in st.session_state:
    st.session_state.last_date = arrival_date

edited_df = st.data_editor(
    st.session_state.base_data,
    num_rows="dynamic",
    column_config={
        "Date": st.column_config.DateColumn(
            "Charge Date", 
            default=st.session_state.last_date,
            format="YYYY-MM-DD"
        ),
        "Category": st.column_config.SelectboxColumn(
            "Category",
            options=["Field Notes (Breakfast)", "Other Property Charge"],
            required=True
        ),
        "Amount": st.column_config.TextColumn(
            "Amount ($)", 
            help="Enter the dollar amount (e.g. 34.59)"
        )
    },
    use_container_width=True,
    key="charge_editor"
)

if not edited_df.empty:
    try:
        st.session_state.last_date = pd.to_datetime(edited_df["Date"].iloc[-1]).date()
    except Exception:
        st.session_state.last_date = arrival_date

# 3. Calculation Logic
if st.button("Calculate Credits", type="primary"):
    calc_df = edited_df.copy()
    calc_df["Date"] = pd.to_datetime(calc_df["Date"]).dt.date
    
    def clean_amount(val):
        try:
            cleaned = str(val).replace("$", "").replace(",", "").strip()
            return float(cleaned) if cleaned else 0.0
        except ValueError:
            return 0.0
            
    calc_df["Amount_Num"] = calc_df["Amount"].apply(clean_amount)
    
    total_breakfast_credit = 0.0
    total_breakfast_overage = 0.0
    breakdown = []
    
    # --- BREAKFAST CREDIT ($60/day non-rolling for stayed nights ONLY) ---
    # Nights eligible for breakfast credit start the day AFTER arrival up through departure day
    breakfast_df = calc_df[calc_df["Category"] == "Field Notes (Breakfast)"]
    
    # Any breakfast charges on the exact arrival date are moved to property charges pool
    arrival_breakfast_charges = breakfast_df[breakfast_df["Date"] == arrival_date]["Amount_Num"].sum()
    
    valid_breakfast_df = breakfast_df[breakfast_df["Date"] > arrival_date]
    daily_breakfast = valid_breakfast_df.groupby("Date")["Amount_Num"].sum().reset_index()
    
    current_date = arrival_date + timedelta(days=1)
    while current_date <= departure_date:
        day_charge = daily_breakfast[daily_breakfast["Date"] == current_date]["Amount_Num"].sum() if current_date in daily_breakfast["Date"].values else 0.0
        
        eligible_credit = min(day_charge, 60.0)
        day_overage = max(0.0, day_charge - 60.0)
        
        total_breakfast_credit += eligible_credit
        total_breakfast_overage += day_overage
        
        breakdown.append({
            "Date": current_date.strftime("%Y-%m-%d"),
            "Breakfast Charged": f"${day_charge:.2f}",
            "Breakfast Credit Applied": f"${eligible_credit:.2f}",
            "Uncovered Overage": day_overage 
        })
        current_date += timedelta(days=1)
        
    # --- PROPERTY CREDIT ($100 Pool) ---
    other_df = calc_df[calc_df["Category"] == "Other Property Charge"]
    total_other_charges = other_df["Amount_Num"].sum() + arrival_breakfast_charges
    
    prop_credit_applied_to_other = min(total_other_charges, 100.0)
    remaining_prop_credit = 100.0 - prop_credit_applied_to_other
    
    prop_credit_applied_to_overage = min(total_breakfast_overage, remaining_prop_credit)
    final_remaining_prop_credit = remaining_prop_credit - prop_credit_applied_to_overage
    
    total_property_credit_to_post = prop_credit_applied_to_other + prop_credit_applied_to_overage
    total_credit_to_post = total_breakfast_credit + total_property_credit_to_post
    
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
            help=f"${prop_credit_applied_to_other:.2f} to property/arrival charges, ${prop_credit_applied_to_overage:.2f} to breakfast overage."
        )
        
    if arrival_breakfast_charges > 0:
        st.info(f"Note: **${arrival_breakfast_charges:.2f}** in Field Notes charges logged on the arrival date were automatically routed to the $100 property credit pool.")
        
    if final_remaining_prop_credit > 0:
        st.info(f"Guest left **${final_remaining_prop_credit:.2f}** of their $100 property credit unused.")
        
    st.markdown("#### Daily Breakfast Breakdown (Stayed Nights)")
    st.dataframe(pd.DataFrame(breakdown), use_container_width=True)
