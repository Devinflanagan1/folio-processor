import streamlit as st
import pandas as pd
import pdfplumber
import io
import re
from PIL import Image

st.set_page_config(page_title="Folio Processor", layout="wide")
st.markdown("### Folio Processing")

uploaded_file = st.file_uploader("Upload your document (PDF, Image, or Spreadsheet)", type=["pdf", "png", "jpg", "jpeg", "csv", "xlsx"])

if uploaded_file is not None:
    if "current_file" not in st.session_state or st.session_state.current_file != uploaded_file.name:
        st.session_state.current_file = uploaded_file.name
        extracted_items = []
        bytes_data = uploaded_file.getvalue()
        full_text = ""
        
        try:
            # 1. Handle PDF using pdfplumber (best for table layouts and hotel folios)
            if uploaded_file.name.lower().endswith(".pdf"):
                with pdfplumber.open(io.BytesIO(bytes_data)) as pdf:
                    for page in pdf.pages:
                        text = page.extract_text()
                        if text:
                            full_text += text + "\n"
                        # Also try extracting tables directly if text layer fails
                        tables = page.extract_tables()
                        for table in tables:
                            for row in table:
                                row_str = " ".join([str(cell) for cell in row if cell])
                                if row_str.strip():
                                    full_text += row_str + "\n"
                                    
            # 2. Handle Image Uploads via basic Pillow info check
            elif uploaded_file.name.lower().endswith((".png", ".jpg", ".jpeg")):
                img = Image.open(io.BytesIO(bytes_data))
                full_text = f"Image uploaded: {img.size[0]}x{img.size[1]} pixels. (Please paste folio text below if OCR isn't available)"
                
            # 3. Handle Spreadsheets
            elif uploaded_file.name.lower().endswith(".csv"):
                df_upload = pd.read_csv(io.BytesIO(bytes_data))
                extracted_items = df_upload.to_dict("records")
            elif uploaded_file.name.lower().endswith(".xlsx"):
                df_upload = pd.read_excel(io.BytesIO(bytes_data))
                extracted_items = df_upload.to_dict("records")
        except Exception as e:
            st.error(f"Processing Error: {str(e)}")

        # Parse text lines into items if we extracted text
        if full_text.strip() and not extracted_items:
            lines = [line.strip() for line in full_text.split("\n") if line.strip()]
            for line in lines:
                amounts = re.findall(r'-?\d{1,3}(?:,\d{3})*\.\d{2}', line)
                amount_val = 0.0
                if amounts:
                    try:
                        amount_val = float(amounts[-1].replace(",", ""))
                    except ValueError:
                        amount_val = 0.0
                        
                extracted_items.append({
                    "description": line,
                    "amount": amount_val
                })
                
        if not extracted_items:
            extracted_items = [{"description": "Manual Entry (Type or paste rows here)", "amount": 0.0}]
            
        st.session_state.items = extracted_items

    safe_items = st.session_state.items if isinstance(st.session_state.items, list) and len(st.session_state.items) > 0 else [{"description": "Manual Entry", "amount": 0.0}]

    ignored_descriptions = ["AMEX Breakfast Credit", "THC AMEX CREDIT"]
    filtered_items = [
        item for item in safe_items 
        if isinstance(item, dict) and not any(ignored in str(item.get("description", "")) for ignored in ignored_descriptions)
    ]
    
    if not filtered_items:
        filtered_items = [{"description": "Manual Entry", "amount": 0.0}]

    df_items = pd.DataFrame(filtered_items)
    
    st.info("Review and edit your folio items below:")
    
    edited_df = st.data_editor(
        df_items, 
        num_rows="dynamic", 
        use_container_width=True,
        key="folio_editor_main"
    )
    st.session_state.items = edited_df.to_dict("records")
else:
    if "items" in st.session_state:
        del st.session_state.items
    if "current_file" in st.session_state:
        del st.session_state.current_file
        
    st.info("Please upload a file to begin.")
