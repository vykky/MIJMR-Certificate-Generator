import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import io
import zipfile
import textwrap

# பக்கத்தின் தலைப்பு
st.set_page_config(page_title="MIJMR Certificate Generator", layout="wide")
st.title("🎓 MIJMR Bulk Certificate Generator")

# இடதுபுறம் ஃபைல்களை அப்லோட் செய்யும் வசதி
st.sidebar.header("📂 1. ஃபைல்களை அப்லோட் செய்யவும்")
template_file = st.sidebar.file_uploader("Blank Certificate (PNG/JPG)", type=["png", "jpg", "jpeg"])
font_file = st.sidebar.file_uploader("Font File (.ttf)", type=["ttf"])
data_file = st.sidebar.file_uploader("Excel File (Data)", type=["xlsx", "csv"])

# எழுத்துக்கள் வர வேண்டிய இடத்தை செட் செய்யும் வசதி (Y-Axis)
st.sidebar.header("📏 2. அளவுகளை சரிசெய்ய (Coordinates)")
name_y = st.sidebar.number_input("பெயர் வரும் இடம் (Y-Axis)", value=600, step=10)
title_y = st.sidebar.number_input("பாராக்ராப் வரும் இடம் (Y-Axis)", value=800, step=10)
doi_y = st.sidebar.number_input("DOI & ISSN வரும் இடம் (Y-Axis)", value=1250, step=10)
date_x = st.sidebar.number_input("தேதி வரும் இடம் (X-Axis)", value=400, step=10)
date_y = st.sidebar.number_input("தேதி வரும் இடம் (Y-Axis)", value=1450, step=10)

# ஃபான்ட் சைஸ்
st.sidebar.header("🔠 3. எழுத்தின் அளவு (Font Size)")
name_size = st.sidebar.number_input("பெயரின் அளவு", value=120)
text_size = st.sidebar.number_input("பாராக்ராப் அளவு", value=45)

# அப்லோட் செய்த பிறகு வேலை தொடங்கும் இடம்
if template_file and font_file and data_file:
    # எக்செல் டேட்டாவை படிப்பது
    if data_file.name.endswith('.csv'):
        df = pd.read_csv(data_file)
    else:
        df = pd.read_excel(data_file)
        
    st.write("📊 **அப்லோட் செய்யப்பட்ட தகவல்கள் (Preview):**")
    st.dataframe(df.head())
    
    if st.button("🚀 Generate Certificates (சர்டிபிகேட்களை உருவாக்கு)"):
        with st.spinner('சான்றிதழ்கள் தயாராகி வருகின்றன...'):
            zip_buffer = io.BytesIO()
            
            with zipfile.ZipFile(zip_buffer, "w") as zip_file:
                for index, row in df.iterrows():
                    img = Image.open(template_file)
                    draw = ImageDraw.Draw(img)
                    
                    font_name = ImageFont.truetype(font_file, name_size)
                    font_text = ImageFont.truetype(font_file, text_size)
                    
                    # எக்செல் ஷீட்டில் இருந்து தகவல்களை எடுத்தல்
                    author_name = str(row.get('Name', f'Author_{index}'))
                    title = str(row.get('Title', ''))
                    vol = str(row.get('Volume', ''))
                    issue = str(row.get('Issue', ''))
                    doi = str(row.get('DOI', ''))
                    date = str(row.get('Date', ''))
                    
                    # மையத்தில் எழுத்துக்களை அச்சிடுவதற்கான ஃபங்க்ஷன்
                    def draw_centered_text(y_pos, text, font, fill_color):
                        bbox = draw.textbbox((0, 0), text, font=font)
                        text_width = bbox[2] - bbox[0]
                        x_pos = (img.width - text_width) / 2
                        draw.text((x_pos, y_pos), text, font=font, fill=fill_color)
                        
                    # 1. பெயரை அச்சிடுதல் (பச்சை நிறத்தில்)
                    draw_centered_text(name_y, author_name, font_name, "#00796B")
                    
                    # 2. பாராக்ராப்பை உருவாக்குதல்
                    full_text = f'For the successful publication of the research paper titled "{title}" in Volume {vol}, Issue {issue}. This work has been rigorously peer-reviewed and published under the guidelines of academic excellence.'
                    
                    # பாராக்ராப்பை வரியாக உடைத்தல் (Word Wrap)
                    wrapped_text = textwrap.wrap(full_text, width=85)
                    current_y = title_y
                    for line in wrapped_text:
                        draw_centered_text(current_y, line, font_text, "black")
                        current_y += (text_size + 15) # அடுத்த வரிக்கு இடைவெளி
                        
                    # 3. DOI மற்றும் Date அச்சிடுதல்
                    draw.text((250, doi_y), f"ISSN: 3139-2571  |  DOI: {doi}", font=font_text, fill="black")
                    draw.text((date_x, date_y), date, font=font_text, fill="black")
                    
                    # PDF ஆக மாற்றி Zip ஃபைலில் சேர்ப்பது
                    img_bytes = io.BytesIO()
                    img.save(img_bytes, format="PDF", resolution=300.0)
                    zip_file.writestr(f"{author_name}_Certificate.pdf", img_bytes.getvalue())
            
            st.success("✅ அனைத்து சான்றிதழ்களும் வெற்றிகரமாக உருவாக்கப்பட்டுவிட்டன!")
            st.download_button(
                label="📥 Download All Certificates (ZIP ஃபைலாக தரவிறக்க)",
                data=zip_buffer.getvalue(),
                file_name="MIJMR_Certificates.zip",
                mime="application/zip"
            )
else:
    st.info("👈 இடதுபுறம் உள்ள மெனுவில் Blank Image, Font மற்றும் Excel ஃபைலை அப்லோட் செய்யவும்.")
