import streamlit as st
import pandas as pd

st.set_page_config(page_title="Folio Processor", layout="wide")
st.markdown("### Folio Processing")

uploaded_file = st.file_uploader("Upload your document (PDF or spreadsheet)", type=["pdf", "csv", "xlsx"])

if uploaded_file is not None:
    # Initialize session state data if not present
    if "items" not in st.session_state or not isinstance(st.session_state.items, list) or len(st.session_state.items) == 0:
        st.session_state.items = [
            {"description": "Room Charge", "amount": 0.0},
            {"description": "Lodging Tax", "amount": 0.0}
        ]

    ignored_descriptions = ["AMEX Breakfast Credit", "THC AMEX CREDIT"]
    
    safe_items = st.session_state.items if isinstance(st.session_state.items, list) else [{"description": "Manual Entry", "amount": 0.0}]
    
    filtered_items = [
        item for item in safe_items 
        if isinstance(item, dict) and not any(ignored in str(item.get("description", "")) for ignored in ignored_descriptions)
    ]
    
    if not filtered_items:
        filtered_items = [{"description": "Manual Entry", "amount": 0.0}]

    df_items = pd.DataFrame(filtered_items)
    
    st.info("File uploaded. Review, edit, add, or delete line items directly in the interactive table below:")
    
    edited_df = st.data_editor(
        df_items, 
        num_rows="dynamic", 
        use_container_width=True,
        key="folio_editor"
    )
    st.session_state.items = edited_df.to_dict("records")
else:
    if "items" in st.session_state:
        del st.session_state.items
        
    st.info("Please upload a file to begin.")
