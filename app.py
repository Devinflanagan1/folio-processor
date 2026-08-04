import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Folio Processor", layout="wide")
st.markdown("### Folio Processing")

# 1. Initialize permanent session state safely
if "folio_data" not in st.session_state:
    st.session_state.folio_data = [{"description": "Room Charge", "amount": 0.0}]

# 2. Input controls
uploaded_file = st.file_uploader("Upload spreadsheet (.csv or .xlsx)", type=["csv", "xlsx"])
pasted_data = st.text_area("Or paste copied folio text/lines here (one item and amount per line):", placeholder="Example:\nRoom Charge 250.00\nValet Parking 45.00")

if st.button("Process & Load Data"):
    new_items = []
    
    if pasted_data.strip():
        for line in pasted_data.split("\n"):
            clean_line = line.strip()
            if clean_line:
                amounts = re.findall(r'-?\d{1,3}(?:,\d{3})*\.\d{2}', clean_line)
                amount_val = 0.0
                if amounts:
                    try:
                        amount_val = float(amounts[-1].replace(",", ""))
                    except ValueError:
                        amount_val = 0.0
                # Remove the amount text from the description if desired, or keep clean line
                new_items.append({
                    "description": clean_line,
                    "amount": amount_val
                })
    elif uploaded_file is not None:
        try:
            filename = uploaded_file.name.lower()
            if filename.endswith(".csv"):
                df_upload = pd.read_csv(uploaded_file)
                new_items = df_upload.to_dict("records")
            elif filename.endswith(".xlsx"):
                df_upload = pd.read_excel(uploaded_file)
                new_items = df_upload.to_dict("records")
        except Exception as e:
            st.error(f"Error reading file: {e}")
            
    if new_items:
        st.session_state.folio_data = new_items
        st.success("Data loaded successfully!")
        st.rerun()

st.markdown("---")
st.markdown("#### Review & Edit Folio Items")

# 3. Filter out unwanted credit rows automatically
ignored_descriptions = ["AMEX Breakfast Credit", "THC AMEX CREDIT"]
valid_items = [
    item for item in st.session_state.folio_data 
    if isinstance(item, dict) and not any(ignored in str(item.get("description", "")) for ignored in ignored_descriptions)
]

if not valid_items:
    valid_items = [{"description": "Manual Entry", "amount": 0.0}]

df_display = pd.DataFrame(valid_items)

# 4. Interactive data editor tied securely to session state
edited_df = st.data_editor(
    df_display, 
    num_rows="dynamic", 
    use_container_width=True,
    key="main_folio_editor"
)

# Update session state dynamically when edits are made
if isinstance(edited_df, pd.DataFrame):
    st.session_state.folio_data = edited_df.to_dict("records")
