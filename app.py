import streamlit as st
import pandas as pd
import io
import re
from PIL import Image
import pytesseract

st.set_page_config(page_title="Folio Processor", layout="wide")
st.markdown("### Folio Processing")

# Initialize session state
if "folio_data" not in st.session_state:
    st.session_state.folio_data = [{"description": "Manual Entry", "amount": 0.0}]

uploaded_file = st.file_uploader("Upload screenshot, image, or spreadsheet", type=["png", "jpg", "jpeg", "csv", "xlsx"])
pasted_data = st.text_area("Or paste copied folio text/lines here:", placeholder="Example:\nRoom Charge 250.00\nValet Parking 45.00")

# Require button click to process to prevent loop errors
if st.button("Process & Load Data"):
    new_items = []
    
    if pasted_data.strip():
        for line in pasted_data.split("\n"):
            clean_line = line.strip()
            if clean_line:
                amounts = re.findall(r'-?\d{1,3}(?:,\d{3})*\.\d{2}', clean_line)
                amount_val = 0.0
                if amounts:
                    try:
                        amount_val = float(amounts[-1].replace(",", ""))
                    except ValueError:
                        amount_val = 0.0
                new_items.append({
                    "description": clean_line,
                    "amount": amount_val
                })
                
    elif uploaded_file is not None:
        filename = uploaded_file.name.lower()
        
        # Screenshot / Image Processing
        if filename.endswith((".png", ".jpg", ".jpeg")):
            try:
                img = Image.open(io.BytesIO(uploaded_file.getvalue()))
                extracted_text = pytesseract.image_to_string(img)
                
                if extracted_text.strip():
                    for line in extracted_text.split("\n"):
                        clean_line = line.strip()
                        if clean_line:
                            amounts = re.findall(r'-?\d{1,3}(?:,\d{3})*\.\d{2}', clean_line)
                            amount_val = 0.0
                            if amounts:
                                try:
                                    amount_val = float(amounts[-1].replace(",", ""))
                                except ValueError:
                                    amount_val = 0.0
                            new_items.append({
                                "description": clean_line,
                                "amount": amount_val
                            })
                else:
                    new_items = [{"description": "No text found in image. Please try pasting.", "amount": 0.0}]
            except Exception as e:
                st.error(f"Image processing error. Ensure packages.txt has tesseract-ocr. Error: {e}")
                
        # Spreadsheet Processing
        elif filename.endswith(".csv"):
            df_upload = pd.read_csv(uploaded_file)
            new_items = df_upload.to_dict("records")
        elif filename.endswith(".xlsx"):
            df_upload = pd.read_excel(uploaded_file)
            new_items = df_upload.to_dict("records")
            
    if new_items:
        st.session_state.folio_data = new_items
        st.success("Data processed successfully!")
        st.rerun()

st.markdown("---")
st.markdown("#### Review & Edit Folio Items")

ignored_descriptions = ["AMEX Breakfast Credit", "THC AMEX CREDIT"]
valid_items = [
    item for item in st.session_state.folio_data 
    if isinstance(item, dict) and not any(ignored in str(item.get("description", "")) for ignored in ignored_descriptions)
]

if not valid_items:
    valid_items = [{"description": "Manual Entry", "amount": 0.0}]

df_display = pd.DataFrame(valid_items)

edited_df = st.data_editor(
    df_display, 
    num_rows="dynamic", 
    use_container_width=True,
    key="main_folio_editor"
)

if isinstance(edited_df, pd.DataFrame):
    st.session_state.folio_data = edited_df.to_dict("records")
