from flask import Flask, render_template, request, send_file
import tempfile, os
import pytesseract
from pdf2image import convert_from_path
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lex_rank import LexRankSummarizer
import yake
import pdfplumber
import nltk
from fpdf import FPDF
from docx import Document

nltk.download('punkt')

app = Flask(__name__)

def extract_text_from_pdf(pdf_path):
    output_text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages, start=1):
                txt = page.extract_text()
                if txt and txt.strip():
                    output_text += f"\n--- Page {i} ---\n{txt.strip()}\n"
                else:
                    # fallback to OCR
                    images = convert_from_path(pdf_path, first_page=i, last_page=i)
                    ocr = pytesseract.image_to_string(images[0], lang="eng")
                    output_text += f"\n--- Page {i} (OCR) ---\n{ocr.strip()}\n"
        return output_text.strip() or "⚠️ No content found."
    except Exception as e:
        return f"❌ Error extracting text: {e}"

def summarize_text(text, sentences=3):
    try:
        parser = PlaintextParser.from_string(text, Tokenizer("english"))
        summary = LexRankSummarizer()(parser.document, sentences)
        return " ".join(str(s) for s in summary)
    except:
        return "⚠️ Summary generation failed."

def extract_keywords(text, top_n=10):
    try:
        kw = yake.KeywordExtractor(n=1, top=top_n).extract_keywords(text)
        return [w for w,_ in kw]
    except:
        return []

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        f = request.files.get("pdf_file")
        if f:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                f.save(tmp.name)
                full = extract_text_from_pdf(tmp.name)
                summary = summarize_text(full) if "summary" in request.form else "Not requested."
                keywords = extract_keywords(full) if "keywords" in request.form else []
            os.unlink(tmp.name)
            return render_template("result.html", text=full, summary=summary, keywords=keywords)
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
