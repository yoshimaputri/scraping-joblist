# ===========================================================
# [ SCRAPING JOB LISTING from JobKorea ]
# 
# Author: Yoshima Putri
# GitHub: https://github.com/yoshimaputri
# If you are interested in more projects or repositories, 
# feel free to visit the GitHub link above.
# 
# This Program is only scrap the official job list by company
# Does not include Headhunter job posting
# ===========================================================
from flask import Flask, jsonify, request, Response
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
import time
import json
import logging

app = Flask('JOBKOREA_SCRAP')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
file_handler = logging.FileHandler('scrap.log', mode='a', encoding='utf-8')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logging.getLogger().addHandler(file_handler)

def scrape_jobs(searchjob, max_get):
    ## @EXAMPLE
    # searchjob = "Product Designer"
    # max_get = 30
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)
    wait = WebDriverWait(driver, 10)
    
    job_search_url = f'https://www.jobkorea.co.kr/Search/?stext={searchjob}'
    driver.get(job_search_url) 
    time.sleep(1)  # Let the page load
    # to see what we can scrap or not --> jobkorea.co.kr/robots.txt

    job_count = len(driver.find_elements(By.CLASS_NAME, 'list-item'))
    if max_get < job_count:
        job_count = max_get
        
    logging.info(f'[INIT...] Getting top {job_count} JOBS')
    jobs_listing = []
    total_filtered_jobs = 0

    def go_to_next_page():
        try:
            next_button = driver.find_element(By.CLASS_NAME, 'button-next')
            if next_button:
                next_button.click()
                time.sleep(2)
                return True
        except NoSuchElementException:
            logging.warn("No more pages found or next button not found.")
            return False
        
    def get_article(id):
        job = None
        try:
            job = driver.find_element(By.CSS_SELECTOR, f"article.list-item[data-listno='{id}']")
        except Exception as e:
            job = None
        return job

    # Iterate through job postings and scrape relevant data
    for idx in range(1, job_count+1):
        job = get_article(idx)
        while job is None:
            if go_to_next_page():
                job = get_article(idx)
            else: break
        info = job.get_attribute('data-gainfo')

        try:
            data_info = json.loads(info)
            title = data_info['dimension45']
            company = data_info['dimension48']
            location = data_info['dimension46']
            corp_section = job.find_element(By.CLASS_NAME, 'list-section-corp')
            link = corp_section.find_element(By.TAG_NAME, 'a').get_attribute('href')
            corp_web, job_details, due_date, check = '', '', '', False

            driver.get(link)
            time.sleep(2)
            try:
                corp_web = driver.find_element(By.CLASS_NAME, 'devCoHomepageLink').get_attribute('href')
                try:
                    dt_elements = driver.find_element(By.CLASS_NAME, 'date').find_elements(By.TAG_NAME, 'dt')
                    dd_elements = driver.find_element(By.CLASS_NAME, 'date').find_elements(By.TAG_NAME, 'dd')
                    for i, dt in enumerate(dt_elements):
                        if '마감일' in dt.text:
                            due_date = dd_elements[i].text
                except Exception as e:
                    due_date = 'always open'

                try:
                    driver.switch_to.frame('gib_frame')
                    check = driver.find_element(By.CLASS_NAME, 'recruitment-items')
                except Exception as e:
                    logging.error(f"[Error No Job Description, might be poster/img/multiple job advertisement.]")

                if check:
                    job_details = check.text

            except Exception as e:
                logging.error(f"[Error Job Details] Company Web doesn't exist (direct recruit by Headhunting) or can't get job details.")

            if job_details: # Only crawl data that publicly shared via job details
                total_filtered_jobs += 1
                job_info = {
                    "Job Title": title,
                    "Company": company,
                    "Location": location,
                    "Job Link": link,
                    "Corp Web": corp_web,
                    "Job Details": job_details,  # Save first 50 characters of job details
                    "Due Date": due_date
                }
                # Append the dictionary to the jobs_data list
                jobs_listing.append(job_info)

                logging.info(f"======== Job Information {total_filtered_jobs} ======")
                logging.info(f"Job Title: {title}")
                logging.info(f"Company: {company}")
                logging.info(f"Location: {location}")
                logging.info(f"Job Link: {link}")
                logging.info(f"Corp Web: {corp_web}")
                logging.info(f"Job Details: (available)")
                logging.info(f"Due Date: {due_date}")
                logging.info("="*40)

            driver.back()

        except Exception as e:
            logging.error(f"[Error] {e}")

    # Save into .json file
    file_name = f"jobs_listing_{searchjob.replace(' ','')}.json"
    with open(file_name, 'w', encoding='utf-8') as json_file:
        json.dump(jobs_listing, json_file, ensure_ascii=False, indent=4)
    logging.info(f"Job data successfully saved to {file_name}")
    
    logging.info(f"Total {total_filtered_jobs} Filtered Jobs.")
    driver.quit()

    return jobs_listing

@app.route("/scraping", methods=["GET"])
def scraping():
    try:
        searchjob = request.args.get('search', default='Data Scientist', type=str)
        total = request.args.get('total', default=50, type=int)
        logging.info(f"Received request to scrape jobs: search={searchjob}, total={total}")

        scraped_data = scrape_jobs(searchjob, total)

        return Response(json.dumps({"status": "success", "data": scraped_data}, ensure_ascii=False),
                        content_type='application/json; charset=utf-8')
    except Exception as e:
        logging.error(f"Error during scraping: {e}")
        return Response(json.dumps({"status": "success", "message": str(e)}, ensure_ascii=False),
                        content_type='application/json; charset=utf-8'), 500
    
if __name__ == '__main__':
    app.run(debug=True)