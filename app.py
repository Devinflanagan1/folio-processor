import streamlit as st
import pandas as pd
import pdfplumber
import re

st.set_page_config(page_title="Folio Processor", layout="wide")
st.markdown("### Folio Processing")

uploaded_file = st.file_uploader("Upload your document (PDF or spreadsheet)", type=["pdf", "csv", "xlsx"])

if uploaded_file is not None:
    # --- EXACT LAYOUT FOLIO PARSING ---
    if "items" not in st.session_state or not isinstance(st.session_state.items, list) or len(st.session_state.items) == 0:
        extracted_items = []
        
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    lines = text.split("\n")
                    i = 0
                    while i < len(lines):
                        line = lines[i].strip()
                        # Check if line starts with a date pattern (MM/DD/YYYY)
                        if re.match(r'^\d{2}/\d{2}/\d{4}', line):
                            date_str = line
                            description_parts = []
                            amount_str = "0.00"
                            
                            # Look ahead to grab the description text and amounts on following lines
                            i += 1
                            while i < len(lines):
                                next_line = lines[i].strip()
                                # Stop looking ahead if we hit another date or summary keyword
                                if re.match(r'^\d{2}/\d{2}/\d{4}', next_line) or "Total" in next_line or "Balance" in next_line:
                                    i -= 1 # Step back so the outer loop handles it next
                                    break
                                
                                # Check if the line contains a dollar amount
                                if "$" in next_line:
                                    amount_str = next_line
                                else:
                                    if next_line:
                                        description_parts.append(next_line)
                                i += 1
                            
                            full_description = f"{date_str} - " + " ".join(description_parts)
                            
                            # Clean up amount into a float value if possible
                            try:
                                clean_amt = float(amount_str.replace("$", "").replace(",", "").strip())
                            except ValueError:
                                clean_amt = 0.0
                                
                            extracted_items.append({
                                "description": full_description,
                                "amount": clean_amt
                            })
                        i += 1
                        
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
        st.warning("The file was uploaded, but no transaction rows could be matched.")
else:
    if "items" in st.session_state:
        del st.session_state.items
        
    st.info("Please upload a file to begin editing the data.")
