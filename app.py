import streamlit as st
import pandas as pd
import pdfplumber
import io
import re

st.set_page_config(page_title="Folio Processor", layout="wide")
st.markdown("### Folio Processing")

uploaded_file = st.file_uploader("Upload your document (PDF or spreadsheet)", type=["pdf", "csv", "xlsx"])

if uploaded_file is not None:
    if "items" not in st.session_state or not isinstance(st.session_state.items, list) or len(st.session_state.items) == 0:
        extracted_items = []
        bytes_data = uploaded_file.getvalue()
        
        with pdfplumber.open(io.BytesIO(bytes_data)) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    lines = [line.strip() for line in text.split("\n") if line.strip()]
                    i = 0
                    while i < len(lines):
                        line = lines[i]
                        # Look for lines starting with a date (e.g., 07/31/2026)
                        if re.match(r'^\d{2}/\d{2}/\d{4}$', line):
                            date_str = line
                            desc_parts = []
                            amount_val = 0.0
                            
                            i += 1
                            # Read subsequent lines until we hit another date or a total/tax section
                            while i < len(lines):
                                next_line = lines[i]
                                if re.match(r'^\d{2}/\d{2}/\d{4}$', next_line) or "Total" in next_line or "Balance" in next_line or "Tax" in next_line:
                                    i -= 1
                                    break
                                
                                if "$" in next_line:
                                    # Clean and parse amount string like "$ 34.59" or "\$-207.00"
                                    clean_amt_str = next_line.replace("$", "").replace("\\", "").replace(",", "").strip()
                                    try:
                                        amount_val = float(clean_amt_str)
                                    except ValueError:
                                        pass
                                else:
                                    desc_parts.append(next_line)
                                i += 1
                            
                            full_desc = f"{date_str} - " + " ".join(desc_parts)
                            extracted_items.append({
                                "description": full_desc,
                                "amount": amount_val
                            })
                        i += 1
                        
        st.session_state.items = extracted_items

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
        st.warning("Could not match the date-led line structure.")
else:
    if "items" in st.session_state:
        del st.session_state.items
        
    st.info("Please upload a file to begin editing the data.")
