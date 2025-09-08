from flask import Flask, render_template, request
import PyPDF2
import os
import tempfile
import re
import yake
import math
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)

# -------------------------------
# PDF text extraction
# -------------------------------
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

# -------------------------------
# Simple sentence splitter
# -------------------------------
def split_sentences(text):
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s for s in sentences if s]

# -------------------------------
# Custom LexRank-like summarizer
# -------------------------------
def summarize_text(text, sentences=3):
    try:
        sents = split_sentences(text)
        if not sents:
            return "⚠️ No summary generated."
        if len(sents) <= sentences:
            return " ".join(sents)

        # TF-IDF for sentence embeddings
        vectorizer = TfidfVectorizer().fit_transform(sents)
        sim_matrix = cosine_similarity(vectorizer)

        # Degree centrality (approx LexRank)
        scores = sim_matrix.sum(axis=1)

        ranked_sentences = [s for _, s in sorted(zip(scores, sents), reverse=True)]
        summary = " ".join(ranked_sentences[:sentences])
        return summary
    except Exception as e:
        return f"❌ Summary error: {str(e)}"

# -------------------------------
# Keyword extraction with YAKE
# -------------------------------
def extract_keywords(text, top_n=10):
    try:
        kw_extractor = yake.KeywordExtractor(n=1, top=top_n)
        keywords = kw_extractor.extract_keywords(text)
        return [kw[0] for kw in keywords] if keywords else ["⚠️ No keywords found."]
    except Exception as e:
        return [f"❌ Keyword error: {str(e)}"]

# -------------------------------
# Flask routes
# -------------------------------
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

            os.unlink(file_path)  # remove temp file

            return render_template("result.html", text=full_text, summary=summary, keywords=keywords)

    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
