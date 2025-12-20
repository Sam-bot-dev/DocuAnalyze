from flask import Flask, render_template, request, jsonify
import os
from werkzeug.utils import secure_filename
from transformers import pipeline

# Load once at startup
summary_model = pipeline(
    "summarization",
    model="facebook/bart-large-cnn",
    tokenizer="facebook/bart-large-cnn"
)



app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploads"
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
from reportlab.pdfgen import canvas
from io import BytesIO
from flask import send_file



@app.route("/api/export-pdf")
def export_pdf():
    if len(uploaded_files) == 0:
        return "No files uploaded", 400

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer)

    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(50, 800, "DocuAnalyze - Final Report")

    # Score
    pdf.setFont("Helvetica", 14)
    pdf.drawString(50, 760, f"Score: 92")

    pdf.drawString(50, 730, "Issues:")
    y = 700
    for issue in [
        "High Severity Issue - Wrong date",
        "Medium Severity Issue - Tone",
    ]:
        pdf.drawString(70, y, f"- {issue}")
        y -= 30

    pdf.save()
    buffer.seek(0)

    return send_file(buffer, as_attachment=True,
                     download_name="report.pdf",
                     mimetype="application/pdf")

uploaded_files = []
original_text = {}
modified_text = {}

# Dummy text extractor (replace with real PDF/DOCX reader later)
def extract_text(file_path):
    try:
        with open(file_path, "r") as f:
            return f.read()
    except:
        return "Sample extracted text from " + os.path.basename(file_path)


# Dummy AI modifier (replace with real LLM later)
def modify_text(text):
    return text.replace(".", ". (modified)")


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

    files = request.files.getlist("files[]")
    if len(files) == 0:
        files = request.files.getlist("files")

    if len(files) == 0:
        return jsonify({"error": "No files uploaded"}), 400

    for file in files:
        filename = secure_filename(file.filename)
        path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(path)

        uploaded_files.append(filename)

        # Extract text
        text = extract_text(path)
        original_text[filename] = text

        # Create modified version
        modified = modify_text(text)
        modified_text[filename] = modified

    return jsonify({"status": "success", "files": uploaded_files})

def transformer_summarize(text):
    if not text.strip():
        return "No readable content found."

    # BART cannot take extremely long texts at once (limit ~1024 tokens)
    # So we chunk the text safely
    max_chunk_size = 1024
    chunks = []

    words = text.split()
    current_chunk = []

    for word in words:
        current_chunk.append(word)
        if len(current_chunk) >= max_chunk_size:
            chunks.append(" ".join(current_chunk))
            current_chunk = []

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    summaries = []
    for chunk in chunks:
        try:
            out = summary_model(
                chunk,
                max_length=180,
                min_length=60,
                do_sample=False
            )[0]['summary_text']
            summaries.append(out)
        except:
            summaries.append(chunk[:300])

    # Combine all summary parts into one paragraph
    return " ".join(summaries)
# ----------------------------
# API — SUMMARIES
# ----------------------------
@app.route("/api/summaries")
def api_summaries():
    data = []

    for fname in uploaded_files:
        text = original_text.get(fname, "")

        # Generate AI summary using Transformers
        paragraph = transformer_summarize(text)

        data.append({
            "filename": fname,
            "agent": "BART Transformer",
            "summary": paragraph,
            "tags": ["AI Summary", "Transformers", "Paragraph"]
        })

    return jsonify(data)





# ----------------------------
# API — COMPARISON
# ----------------------------
@app.route("/api/comparison")
def api_comparison():

    if len(uploaded_files) == 0:
        return jsonify({"error": "No uploaded files"}), 400

    # ALWAYS compare original vs modified of the FIRST FILE
    fname = uploaded_files[0]

    left_text = original_text.get(fname, "")
    right_text = modified_text.get(fname, "")

    sections = [
        {
            "title": "Full Document",
            "left": left_text,
            "right": right_text,
            "diffs": [
                {
                    "left": ".",
                    "right": ". (modified)"
                }
            ]
        }
    ]

    return jsonify({
        "fileA": fname,
        "fileB": fname + " (Modified)",
        "versionA": "Original",
        "versionB": "AI Updated",
        "stats": {
            "matches": max(1, len(left_text.split()) - 3),
            "differences": 3
        },
        "sections": sections
    })

@app.route("/api/discrepancy")
def api_discrepancy():
    if len(uploaded_files) == 0:
        return jsonify({"error": "No files uploaded"}), 400

    # Work with first file
    fname = uploaded_files[0]

    original = original_text.get(fname, "")
    modified = modified_text.get(fname, "")

    if not original or not modified:
        return jsonify({"error": "Missing text data"}), 400

    issues = []

    # Detect basic differences (dummy logic—replace with AI later)
    if original != modified:
        issues.append({
            "title": "Text Changed",
            "severity": "medium",
            "category": "content",
            "original": original[:120] + "...",
            "suggested": modified[:120] + "...",
            "page": 1,
            "bbox": [0.10, 0.20, 0.80, 0.26]
        })

    # Example: detect added "(modified)" keyword
    if "(modified)" in modified:
        issues.append({
            "title": "AI Modification Applied",
            "severity": "low",
            "category": "automatic-change",
            "original": "No AI changes",
            "suggested": "Added AI modifications",
            "page": 1,
            "bbox": [0.15, 0.35, 0.70, 0.42]
        })

    return jsonify({
        "document": fname,
        "total": len(issues),
        "pages": 1,
        "issues": issues
    })
# ---------------------------------
# API: Score (Step 4)
# ---------------------------------
@app.route("/api/score")
def api_score():
    if len(uploaded_files) == 0:
        return jsonify({"error": "No files uploaded"}), 400

    fname = uploaded_files[0]

    return jsonify({
        "document": fname,
        "score": 92,
        "severity": {
            "high": 1,
            "medium": 3,
            "low": 8
        },
        "breakdown": [85, 90, 80, 95, 88],
        "issues": [
            {
                "category": "Tone",
                "severity": "medium",
                "description": "Aggressive wording in Section 2.3",
                "page": 3
            },
            {
                "category": "Factual",
                "severity": "high",
                "description": "Wrong date in Section 1.2",
                "page": 3
            }
        ]
    })

# ----------------------------
# RUN
# ----------------------------
if __name__ == "__main__":
    app.run(debug=True)
