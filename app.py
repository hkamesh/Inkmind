from flask import Flask, render_template, request, redirect, url_for
import fitz  
import pytesseract
from pdf2image import convert_from_path
import tempfile
import os
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lex_rank import LexRankSummarizer
import yake

app = Flask(__name__)

def extract_text_from_pdf(pdf_path):
    output_text = ""
    try:
        doc = fitz.open(pdf_path)
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text = page.get_text().strip()
            if text:
                output_text += f"\n--- Page {page_num + 1} (Text) ---\n{text}\n"
            else:
                images = convert_from_path(pdf_path, first_page=page_num + 1, last_page=page_num + 1)
                ocr_text = pytesseract.image_to_string(images[0], lang="eng")
                output_text += f"\n--- Page {page_num + 1} (OCR) ---\n{ocr_text.strip()}\n"
        doc.close()
        return output_text.strip() if output_text.strip() else "⚠️ No content found."
    except Exception as e:
        return f"❌ Error extracting text: {str(e)}"

def summarize_text(text, sentences=3):
    try:
        parser = PlaintextParser.from_string(text, Tokenizer("english"))
        summarizer = LexRankSummarizer()
        summary = summarizer(parser.document, sentences)
        return " ".join(str(s) for s in summary)
    except:
        return "⚠️ Summary generation failed."

def extract_keywords(text, top_n=10):
    try:
        kw_extractor = yake.KeywordExtractor(n=1, top=top_n)
        keywords = kw_extractor.extract_keywords(text)
        return [kw[0] for kw in keywords]
    except:
        return ["⚠️ Keyword extraction failed."]

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        uploaded_file = request.files["pdf_file"]
        do_summary = "summary" in request.form
        do_keywords = "keywords" in request.form

        if uploaded_file.filename != "":
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                file_path = tmp.name
                uploaded_file.save(file_path)

            full_text = extract_text_from_pdf(file_path)
            summary = summarize_text(full_text) if do_summary else "Summary not requested."
            keywords = extract_keywords(full_text) if do_keywords else []

            os.unlink(file_path)

            return render_template("result.html", text=full_text, summary=summary, keywords=keywords)

    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
