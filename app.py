import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Folio Processor", layout="wide")
st.markdown("### Folio Processing")

uploaded_file = st.file_uploader("Upload spreadsheet or document", type=["pdf", "csv", "xlsx"])

pasted_data = st.text_area("Or paste copied folio text/lines here (one per line):", placeholder="Example:\nRoom Charge 250.00\nValet Parking 45.00")

# Initialize session state for items securely if not present
if "items" not in st.session_state or not isinstance(st.session_state.items, list):
    st.session_state.items = [{"description": "Manual Entry", "amount": 0.0}]

# Handle text area input
if pasted_data.strip():
    new_items = []
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
            new_items.append({
                "description": clean_line,
                "amount": amount_val
            })
    if new_items:
        st.session_state.items = new_items

# Handle file upload input
elif uploaded_file is not None:
    current_filename = getattr(uploaded_file, "name", None)
    if "current_file" not in st.session_state or st.session_state.current_file != current_filename:
        st.session_state.current_file = current_filename
        file_items = []
        try:
            if current_filename.lower().endswith(".csv"):
                df_upload = pd.read_csv(uploaded_file)
                file_items = df_upload.to_dict("records")
            elif current_filename.lower().endswith(".xlsx"):
                df_upload = pd.read_excel(uploaded_file)
                file_items = df_upload.to_dict("records")
            elif current_filename.lower().endswith(".pdf"):
                file_items = [{
                    "description": "PDF text is locked/vectorized. Please copy text from PDF and paste it in the text box above.", 
                    "amount": 0.0
                }]
        except Exception:
            pass
        
        if file_items:
            st.session_state.items = file_items

ignored_descriptions = ["AMEX Breakfast Credit", "THC AMEX CREDIT"]

safe_items = st.session_state.items if isinstance(st.session_state.items, list) else [{"description": "Manual Entry", "amount": 0.0}]

filtered_items = [
    item for item in safe_items 
    if isinstance(item, dict) and not any(ignored in str(item.get("description", "")) for ignored in ignored_descriptions)
]

if not filtered_items:
    filtered_items = [{"description": "Manual Entry", "amount": 0.0}]

df_items = pd.DataFrame(filtered_items)

st.markdown("---")
st.info("Review and edit your folio items below:")

edited_df = st.data_editor(
    df_items, 
    num_rows="dynamic", 
    use_container_width=True,
    key="folio_editor_main"
)

if isinstance(edited_df, pd.DataFrame):
    st.session_state.items = edited_df.to_dict("records")
