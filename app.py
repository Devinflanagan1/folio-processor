import streamlit as st
import pandas as pd
from pypdf import PdfReader
import io

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
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    for line in text.split("\n"):
                        clean_line = line.strip()
                        if clean_line:
                            extracted_items.append({
                                "description": clean_line,
                                "amount": 0.0
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
    
    st.info("File loaded successfully. You can edit descriptions and amounts directly in the table below:")
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
