import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import io
import textwrap
import pdfplumber

st.set_page_config(page_title="MIJMR Certificate Generator", layout="wide")
st.title("🎓 MIJMR Certificate Generator (JPG Output)")

# 1. ஃபைல்களை அப்லோட் செய்யும் வசதி
st.sidebar.header("📂 1. அடிப்படை ஃபைல்கள்")
template_file = st.sidebar.file_uploader("Blank Certificate (PNG/JPG)", type=["png", "jpg", "jpeg"])
font_file = st.sidebar.file_uploader("Font File (.ttf)", type=["ttf"])

# 2. அளவுகளை சரிசெய்யும் வசதி
st.sidebar.header("📏 2. அளவுகளை சரிசெய்ய (Coordinates)")
name_y = st.sidebar.number_input("பெயர் வரும் இடம் (Y-Axis)", value=250, step=10)
title_y = st.sidebar.number_input("பாராக்ராப் வரும் இடம் (Y-Axis)", value=320, step=10)

# DOI-க்கான X மற்றும் Y அளவுகள் தனித்தனியாக
doi_x = st.sidebar.number_input("DOI வரும் இடம் (X-Axis)", value=350, step=10)
doi_y = st.sidebar.number_input("DOI வரும் இடம் (Y-Axis)", value=550, step=10)

date_x = st.sidebar.number_input("தேதி வரும் இடம் (X-Axis)", value=150, step=10)
date_y = st.sidebar.number_input("தேதி வரும் இடம் (Y-Axis)", value=600, step=10)

# 3. எழுத்தின் அளவு
st.sidebar.header("🔠 3. எழுத்தின் அளவு மற்றும் நீளம்")
name_size = st.sidebar.number_input("பெயரின் அளவு (Font Size)", value=40)
text_size = st.sidebar.number_input("பாராக்ராப் அளவு (Font Size)", value=18)
wrap_width = st.sidebar.number_input("ஒரு வரியின் நீளம் (Word Wrap)", value=60)

st.subheader("📄 கட்டுரைகளை (PDF) அப்லோட் செய்யவும்")
uploaded_pdfs = st.file_uploader("PDF ஃபைல்களைத் தேர்ந்தெடுக்கவும்", type="pdf", accept_multiple_files=True)

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
    
    st.markdown("### ⚠️ மிக முக்கியம்: கீழே உள்ள கட்டத்தில் பெயரையும் தலைப்பையும் சரிபார்த்து திருத்தவும்!")
    edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)
    
    if st.button("🚀 Generate Certificates"):
        with st.spinner('சான்றிதழ்கள் தயாராகி வருகின்றன...'):
            template_bytes = template_file.getvalue()
            font_bytes = font_file.getvalue()
            
            for index, row in edited_df.iterrows():
                
                img = Image.open(io.BytesIO(template_bytes))
                # JPG ஆக மாற்றுவதற்காக RGBA மோடில் இருந்து RGB ஆக மாற்றுகிறோம்
                if img.mode == 'RGBA':
                    img = img.convert('RGB')
                    
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
                
                wrapped_text = textwrap.wrap(full_text, width=wrap_width)
                current_y = title_y
                for line in wrapped_text:
                    draw_centered_text(current_y, line, font_text, "black")
                    current_y += (text_size + 10)
                    
                # 3. DOI மற்றும் Date அச்சிடுதல் (DOI நம்பரை மட்டும் அச்சிடுகிறோம்)
                if doi:
                    draw.text((doi_x, doi_y), doi, font=font_text, fill="black")
                draw.text((date_x, date_y), date, font=font_text, fill="black")
                
                # 4. திரையில் காட்டுவது மற்றும் JPG ஆக டவுன்லோட் செய்யும் பட்டன்
                st.image(img, caption=f"{author_name} - Certificate", use_container_width=True)
                
                img_bytes = io.BytesIO()
                img.save(img_bytes, format="JPEG", quality=95)
                
                st.download_button(
                    label=f"📥 Download {author_name} Certificate (JPG)",
                    data=img_bytes.getvalue(),
                    file_name=f"{author_name}_Certificate.jpg",
                    mime="image/jpeg",
                    key=f"download_{index}"
                )
                
            st.success("✅ சான்றிதழ்கள் தயார்! மேலே உள்ள பட்டன்களைப் பயன்படுத்தி JPG ஆகத் தரவிறக்கம் செய்துகொள்ளலாம்.")
else:
    st.info("👈 இடதுபுறம் Blank Image, Font மற்றும் நடுவில் PDF ஃபைல்களை அப்லோட் செய்யவும்.")
