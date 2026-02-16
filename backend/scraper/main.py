from fastapi import FastAPI
from swissdevjobs import scrape_jobs
from schemas import JobListing

app = FastAPI(title="JobGenie Scraper")

@app.get("/jobs", response_model=list[JobListing])
async def get_jobs(limit: int = 10):
    """
    Return top N jobs from swissdevjobs.ch
    """
    jobs = scrape_jobs(limit)
    return jobs
