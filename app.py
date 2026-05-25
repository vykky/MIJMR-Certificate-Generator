import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import io
import textwrap
import pdfplumber
import re
from datetime import datetime

st.set_page_config(page_title="MIJMR Certificate Generator", layout="wide")
st.title("🎓 MIJMR Certificate Generator (4K & Auto-Extract)")

# 1. ஃபைல்களை அப்லோட் செய்யும் வசதி
st.sidebar.header("📂 1. அடிப்படை ஃபைல்கள்")
template_file = st.sidebar.file_uploader("Blank Certificate (PNG/JPG)", type=["png", "jpg", "jpeg"])
font_file = st.sidebar.file_uploader("Font File (.ttf)", type=["ttf"])

# 2. அளவுகளை சரிசெய்யும் வசதி (Original இமேஜின் படி)
st.sidebar.header("📏 2. அளவுகளை சரிசெய்ய (Coordinates)")
name_y = st.sidebar.number_input("பெயர் வரும் இடம் (Y-Axis)", value=250, step=10)
title_y = st.sidebar.number_input("பாராக்ராப் வரும் இடம் (Y-Axis)", value=320, step=10)

# DOI-க்கான X மற்றும் Y அளவுகள் தனித்தனியாக
doi_x = st.sidebar.number_input("DOI வரும் இடம் (X-Axis)", value=280, step=10)
doi_y = st.sidebar.number_input("DOI வரும் இடம் (Y-Axis)", value=550, step=10)

date_x = st.sidebar.number_input("தேதி வரும் இடம் (X-Axis)", value=150, step=10)
date_y = st.sidebar.number_input("தேதி வரும் இடம் (Y-Axis)", value=600, step=10)

# 3. எழுத்தின் அளவு
st.sidebar.header("🔠 3. எழுத்தின் அளவு மற்றும் நீளம்")
name_size = st.sidebar.number_input("பெயரின் அளவு (Font Size)", value=40)
text_size = st.sidebar.number_input("பாராக்ராப் அளவு (Font Size)", value=18)
wrap_width = st.sidebar.number_input("ஒரு வரியின் நீளம் (Word Wrap)", value=70)

st.subheader("📄 கட்டுரைகளை (PDF) அப்லோட் செய்யவும்")
uploaded_pdfs = st.file_uploader("PDF ஃபைல்களைத் தேர்ந்தெடுக்கவும்", type="pdf", accept_multiple_files=True)

# PDF லிருந்து தகவல்களைப் பிரித்தெடுக்கும் ஸ்மார்ட் ஃபங்க்ஷன்
# PDF லிருந்து தகவல்களைப் பிரித்தெடுக்கும் ஸ்மார்ட் ஃபங்க்ஷன் (Smart AI Logic)
# PDF லிருந்து தகவல்களைப் பிரித்தெடுக்கும் ஸ்மார்ட் ஃபங்க்ஷன் (Multiple Authors Update)
def clean_pdf_text(pdf_file):
    try:
        with pdfplumber.open(pdf_file) as pdf:
            text = pdf.pages[0].extract_text()
            if not text: return "Title Not Found", ["Name Not Found"], ""
            
            lines = [l.strip() for l in text.split('\n') if l.strip()]
            
            # 1. தேவையற்ற ஹெடர்களை நீக்குதல் (Volume, Journal Name)
            ignore_keywords = ['volume', 'issue', 'issn', 'mijmr', 'international journal']
            start_idx = 0
            for i, line in enumerate(lines[:4]):
                if any(kw in line.lower() for kw in ignore_keywords):
                    start_idx = i + 1
                    
            # 2. "Abstract" எங்குள்ளது என்று தேடுதல்
            abstract_idx = len(lines)
            for i, line in enumerate(lines):
                if line.lower() == 'abstract' or line.lower().startswith('abstract'):
                    abstract_idx = i
                    break
                    
            # 3. தலைப்பு மற்றும் பெயர்களைப் பிரித்தெடுத்தல்
            target_lines = lines[start_idx:abstract_idx]
            if not target_lines: return "Title Not Found", ["Name Not Found"], ""
            
            title_lines = []
            author_lines = []
            author_found = False
            
            # ஆசிரியரைக் கண்டுபிடிக்க உதவும் வார்த்தைகள்
            designation_kw = ['professor', 'scholar', 'student', 'dept', 'department', 'college', 'university', 'institute', 'research', 'dr.', 'mr.', 'ms.']
            
            for line in target_lines:
                if not author_found:
                    # இந்த வரியில் ஆசிரியர்/பதவிக்கான வார்த்தைகள் உள்ளதா எனப் பார்த்தல்
                    if any(kw in line.lower() for kw in designation_kw):
                        author_found = True
                        author_lines.append(line)
                    else:
                        title_lines.append(line) # இல்லையென்றால் அது தலைப்பு
                else:
                    author_lines.append(line)
                    
            # கண்டுபிடிக்க முடியவில்லை என்றால், கடைசி வரியை மட்டும் பெயராக எடுப்பது
            if not author_found and len(target_lines) > 1:
                title_lines = target_lines[:-1]
                author_lines = [target_lines[-1]]
                
            # தலைப்பை முழுமையாக இணைத்தல்
            title = " ".join(title_lines)
            
            # 4. பல ஆசிரியர்களைக் கண்டுபிடிக்கும் புதிய லாஜிக் (New Logic for Multiple Authors)
            author_text = ""
            # பதவிகளைக் குறிக்கும் வார்த்தைகள் (இங்கு வந்தால் பெயர் முடிந்துவிட்டது என்று அர்த்தம்)
            affiliation_kw = ['professor', 'scholar', 'student', 'dept', 'department', 'college', 'university', 'institute', 'research']
            
            for idx, al in enumerate(author_lines):
                if any(kw in al.lower() for kw in affiliation_kw):
                    if idx == 0:
                        # ஒரே வரியில் பெயரும் பதவியும் இருந்தால் கமாவுக்கு முன் உள்ளதை மட்டும் எடுக்க
                        author_text = al.split(',')[0]
                    break
                else:
                    author_text += " " + al
                    
            if not author_text and author_lines:
                author_text = author_lines[0].split(',')[0]
                
            # '&', 'and', அல்லது ',' (கமா) இருந்தால் பெயர்களைத் தனித்தனியாகப் பிரிப்பது
            authors_list = [a.strip() for a in re.split(r'\band\b|&|,', author_text) if a.strip() and len(a.strip()) > 2]
            
            # 5. தேதியை எடுப்பது
            date_match = re.search(r'\b\d{1,2}[-/thstndrd\s]+\w+[-/\s]+\d{2,4}\b', text)
            date = date_match.group(0) if date_match else datetime.today().strftime('%d-%m-%Y')
            
            return title, authors_list, date
    except Exception as e:
        return "Error", ["Error"], ""

if template_file and font_file and uploaded_pdfs:
    extracted_data = []
    
    for pdf_file in uploaded_pdfs:
        title, authors_list, date = clean_pdf_text(pdf_file)
        
        # பிரித்தெடுக்கப்பட்ட ஒவ்வொரு ஆசிரியருக்கும் தனித்தனி வரி (Row) உருவாக்கப்படும்
        for author in authors_list:
            extracted_data.append({
                "File Name": pdf_file.name, 
                "Name": author, 
                "Title": title, 
                "Volume": "1", 
                "Issue": "1", 
                "DOI": "", 
                "Date": date
            })

    df = pd.DataFrame(extracted_data)
    
    st.markdown("### ⚠️ சரிபார்க்கவும் (Verify & Edit):")
    edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)
    
    if st.button("🚀 Generate 4K Certificates"):
        with st.spinner('4K தரத்தில் சான்றிதழ்கள் தயாராகி வருகின்றன...'):
            template_bytes = template_file.getvalue()
            font_bytes = font_file.getvalue()
            
            for index, row in edited_df.iterrows():
                
                # இமேஜை ஓபன் செய்து 4K (3840px) அளவுக்கு உயர்த்துதல் (Upscaling)
                img = Image.open(io.BytesIO(template_bytes))
                if img.mode == 'RGBA':
                    img = img.convert('RGB')
                
                # 4K Scale அளவீடு
                scale_factor = 3840 / img.width
                new_height = int(img.height * scale_factor)
                img = img.resize((3840, new_height), Image.Resampling.LANCZOS)
                
                draw = ImageDraw.Draw(img)
                
                # அளவுகளையும் 4K-க்கு ஏற்ப மாற்றுதல்
                f_name = ImageFont.truetype(io.BytesIO(font_bytes), int(name_size * scale_factor))
                f_text = ImageFont.truetype(io.BytesIO(font_bytes), int(text_size * scale_factor))
                
                sy_name = name_y * scale_factor
                sy_title = title_y * scale_factor
                sx_doi = doi_x * scale_factor
                sy_doi = doi_y * scale_factor
                sx_date = date_x * scale_factor
                sy_date = date_y * scale_factor
                
                author_name = str(row['Name'])
                title = str(row['Title']).upper() # தலைப்பு முழுவதும் Capital-ல் வரும்
                vol = str(row['Volume'])
                issue = str(row['Issue'])
                doi = str(row['DOI'])
                date = str(row['Date'])
                
                def draw_centered(y_pos, text, font, color, is_bold=False):
                    bbox = draw.textbbox((0, 0), text, font=font)
                    text_width = bbox[2] - bbox[0]
                    x_pos = (img.width - text_width) / 2
                    
                    if is_bold:
                        # போல்ட் ஆக அச்சிட stroke_width பயன்படுத்துகிறோம்
                        draw.text((x_pos, y_pos), text, font=font, fill=color, stroke_width=int(2*scale_factor), stroke_fill=color)
                    else:
                        draw.text((x_pos, y_pos), text, font=font, fill=color)
                        
                    return y_pos + (bbox[3] - bbox[1])
                    
                # 1. பெயரை அச்சிடுதல்
                draw_centered(sy_name, author_name, f_name, "#00796B")
                
                # 2. பாராக்ராப்பை 3 பகுதியாக அச்சிடுதல் (தலைப்பு மட்டும் போல்ட்)
                current_y = sy_title
                current_y = draw_centered(current_y, "For the successful publication of the research paper titled", f_text, "black") + int(15 * scale_factor)
                
                # தலைப்பை உடைத்து போல்ட் (Bold) ஆக அச்சிடுதல்
                wrapped_title = textwrap.wrap(title, width=wrap_width - 10)
                for t_line in wrapped_title:
                    current_y = draw_centered(current_y, f'"{t_line}"', f_text, "black", is_bold=True) + int(15 * scale_factor)
                    
                # மீதமுள்ள வாசகங்கள்
                current_y = draw_centered(current_y, f"in Volume {vol}, Issue {issue}. This work has been rigorously peer-", f_text, "black") + int(10 * scale_factor)
                draw_centered(current_y, "reviewed and published under the guidelines of academic excellence.", f_text, "black")
                
                # 3. DOI மற்றும் Date அச்சிடுதல்
                if doi:
                    draw.text((sx_doi, sy_doi), doi, font=f_text, fill="black")
                draw.text((sx_date, sy_date), date, font=f_text, fill="black")
                
                # 4. திரையில் காட்டுவது மற்றும் 4K JPG ஆக டவுன்லோட் செய்யும் பட்டன்
                st.image(img, caption=f"{author_name} - Certificate (4K)", use_container_width=True)
                
                img_bytes = io.BytesIO()
                img.save(img_bytes, format="JPEG", quality=100, subsampling=0)
                
                st.download_button(
                    label=f"📥 Download {author_name} Certificate (4K JPG)",
                    data=img_bytes.getvalue(),
                    file_name=f"{author_name}_MIJMR_Certificate.jpg",
                    mime="image/jpeg",
                    key=f"download_{index}"
                )
                
            st.success("✅ 4K சான்றிதழ்கள் தயார்! கீழே தரவிறக்கம் செய்துகொள்ளவும்.")
else:
    st.info("👈 இடதுபுறம் Blank Image, Font மற்றும் நடுவில் PDF ஃபைல்களை அப்லோட் செய்யவும்.")
