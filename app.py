from flask import Flask, render_template, request
import PyPDF2
import os
import tempfile
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lex_rank import LexRankSummarizer
import yake
import nltk

# Ensure NLTK data is available (safe check)
for resource in ["punkt", "punkt_tab", "stopwords"]:
    try:
        nltk.data.find(f"tokenizers/{resource}")
    except LookupError:
        nltk.download(resource)

app = Flask(__name__)

# ------------------ PDF TEXT EXTRACTION ------------------
def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        with open(pdf_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for i, page in enumerate(reader.pages):
                page_text = page.extract_text() or ""
                text += f"\n--- Page {i+1} ---\n{page_text.strip()}\n"
        return text.strip() if text.strip() else "⚠️ No readable text found in PDF."
    except Exception as e:
        return f"❌ Error extracting text: {str(e)}"

# ------------------ SUMMARIZATION ------------------
def summarize_text(text, sentences=5):
    try:
        parser = PlaintextParser.from_string(text, Tokenizer("english"))
        summarizer = LexRankSummarizer()
        summary = summarizer(parser.document, sentences)

        # Return bullet point sentences
        summary_sentences = [str(s).strip() for s in summary if str(s).strip()]
        return summary_sentences if summary_sentences else ["⚠️ No summary generated."]
    except Exception as e:
        return [f"❌ Summary error: {str(e)}"]

# ------------------ KEYWORDS ------------------
def extract_keywords(text, top_n=10):
    try:
        kw_extractor = yake.KeywordExtractor(n=1, top=top_n)
        keywords = kw_extractor.extract_keywords(text)
        return [kw[0] for kw in keywords] if keywords else ["⚠️ No keywords found."]
    except Exception as e:
        return [f"❌ Keyword error: {str(e)}"]

# ------------------ ROUTES ------------------
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        uploaded_file = request.files["pdf_file"]

        if uploaded_file.filename != "":
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                file_path = tmp.name
                uploaded_file.save(file_path)

            full_text = extract_text_from_pdf(file_path)
            summary = summarize_text(full_text)
            keywords = extract_keywords(full_text)

            os.unlink(file_path)  

            return render_template("result.html", text=full_text, summary=summary, keywords=keywords)

    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
