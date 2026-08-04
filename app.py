import streamlit as st
import pandas as pd
from pdf2image import convert_from_bytes
import pytesseract
import io
import re

st.set_page_config(page_title="Folio Processor", layout="wide")
st.markdown("### Folio Processing")

uploaded_file = st.file_uploader("Upload your document (PDF, Image, or spreadsheet)", type=["pdf", "png", "jpg", "jpeg", "csv", "xlsx"])

if uploaded_file is not None:
    if "current_file" not in st.session_state or st.session_state.current_file != uploaded_file.name:
        st.session_state.current_file = uploaded_file.name
        extracted_items = []
        bytes_data = uploaded_file.getvalue()
        
        full_text = ""
        
        # Handle PDFs (including locked/vector PDFs via OCR image conversion)
        if uploaded_file.name.lower().endswith(".pdf"):
            try:
                images = convert_from_bytes(bytes_data)
                for image in images:
                    text = pytesseract.image_to_string(image)
                    if text:
                        full_text += text + "\n"
            except Exception as e:
                extracted_items.append({"description": f"OCR Error: {str(e)}", "amount": 0.0})
                
        # Handle Direct Image Uploads (Snipping Tool / Screenshots)
        elif uploaded_file.name.lower().endswith((".png", ".jpg", ".jpeg")):
            try:
                from PIL import Image
                image = Image.open(io.BytesIO(bytes_data))
                full_text = pytesseract.image_to_string(image)
            except Exception as e:
                extracted_items.append({"description": f"Image Error: {str(e)}", "amount": 0.0})
                
        # Handle Spreadsheets
        elif uploaded_file.name.lower().endswith(".csv"):
            df_upload = pd.read_csv(uploaded_file)
            extracted_items = df_upload.to_dict("records")
        elif uploaded_file.name.lower().endswith(".xlsx"):
            df_upload = pd.read_excel(uploaded_file)
            extracted_items = df_upload.to_dict("records")

        # Parse text lines if we gathered text from PDF/OCR/Screenshot
        if full_text.strip():
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
            extracted_items = [{"description": "Manual Entry - No text found", "amount": 0.0}]
            
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
    
    st.info("Folio successfully processed via OCR/Upload. Review and edit items below:")
    
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
        
    st.info("Please upload a file or screenshot to begin.")
