import streamlit as st
import pandas as pd
import pdfplumber

st.set_page_config(page_title="Folio Processor", layout="wide")
st.markdown("### Folio Processing")

uploaded_file = st.file_uploader("Upload your document (PDF or spreadsheet)", type=["pdf", "csv", "xlsx"])

if uploaded_file is not None:
    # --- ACTUAL PDF PARSING LOGIC ---
    if "items" not in st.session_state:
        extracted_items = []
        
        # Read the uploaded PDF using pdfplumber
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    # Split the page text into individual lines
                    lines = text.split("\n")
                    for line in lines:
                        # (Optional) Add custom logic here to parse columns like Date, Description, Amount
                        # For now, we add each text line as a description row to see it populate:
                        extracted_items.append({"description": line, "amount": 0.0})
                        
        st.session_state.items = extracted_items

    # --- FILTERING & DISPLAY LOGIC ---
    if "items" in st.session_state and st.session_state.items:
        ignored_descriptions = ["AMEX Breakfast Credit", "THC AMEX CREDIT"]
        
        filtered_items = [
            item for item in st.session_state.items 
            if not any(ignored in str(item.get("description", "")) for ignored in ignored_descriptions)
        ]
        
        df_items = pd.DataFrame(filtered_items)
        
        if not df_items.empty:
            edited_df = st.data_editor(
                df_items, 
                num_rows="dynamic", 
                use_container_width=True,
                key="folio_editor"
            )
            st.session_state.items = edited_df.to_dict("records")
        else:
            st.info("All line items were filtered out based on your criteria.")
    else:
        st.warning("The file was uploaded, but no text or line items could be extracted from this PDF format.")
else:
    if "items" in st.session_state:
        del st.session_state.items
        
    st.info("Please upload a file to begin editing the data.")
