from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import os
import shutil
import json
import re
from backend.cv_parser.parser import extract_text_from_pdf, extract_text_from_docx, parse_cv_text_with_llm
from backend.cv_parser.schemas import CVProfile
from backend.scraper.swissdevjobs import scrape_swissdevjobs
from backend.matcher.matcher import llm_match_jobs
from backend.scraper import adzuna_client as adzuna
from backend.scraper import jooble as jooble


UPLOAD_DIR = os.path.join(os.path.dirname(__file__), '../cv_parser/uploads')
CV_PATH = os.path.join(os.path.dirname(__file__), '../cv_parser/cv_parsed.json')
JOBS_PATH = os.path.join(os.path.dirname(__file__), '../scraper/jobs.json')

router = APIRouter()

@router.post("/upload-cv")
async def upload_cv(file: UploadFile = File(...)):
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    if file.filename.endswith(".pdf"):
        text = extract_text_from_pdf(file_path)
    elif file.filename.endswith(".docx"):
        text = extract_text_from_docx(file_path)
    else:
        raise HTTPException(status_code=400, detail="Unsupported file type")
    # Use LLM to parse CV text
    try:
        profile_data = parse_cv_text_with_llm(text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM parsing failed: {e}")
    with open(CV_PATH, "w", encoding="utf-8") as f:
        json.dump(profile_data, f, ensure_ascii=False, indent=2)
    return profile_data

@router.get("/jobs")
def get_jobs(top_n: int = 5):
    if not os.path.exists(CV_PATH):
        raise HTTPException(status_code=404, detail="No CV uploaded.")
    jobs_path = os.path.join(os.path.dirname(__file__), '../scraper/jobs.json')
    if not os.path.exists(jobs_path):
        raise HTTPException(status_code=404, detail="No jobs scraped.")
    with open(CV_PATH, "r", encoding="utf-8") as f:
        cv = json.load(f)
    with open(jobs_path, "r", encoding="utf-8") as f:
        jobs = json.load(f)
    try:
        top_matches = llm_match_jobs(cv, jobs, top_n=top_n)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM job matching failed: {e}")
    return top_matches

@router.post("/fetch-jobs")
def fetch_jobs(source: str, keywords: str, location: str, country: str = None):
    """
    Fetch jobs from a specified source: 'adzuna' or 'jooble'.
    - keywords: search terms
    - location: city/country
    - country: optional filter to ensure jobs are from this country
    """
    try:
        if source.lower() == "adzuna":
            jobs = adzuna.fetch_all_jobs()  # Adzuna can also be updated to accept keywords/location
        elif source.lower() == "jooble":
            jobs = jooble.fetch_jobs_jooble(keywords, location, country)
        else:
            raise HTTPException(status_code=400, detail="Invalid source. Choose 'adzuna' or 'jooble'.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Job fetching failed: {e}")

    with open(JOBS_PATH, "w", encoding="utf-8") as f:
        json.dump(jobs, f, indent=2, ensure_ascii=False)

    return {"message": "Jobs fetched successfully", "count": len(jobs)}