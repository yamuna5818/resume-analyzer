import os
import re
from flask import Flask, render_template, request, jsonify
from pypdf import PdfReader
from docx import Document

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5 MB

SKILLS = ["python", "java", "javascript", "typescript", "c++", "sql", "html", "css", "react",
          "node.js", "express", "flask", "django", "fastapi", "mongodb", "mysql", "postgresql",
          "bootstrap", "tailwind", "git", "github", "docker", "aws", "rest api", "jwt",
          "machine learning", "nlp", "pandas", "numpy", "scikit-learn", "redux", "testing",
          "agile", "linux", "figma", "ci/cd"]

def extract_text(f):
    name = f.filename.lower()
    if name.endswith(".pdf"):
        return " ".join((p.extract_text() or "") for p in PdfReader(f).pages)
    if name.endswith(".docx"):
        return " ".join(p.text for p in Document(f).paragraphs)
    if name.endswith(".txt"):
        return f.read().decode("utf-8", errors="ignore")
    raise ValueError("Only PDF, DOCX or TXT files are supported")

def find_skills(text):
    text = text.lower()
    return [s for s in SKILLS
            if re.search(r"(?<![a-z0-9+#])" + re.escape(s) + r"(?![a-z0-9+#])", text)]

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    f, jd = request.files.get("resume"), request.form.get("jd", "")
    if not f or not f.filename:
        return jsonify(error="Please upload a resume file"), 400
    try:
        text = extract_text(f)
    except ValueError as e:
        return jsonify(error=str(e)), 400
    except Exception:
        return jsonify(error="Could not read this file"), 400

    resume_skills, jd_skills = find_skills(text), find_skills(jd)
    matched = [s for s in jd_skills if s in resume_skills]
    missing = [s for s in jd_skills if s not in resume_skills]
    score = round(len(matched) / len(jd_skills) * 100) if jd_skills else 0

    tips, words = [], len(text.split())
    if missing:
        tips.append("Add these skills if you have them: " + ", ".join(missing))
    if not re.search(r"\d+%|\d+\+|\b\d{2,}\b", text):
        tips.append("Add numbers (users, % improvement, count) to show impact")
    if not re.search(r"[\w.]+@[\w.]+\.\w+", text):
        tips.append("Add a professional email address")
    if words < 200:
        tips.append("Resume looks short - add more project details")
    elif words > 900:
        tips.append("Resume is long - keep it to one page")
    if not jd.strip():
        tips.append("Paste a job description to get a match score")
    if not tips:
        tips.append("Great resume! Tailor keywords for each job")

    return jsonify(score=score, resume_skills=resume_skills, matched=matched,
                   missing=missing, words=words, tips=tips)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
