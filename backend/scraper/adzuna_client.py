import os
import requests
import json
import time

from dotenv import load_dotenv
load_dotenv()

APP_ID = os.getenv("ADZUNA_APP_ID")
APP_KEY = os.getenv("ADZUNA_APP_KEY")

BASE_URL = "https://api.adzuna.com/v1/api/jobs/{country}/search/{page}"
COUNTRY = "ch"  # Switzerland


def fetch_page(page):
    url = BASE_URL.format(country=COUNTRY, page=page)

    params = {
        "app_id": APP_ID,
        "app_key": APP_KEY,
        "results_per_page": 50,
        "what": "engineer OR developer",
        "category": "it-jobs"
    }

    r = requests.get(url, params=params)

    print("Request URL:", r.url)
    print("Status Code:", r.status_code)
    print("Response:", r.text)

    r.raise_for_status()
    return r.json()


def normalize_job(job):
    title = job.get("title", "").strip()

    company = ""
    if job.get("company"):
        company = job["company"].get("display_name", "").strip()

    location = ""
    if job.get("location"):
        location = job["location"].get("display_name", "").strip()

    salary_min = job.get("salary_min")
    salary_max = job.get("salary_max")

    salary = ""
    if salary_min and salary_max:
        salary = f"CHF {int(salary_min):,} - {int(salary_max):,}"
    elif salary_min:
        salary = f"CHF {int(salary_min):,}"
    elif salary_max:
        salary = f"CHF {int(salary_max):,}"

    description = job.get("description", "").strip()

    # Adzuna doesn't split req/resp — use description for now
    requirements = description
    responsibilities = ""

    url = job.get("redirect_url", "")

    return {
        "title": title,
        "company": company,
        "location": location,
        "salary": salary,
        "requirements": requirements,
        "responsibilities": responsibilities,
        "url": url,
    }


def fetch_all_jobs():
    all_jobs = []
    page = 1

    while True:
        print(f"Fetching page {page}...")
        data = fetch_page(page)
        results = data.get("results", [])

        if not results:
            break

        for job in results:
            normalized = normalize_job(job)
            all_jobs.append(normalized)

        page += 1
        time.sleep(0.3)
    
    

    return all_jobs


if __name__ == "__main__":
    jobs = fetch_all_jobs()

    print(f"\nTotal jobs fetched: {len(jobs)}")

    with open("jobs.json", "w", encoding="utf-8") as f:
        json.dump(jobs, f, indent=2, ensure_ascii=False)

    print("Saved jobs.json")
