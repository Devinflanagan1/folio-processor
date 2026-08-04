import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
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
        
        # Handle PDF Files
        if uploaded_file.name.lower().endswith(".pdf"):
            try:
                # Open PDF with PyMuPDF
                doc = fitz.open(stream=bytes_data, filetype="pdf")
                full_text = ""
                for page in doc:
                    full_text += page.get_text("text") + "\n"
                
                # Process extracted text
                lines = [line.strip() for line in full_text.split("\n") if line.strip()]
                for line in lines:
                    amounts = re.findall(r'-?\d{1,3}(?:,\d{3})*\.\d{2}', line)
                    amount_val = 0.0
                    
                    if amounts:
                        amount_str = amounts[-1]
                        try:
                            amount_val = float(amount_str.replace(",", ""))
                        except ValueError:
                            amount_val = 0.0
                            
                    extracted_items.append({
                        "description": line,
                        "amount": amount_val
                    })
            except Exception:
                pass
        
        # Handle CSV or Excel fallback
        elif uploaded_file.name.lower().endswith(".csv"):
            df = pd.read_csv(uploaded_file)
            extracted_items = df.to_dict("records")
        elif uploaded_file.name.lower().endswith(".xlsx"):
            df = pd.read_excel(uploaded_file)
            extracted_items = df.to_dict("records")

        # Fallback if entirely unreadable
        if not extracted_items:
            extracted_items = [{"description": "Manual Entry (No text extracted)", "amount": 0.0}]
                        
        st.session_state.items = extracted_items

    # Safety checks for session state formatting
    if "items" not in st.session_state or not isinstance(st.session_state.items, list):
        st.session_state.items = [{"description": "Manual Entry", "amount": 0.0}]

    ignored_descriptions = ["AMEX Breakfast Credit", "THC AMEX CREDIT"]
    safe_items = st.session_state.items if isinstance(st.session_state.items, list) else [{"description": "Manual Entry", "amount": 0.0}]
    
    # Filter out ignored terms
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
    # Clear state when file is removed
    if "items" in st.session_state:
        del st.session_state.items
    if "current_file" in st.session_state:
        del st.session_state.current_file
        
    st.info("Please upload a file to begin editing the data.")
