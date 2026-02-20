import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

JOOBLE_API_KEY = os.getenv("JOOBLE_API_KEY")
BASE_URL = f"https://jooble.org/api/{JOOBLE_API_KEY}"


def fetch_jobs_jooble(keywords: str, location: str, country: str = None):
    """
    Fetch jobs from Jooble API.
    - keywords: string, search terms
    - location: city/country string for Jooble search
    - country: optional, filter results to this country (e.g., "Luxembourg")
    """
    headers = {"Content-Type": "application/json"}
    payload = {
        "keywords": keywords,
        "location": location,
        "page": 1
    }

    all_jobs = []

    while True:
        print(f"Fetching Jooble page {payload['page']}...")
        r = requests.post(BASE_URL, headers=headers, data=json.dumps(payload))
        print("Status code:", r.status_code)

        if r.status_code == 403:
            raise Exception("403 Forbidden — check your API key and make sure it’s activated")

        r.raise_for_status()
        data = r.json()
        jobs = data.get("jobs", [])

        if not jobs:
            break

        for job in jobs:
            normalized = {
                "title": job.get("title", "").strip(),
                "company": job.get("company", "").strip(),
                "location": job.get("location", "").strip(),
                "salary": job.get("salary", "").strip() if job.get("salary") else None,
                "requirements": job.get("requirements", "").strip(),
                "responsibilities": job.get("responsibilities", "").strip(),
                "url": job.get("link", "").strip(),
            }

            # Optional country filter
            if country:
                if country.lower() not in normalized["location"].lower():
                    continue

            all_jobs.append(normalized)

        payload["page"] += 1

    return all_jobs


if __name__ == "__main__":
    # Example dynamic input
    keywords_input = input("Enter keywords: ")
    location_input = input("Enter location: ")
    country_input = input("Filter by country (optional): ")

    jobs = fetch_jobs_jooble(keywords_input, location_input, country_input)
    print(f"Fetched {len(jobs)} jobs")

    with open("jobs.json", "w", encoding="utf-8") as f:
        json.dump(jobs, f, indent=2, ensure_ascii=False)
