from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
import shutil
import os

from parser import extract_text_from_pdf, extract_text_from_docx, parse_cv_text
from schemas import CVProfile

app = FastAPI(title="JobGenie CV Parser")

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/upload-cv", response_model=CVProfile)
async def upload_cv(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    
    # Save uploaded file
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    
    # Extract text
    if file.filename.endswith(".pdf"):
        text = extract_text_from_pdf(file_path)
    elif file.filename.endswith(".docx"):
        text = extract_text_from_docx(file_path)
    else:
        return JSONResponse(status_code=400, content={"error": "Unsupported file type"})
    
    # Parse CV
    profile_data = parse_cv_text(text)
    
    return profile_data
