import re
import pdfplumber
import docx
from email_validator import validate_email, EmailNotValidError

# -----------------------------
# File extraction functions
# -----------------------------

def extract_text_from_pdf(file_path: str) -> str:
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text

def extract_text_from_docx(file_path: str) -> str:
    doc = docx.Document(file_path)
    return "\n".join([p.text for p in doc.paragraphs])

# -----------------------------
# CV parsing functions
# -----------------------------

# Predefined skill list (expand later)
SKILL_KEYWORDS = [
    "Python", "FastAPI", "Docker", "Kubernetes", "React",
    "SQL", "PostgreSQL", "MongoDB", "AWS", "Git", "CI/CD"
]

EDUCATION_KEYWORDS = ["BSc", "MSc", "PhD", "Bachelor", "Master"]

SWISS_CITIES = ["Zurich", "Bern", "Geneva", "Basel", "Lausanne"]

def extract_email(text: str) -> str | None:
    emails = re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)
    for email in emails:
        try:
            valid = validate_email(email)
            return valid.email
        except EmailNotValidError:
            continue
    return None

def extract_skills(text: str) -> list[str]:
    skills_found = []
    for skill in SKILL_KEYWORDS:
        if re.search(rf"\b{re.escape(skill)}\b", text, re.IGNORECASE):
            skills_found.append(skill)
    return skills_found

def extract_education(text: str) -> list[str]:
    return [edu for edu in EDUCATION_KEYWORDS if re.search(rf"\b{edu}\b", text)]

def extract_experience_years(text: str) -> int | None:
    match = re.search(r"(\d+)\+?\s+years?", text, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None

def extract_location(text: str) -> str | None:
    for city in SWISS_CITIES:
        if re.search(rf"\b{city}\b", text, re.IGNORECASE):
            return city
    return None

def extract_name(text: str) -> str | None:
    # Simple heuristic: first non-empty line that doesn't look like email
    lines = text.strip().split("\n")
    for line in lines:
        line = line.strip()
        if line and not extract_email(line):
            return line
    return None

# -----------------------------
# Main parser function
# -----------------------------

def parse_cv_text(text: str) -> dict:
    """
    Parses raw CV text and returns structured profile info.
    """
    profile = {
        "name": extract_name(text),
        "email": extract_email(text),
        "location": extract_location(text),
        "skills": extract_skills(text),
        "experience_years": extract_experience_years(text),
        "education": extract_education(text)
    }
    return profile
