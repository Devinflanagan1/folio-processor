import streamlit as st
import pandas as pd
import pdfplumber

st.set_page_config(page_title="Folio Processor", layout="wide")
st.markdown("### Folio Processing")

uploaded_file = st.file_uploader("Upload your document (PDF or spreadsheet)", type=["pdf", "csv", "xlsx"])

if uploaded_file is not None:
    # --- TABLE-BASED FOLIO PARSING ---
    if "items" not in st.session_state or not isinstance(st.session_state.items, list) or len(st.session_state.items) == 0:
        extracted_items = []
        
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                # Extract tables using layout analysis
                tables = page.extract_tables()
                for table in tables:
                    for row in table:
                        # Clean cells and join text parts
                        row_cells = [str(cell).strip() for cell in row if cell is not None and str(cell).strip() != ""]
                        if row_cells:
                            combined_text = " - ".join(row_cells)
                            extracted_items.append({
                                "description": combined_text,
                                "amount": 0.0
                            })
                
                # Fallback if no structured tables triggered: grab line blocks
                if not extracted_items:
                    text = page.extract_text()
                    if text:
                        for line in text.split("\n"):
                            clean_line = line.strip()
                            if clean_line:
                                extracted_items.append({
                                    "description": clean_line,
                                    "amount": 0.0
                                })
                                
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
        st.warning("The file was uploaded, but no content could be extracted.")
else:
    if "items" in st.session_state:
        del st.session_state.items
        
    st.info("Please upload a file to begin editing the data.")
