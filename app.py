import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import io
import zipfile
import textwrap
import pdfplumber

st.set_page_config(page_title="MIJMR Certificate Generator", layout="wide")
st.title("🎓 MIJMR Bulk Certificate Generator")

# இடதுபுறம் ஃபைல்களை அப்லோட் செய்யும் வசதி
st.sidebar.header("📂 1. அடிப்படை ஃபைல்கள்")
template_file = st.sidebar.file_uploader("Blank Certificate (PNG/JPG)", type=["png", "jpg", "jpeg"])
font_file = st.sidebar.file_uploader("Font File (.ttf)", type=["ttf"])

# எழுத்துக்கள் வர வேண்டிய இடத்தை செட் செய்யும் வசதி (சிறிய இமேஜுக்கு ஏற்ற அளவுகள்)
st.sidebar.header("📏 2. அளவுகளை சரிசெய்ய (Coordinates)")
name_y = st.sidebar.number_input("பெயர் வரும் இடம் (Y-Axis)", value=250, step=10)
title_y = st.sidebar.number_input("பாராக்ராப் வரும் இடம் (Y-Axis)", value=320, step=10)
doi_y = st.sidebar.number_input("DOI & ISSN வரும் இடம் (Y-Axis)", value=550, step=10)
date_x = st.sidebar.number_input("தேதி வரும் இடம் (X-Axis)", value=150, step=10)
date_y = st.sidebar.number_input("தேதி வரும் இடம் (Y-Axis)", value=600, step=10)

st.sidebar.header("🔠 3. எழுத்தின் அளவு மற்றும் நீளம்")
name_size = st.sidebar.number_input("பெயரின் அளவு (Font Size)", value=40)
text_size = st.sidebar.number_input("பாராக்ராப் அளவு (Font Size)", value=18)
wrap_width = st.sidebar.number_input("ஒரு வரியின் நீளம் (Word Wrap)", value=60, help="இந்த எண்ணைக் குறைத்தால் வார்த்தைகள் அடுத்த வரிக்கு மடங்கி வரும்")

st.subheader("📄 ஆராய்ச்சிக் கட்டுரைகளை (PDF) அப்லோட் செய்யவும்")
uploaded_pdfs = st.file_uploader("எத்தனை PDF ஃபைல்கள் வேண்டுமானாலும் தேர்ந்தெடுக்கலாம்", type="pdf", accept_multiple_files=True)

if template_file and font_file and uploaded_pdfs:
    extracted_data = []
    
    for pdf_file in uploaded_pdfs:
        try:
            with pdfplumber.open(pdf_file) as pdf:
                first_page = pdf.pages[0]
                text = first_page.extract_text()
                lines = text.split('\n') if text else []
                
                title = lines[0] if len(lines) > 0 else "Title"
                author = lines[1] if len(lines) > 1 else "Name"
                
                extracted_data.append({
                    "File Name": pdf_file.name, 
                    "Name": author, 
                    "Title": title, 
                    "Volume": "1", 
                    "Issue": "1", 
                    "DOI": "", 
                    "Date": "20-May-2026"
                })
        except Exception as e:
            st.error(f"{pdf_file.name} ஃபைலை படிப்பதில் பிழை ஏற்பட்டது.")

    df = pd.DataFrame(extracted_data)
    
    # மிக முக்கியம்: இங்கே தான் நீங்கள் பெயரைச் சரிபார்க்க வேண்டும்!
    st.markdown("### ⚠️ மிக முக்கியம்: கீழே உள்ள கட்டத்தில் பெயரையும் தலைப்பையும் சரிபார்த்து திருத்தவும்!")
    edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)
    
    if st.button("🚀 Generate Certificates (சர்டிபிகேட்களை உருவாக்கு)"):
        with st.spinner('சான்றிதழ்கள் தயாராகி வருகின்றன...'):
            zip_buffer = io.BytesIO()
            
            template_bytes = template_file.getvalue()
            font_bytes = font_file.getvalue()
            
            with zipfile.ZipFile(zip_buffer, "w") as zip_file:
                for index, row in edited_df.iterrows():
                    
                    img = Image.open(io.BytesIO(template_bytes))
                    draw = ImageDraw.Draw(img)
                    
                    font_name = ImageFont.truetype(io.BytesIO(font_bytes), name_size)
                    font_text = ImageFont.truetype(io.BytesIO(font_bytes), text_size)
                    
                    author_name = str(row['Name'])
                    title = str(row['Title'])
                    vol = str(row['Volume'])
                    issue = str(row['Issue'])
                    doi = str(row['DOI'])
                    date = str(row['Date'])
                    
                    def draw_centered_text(y_pos, text, font, fill_color):
                        bbox = draw.textbbox((0, 0), text, font=font)
                        text_width = bbox[2] - bbox[0]
                        x_pos = (img.width - text_width) / 2
                        draw.text((x_pos, y_pos), text, font=font, fill=fill_color)
                        
                    # 1. பெயரை அச்சிடுதல்
                    draw_centered_text(name_y, author_name, font_name, "#00796B")
                    
                    # 2. பாராக்ராப்பை உருவாக்குதல்
                    full_text = f'For the successful publication of the research paper titled "{title}" in Volume {vol}, Issue {issue}. This work has been rigorously peer-reviewed and published under the guidelines of academic excellence.'
                    
                    # நீளத்தைக் கட்டுப்படுத்த Word Wrap
                    wrapped_text = textwrap.wrap(full_text, width=wrap_width)
                    current_y = title_y
                    for line in wrapped_text:
                        draw_centered_text(current_y, line, font_text, "black")
                        current_y += (text_size + 10)
                        
                    # 3. DOI மற்றும் Date அச்சிடுதல்
                    doi_text = f"ISSN: 3139-2571  |  DOI: {doi}" if doi else "ISSN: 3139-2571"
                    draw.text((250, doi_y), doi_text, font=font_text, fill="black")
                    draw.text((date_x, date_y), date, font=font_text, fill="black")
                    
                    img_bytes = io.BytesIO()
                    img.save(img_bytes, format="PDF", resolution=300.0)
                    zip_file.writestr(f"{author_name}_Certificate.pdf", img_bytes.getvalue())
            
            st.success("✅ அனைத்து சான்றிதழ்களும் வெற்றிகரமாக உருவாக்கப்பட்டுவிட்டன!")
            st.download_button(
                label="📥 Download All Certificates",
                data=zip_buffer.getvalue(),
                file_name="MIJMR_Certificates.zip",
                mime="application/zip"
            )
else:
    st.info("👈 இடதுபுறம் Blank Image, Font மற்றும் நடுவில் PDF ஃபைல்களை அப்லோட் செய்யவும்.")
