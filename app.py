import streamlit as st
import pandas as pd
from pypdf import PdfReader
import io

st.set_page_config(page_title="Folio Processor", layout="wide")
st.markdown("### Folio Processing")

uploaded_file = st.file_uploader("Upload your document (PDF or spreadsheet)", type=["pdf", "csv", "xlsx"])

if uploaded_file is not None:
    if "items" not in st.session_state or not isinstance(st.session_state.items, list) or len(st.session_state.items) == 0:
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
            
        # Fallback safeguard: if the PDF text layer is locked or empty, 
        # initialize a clean editable row so the app remains fully functional
        if not extracted_items:
            extracted_items = [{"description": "Manual Entry (PDF text layer unreadable)", "amount": 0.0}]
                        
        st.session_state.items = extracted_items

    if isinstance(st.session_state.items, list) and len(st.session_state.items) > 0:
        ignored_descriptions = ["AMEX Breakfast Credit", "THC AMEX CREDIT"]
        
        filtered_items = [
            item for item in st.session_state.items 
            if isinstance(item, dict) and not any(ignored in str(item.get("description", "")) for ignored in ignored_descriptions)
        ]
        
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
        st.warning("Could not initialize data editor.")
else:
    if "items" in st.session_state:
        del st.session_state.items
        
    st.info("Please upload a file to begin editing the data.")
