import streamlit as st
import pandas as pd
from pypdf import PdfReader
import io
import re

st.set_page_config(page_title="Folio Processor", layout="wide")
st.markdown("### Folio Processing")

uploaded_file = st.file_uploader("Upload your document (PDF or spreadsheet)", type=["pdf", "csv", "xlsx"])

if uploaded_file is not None:
    if "current_file" not in st.session_state or st.session_state.current_file != uploaded_file.name:
        st.session_state.current_file = uploaded_file.name
        extracted_items = []
        bytes_data = uploaded_file.getvalue()
        
        try:
            reader = PdfReader(io.BytesIO(bytes_data))
            full_text = ""
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    full_text += text + "\n"
            
            # Look for lines that contain a date and potentially a dollar amount
            lines = [line.strip() for line in full_text.split("\n") if line.strip()]
            for line in lines:
                # Search for currency amounts in the line (e.g., 45.00, -207.00, 1,234.56)
                amounts = re.findall(r'-?\d{1,3}(?:,\d{3})*\.\d{2}', line)
                
                # Try to clean description by removing the matched amount and standard dates if present
                clean_desc = line
                amount_val = 0.0
                
                if amounts:
                    # Take the last found number on the line as the transaction amount
                    amount_str = amounts[-1]
                    try:
                        amount_val = float(amount_str.replace(",", ""))
                    except ValueError:
                        amount_val = 0.0
                        
                if line:
                    extracted_items.append({
                        "description": line,
                        "amount": amount_val
                    })
        except Exception:
            pass
            
        if not extracted_items:
            extracted_items = [{"description": "Manual Entry", "amount": 0.0}]
                        
        st.session_state.items = extracted_items

    if "items" not in st.session_state or not isinstance(st.session_state.items, list):
        st.session_state.items = [{"description": "Manual Entry", "amount": 0.0}]

    ignored_descriptions = ["AMEX Breakfast Credit", "THC AMEX CREDIT"]
    
    safe_items = st.session_state.items if isinstance(st.session_state.items, list) else [{"description": "Manual Entry", "amount": 0.0}]
    
    filtered_items = [
        item for item in safe_items 
        if isinstance(item, dict) and not any(ignored in str(item.get("description", "")) for ignored in ignored_descriptions)
    ]
    
    if not filtered_items:
        filtered_items = [{"description": "Manual Entry", "amount": 0.0}]

    df_items = pd.DataFrame(filtered_items)
    
    st.info("Folio loaded. Review the extracted descriptions and amounts below, and make adjustments as needed:")
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
    if "current_file" in st.session_state:
        del st.session_state.current_file
        
    st.info("Please upload a file to begin editing the data.")
