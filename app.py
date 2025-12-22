from flask import Flask, render_template, request, jsonify, send_file
import os
from werkzeug.utils import secure_filename
from reportlab.pdfgen import canvas
from io import BytesIO
import re

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploads"
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

uploaded_files = []
original_text = {}
modified_text = {}

# ----------------------------
# SIMPLE TEXT EXTRACTOR (SAFE)
# ----------------------------
def extract_text(file_path):
    try:
        with open(file_path, "r", errors="ignore") as f:
            return f.read()
    except:
        return "This document contains structured or scanned content."

# ----------------------------
# LIGHTWEIGHT EXTRACTIVE SUMMARY
# ----------------------------
def summarize_text(text, max_sentences=5):
    if not text.strip():
        return "No readable content found."

    # Clean text
    text = re.sub(r"\s+", " ", text)
    sentences = re.split(r'(?<=[.!?]) +', text)

    # Take first meaningful sentences
    summary = sentences[:max_sentences]
    return " ".join(summary)

# ----------------------------
# MOCK AI MODIFICATION
# ----------------------------
def modify_text(text):
    return text.replace(".", ". (reviewed)")

# ----------------------------
# FRONTEND ROUTES
# ----------------------------
@app.route("/")
def upload_page():
    return render_template("upload.html")

@app.route("/summaries")
def summaries_page():
    return render_template("summaries.html")

@app.route("/comparison")
def comparison_page():
    return render_template("comparison.html")

@app.route("/discrepancy")
def discrepancy_page():
    return render_template("discrepancy.html")

@app.route("/score")
def score_page():
    return render_template("score.html")

# ----------------------------
# API — UPLOAD
# ----------------------------
@app.route("/api/upload", methods=["POST"])
def api_upload():
    global uploaded_files, original_text, modified_text
    uploaded_files = []
    original_text = {}
    modified_text = {}

    files = request.files.getlist("files[]") or request.files.getlist("files")
    if not files:
        return jsonify({"error": "No files uploaded"}), 400

    for file in files:
        filename = secure_filename(file.filename)
        path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(path)

        uploaded_files.append(filename)

        text = extract_text(path)
        original_text[filename] = text
        modified_text[filename] = modify_text(text)

    return jsonify({"status": "success", "files": uploaded_files})

# ----------------------------
# API — SUMMARIES
# ----------------------------
@app.route("/api/summaries")
def api_summaries():
    data = []

    for fname in uploaded_files:
        text = original_text.get(fname, "")
        paragraph = summarize_text(text)

        data.append({
            "filename": fname,
            "agent": "Lightweight NLP Engine",
            "summary": paragraph,
            "tags": ["Fast", "Extractive", "Render-Safe"]
        })

    return jsonify(data)

# ----------------------------
# API — COMPARISON
# ----------------------------
@app.route("/api/comparison")
def api_comparison():
    if not uploaded_files:
        return jsonify({"error": "No uploaded files"}), 400

    fname = uploaded_files[0]

    return jsonify({
        "fileA": fname,
        "fileB": fname + " (Reviewed)",
        "versionA": "Original",
        "versionB": "AI Reviewed",
        "stats": {
            "matches": 120,
            "differences": 5
        },
        "sections": [
            {
                "title": "Full Document",
                "left": original_text.get(fname, ""),
                "right": modified_text.get(fname, ""),
                "diffs": [{"left": ".", "right": ". (reviewed)"}]
            }
        ]
    })

# ----------------------------
# API — DISCREPANCY
# ----------------------------
@app.route("/api/discrepancy")
def api_discrepancy():
    if not uploaded_files:
        return jsonify({"error": "No files uploaded"}), 400

    fname = uploaded_files[0]

    return jsonify({
        "document": fname,
        "total": 2,
        "pages": 1,
        "issues": [
            {
                "title": "Text Updated",
                "severity": "medium",
                "category": "content",
                "original": "Original sentence",
                "suggested": "Reviewed sentence",
                "page": 1,
                "bbox": [0.1, 0.2, 0.8, 0.3]
            }
        ]
    })

# ----------------------------
# API — SCORE
# ----------------------------
@app.route("/api/score")
def api_score():
    if not uploaded_files:
        return jsonify({"error": "No files uploaded"}), 400

    return jsonify({
        "score": 92,
        "severity": {"high": 1, "medium": 3, "low": 8},
        "breakdown": [85, 90, 80, 95, 88],
        "issues": [
            {"category": "Tone", "severity": "medium", "description": "Harsh wording", "page": 2}
        ]
    })

# ----------------------------
# API — EXPORT PDF
# ----------------------------
@app.route("/api/export-pdf")
def export_pdf():
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer)
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(50, 800, "DocuAnalyze - Final Report")
    pdf.setFont("Helvetica", 14)
    pdf.drawString(50, 760, "Score: 92")
    pdf.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="report.pdf")

# ----------------------------
# RUN
# ----------------------------
if __name__ == "__main__":
    app.run()
