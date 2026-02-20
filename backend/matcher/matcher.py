from collections import Counter
import re
from google import genai
import os
import json

client = genai.Client()

MATCH_SCHEMA = '''
{
    "title": "string (Job title)",
    "company": "string (Company name)",
    "location": "string or null (Job location)",
    "salary": "string or null (Salary info)",
    "summary": "string (One-sentence summary)",
    "score": "number (Relevance score, 0-100)",
    "url": "string (Job URL)"
}
'''

def llm_match_jobs(cv_json, jobs_json, top_n=5):
    prompt = f"""
You are a job matching assistant. Given the following candidate CV (as JSON) and a list of job descriptions (as JSON), analyze and select the top {top_n} most relevant jobs for this candidate.

For each top job, output a JSON object with the following schema:
{MATCH_SCHEMA}

The "score" should reflect how well the job matches the candidate (higher is better, 0-100). The "summary" should be a one-sentence explanation of the match.

CV JSON:
{json.dumps(cv_json, ensure_ascii=False, indent=2)}

Jobs JSON:
{json.dumps(jobs_json, ensure_ascii=False, indent=2)}

Output only a JSON array of the top {top_n} matches.
"""
    response = client.models.generate_content(
        model="gemini-3-flash-preview", contents=prompt
    )
    content = response.text.strip()
    if content.startswith("```"):
        content = content.split("\n", 1)[1].rsplit("\n", 1)[0]
    try:
        return json.loads(content)
    except Exception as e:
        raise ValueError(f"Failed to parse LLM response as JSON: {e}\nRaw response: {response.text}")

if __name__ == "__main__":
    with open("cv_parsed.json", "r", encoding="utf-8") as f:
        cv = json.load(f)
    with open("jobs.json", "r", encoding="utf-8") as f:
        jobs = json.load(f)
    top_matches = llm_match_jobs(cv, jobs)
    print(json.dumps(top_matches, indent=2, ensure_ascii=False))
