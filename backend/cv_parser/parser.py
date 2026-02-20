from dotenv import load_dotenv
load_dotenv()

import re
import pdfplumber
import docx
from email_validator import validate_email, EmailNotValidError
from google import genai
import os
import json

# The client gets the API key from GEMINI_API_KEY environment variable
client = genai.Client()

# The schema for the LLM to follow
CV_SCHEMA = '''{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "CV Schema",
  "description": "Schema for structured CV data extracted from a resume",
  "type": "object",
  "properties": {
    "name": {"type": "string"},
    "email": {"type": "string", "format": "email"},
    "phone": {"type": "string"},
    "location": {"type": ["string", "null"]},
    "skills": {"type": "array", "items": {"type": "string"}},
    "experience_years": {"type": ["number", "null"]},
    "experience": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "title": {"type": "string"},
          "company": {"type": "string"},
          "location": {"type": "string"},
          "start_date": {"type": "string", "format": "date"},
          "end_date": {"type": ["string", "null"], "format": "date"},
          "description": {"type": "string"}
        },
        "required": ["title", "company"]
      }
    },
    "education": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "degree": {"type": "string"},
          "field": {"type": "string"},
          "institution": {"type": "string"},
          "start_date": {"type": "string", "format": "date"},
          "end_date": {"type": ["string", "null"], "format": "date"}
        },
        "required": ["degree", "institution"]
      }
    },
    "languages": {"type": "array", "items": {"type": "string"}},
    "certifications": {"type": "array", "items": {"type": "string"}}
  },
  "required": ["name", "email", "skills"]
}'''

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

def parse_cv_text_with_llm(cv_text: str) -> dict:
    prompt = f"""
Extract structured metadata from this CV. Output only valid JSON matching this schema:
{CV_SCHEMA}
CV:
{cv_text}
"""
    response = client.models.generate_content(
        model="gemini-3-flash-preview", contents=prompt
    )
    # Try to extract JSON from the response
    try:
        content = response.text.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1].rsplit("\n", 1)[0]
        return json.loads(content)
    except Exception as e:
        raise ValueError(f"Failed to parse LLM response as JSON: {e}\nRaw response: {response.text}")
