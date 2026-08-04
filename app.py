import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Folio Processor", layout="wide")
st.markdown("### Folio Processing")

uploaded_file = st.file_uploader("Upload spreadsheet or document", type=["pdf", "csv", "xlsx"])

pasted_data = st.text_area("Or paste copied folio text/lines here (one per line):", placeholder="Example:\nRoom Charge 250.00\nValet Parking 45.00")

extracted_items = []

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
            extracted_items.append({
                "description": clean_line,
                "amount": amount_val
            })
elif uploaded_file is not None:
    try:
        if uploaded_file.name.lower().endswith(".csv"):
            df_upload = pd.read_csv(uploaded_file)
            extracted_items = df_upload.to_dict("records")
        elif uploaded_file.name.lower().endswith(".xlsx"):
            df_upload = pd.read_excel(uploaded_file)
            extracted_items = df_upload.to_dict("records")
        elif uploaded_file.name.lower().endswith(".pdf"):
            extracted_items = [{
                "description": "PDF text is locked/vectorized. Please copy text from PDF and paste in the text box above.", 
                "amount": 0.0
            }]
    except Exception:
        pass

# Always ensure session state handles updates smoothly without resetting active edits
if "current_file" not in st.session_state or st.session_state.current_file != getattr(uploaded_file, "name", None) or pasted_data.strip():
    if extracted_items:
        st.session_state.items = extracted_items
    st.session_state.current_file = getattr(uploaded_file, "name", None)

if "items" not in st.session_state or not isinstance(st.session_state.items, list) or len(st.session_state.items) == 0:
    st.session_state.items = [{"description": "Manual Entry", "amount": 0.0}]

ignored_descriptions = ["AMEX Breakfast Credit", "THC AMEX CREDIT"]

filtered_items = [
    item for item in st.session_state.items 
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
st.session_state.items = edited_df.to_dict("records")
