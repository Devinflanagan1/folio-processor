import streamlit as st
import pandas as pd
import pdfplumber

st.set_page_config(page_title="Folio Processor", layout="wide")
st.markdown("### Folio Processing")

uploaded_file = st.file_uploader("Upload your document (PDF or spreadsheet)", type=["pdf", "csv", "xlsx"])

if uploaded_file is not None:
    # --- ROBUST PDF PARSING LOGIC ---
    if "items" not in st.session_state or not isinstance(st.session_state.items, list) or len(st.session_state.items) == 0:
        extracted_items = []
        
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                # First, try extracting tables (common in hotel folios)
                tables = page.extract_tables()
                if tables:
                    for table in tables:
                        for row in table:
                            # Clean up and map row cells if they contain text
                            row_text = " ".join([str(cell) for cell in row if cell])
                            if row_text.strip():
                                extracted_items.append({"description": row_text, "amount": 0.0})
                else:
                    # Fallback to plain text lines if no structured tables are found
                    text = page.extract_text()
                    if text:
                        for line in text.split("\n"):
                            if line.strip():
                                extracted_items.append({"description": line.strip(), "amount": 0.0})
                                
        st.session_state.items = extracted_items

    # --- SAFETY CHECK & FILTERING ---
    if isinstance(st.session_state.items, list) and len(st.session_state.items) > 0:
        ignored_descriptions = ["AMEX Breakfast Credit", "THC AMEX CREDIT"]
        
        filtered_items = [
            item for item in st.session_state.items 
            if isinstance(item, dict) and not any(ignored in str(item.get("description", "")) for ignored in ignored_descriptions)
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
        st.warning("The file was uploaded, but no valid text or tables could be extracted from this PDF format.")
else:
    if "items" in st.session_state:
        del st.session_state.items
        
    st.info("Please upload a file to begin editing the data.")
