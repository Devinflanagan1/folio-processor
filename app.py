import streamlit as st
import pandas as pd

# Page Configuration
st.set_page_config(page_title="Folio Processor", layout="wide")

st.markdown("### Folio Processing")

# 1. File uploader widget
uploaded_file = st.file_uploader("Upload your document (PDF or spreadsheet)", type=["pdf", "csv", "xlsx"])

# 2. Only process if a file is uploaded
if uploaded_file is not None:
    # ---------------------------------------------------------
    # TODO: INSERT YOUR PDF / FILE PARSING LOGIC HERE
    # This should read 'uploaded_file' and store a list of dictionaries into st.session_state.items
    # Example format:
    # st.session_state.items = [
    #     {"date": "2026-06-01", "description": "Room Charge", "amount": 250.0},
    #     {"date": "2026-06-02", "description": "AMEX Breakfast Credit", "amount": -40.0}
    # ]
    # ---------------------------------------------------------
    
    # 3. Check if items exist and are loaded correctly
    if "items" in st.session_state and st.session_state.items:
        # Define line items to automatically ignore/filter out for testing
        ignored_descriptions = ["AMEX Breakfast Credit", "THC AMEX CREDIT"]
        
        # Filter out the matching rows
        filtered_items = [
            item for item in st.session_state.items 
            if not any(ignored in str(item.get("description", "")) for ignored in ignored_descriptions)
        ]
        
        df_items = pd.DataFrame(filtered_items)
        
        # 4. Render data editor if dataframe is not empty
        if not df_items.empty:
            edited_df = st.data_editor(
                df_items, 
                num_rows="dynamic", 
                use_container_width=True,
                key="folio_editor"
            )
            # Save updates back to session state
            st.session_state.items = edited_df.to_dict("records")
        else:
            st.info("All line items were filtered out based on your criteria.")
    else:
        st.warning("The file was uploaded, but no line items could be extracted.")
else:
    # Clear session state when no file is present to prevent leftover cache issues
    if "items" in st.session_state:
        del st.session_state.items
        
    st.info("Please upload a file to begin editing the data.")
