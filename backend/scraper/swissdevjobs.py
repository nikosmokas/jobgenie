import asyncio
from playwright.async_api import async_playwright
import json

BASE_URL = "https://www.swissdevjobs.ch/jobs"


async def scroll_until_loaded(page):
    previous_count = 0
    while True:
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(2000)
        current_count = await page.eval_on_selector_all(
            "#job-postings-inner-wrapper li",
            "els => els.length"
        )
        if current_count == previous_count:
            break
        previous_count = current_count


async def scrape_swissdevjobs():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto(BASE_URL, timeout=60000)

        print("Scrolling jobs...")
        await scroll_until_loaded(page)

        # grab all job links from job cards
        job_card_divs = await page.query_selector_all("div[data-test='card-body']")
        job_links = []
        for card in job_card_divs:
            anchors = await card.query_selector_all("a[href*='/jobs/']")
            for anchor in anchors:
                # Check if anchor contains job name header div
                job_header = await anchor.query_selector("div.jobteaser-name-header")
                href = await anchor.get_attribute("href")
                if job_header and href and href.startswith("/jobs/"):
                    job_links.append(BASE_URL + href[len("/jobs"):])
        job_links = list(set(job_links))  # remove duplicates
        print(f"Found {len(job_links)} jobs, scraping all...")

        jobs = []

        for i, url in enumerate(job_links):
            print(f"\nScraping job {i+1}/{len(job_links)}...")
            try:
                # Only select job card divs when on the listing page
                clicked = False
                await page.goto(BASE_URL, timeout=60000)
                await scroll_until_loaded(page)
                job_card_divs = await page.query_selector_all("div[data-test='card-body']")
                for card in job_card_divs:
                    anchors = await card.query_selector_all("a[href*='/jobs/']")
                    for anchor in anchors:
                        job_header = await anchor.query_selector("div.jobteaser-name-header")
                        href = await anchor.get_attribute("href")
                        if job_header and href and (BASE_URL + href[len("/jobs"):]) == url:
                            await anchor.click()
                            await page.wait_for_timeout(1000)
                            clicked = True
                            break
                    if clicked:
                        break
                if not clicked:
                    await page.goto(url, timeout=60000)
                    await page.wait_for_timeout(1000)

                title = await page.text_content("h1") or ""

                # Company name
                try:
                    company = await page.text_content("div[aria-label='hiring organization']") or ""
                except:
                    company = ""

                # Location
                try:
                    location = await page.text_content("span.icon-map-marker") or ""
                except:
                    location = ""

                # Salary
                try:
                    salary = await page.text_content("div.salary-info") or ""
                except:
                    salary = ""

                # Requirements
                requirements = ""
                try:
                    req_header = await page.query_selector("h2.section-title:has-text('Requirements')")
                    if req_header:
                        req_box = await req_header.evaluate_handle("el => el.closest('.job-details-section-box')")
                        if req_box:
                            req_divs = await req_box.query_selector_all("div.format-with-white-space")
                            req_texts = []
                            for div in req_divs:
                                text = await div.inner_text()
                                req_texts.append(text)
                            requirements = "\n\n".join(req_texts)
                except Exception as e:
                    print(f"Requirements extraction failed: {e}")
                    requirements = ""

                # Responsibilities
                responsibilities = ""
                try:
                    resp_header = await page.query_selector("h2.section-title:has-text('Responsibilities')")
                    if resp_header:
                        resp_box = await resp_header.evaluate_handle("el => el.closest('.job-details-section-box')")
                        if resp_box:
                            resp_divs = await resp_box.query_selector_all("div.format-with-white-space")
                            resp_texts = []
                            for div in resp_divs:
                                text = await div.inner_text()
                                resp_texts.append(text)
                            responsibilities = "\n\n".join(resp_texts)
                except Exception as e:
                    print(f"Responsibilities extraction failed: {e}")
                    responsibilities = ""

                jobs.append({
                    "title": title.strip(),
                    "company": company.strip(),
                    "location": location.strip(),
                    "salary": salary.strip(),
                    "requirements": requirements.strip(),
                    "responsibilities": responsibilities.strip(),
                    "url": url,
                })

                print(f"Scraped job: {title.strip()}")

            except Exception as e:
                print(f"Error scraping {url}: {e}")
                continue

            # go back to main listing for next job
            await page.goto(BASE_URL, timeout=60000)
            await scroll_until_loaded(page)  # ensure all jobs still loaded

        await browser.close()
        return jobs


if __name__ == "__main__":
    jobs = asyncio.run(scrape_swissdevjobs())
    print("\nScraped jobs:")
    print(jobs)

    with open("jobs.json", "w", encoding="utf-8") as f:
        json.dump(jobs, f, indent=2, ensure_ascii=False)

    print("Saved jobs.json")
