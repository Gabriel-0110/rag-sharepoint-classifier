import os
from docx import Document
import fitz           # PyMuPDF
from PIL import Image
import pytesseract

def extract_text(path):
    ext = path.lower().split('.')[-1]
    if ext == 'pdf':
        doc = fitz.open(path)
        text = ''
        for page in doc:
            page_text = page.get_text().strip()
            if page_text:
                text += page_text + '\\n'
            else:
                pix = page.get_pixmap()
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                text += pytesseract.image_to_string(img) + '\\n'
        return text
    elif ext in ('docx',):
        doc = Document(path)
        return '\\n'.join(p.text for p in doc.paragraphs)
    else:
        return pytesseract.image_to_string(Image.open(path))

if __name__ == '__main__':
    # pick the most recent download
    dl_dir = os.path.join(os.path.dirname(__file__), 'downloads')
    files = [f for f in os.listdir(dl_dir) if os.path.isfile(os.path.join(dl_dir, f))]
    if not files:
        print('No files in downloads/')
        exit()
    latest = max(files, key=lambda f: os.path.getctime(os.path.join(dl_dir, f)))
    path = os.path.join(dl_dir, latest)
    print(f'Extracting from: {path}\\n')
    txt = extract_text(path)
    print(txt[:1000])
