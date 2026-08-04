import streamlit as st
import pandas as pd

st.set_page_config(page_title="Folio Processor", layout="wide")
st.markdown("### Folio Processing")

uploaded_file = st.file_uploader("Upload your document (PDF or spreadsheet)", type=["pdf", "csv", "xlsx"])

if uploaded_file is not None:
    if "current_file" not in st.session_state or st.session_state.current_file != uploaded_file.name:
        st.session_state.current_file = uploaded_file.name
        
        # Parse spreadsheet directly if uploaded as CSV or Excel
        loaded_items = []
        try:
            if uploaded_file.name.lower().endswith(".csv"):
                df_upload = pd.read_csv(uploaded_file)
                loaded_items = df_upload.to_dict("records")
            elif uploaded_file.name.lower().endswith(".xlsx"):
                df_upload = pd.read_excel(uploaded_file)
                loaded_items = df_upload.to_dict("records")
        except Exception:
            pass
            
        if loaded_items:
            st.session_state.items = loaded_items
        else:
            st.session_state.items = [
                {"description": "Paste or type folio items here", "amount": 0.0}
            ]

    safe_items = st.session_state.items if isinstance(st.session_state.items, list) and len(st.session_state.items) > 0 else [{"description": "Paste or type folio items here", "amount": 0.0}]

    ignored_descriptions = ["AMEX Breakfast Credit", "THC AMEX CREDIT"]
    filtered_items = [
        item for item in safe_items 
        if isinstance(item, dict) and not any(ignored in str(item.get("description", "")) for ignored in ignored_descriptions)
    ]
    
    if not filtered_items:
        filtered_items = [{"description": "Paste or type folio items here", "amount": 0.0}]

    df_items = pd.DataFrame(filtered_items)
    
    st.info("Edit, add, or paste your folio line items and amounts directly below:")
    
    edited_df = st.data_editor(
        df_items, 
        num_rows="dynamic", 
        use_container_width=True,
        key="folio_editor_main"
    )
    st.session_state.items = edited_df.to_dict("records")
else:
    if "items" in st.session_state:
        del st.session_state.items
    if "current_file" in st.session_state:
        del st.session_state.current_file
        
    st.info("Please upload a file to begin.")
